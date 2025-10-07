"""
Servizio per trascrizione real-time usando Whisper large-v3-turbo
Basato sull'implementazione HuggingFace Spaces
"""

import os
import json
import logging
import asyncio
import websockets
import tempfile
import wave
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from threading import Thread
import time

try:
    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
    import numpy as np
    import librosa
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers non disponibile - trascrizione real-time disabilitata")

try:
    import webrtcvad
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("PyAudio/WebRTCVAD non disponibili - acquisizione audio real-time disabilitata")

logger = logging.getLogger(__name__)


class WhisperRealtimeService:
    """
    Servizio per trascrizione real-time con Whisper large-v3-turbo
    """
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.pipe = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model_id = "openai/whisper-large-v3-turbo"
        
        # Configurazione audio
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        
        # VAD per rilevamento voce
        self.vad = webrtcvad.Vad(2) if AUDIO_AVAILABLE else None  # Aggressività media
        
        # Buffer per audio chunks
        self.audio_buffer = []
        self.is_recording = False
        self.is_processing = False
        
        # Callbacks
        self.on_partial_transcript = None
        self.on_final_transcript = None
        self.on_error = None
        
        self._load_model()
    
    def _load_model(self):
        """Carica il modello Whisper large-v3-turbo"""
        if not TRANSFORMERS_AVAILABLE:
            logger.error("Transformers non disponibile - impossibile caricare Whisper")
            return
        
        try:
            logger.info(f"Caricamento Whisper {self.model_id} su {self.device}")
            
            # Carica il modello
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                attn_implementation="flash_attention_2" if torch.cuda.is_available() else "eager"
            )
            self.model.to(self.device)
            
            # Carica il processor
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            
            # Crea pipeline
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16,
                return_timestamps=True,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
            
            logger.info("Modello Whisper caricato con successo")
            
        except Exception as e:
            logger.error(f"Errore caricamento modello Whisper: {e}")
            self.model = None
            self.pipe = None
    
    def is_available(self) -> bool:
        """Verifica se il servizio è disponibile"""
        return (TRANSFORMERS_AVAILABLE and 
                AUDIO_AVAILABLE and 
                self.pipe is not None)
    
    def start_realtime_transcription(self, 
                                   on_partial: Callable[[str], None] = None,
                                   on_final: Callable[[str, dict], None] = None,
                                   on_error: Callable[[str], None] = None):
        """
        Avvia trascrizione real-time da microfono
        
        Args:
            on_partial: Callback per trascrizione parziale
            on_final: Callback per trascrizione finale
            on_error: Callback per errori
        """
        if not self.is_available():
            if on_error:
                on_error("Servizio trascrizione real-time non disponibile")
            return
        
        self.on_partial_transcript = on_partial
        self.on_final_transcript = on_final
        self.on_error = on_error
        
        # Avvia thread per acquisizione audio
        self.is_recording = True
        self.audio_buffer = []
        
        audio_thread = Thread(target=self._audio_capture_loop, daemon=True)
        audio_thread.start()
        
        # Avvia thread per processing
        processing_thread = Thread(target=self._processing_loop, daemon=True)
        processing_thread.start()
        
        logger.info("Trascrizione real-time avviata")
    
    def stop_realtime_transcription(self) -> dict:
        """
        Ferma la trascrizione real-time e restituisce risultato finale
        
        Returns:
            Dizionario con trascrizione completa e metadati
        """
        self.is_recording = False
        self.is_processing = False
        
        # Processa il buffer finale
        final_transcript = self._process_final_buffer()
        
        logger.info("Trascrizione real-time fermata")
        return final_transcript
    
    def transcribe_audio_file(self, file_path: str, language: str = "it") -> dict:
        """
        Trascrivi un file audio preregistrato
        
        Args:
            file_path: Path del file audio
            language: Lingua (default: italiano)
            
        Returns:
            Dizionario con trascrizione e metadati
        """
        if not self.is_available():
            return {"error": "Servizio trascrizione non disponibile"}
        
        try:
            logger.info(f"Trascrizione file: {file_path}")
            
            # Carica audio
            audio_data, sample_rate = librosa.load(file_path, sr=16000, mono=True)
            
            # Trascrivi
            result = self.pipe(
                audio_data,
                generate_kwargs={"language": language, "task": "transcribe"}
            )
            
            # Processa risultato
            transcript_data = {
                "text": result["text"].strip(),
                "chunks": result.get("chunks", []),
                "language": language,
                "duration": len(audio_data) / sample_rate,
                "sample_rate": sample_rate,
                "model": self.model_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Applica normalizzazioni per il dominio medico
            transcript_data["text"] = self._normalize_medical_text(transcript_data["text"])
            
            logger.info(f"Trascrizione completata: {len(transcript_data['text'])} caratteri")
            return transcript_data
            
        except Exception as e:
            logger.error(f"Errore trascrizione file: {e}")
            return {"error": str(e)}
    
    def _audio_capture_loop(self):
        """Loop per acquisizione audio dal microfono"""
        if not AUDIO_AVAILABLE:
            return
        
        try:
            # Inizializza PyAudio
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Acquisizione audio avviata")
            
            while self.is_recording:
                # Leggi chunk audio
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Converti in float32 normalizzato
                audio_float = audio_chunk.astype(np.float32) / 32768.0
                
                # Aggiungi al buffer
                self.audio_buffer.extend(audio_float)
                
                time.sleep(0.01)  # Piccola pausa
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            logger.info("Acquisizione audio fermata")
            
        except Exception as e:
            logger.error(f"Errore acquisizione audio: {e}")
            if self.on_error:
                self.on_error(f"Errore acquisizione audio: {e}")
    
    def _processing_loop(self):
        """Loop per processing trascrizione in tempo reale"""
        buffer_size = self.sample_rate * 3  # Buffer di 3 secondi
        overlap_size = self.sample_rate * 1  # Overlap di 1 secondo
        
        self.is_processing = True
        
        while self.is_processing:
            try:
                # Aspetta che il buffer abbia abbastanza dati
                if len(self.audio_buffer) < buffer_size:
                    time.sleep(0.1)
                    continue
                
                # Estrai chunk da processare
                audio_chunk = np.array(self.audio_buffer[:buffer_size])
                
                # Rimuovi dal buffer (mantenendo overlap)
                self.audio_buffer = self.audio_buffer[buffer_size - overlap_size:]
                
                # Trascrivi chunk
                result = self.pipe(
                    audio_chunk,
                    generate_kwargs={"language": "it", "task": "transcribe"}
                )
                
                partial_text = result["text"].strip()
                
                if partial_text and self.on_partial_transcript:
                    # Normalizza testo medico
                    normalized_text = self._normalize_medical_text(partial_text)
                    self.on_partial_transcript(normalized_text)
                
            except Exception as e:
                logger.error(f"Errore processing real-time: {e}")
                if self.on_error:
                    self.on_error(f"Errore processing: {e}")
                time.sleep(0.5)
    
    def _process_final_buffer(self) -> dict:
        """Processa il buffer finale per trascrizione completa"""
        if not self.audio_buffer:
            return {"text": "", "duration": 0}
        
        try:
            # Converti buffer in numpy array
            final_audio = np.array(self.audio_buffer)
            
            # Trascrizione finale
            result = self.pipe(
                final_audio,
                generate_kwargs={"language": "it", "task": "transcribe"}
            )
            
            final_text = result["text"].strip()
            normalized_text = self._normalize_medical_text(final_text)
            
            final_result = {
                "text": normalized_text,
                "raw_text": final_text,
                "chunks": result.get("chunks", []),
                "duration": len(final_audio) / self.sample_rate,
                "sample_rate": self.sample_rate,
                "model": self.model_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self.on_final_transcript:
                self.on_final_transcript(normalized_text, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Errore processing finale: {e}")
            return {"error": str(e)}
    
    def _normalize_medical_text(self, text: str) -> str:
        """
        Normalizza il testo per il dominio medico
        Ripresa dalla logica del Project 2
        """
        import re
        
        # Normalizzazioni unità di misura mediche
        text = re.sub(r"\\bmilligrams?\\s+per\\s+deciliter\\b", "mg/dl", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bmilligrammi?\\s+per\\s+decilitro\\b", "mg/dl", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bmg?\\s+per\\s+decilitro\\b", "mg/dl", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bmillimeters?\\s+of\\s+mercury\\b", "mmHg", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bmillimetri?\\s+di\\s+merc[ur]io\\b", "mmHg", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bmm?\\s+di\\s+merc[ur]io\\b", "mmHg", text, flags=re.IGNORECASE)
        
        # Normalizzazioni pressione arteriosa
        text = re.sub(r"\\b(\\d+)\\s+over\\s+(\\d+)\\b", r"\\1/\\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\\b(\\d+)\\s+su\\s+(\\d+)\\b", r"\\1/\\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\\b(\\d+)\\s+slash\\s+(\\d+)\\b", r"\\1/\\2", text, flags=re.IGNORECASE)
        
        # Normalizzazioni frequenza cardiaca
        text = re.sub(r"\\bbeats?\\s+per\\s+minute\\b", "bpm", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bbattiti?\\s+al\\s+minuto\\b", "bpm", text, flags=re.IGNORECASE)
        
        # Normalizzazioni temperatura
        text = re.sub(r"\\bdegrees?\\s+celsius\\b", "°C", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bgradi?\\s+celsius\\b", "°C", text, flags=re.IGNORECASE)
        
        # Normalizzazioni percentuali
        text = re.sub(r"\\b(\\d+)\\s+percent\\b", r"\\1%", text, flags=re.IGNORECASE)
        text = re.sub(r"\\bper\\s+cento\\b", "%", text, flags=re.IGNORECASE)
        
        return text.strip()


# Istanza singleton del servizio
whisper_realtime_service = WhisperRealtimeService()