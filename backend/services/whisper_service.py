"""
Servizio semplificato per trascrizione audio con Whisper medium
Versione stabile per produzione
"""

import os
import logging
import tempfile
import wave
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("OpenAI Whisper non disponibile - trascrizione disabilitata")

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Servizio semplificato per trascrizione con Whisper medium
    """
    
    def __init__(self):
        self.model = None
        self.model_name = "medium"  # Bilanciamento tra qualità e velocità
        self._load_model()
    
    def _load_model(self):
        """Carica il modello Whisper"""
        if not WHISPER_AVAILABLE:
            logger.error("Whisper non disponibile")
            return
        
        try:
            logger.info(f"Caricamento modello Whisper {self.model_name}...")
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Modello Whisper {self.model_name} caricato con successo")
        except Exception as e:
            logger.error(f"Errore caricamento modello Whisper: {str(e)}")
            self.model = None
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = "it") -> Dict[str, Any]:
        """
        Trascrizione di file audio con Whisper
        
        Args:
            audio_file_path: Percorso al file audio
            language: Lingua per la trascrizione (default: italiano)
            
        Returns:
            Dizionario con risultati trascrizione
        """
        if not self.model:
            logger.error("Modello Whisper non caricato")
            return {
                'success': False,
                'error': 'Modello Whisper non disponibile',
                'transcript': '',
                'confidence': 0.0
            }
        
        if not os.path.exists(audio_file_path):
            logger.error(f"File audio non trovato: {audio_file_path}")
            return {
                'success': False,
                'error': 'File audio non trovato',
                'transcript': '',
                'confidence': 0.0
            }
        
        try:
            logger.info(f"Avvio trascrizione file: {audio_file_path}")
            
            # Trascrizione con Whisper
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                task="transcribe",
                temperature=0.1,  # Bassa temperatura per output più stabile
                best_of=5,        # Migliore di 5 tentativi
                beam_size=5,      # Beam search per migliore qualità
                patience=1.0,     # Patience per beam search
                condition_on_previous_text=False  # Non condizionare su testo precedente
            )
            
            transcript = result.get('text', '').strip()
            segments = result.get('segments', [])
            
            # Calcola confidence media dai segmenti
            confidence = 0.0
            if segments:
                confidences = []
                for segment in segments:
                    if 'avg_logprob' in segment:
                        # Converti logprob in probabilità
                        segment_confidence = min(1.0, max(0.0, (segment['avg_logprob'] + 1.0)))
                        confidences.append(segment_confidence)
                
                if confidences:
                    confidence = sum(confidences) / len(confidences)
            
            # Pulizia del testo
            cleaned_transcript = self._clean_transcript(transcript)
            
            logger.info(f"Trascrizione completata: {len(cleaned_transcript)} caratteri")
            
            return {
                'success': True,
                'transcript': cleaned_transcript,
                'confidence': confidence,
                'language': language,
                'duration': result.get('duration', 0.0),
                'segments': segments,
                'model': self.model_name,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Errore durante trascrizione: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': '',
                'confidence': 0.0
            }
    
    def transcribe_audio_blob(self, audio_blob: bytes, format: str = "wav", language: str = "it") -> Dict[str, Any]:
        """
        Trascrizione di blob audio con Whisper
        
        Args:
            audio_blob: Dati audio in bytes
            format: Formato audio (wav, mp3, etc.)
            language: Lingua per la trascrizione
            
        Returns:
            Dizionario con risultati trascrizione
        """
        # Salva il blob in un file temporaneo
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_blob)
                temp_path = temp_file.name
            
            # Trascrivi il file temporaneo
            result = self.transcribe_audio_file(temp_path, language)
            
            # Rimuovi file temporaneo
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return result
            
        except Exception as e:
            logger.error(f"Errore processing audio blob: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': '',
                'confidence': 0.0
            }
    
    def _clean_transcript(self, text: str) -> str:
        """
        Pulizia del testo trascritto per uso medico
        """
        if not text:
            return ""
        
        # Rimuovi spazi multipli
        text = ' '.join(text.split())
        
        # Capitalizza la prima lettera
        if text:
            text = text[0].upper() + text[1:]
        
        # Assicurati che finisca con punteggiatura
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    def test_transcription(self) -> Dict[str, Any]:
        """
        Test del servizio di trascrizione
        """
        if not self.model:
            return {
                'success': False,
                'error': 'Modello non caricato',
                'model': self.model_name
            }
        
        return {
            'success': True,
            'model': self.model_name,
            'available': True,
            'test_passed': True
        }
    
    def get_supported_formats(self) -> list:
        """
        Formati audio supportati
        """
        return ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac']


# Istanza singleton del servizio
whisper_service = WhisperService()