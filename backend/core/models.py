"""
Module for models in the healthcare system
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class Doctor(AbstractUser):
    """
    Model for representing a doctor in the healthcare system.

    Extends the Django User model to support AGID authentication
    and adds fields specific to the medical profession.

    :ivar doctor_id: Unique UUID identifier for the doctor
    :type doctor_id: uuid.UUID
    :ivar specialization: Medical specialization of the doctor
    :type specialization: str
    :ivar department: Department to which the doctor belongs
    :type department: str
    :ivar license_number: Medical license number
    :type license_number: str
    :ivar is_emergency_doctor: Flag for emergency doctor authorization
    :type is_emergency_doctor: bool
    :ivar created_at: Timestamp for record creation
    :type created_at: datetime
    :ivar last_login_at: Timestamp for last login
    :type last_login_at: datetime
    """
    doctor_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    specialization = models.CharField(max_length=100, help_text="Specializzazione medica")
    department = models.CharField(max_length=100, help_text="Reparto di appartenenza")
    license_number = models.CharField(max_length=50, unique=True, help_text="Numero ordine medici")
    is_emergency_doctor = models.BooleanField(default=False, help_text="Abilitato al pronto soccorso")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """
        Meta options for the Doctor model.
        """
        verbose_name = "Medico"
        verbose_name_plural = "Medici"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        """
        String representation of the Doctor model.
        
        :returns: String with doctor's title, name, and specialization
        :rtype: str
        """
        return f"Dr. {self.first_name} {self.last_name} - {self.specialization}"

    def get_full_name(self):
        """
        Returns the full name of the doctor with professional title.

        :returns: Full name formatted with title "Dr."
        :rtype: str
        """
        return f"Dr. {self.first_name} {self.last_name}"


class Patient(models.Model):
    """
    Model for representing a patient with essential demographic and clinical data.

    Contains all the information necessary to uniquely identify a patient
    and manage their basic clinical data within the healthcare system.

    :ivar patient_id: Unique UUID identifier for the patient
    :type patient_id: uuid.UUID
    :ivar first_name: First name of the patient
    :type first_name: str
    :ivar last_name: Last name of the patient
    :type last_name: str
    :ivar date_of_birth: Date of birth of the patient
    :type date_of_birth: date
    :ivar place_of_birth: Place of birth of the patient
    :type place_of_birth: str
    :ivar fiscal_code: Fiscal code of the patient (optional)
    :type fiscal_code: str
    :ivar gender: Gender of the patient ('M', 'F', 'O')
    :type gender: str
    :ivar phone: Phone number of the patient (optional)
    :type phone: str
    :ivar emergency_contact: Emergency contact (optional)
    :type emergency_contact: str
    :ivar weight: Weight of the patient in kg (optional)
    :type weight: float
    :ivar height: Height of the patient in cm (optional)
    :type height: float
    :ivar blood_type: Blood type of the patient (optional)
    :type blood_type: str
    :ivar allergies: Allergies notes of the patient (optional)
    :type allergies: str
    :ivar created_at: Timestamp of record creation
    :type created_at: datetime
    :ivar updated_at: Timestamp of last update
    :type updated_at: datetime
    """
    GENDER_CHOICES = [
        ('M', 'Maschio'),
        ('F', 'Femmina'),
        ('O', 'Altro'),
    ]

    patient_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    first_name = models.CharField(max_length=100, verbose_name="Nome")
    last_name = models.CharField(max_length=100, verbose_name="Cognome")
    date_of_birth = models.DateField(verbose_name="Data di nascita")
    place_of_birth = models.CharField(max_length=100, verbose_name="Luogo di nascita")
    fiscal_code = models.CharField(max_length=16, unique=True, null=True, blank=True, verbose_name="Codice fiscale")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Sesso")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefono")
    emergency_contact = models.CharField(max_length=200, null=True, blank=True, verbose_name="Contatto emergenza")
    
    # Dati clinici di base
    weight = models.FloatField(null=True, blank=True, verbose_name="Peso (kg)")
    height = models.FloatField(null=True, blank=True, verbose_name="Altezza (cm)")
    blood_type = models.CharField(max_length=5, null=True, blank=True, verbose_name="Gruppo sanguigno")
    allergies = models.TextField(null=True, blank=True, verbose_name="Allergie note")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta options for the Patient model.
        """
        verbose_name = "Paziente"
        verbose_name_plural = "Pazienti"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['fiscal_code']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),
        ]

    def __str__(self):
        """
        String representation of the Patient model.
        
        :returns: String with patient's name and fiscal code
        :rtype: str
        """
        return f"{self.first_name} {self.last_name} ({self.fiscal_code})"

    @property
    def age(self):
        """
        Calculate the patient's age in years as of the current date.

        :returns: Patient's age in years
        :rtype: int
        """
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def get_full_name(self):
        """
        Return the full name of the patient.

        :returns: Full name of the patient
        :rtype: str
        """
        return f"{self.first_name} {self.last_name}"


class Encounter(models.Model):
    """
    Encounter model for episodes of care in the Emergency Room
    
    :ivar models.UUIDField encounter_id: Unique UUID identifier for the encounter
    :type encounter_id: uuid.UUID
    :ivar models.ForeignKey patient: Reference to the Patient involved in the encounter
    :type patient: Patient
    :ivar models.ForeignKey doctor: Reference to the Doctor managing the encounter
    :type doctor: Doctor
    :ivar models.DateTimeField admission_time: Timestamp of patient admission
    :type admission_time: datetime
    :ivar models.TextField chief_complaint: Chief complaint reported at admission
    :type chief_complaint: str
    :ivar models.CharField triage_priority: Triage priority code assigned at admission
    :type triage_priority: str
    :ivar models.CharField status: Current status of the encounter
    :type status: str
    :ivar models.DateTimeField discharge_time: Timestamp of patient discharge (optional)
    :type discharge_time: datetime
    :ivar models.DateTimeField created_at: Timestamp of record creation
    :type created_at: datetime
    :ivar models.DateTimeField updated_at: Timestamp of last update
    :type updated_at: datetime
    """
    STATUS_CHOICES = [
        ('in_progress', 'In corso'),
        ('completed', 'Completato'),
        ('cancelled', 'Annullato'),
    ]

    PRIORITY_CHOICES = [
        ('white', 'Codice Bianco'),
        ('green', 'Codice Verde'),
        ('yellow', 'Codice Giallo'),
        ('red', 'Codice Rosso'),
        ('black', 'Codice Nero'),
    ]

    encounter_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='encounters')
    
    # Dati triage
    admission_time = models.DateTimeField(default=timezone.now, verbose_name="Ora di ammissione")
    chief_complaint = models.TextField(verbose_name="Motivo accesso")
    triage_priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, verbose_name="Codice triage")
    
    # Status encounter
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    discharge_time = models.DateTimeField(null=True, blank=True, verbose_name="Ora dimissione")
    
    # Metadati
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta options for the Encounter model.
        """
        verbose_name = "Episodio di cura"
        verbose_name_plural = "Episodi di cura"
        ordering = ['-admission_time']
        indexes = [
            models.Index(fields=['admission_time']),
            models.Index(fields=['status']),
            models.Index(fields=['triage_priority']),
        ]

    def __str__(self):
        """
        String representation of the Encounter model.
        
        :returns: String with encounter ID, patient name, and admission time
        :rtype: str
        """
        return f"Encounter {self.encounter_id} - {self.patient.get_full_name()} ({self.admission_time})"

    @property
    def duration(self):
        """Calculates the duration of the encounter in minutes
        
        :returns: Duration in minutes
        :rtype: float
        """
        if self.discharge_time:
            return (self.discharge_time - self.admission_time).total_seconds() / 60
        return (timezone.now() - self.admission_time).total_seconds() / 60


class AudioTranscript(models.Model):
    """
    Model for audio transcripts of encounters
    
    :ivar models.UUIDField transcript_id: Unique UUID identifier for the transcript
    :type transcript_id: uuid.UUID
    :ivar models.ForeignKey encounter: Reference to the associated Encounter
    :type encounter: Encounter
    :ivar models.FileField audio_file: Uploaded audio file
    :type audio_file: File
    :ivar models.FloatField audio_duration: Duration of the audio in seconds
    :type audio_duration: float
    :ivar models.TextField transcript_text: Transcribed text from the audio
    :type transcript_text: str
    :ivar models.FloatField confidence_score: Confidence score of the transcription
    :type confidence_score: float
    :ivar models.CharField language: Language code of the audio
    :type language: str
    :ivar models.CharField status: Current status of the transcription process
    :type status: str
    :ivar models.TextField error_message: Error message if transcription failed
    :type error_message: str
    :ivar models.DateTimeField created_at: Timestamp of record creation
    :type created_at: datetime
    :ivar models.DateTimeField updated_at: Timestamp of last update
    :type updated_at: datetime
    :ivar models.DateTimeField transcription_completed_at: Timestamp when transcription was completed
    :type transcription_completed_at: datetime
    """
    STATUS_CHOICES = [
        ('pending', 'In attesa'),
        ('transcribing', 'Trascrizione in corso'),
        ('completed', 'Completato'),
        ('error', 'Errore'),
    ]

    transcript_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='transcripts')
    
    # File audio
    audio_file = models.FileField(upload_to='audio/', null=True, blank=True)
    audio_duration = models.FloatField(null=True, blank=True, verbose_name="Durata (secondi)")
    
    # Trascrizione
    transcript_text = models.TextField(blank=True, verbose_name="Testo trascritto")
    confidence_score = models.FloatField(null=True, blank=True, verbose_name="Score di confidenza")
    language = models.CharField(max_length=10, default='it-IT', verbose_name="Lingua")
    
    # Status e metadati
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, verbose_name="Messaggio di errore")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transcription_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """
        Meta options for the AudioTranscript model.
        """
        verbose_name = "Trascrizione Audio"
        verbose_name_plural = "Trascrizioni Audio"
        ordering = ['-created_at']

    def __str__(self):
        """
        String representation of the AudioTranscript model.
        
        :returns: String with transcript ID and associated encounter
        :rtype: str
        """
        return f"Transcript {self.transcript_id} - {self.encounter}"


class ClinicalData(models.Model):
    """
    Model for clinical data extracted from the transcription
    
    :ivar models.OneToOneField transcript: Reference to the associated AudioTranscript
    :type transcript: AudioTranscript
    :ivar models.CharField patient_name: Extracted patient name
    :type patient_name: str
    :ivar models.IntegerField patient_age: Extracted patient age
    :type patient_age: int
    :ivar models.CharField codice_fiscale: Extracted fiscal code
    :type codice_fiscale: str
    :ivar models.CharField patient_gender: Extracted patient gender
    :type patient_gender: str
    :ivar models.TextField chief_complaint: Extracted chief complaint
    :type chief_complaint: str
    :ivar models.TextField history_present_illness: Extracted history of present illness
    :type history_present_illness: str
    :ivar models.JSONField past_medical_history: Extracted past medical history
    :type past_medical_history: list
    :ivar models.JSONField medications: Extracted current medications
    :type medications: list
    :ivar models.JSONField allergies: Extracted allergies
    :type allergies: list
    :ivar models.JSONField vital_signs: Extracted vital signs
    :type vital_signs: dict
    :ivar models.JSONField physical_examination: Extracted physical examination findings
    :type physical_examination: dict
    :ivar models.TextField assessment: Extracted assessment
    :type assessment: str
    :ivar models.JSONField diagnosis: Extracted diagnosis
    :type diagnosis: list
    :ivar models.TextField treatment_plan: Extracted treatment plan
    :type treatment_plan: str
    :ivar models.FloatField confidence_score: Confidence score of the extraction
    :type confidence_score: float
    :ivar models.DateTimeField extracted_at: Timestamp when data was extracted
    :type extracted_at: datetime
    :ivar models.BooleanField validated: Flag indicating if data has been validated
    :type validated: bool
    :ivar models.ForeignKey validated_by: Reference to the Doctor who validated the data (optional)
    :type validated_by: Doctor
    """
    transcript = models.OneToOneField(AudioTranscript, on_delete=models.CASCADE, related_name='clinical_data')
    
    # Dati anagrafici estratti
    patient_name = models.CharField(max_length=200, blank=True)
    patient_age = models.IntegerField(null=True, blank=True)
    codice_fiscale = models.CharField(max_length=16, blank=True)
    patient_gender = models.CharField(max_length=10, blank=True)
    
    # Anamnesi
    chief_complaint = models.TextField(blank=True, verbose_name="Motivo accesso")
    history_present_illness = models.TextField(blank=True, verbose_name="Anamnesi patologia remota")
    past_medical_history = models.JSONField(default=list, blank=True, verbose_name="Anamnesi patologica remota")
    medications = models.JSONField(default=list, blank=True, verbose_name="Farmaci")
    allergies = models.JSONField(default=list, blank=True, verbose_name="Allergie")
    
    # Esame obiettivo
    vital_signs = models.JSONField(default=dict, blank=True, verbose_name="Parametri vitali")
    physical_examination = models.JSONField(default=dict, blank=True, verbose_name="Esame obiettivo")
    
    # Valutazione e piano
    assessment = models.TextField(blank=True, verbose_name="Valutazione")
    diagnosis = models.JSONField(default=list, blank=True, verbose_name="Diagnosi")
    treatment_plan = models.TextField(blank=True, verbose_name="Piano terapeutico")
    
    # Metadati
    confidence_score = models.FloatField(null=True, blank=True)
    extracted_at = models.DateTimeField(auto_now_add=True)
    validated = models.BooleanField(default=False)
    validated_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        """
        Meta options for the ClinicalData model.
        """
        verbose_name = "Dati Clinici"
        verbose_name_plural = "Dati Clinici"
        ordering = ['-extracted_at']

    def __str__(self):
        """
        String representation of the ClinicalData model.
        """
        return f"Clinical Data for {self.transcript}"


class ClinicalReport(models.Model):
    """
    Model for clinical reports of finalized encounters
    
    :ivar models.UUIDField report_id: Unique UUID identifier for the report
    :type report_id: uuid.UUID
    :ivar models.ForeignKey encounter: Reference to the associated Encounter
    :type encounter: Encounter
    :ivar models.ForeignKey clinical_data: Reference to the associated ClinicalData (optional)
    :type clinical_data: ClinicalData
    :ivar models.CharField template_type: Type of report template used
    :type template_type: str
    :ivar models.JSONField report_content: Structured content of the report
    :type report_content: dict
    :ivar models.FileField pdf_file: Uploaded PDF file of the report (optional)
    :type pdf_file: File
    :ivar models.BooleanField is_finalized: Flag indicating if the report is finalized
    :type is_finalized: bool
    :ivar models.DateTimeField finalized_at: Timestamp when the report was finalized (optional)
    :type finalized_at: datetime
    :ivar models.ForeignKey finalized_by: Reference to the Doctor who finalized the report (optional)
    :type finalized_by: Doctor
    :ivar models.DateTimeField created_at: Timestamp of record creation
    :type created_at: datetime
    :ivar models.DateTimeField updated_at: Timestamp of last update
    :type updated_at: datetime
    """
    TEMPLATE_CHOICES = [
        ('emergency', 'Pronto Soccorso'),
        ('consultation', 'Consulenza'),
        ('admission', 'Ricovero'),
    ]

    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='reports')
    clinical_data = models.ForeignKey(ClinicalData, on_delete=models.CASCADE, null=True, blank=True)
    
    # Template e contenuto
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='emergency')
    report_content = models.JSONField(default=dict, verbose_name="Contenuto strutturato")
    
    # File PDF
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Finalizzazione
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta options for the ClinicalReport model.
        """
        verbose_name = "Report Clinico"
        verbose_name_plural = "Report Clinici"
        ordering = ['-created_at']

    def __str__(self):
        """
        String representation of the ClinicalReport model.
        """
        return f"Report {self.report_id} - {self.encounter}"
