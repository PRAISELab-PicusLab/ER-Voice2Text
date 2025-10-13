"""
Modelli MongoDB per transcript, audio, e clinical data
Utilizza MongoEngine per l'integrazione con Django
"""

from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime
import uuid


class AudioSegment(EmbeddedDocument):
    """
    Segmento audio con timestamp e metadati
    """
    segment_id = fields.StringField(default=lambda: str(uuid.uuid4()))
    start_ms = fields.IntField(required=True, help_text="Timestamp inizio in millisecondi")
    end_ms = fields.IntField(required=True, help_text="Timestamp fine in millisecondi")
    duration_ms = fields.IntField(help_text="Durata segmento in millisecondi")
    file_path = fields.StringField(help_text="Path del file audio segmentato")
    chunk_index = fields.IntField(help_text="Indice del chunk nel flusso")


class TranscriptSegment(EmbeddedDocument):
    """
    Singolo segmento di trascrizione con speaker e confidence
    """
    segment_id = fields.StringField(default=lambda: str(uuid.uuid4()))
    text = fields.StringField(required=True, help_text="Testo trascritto")
    speaker_id = fields.IntField(default=0, help_text="ID speaker (0=medico, 1=paziente, 2=altro)")
    speaker_label = fields.StringField(help_text="Label speaker (Medico, Paziente, Accompagnatore)")
    start_ms = fields.IntField(required=True, help_text="Timestamp inizio in millisecondi")
    end_ms = fields.IntField(required=True, help_text="Timestamp fine in millisecondi")
    confidence = fields.FloatField(min_value=0.0, max_value=1.0, help_text="Confidence score STT")
    language = fields.StringField(default='it', help_text="Lingua rilevata")
    engine = fields.StringField(help_text="Engine STT utilizzato (whisper/azure)")
    tokens = fields.ListField(fields.StringField(), help_text="Tokens individuali")
    
    # Post-processing flags
    is_corrected = fields.BooleanField(default=False, help_text="Testo corretto manualmente")
    original_text = fields.StringField(help_text="Testo originale pre-correzione")


class MedicalPatientData(EmbeddedDocument):
    """
    Dati anagrafici estratti dal testo medico seguendo la struttura del Project 2
    """
    # Anagrafica
    first_name = fields.StringField()
    last_name = fields.StringField()
    codice_fiscale = fields.StringField(max_length=16)
    age = fields.IntField()
    gender = fields.StringField()
    birth_date = fields.StringField()
    birth_place = fields.StringField()
    
    # Contatti e residenza
    residence_city = fields.StringField()
    residence_address = fields.StringField()
    phone = fields.StringField()
    
    # Modalità accesso
    access_mode = fields.StringField()  # Come è arrivato il paziente


class VitalSigns(EmbeddedDocument):
    """
    Parametri vitali estratti dalla trascrizione
    """
    heart_rate = fields.StringField()  # es. "80 bpm"
    blood_pressure = fields.StringField()  # es. "120/80 mmHg"
    temperature = fields.FloatField()  # es. 36.5
    oxygenation = fields.StringField()  # es. "98%"
    blood_glucose = fields.StringField()  # es. "90 mg/dl"


class ClinicalAssessment(EmbeddedDocument):
    """
    Valutazione clinica strutturata
    """
    # Stato fisico
    skin_state = fields.StringField()
    consciousness_state = fields.StringField()
    pupils_state = fields.StringField()
    respiratory_state = fields.StringField()
    
    # Anamnesi e sintomi
    history = fields.StringField()
    medications_taken = fields.StringField()
    symptoms = fields.StringField()
    
    # Valutazione e terapia
    medical_actions = fields.StringField()
    assessment = fields.StringField()
    plan = fields.StringField()
    triage_code = fields.StringField()


class ClinicalData(EmbeddedDocument):
    """
    Dati clinici completi estratti dal transcript
    """
    patient_data = fields.EmbeddedDocumentField(MedicalPatientData)
    vital_signs = fields.EmbeddedDocumentField(VitalSigns)
    clinical_assessment = fields.EmbeddedDocumentField(ClinicalAssessment)
    
    # Metadati estrazione
    extraction_timestamp = fields.DateTimeField(default=datetime.utcnow)
    llm_model_used = fields.StringField()
    confidence_score = fields.FloatField()
    validation_errors = fields.ListField(fields.StringField())
    is_validated = fields.BooleanField(default=False)
    validated_by = fields.StringField()  # username del validatore


class AudioTranscript(Document):
    """
    Documento principale per audio e transcript di un encounter
    """
    # Identificatori
    transcript_id = fields.StringField(default=lambda: str(uuid.uuid4()), unique=True)
    encounter_id = fields.StringField(required=True, help_text="UUID dell'encounter Django")
    patient_id = fields.StringField(required=True, help_text="UUID del paziente Django")
    doctor_id = fields.StringField(required=True, help_text="UUID del medico Django")
    
    # Metadati audio
    audio_file_path = fields.StringField(help_text="Path file audio originale")
    audio_format = fields.StringField(help_text="Formato audio (mp3, wav, webm)")
    audio_duration_ms = fields.IntField(help_text="Durata totale audio in millisecondi")
    audio_size_bytes = fields.IntField(help_text="Dimensione file in bytes")
    sample_rate = fields.IntField(help_text="Sample rate audio")
    channels = fields.IntField(help_text="Numero canali")
    
    # Segmenti audio e transcript
    audio_segments = fields.ListField(fields.EmbeddedDocumentField(AudioSegment))
    transcript_segments = fields.ListField(fields.EmbeddedDocumentField(TranscriptSegment))
    
    # Transcript completo
    full_transcript = fields.StringField(help_text="Trascrizione completa concatenata")
    
    # Dati clinici estratti
    clinical_data = fields.EmbeddedDocumentField(ClinicalData)
    
    # Processing status
    processing_status = fields.StringField(
        choices=['pending', 'transcribing', 'transcribed', 'extracting', 'extracted', 'validated', 'error'],
        default='pending'
    )
    error_message = fields.StringField()
    
    # Versioning
    version = fields.IntField(default=1, help_text="Versione documento")
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    transcription_completed_at = fields.DateTimeField()
    extraction_completed_at = fields.DateTimeField()
    
    meta = {
        'collection': 'audio_transcripts',
        'indexes': [
            'encounter_id',
            'patient_id',
            'doctor_id',
            'processing_status',
            '-created_at',
            ('encounter_id', 'version'),  # Compound index
        ]
    }
    
    def save(self, *args, **kwargs):
        """Override save per aggiornare timestamp"""
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Transcript {self.transcript_id} - Encounter {self.encounter_id}"
    
    @property
    def duration_seconds(self):
        """Durata in secondi"""
        return self.audio_duration_ms / 1000 if self.audio_duration_ms else 0
    
    @property
    def total_segments(self):
        """Numero totale segmenti"""
        return len(self.transcript_segments)
    
    @property
    def average_confidence(self):
        """Confidence media dei segmenti"""
        if not self.transcript_segments:
            return 0.0
        confidences = [seg.confidence for seg in self.transcript_segments if seg.confidence]
        return sum(confidences) / len(confidences) if confidences else 0.0


class ClinicalReport(Document):
    """
    Report clinico finalizzato per generazione PDF
    """
    # Identificatori
    report_id = fields.StringField(default=lambda: str(uuid.uuid4()), unique=True)
    encounter_id = fields.StringField(required=True)
    transcript_id = fields.StringField(required=True)
    
    # Template e contenuto
    template_name = fields.StringField(default='er_standard', help_text="Template PDF utilizzato")
    report_content = fields.DictField(help_text="Contenuto strutturato report")
    
    # Stato finalizzazione
    is_finalized = fields.BooleanField(default=False, help_text="Report finalizzato e immutabile")
    finalized_at = fields.DateTimeField()
    finalized_by = fields.StringField(help_text="ID medico che ha finalizzato")
    
    # File generati
    pdf_file_path = fields.StringField(help_text="Path PDF generato")
    pdf_checksum = fields.StringField(help_text="Checksum PDF per integrità")
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'clinical_reports',
        'indexes': [
            'encounter_id',
            'transcript_id',
            'is_finalized',
            '-created_at',
        ]
    }
    
    def save(self, *args, **kwargs):
        """Override save per aggiornare timestamp"""
        if not self.is_finalized:  # Solo se non finalizzato
            self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Report {self.report_id} - Encounter {self.encounter_id}"