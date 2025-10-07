"""
Servizi per trascrizione audio utilizzando Whisper
"""
import os
import tempfile
import re
from typing import Tuple, Optional
from django.core.files.base import ContentFile
from core.models import AudioTranscript, Encounter
import logging

logger = logging.getLogger(__name__)

def check_dependencies():
    """
    Verifica che tutte le dipendenze necessarie siano disponibili
    """
    missing_deps = []
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import torch
    except ImportError:
        missing_deps.append("torch")
    
    try:
        import whisper
    except ImportError:
        missing_deps.append("openai-whisper")
    
    try:
        import librosa
    except ImportError:
        missing_deps.append("librosa")
    
    if missing_deps:
        deps_str = ", ".join(missing_deps)
        raise ImportError(f"Dipendenze mancanti: {deps_str}. Installa con: pip install {deps_str}")
    
    return True

class TranscriptionService:
    """
    Servizio per la trascrizione audio usando Whisper
    """
    
    def __init__(self, model_size: str = "base"):
        """
        Inizializza il servizio con un modello Whisper
        """
        self.model_size = model_size
        self.model = None
        
    def _load_model(self):
        """
        Carica il modello Whisper solo quando necessario (lazy loading)
        """
        if self.model is None:
            try:
                # Verifica prima tutte le dipendenze
                check_dependencies()
                
                # Importa le dipendenze necessarie
                import numpy as np
                import torch
                import whisper
                
                self.model = whisper.load_model(self.model_size)
                logger.info(f"Modello Whisper '{self.model_size}' caricato con successo")
            except ImportError as e:
                logger.error(f"Dipendenza mancante: {e}")
                raise ImportError(f"Libreria richiesta non trovata: {e}")
            except Exception as e:
                logger.error(f"Errore nel caricamento del modello Whisper: {e}")
                raise

    def transcribe_audio_file(self, audio_file, encounter_id: str, language: str = "it") -> AudioTranscript:
        """
        Trascrivi un file audio e salva il risultato nel database
        
        Args:
            audio_file: File audio da trascrivere
            encounter_id: ID dell'encounter associato
            language: Lingua del contenuto audio
            
        Returns:
            AudioTranscript: Oggetto trascrizione salvato nel database
        """
        try:
            # Ottieni l'encounter
            encounter = Encounter.objects.get(encounter_id=encounter_id)
            
            # Crea record di trascrizione
            transcript = AudioTranscript.objects.create(
                encounter=encounter,
                status='transcribing',
                language=language
            )
            
            # Salva il file audio
            transcript.audio_file.save(
                f"audio_{transcript.transcript_id}.mp3",
                ContentFile(audio_file.read()),
                save=True
            )
            
            # Trascrivi l'audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                # Copia il contenuto del file
                audio_file.seek(0)  # Reset del puntatore
                temp_file.write(audio_file.read())
                temp_file.flush()
                temp_file_path = temp_file.name
            
            try:
                # Carica librosa solo quando necessario
                try:
                    import numpy as np
                    import librosa
                except ImportError as e:
                    logger.error(f"Dipendenza mancante: {e}")
                    raise ImportError(f"Libreria richiesta non trovata: {e}")
                
                # Carica e preprocessa l'audio
                audio, sr = librosa.load(temp_file_path, sr=16000, mono=True)
                transcript.audio_duration = len(audio) / sr
                
                # Carica il modello se non già fatto
                self._load_model()
                
                # Trascrizione con Whisper
                result = self.model.transcribe(audio, language=language)
                
                # Post-processing del testo
                cleaned_text = self._clean_transcript_text(result["text"])
                
                # Aggiorna il record
                transcript.transcript_text = cleaned_text
                transcript.confidence_score = self._calculate_confidence(result)
                transcript.status = 'completed'
                transcript.save()
                
                logger.info(f"Trascrizione completata per transcript {transcript.transcript_id}")
                return transcript
                
            finally:
                # Pulisci il file temporaneo assicurandoti che sia chiuso
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Impossibile rimuovere file temporaneo {temp_file_path}: {cleanup_error}")
                
        except Encounter.DoesNotExist:
            logger.error(f"Encounter {encounter_id} non trovato")
            raise ValueError(f"Encounter {encounter_id} non esistente")
        except Exception as e:
            logger.error(f"Errore durante la trascrizione: {e}")
            if 'transcript' in locals():
                transcript.status = 'error'
                transcript.error_message = str(e)
                transcript.save()
            raise

    def _clean_transcript_text(self, text: str) -> str:
        """
        Pulisce e normalizza il testo trascritto per terminologia medica
        """
        # Regex per terminologia medica come nel progetto di riferimento
        text = re.sub(r"\bmilligrams?\s+per\s+deciliter\b", "mg/dl", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmilligrammi?\s+per\s+decilitro\b", "mg/dl", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmg?\s+per\s+decilitro\b", "mg/dl", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmillimeters?\s+of\s+mercury\b", "mmHg", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmillimetri?\s+di\s+merc[ur]io\b", "mmHg", text, flags=re.IGNORECASE)
        text = re.sub(r"\bmm?\s+di\s+merc[ur]io\b", "mmHg", text, flags=re.IGNORECASE)

        text = re.sub(r"\b(\d+)\s+over\s+(\d+)\b", r"\1/\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(\d+)\s+su\s+(\d+)\b", r"\1/\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(\d+)\s+slash\s+(\d+)\b", r"\1/\2", text, flags=re.IGNORECASE)

        text = re.sub(r"\bbeats?\s+per\s+minute\b", "bpm", text, flags=re.IGNORECASE)
        text = re.sub(r"\bbattiti?\s+al\s+minuto\b", "bpm", text, flags=re.IGNORECASE)

        text = re.sub(r"\bdegrees?\s+celsius\b", "°C", text, flags=re.IGNORECASE)
        text = re.sub(r"\bgradi?\s+celsius\b", "°C", text, flags=re.IGNORECASE)

        text = re.sub(r"\b(\d+)\s+percent\b", r"\1%", text, flags=re.IGNORECASE)
        text = re.sub(r"\bper\s+cento\b", "%", text, flags=re.IGNORECASE)

        return text.strip()

    def _calculate_confidence(self, whisper_result) -> float:
        """
        Calcola un punteggio di confidenza basato sui risultati di Whisper
        """
        # Whisper non fornisce direttamente un confidence score,
        # quindi usiamo alcune euristiche
        if 'segments' in whisper_result:
            # Media dei confidence scores dei segmenti se disponibili
            scores = []
            for segment in whisper_result['segments']:
                if 'avg_logprob' in segment:
                    # Converte log probability in una scala 0-1
                    confidence = max(0, min(1, (segment['avg_logprob'] + 1) / 1))
                    scores.append(confidence)
            
            if scores:
                return sum(scores) / len(scores)
        
        # Fallback: confidence basata sulla lunghezza del testo
        text_length = len(whisper_result.get('text', ''))
        if text_length > 100:
            return 0.8
        elif text_length > 50:
            return 0.6
        else:
            return 0.4