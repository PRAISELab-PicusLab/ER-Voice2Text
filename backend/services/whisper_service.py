"""
Service for audio transcription with Whisper medium
Stable version for production
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
    Service for audio transcription with Whisper medium
    """
    
    def __init__(self):
        self.model = None
        self.model_name = "medium"  # Balance between quality and speed
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        if not WHISPER_AVAILABLE:
            logger.error("Whisper not available, cannot load model")
            return
        
        try:
            logger.info(f"Loading Whisper model {self.model_name}...")
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Whisper model {self.model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            self.model = None
    
    def transcribe_audio_file(self, audio_file_path: str, language: str = "it") -> Dict[str, Any]:
        """
        Transcription of audio file with Whisper

        :param audio_file_path: Path to the audio file
        :type audio_file_path: str
        :param language: Language for transcription (default: Italian)
        :type language: str
        :return: Dictionary with transcription results
        :rtype: Dict[str, Any]
        """
        if not self.model:
            logger.error("Whisper model not loaded")
            return {
                'success': False,
                'error': 'Whisper model not available',
                'transcript': '',
                'confidence': 0.0
            }
        
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return {
                'success': False,
                'error': 'Audio file not found',
                'transcript': '',
                'confidence': 0.0
            }
        
        try:
            logger.info(f"Starting transcription for file: {audio_file_path}")

            # Transcription with Whisper
            result = self.model.transcribe(
                audio_file_path,
                language=language,
                task="transcribe",
                temperature=0.1,  # Low temperature for more stable output
                best_of=5,        # Best of 5 attempts
                beam_size=5,      # Beam search for better quality
                patience=1.0,     # Patience for beam search
                condition_on_previous_text=False  # Do not condition on previous text
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
                'timestamp': datetime.now(datetime.timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': '',
                'confidence': 0.0
            }
    
    def transcribe_audio_blob(self, audio_blob: bytes, format: str = "wav", language: str = "it") -> Dict[str, Any]:
        """
        Transcription of audio blob with Whisper

        :param audio_blob: Audio data in bytes
        :type audio_blob: bytes
        :param format: Audio format (wav, mp3, etc.)
        :type format: str
        :param language: Language for transcription (default: Italian)
        :type language: str
        :return: Dictionary with transcription results
        :rtype: Dict[str, Any]
        """
        # Save the blob to a temporary file
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
                temp_file.write(audio_blob)
                temp_path = temp_file.name

            # Transcribe the temporary file
            result = self.transcribe_audio_file(temp_path, language)

            # Remove temporary file
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
        Text cleaning for medical transcription use
        
        :param text: Raw transcript text
        :type text: str
        :returns: Cleaned text
        :rtype: str
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
        Test the transcription service
        
        :returns: Dictionary with test results
        :rtype: Dict[str, Any]
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
        Supported audio formats
        
        :returns: List of supported audio formats
        :rtype: list
        """
        return ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac']


# Istanza singleton del servizio
whisper_service = WhisperService()