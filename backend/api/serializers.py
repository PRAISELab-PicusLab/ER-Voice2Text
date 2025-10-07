"""
Serializers per API REST del sistema medico unificato
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from core.models import Patient, Doctor, Encounter, AudioTranscript, ClinicalData, ClinicalReport
# from core.mongodb_models import AudioTranscript, ClinicalData, ClinicalReport


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer per modello Doctor
    """
    full_name = serializers.ReadOnlyField(source='get_full_name')
    
    class Meta:
        model = Doctor
        fields = [
            'id', 'doctor_id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'specialization', 'department', 'license_number',
            'is_emergency_doctor', 'is_active', 'created_at', 'last_login_at'
        ]
        read_only_fields = ['doctor_id', 'created_at', 'last_login_at']


class PatientSerializer(serializers.ModelSerializer):
    """
    Serializer per modello Patient
    """
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField(source='get_full_name')
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_id', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'place_of_birth', 'fiscal_code',
            'gender', 'phone', 'emergency_contact', 'weight', 'height',
            'blood_type', 'allergies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['patient_id', 'created_at', 'updated_at']


class EncounterSerializer(serializers.ModelSerializer):
    """
    Serializer per modello Encounter
    """
    patient_name = serializers.ReadOnlyField(source='patient.get_full_name')
    doctor_name = serializers.ReadOnlyField(source='doctor.get_full_name')
    duration_minutes = serializers.ReadOnlyField(source='duration')
    
    class Meta:
        model = Encounter
        fields = [
            'id', 'encounter_id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'admission_time', 'chief_complaint', 'triage_priority', 'status',
            'discharge_time', 'duration_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['encounter_id', 'duration_minutes', 'created_at', 'updated_at']


class TranscriptSegmentSerializer(serializers.Serializer):
    """
    Serializer per segmenti di trascrizione
    """
    segment_id = serializers.CharField(read_only=True)
    text = serializers.CharField()
    speaker_id = serializers.IntegerField(default=0)
    speaker_label = serializers.CharField(required=False, allow_blank=True)
    start_ms = serializers.IntegerField()
    end_ms = serializers.IntegerField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    language = serializers.CharField(default='it')
    engine = serializers.CharField(required=False, allow_blank=True)
    tokens = serializers.ListField(child=serializers.CharField(), required=False)
    is_corrected = serializers.BooleanField(default=False)
    original_text = serializers.CharField(required=False, allow_blank=True)


class ClinicalDataSerializer(serializers.Serializer):
    """
    Serializer per dati clinici estratti
    """
    # Dati anagrafici
    patient_name = serializers.CharField(required=False, allow_blank=True)
    patient_age = serializers.IntegerField(required=False, allow_null=True)
    patient_gender = serializers.CharField(required=False, allow_blank=True)
    
    # Anamnesi
    chief_complaint = serializers.CharField(required=False, allow_blank=True)
    history_present_illness = serializers.CharField(required=False, allow_blank=True)
    past_medical_history = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    medications = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    allergies = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    
    # Esame obiettivo
    vital_signs = serializers.DictField(required=False)
    physical_examination = serializers.DictField(required=False)
    
    # Assessment e plan
    assessment = serializers.CharField(required=False, allow_blank=True)
    diagnosis = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    plan = serializers.CharField(required=False, allow_blank=True)
    
    # Metadati validazione
    validated = serializers.BooleanField(default=False)
    confidence_score = serializers.FloatField(required=False, allow_null=True)
    extraction_engine = serializers.CharField(required=False, allow_blank=True)


class AudioTranscriptSerializer(serializers.Serializer):
    """
    Serializer per documenti AudioTranscript MongoDB
    """
    transcript_id = serializers.CharField(read_only=True)
    encounter_id = serializers.CharField()
    patient_id = serializers.CharField()
    doctor_id = serializers.CharField()
    
    # Metadati audio
    audio_file_path = serializers.CharField(required=False, allow_blank=True)
    audio_format = serializers.CharField(required=False, allow_blank=True)
    audio_duration_ms = serializers.IntegerField(required=False, allow_null=True)
    audio_size_bytes = serializers.IntegerField(required=False, allow_null=True)
    sample_rate = serializers.IntegerField(required=False, allow_null=True)
    channels = serializers.IntegerField(required=False, allow_null=True)
    
    # Transcript
    transcript_segments = TranscriptSegmentSerializer(many=True, required=False)
    full_transcript = serializers.CharField(required=False, allow_blank=True)
    
    # Clinical data
    clinical_data = ClinicalDataSerializer(required=False, allow_null=True)
    
    # Status
    processing_status = serializers.ChoiceField(
        choices=['pending', 'transcribing', 'transcribed', 'extracting', 'extracted', 'validated', 'error'],
        default='pending'
    )
    error_message = serializers.CharField(required=False, allow_blank=True)
    
    # Timestamps
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    transcription_completed_at = serializers.DateTimeField(required=False, allow_null=True)
    extraction_completed_at = serializers.DateTimeField(required=False, allow_null=True)
    
    # Computed fields
    duration_seconds = serializers.SerializerMethodField()
    total_segments = serializers.SerializerMethodField()
    average_confidence = serializers.SerializerMethodField()
    
    def get_duration_seconds(self, obj):
        return obj.duration_seconds if hasattr(obj, 'duration_seconds') else 0
    
    def get_total_segments(self, obj):
        return obj.total_segments if hasattr(obj, 'total_segments') else 0
    
    def get_average_confidence(self, obj):
        return obj.average_confidence if hasattr(obj, 'average_confidence') else 0.0


class ClinicalReportSerializer(serializers.Serializer):
    """
    Serializer per report clinici finalizzati
    """
    report_id = serializers.CharField(read_only=True)
    encounter_id = serializers.CharField()
    transcript_id = serializers.CharField()
    
    # Template e contenuto
    template_name = serializers.CharField(default='er_standard')
    report_content = serializers.DictField()
    
    # Finalizzazione
    is_finalized = serializers.BooleanField(default=False)
    finalized_at = serializers.DateTimeField(required=False, allow_null=True)
    finalized_by = serializers.CharField(required=False, allow_blank=True)
    
    # File PDF
    pdf_file_path = serializers.CharField(required=False, allow_blank=True)
    pdf_checksum = serializers.CharField(required=False, allow_blank=True)
    
    # Timestamps
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class LoginSerializer(serializers.Serializer):
    """
    Serializer per autenticazione medici
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Credenziali non valide')
            if not user.is_active:
                raise serializers.ValidationError('Account disabilitato')
            if not hasattr(user, 'is_emergency_doctor') or not user.is_emergency_doctor:
                raise serializers.ValidationError('Accesso negato al Pronto Soccorso')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Username e password richiesti')


class AudioUploadSerializer(serializers.Serializer):
    """
    Serializer per upload file audio
    """
    audio = serializers.FileField()
    engine = serializers.ChoiceField(
        choices=['whisper', 'azure'],
        default='whisper',
        required=False
    )
    
    def validate_audio(self, value):
        """Valida file audio"""
        from django.conf import settings
        
        # Controlla dimensione
        if value.size > settings.MAX_AUDIO_SIZE:
            raise serializers.ValidationError(
                f'File troppo grande. Massimo: {settings.MAX_AUDIO_SIZE // (1024*1024)}MB'
            )
        
        # Controlla formato
        allowed_formats = settings.ALLOWED_AUDIO_FORMATS
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_formats:
            raise serializers.ValidationError(
                f'Formato non supportato. Consentiti: {", ".join(allowed_formats)}'
            )
        
        return value


class StreamingStatusSerializer(serializers.Serializer):
    """
    Serializer per status streaming WebSocket
    """
    transcript_id = serializers.CharField()
    status = serializers.ChoiceField(
        choices=['connecting', 'recording', 'processing', 'completed', 'error']
    )
    message = serializers.CharField(required=False, allow_blank=True)
    segment_count = serializers.IntegerField(default=0)
    duration_ms = serializers.IntegerField(default=0)
    confidence = serializers.FloatField(required=False, allow_null=True)
    
    
# Serializers per richieste API
class TranscribeAudioSerializer(serializers.Serializer):
    """
    Serializer per richieste di trascrizione audio
    """
    audio_file = serializers.FileField()
    encounter_id = serializers.UUIDField()
    language = serializers.CharField(default='it-IT', max_length=10)


class ProcessClinicalDataSerializer(serializers.Serializer):
    """
    Serializer per processamento dati clinici
    """
    transcript_text = serializers.CharField()
    encounter_id = serializers.UUIDField()


class GenerateReportSerializer(serializers.Serializer):
    """
    Serializer per generazione report PDF
    """
    encounter_id = serializers.UUIDField()
    template_type = serializers.ChoiceField(
        choices=['emergency', 'consultation'], 
        default='emergency'
    )


class AudioTranscriptSerializer(serializers.ModelSerializer):
    """
    Serializer per trascrizioni audio
    """
    class Meta:
        model = AudioTranscript
        fields = '__all__'
        read_only_fields = ['transcript_id', 'created_at', 'updated_at', 'transcription_completed_at']


class ClinicalDataSerializer(serializers.ModelSerializer):
    """
    Serializer per dati clinici estratti
    """
    class Meta:
        model = ClinicalData
        fields = '__all__'
        read_only_fields = ['extracted_at']


class ClinicalReportSerializer(serializers.ModelSerializer):
    """
    Serializer per report clinici
    """
    class Meta:
        model = ClinicalReport
        fields = '__all__'
        read_only_fields = ['report_id', 'created_at', 'updated_at', 'finalized_at']