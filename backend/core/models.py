from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class Doctor(AbstractUser):
    """
    Modello medico esteso dall'User Django per autenticazione AGID
    """
    doctor_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    specialization = models.CharField(max_length=100, help_text="Specializzazione medica")
    department = models.CharField(max_length=100, help_text="Reparto di appartenenza")
    license_number = models.CharField(max_length=50, unique=True, help_text="Numero ordine medici")
    is_emergency_doctor = models.BooleanField(default=False, help_text="Abilitato al pronto soccorso")
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Medico"
        verbose_name_plural = "Medici"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} - {self.specialization}"

    def get_full_name(self):
        return f"Dr. {self.first_name} {self.last_name}"


class Patient(models.Model):
    """
    Modello paziente con dati anagrafici essenziali
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
        verbose_name = "Paziente"
        verbose_name_plural = "Pazienti"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['fiscal_code']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.fiscal_code})"

    @property
    def age(self):
        """Calcola l'età del paziente"""
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Encounter(models.Model):
    """
    Modello encounter per episodi di cura in Pronto Soccorso
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
        verbose_name = "Episodio di cura"
        verbose_name_plural = "Episodi di cura"
        ordering = ['-admission_time']
        indexes = [
            models.Index(fields=['admission_time']),
            models.Index(fields=['status']),
            models.Index(fields=['triage_priority']),
        ]

    def __str__(self):
        return f"Encounter {self.encounter_id} - {self.patient.get_full_name()} ({self.admission_time})"

    @property
    def duration(self):
        """Calcola la durata dell'encounter in minuti"""
        if self.discharge_time:
            return (self.discharge_time - self.admission_time).total_seconds() / 60
        return (timezone.now() - self.admission_time).total_seconds() / 60


class AudioTranscript(models.Model):
    """
    Modello per trascrizioni audio degli encounter
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
        verbose_name = "Trascrizione Audio"
        verbose_name_plural = "Trascrizioni Audio"
        ordering = ['-created_at']

    def __str__(self):
        return f"Transcript {self.transcript_id} - {self.encounter}"


class ClinicalData(models.Model):
    """
    Modello per dati clinici estratti dalla trascrizione
    """
    transcript = models.OneToOneField(AudioTranscript, on_delete=models.CASCADE, related_name='clinical_data')
    
    # Dati anagrafici estratti
    patient_name = models.CharField(max_length=200, blank=True)
    patient_age = models.IntegerField(null=True, blank=True)
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
        verbose_name = "Dati Clinici"
        verbose_name_plural = "Dati Clinici"
        ordering = ['-extracted_at']

    def __str__(self):
        return f"Clinical Data for {self.transcript}"


class ClinicalReport(models.Model):
    """
    Modello per report clinici finalizzati
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
        verbose_name = "Report Clinico"
        verbose_name_plural = "Report Clinici"
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.report_id} - {self.encounter}"
