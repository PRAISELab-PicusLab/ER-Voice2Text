"""
View API aggiuntive per il workflow medico completo
Gestisce la pipeline di trascrizione, estrazione entità e generazione report
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.utils.dateparse import parse_date
import os
import logging
import tempfile
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple

from core.models import Patient, Doctor, Encounter, AudioTranscript as DjangoAudioTranscript
from services.nvidia_nim import NVIDIANIMService
from services.whisper_service import whisper_service
from services.mongodb_service import mongodb_service
from services.pdf_report import pdf_report_service

logger = logging.getLogger(__name__)


def _safe_parse_date(raw_date: Any) -> Optional[date]:
    """Parsa una data da stringa restituendo None se non valida."""
    if not raw_date:
        return None

    raw_str = str(raw_date).strip()
    if not raw_str:
        return None

    parsed = parse_date(raw_str)
    if parsed:
        return parsed

    for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y'):
        try:
            return datetime.strptime(raw_str, fmt).date()
        except ValueError:
            continue

    return None


def _create_patient_from_extracted_data(extracted: Dict[str, Any]) -> Tuple[Patient, bool]:
    """Crea un nuovo paziente partendo dai dati estratti dalla visita."""
    timestamp_suffix = datetime.now().strftime('%Y%m%d%H%M%S')
    first_name = (extracted.get('first_name') or 'Paziente').strip() or 'Paziente'
    last_name = (extracted.get('last_name') or f'Anonimo {timestamp_suffix}').strip() or f'Anonimo {timestamp_suffix}'

    birth_date = _safe_parse_date(extracted.get('birth_date')) or date.today()
    place_of_birth = (extracted.get('birth_place') or 'Sconosciuto').strip() or 'Sconosciuto'

    raw_gender = (extracted.get('gender') or '').strip().lower()
    gender_map = {
        'm': 'M', 'maschio': 'M', 'male': 'M',
        'f': 'F', 'femmina': 'F', 'female': 'F'
    }
    gender = gender_map.get(raw_gender, 'O')

    phone = (extracted.get('phone') or '').strip() or None
    emergency_contact = (extracted.get('emergency_contact') or '').strip() or None

    patient = Patient.objects.create(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=birth_date,
        place_of_birth=place_of_birth,
        gender=gender,
        phone=phone,
        emergency_contact=emergency_contact
    )

    return patient, True


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard_analytics(request):
    """
    Endpoint per statistiche dashboard
    """
    try:
        # Statistiche MongoDB
        total_patients = len(mongodb_service.get_all_patients_summary())
        visits_today = mongodb_service.get_visits_today()
        waiting_patients = mongodb_service.get_waiting_patients_count()
        
        # Statistiche Django
        total_encounters = Encounter.objects.count()
        active_encounters = Encounter.objects.filter(status='in_progress').count()
        completed_today = Encounter.objects.filter(
            discharge_time__date=date.today()
        ).count()
        
        # Distribuzione triage (ultime 24h)
        from django.utils import timezone
        yesterday = timezone.now() - timezone.timedelta(days=1)
        recent_encounters = Encounter.objects.filter(created_at__gte=yesterday)
        
        triage_distribution = {}
        for encounter in recent_encounters:
            priority = encounter.triage_priority
            triage_distribution[priority] = triage_distribution.get(priority, 0) + 1
        
        analytics_data = {
            'total_patients': total_patients,
            'visits_today': visits_today,
            'waiting_patients': waiting_patients,
            'total_encounters': total_encounters,
            'active_encounters': active_encounters,
            'completed_today': completed_today,
            'triage_distribution': triage_distribution,
            'mongodb_connected': mongodb_service.is_connected(),
            'whisper_available': whisper_service.test_transcription()['success'],
            'nvidia_nim_available': bool(NVIDIANIMService().test_connection()['success']),
            'last_updated': datetime.now().isoformat()
        }
        
        return Response(analytics_data)
        
    except Exception as e:
        logger.error(f"Errore recupero analytics: {e}")
        return Response(
            {'error': 'Errore recupero statistiche'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def patients_list(request):
    """
    Endpoint per lista pazienti con filtri
    """
    try:
        filter_type = request.GET.get('filter', 'all')  # all, waiting, completed
        
        # Recupera pazienti da Django (database principale)
        patients_query = Patient.objects.all().order_by('last_name', 'first_name')
        
        # Recupera anche dati da MongoDB per arricchire con visite
        mongo_patients = mongodb_service.get_all_patients_summary()
        mongo_dict = {p['patient_id']: p for p in mongo_patients}
        
        # Costruisci lista arricchita
        enriched_patients = []
        for patient in patients_query:
            # Dati base da Django
            patient_data = {
                'patient_id': str(patient.patient_id),
                'fiscal_code': patient.fiscal_code,
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'age': patient.age,
                'gender': patient.gender,
                'phone': patient.phone,
                'emergency_contact': patient.emergency_contact,
                'blood_type': patient.blood_type,
                'allergies': patient.allergies,
                'created_at': patient.created_at.isoformat(),
            }
            
            # Arricchisci con dati MongoDB se disponibili
            mongo_data = mongo_dict.get(str(patient.patient_id), {})
            patient_data.update({
                'total_visits': mongo_data.get('total_visits', 0),
                'last_visit_date': mongo_data.get('last_visit_date'),
                'last_triage_code': mongo_data.get('last_triage_code'),
                'status': mongo_data.get('status', 'waiting'),  # Default waiting
            })
            
            # Applica filtri
            if filter_type == 'waiting' and patient_data['status'] != 'in_progress':
                continue
            elif filter_type == 'completed' and patient_data['status'] != 'completed':
                continue
            
            enriched_patients.append(patient_data)
        
        return Response({
            'patients': enriched_patients,
            'total_count': len(enriched_patients),
            'filter': filter_type
        })
        
    except Exception as e:
        logger.error(f"Errore recupero lista pazienti: {e}")
        return Response(
            {'error': 'Errore recupero lista pazienti'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def process_audio_visit(request):
    """
    Endpoint per processare una nuova visita audio
    Pipeline completa: trascrizione -> estrazione entità -> salvataggio MongoDB
    """
    temp_audio_path: Optional[str] = None

    try:
        # Validazione input
        audio_file = request.FILES.get('audio_file')
        raw_patient_id = request.data.get('patient_id')
        sintomi_principali = request.data.get('sintomi_principali', '')
        codice_triage = (request.data.get('codice_triage') or '').strip().lower() or 'white'
        note_triage = request.data.get('note_triage', '')
        usage_mode = 'Emergency'  # Default per nuove visite

        if not audio_file:
            return Response(
                {'error': 'audio_file è richiesto'},
                status=status.HTTP_400_BAD_REQUEST
            )

        patient: Optional[Patient] = None
        patient_created = False

        if raw_patient_id:
            try:
                patient = Patient.objects.get(patient_id=raw_patient_id)
            except Patient.DoesNotExist:
                return Response(
                    {'error': f'Paziente {raw_patient_id} non trovato'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Salva file audio temporaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_audio_path = temp_file.name

        # Step 1: Trascrizione audio
        logger.info("Avvio trascrizione per nuova visita audio")
        transcript_result = whisper_service.transcribe_audio_file(temp_audio_path)

        if not transcript_result.get('success', False):
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                temp_audio_path = None
            return Response(
                {'error': f"Errore trascrizione: {transcript_result.get('error', 'Errore sconosciuto')}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        transcript_text = transcript_result.get('transcript', '')
        logger.info(f"Trascrizione completata: {len(transcript_text)} caratteri")
        print(f"\n=== TRASCRIZIONE WHISPER ===")
        print(f"Testo: {transcript_text}")
        print(f"Lunghezza: {len(transcript_text)} caratteri")
        print(f"================================\n")

        # Step 2: Estrazione entità cliniche
        logger.info("Avvio estrazione entità cliniche")
        nvidia_service = NVIDIANIMService()
        clinical_data = nvidia_service.extract_clinical_entities(transcript_text, usage_mode)

        if not clinical_data:
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                temp_audio_path = None
            return Response(
                {'error': 'Errore durante estrazione entità cliniche'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info("Estrazione entità completata")

        extracted_data = clinical_data.get('extracted_data', {}) or {}

        if not patient:
            patient, patient_created = _create_patient_from_extracted_data(extracted_data)
            logger.info(f"Creato nuovo paziente {patient.patient_id} da dati estratti")

        doctor = getattr(patient, 'assigned_doctor', None)
        if not doctor:
            doctor = Doctor.objects.first()

        if not doctor:
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
                temp_audio_path = None
            return Response(
                {'error': 'Nessun medico disponibile per assegnare la visita'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        valid_triage_codes = {'white', 'green', 'yellow', 'red', 'black'}
        if codice_triage not in valid_triage_codes:
            codice_triage = (extracted_data.get('triage_code') or 'white').strip().lower()
        if codice_triage not in valid_triage_codes:
            codice_triage = 'white'

        chief_complaint = sintomi_principali.strip() or (extracted_data.get('symptoms') or '').strip() or 'Visita registrata tramite audio'

        encounter = Encounter.objects.create(
            patient=patient,
            doctor=doctor,
            chief_complaint=chief_complaint,
            triage_priority=codice_triage,
            status='in_progress'
        )

        encounter_id = str(encounter.encounter_id)

        audio_filename = f"encounter_{encounter_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        audio_file_path = os.path.join('audio', audio_filename)
        final_audio_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
        os.makedirs(os.path.dirname(final_audio_path), exist_ok=True)
        os.rename(temp_audio_path, final_audio_path)
        temp_audio_path = None

        transcript_id = mongodb_service.save_patient_visit(
            encounter_id=encounter_id,
            patient_id=str(patient.patient_id),
            doctor_id=str(doctor.doctor_id),
            audio_file_path=audio_file_path,
            transcript_text=transcript_text,
            clinical_data=clinical_data
        )

        if not transcript_id:
            return Response(
                {'error': 'Errore salvataggio su MongoDB'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"Visita salvata con transcript_id: {transcript_id}")

        # Aggiorna encounter status se necessario
        if encounter.status == 'in_progress':
            encounter.status = 'completed'
            encounter.discharge_time = datetime.now()
            encounter.save()

        patient_payload = {
            'patient_id': str(patient.patient_id),
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            'place_of_birth': patient.place_of_birth,
            'gender': patient.gender,
            'phone': patient.phone,
            'fiscal_code': patient.fiscal_code,
        }

        return Response({
            'message': 'Visita processata con successo',
            'transcript_id': transcript_id,
            'encounter_id': encounter_id,
            'transcript': transcript_text,
            'transcript_length': len(transcript_text),
            'entities_extracted': len(extracted_data),
            'validation_errors': clinical_data.get('validation_errors', []),
            'clinical_data': clinical_data,
            'llm_fallback': clinical_data.get('fallback', False),
            'llm_warnings': clinical_data.get('warnings', []),
            'patient_created': patient_created,
            'patient': patient_payload
        })

    except Exception as e:
        logger.error(f"Errore processing visita audio: {e}", exc_info=True)
        return Response(
            {'error': 'Errore interno processing visita'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_visit_history(request, patient_id):
    """
    Endpoint per cronologia visite di un paziente
    """
    try:
        visits = mongodb_service.get_patient_visits(patient_id)
        
        return Response({
            'patient_id': patient_id,
            'visits': visits,
            'total_visits': len(visits)
        })
        
    except Exception as e:
        logger.error(f"Errore recupero cronologia paziente {patient_id}: {e}")
        return Response(
            {'error': 'Errore recupero cronologia visite'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser])
def update_patient_data(request, patient_id):
    """
    Endpoint per aggiornare dati anagrafia paziente
    """
    try:
        updated_data = request.data
        
        # Aggiorna su MongoDB
        success = mongodb_service.update_patient_data(patient_id, updated_data)
        
        if not success:
            return Response(
                {'error': 'Errore aggiornamento dati paziente'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Aggiorna anche Django se paziente esiste
        try:
            django_patient = Patient.objects.get(patient_id=patient_id)
            
            # Mappa campi MongoDB -> Django
            django_fields = {
                'first_name': 'first_name',
                'last_name': 'last_name', 
                'phone': 'phone',
                'fiscal_code': 'fiscal_code',
                'emergency_contact': 'emergency_contact'
            }
            
            for mongo_field, django_field in django_fields.items():
                if mongo_field in updated_data and hasattr(django_patient, django_field):
                    setattr(django_patient, django_field, updated_data[mongo_field])
            
            django_patient.save()
            
        except Patient.DoesNotExist:
            pass  # Paziente solo su MongoDB
        
        return Response({
            'message': 'Dati paziente aggiornati con successo',
            'patient_id': patient_id
        })
        
    except Exception as e:
        logger.error(f"Errore aggiornamento paziente {patient_id}: {e}")
        return Response(
            {'error': 'Errore aggiornamento dati paziente'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pdf_report(request, transcript_id):
    """
    Endpoint per generare report PDF da transcript MongoDB
    """
    try:
        # Recupera contenuto report da MongoDB
        report_content = mongodb_service.generate_report_content(transcript_id)
        
        if not report_content:
            return Response(
                {'error': 'Transcript non trovato o dati insufficienti'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Genera PDF
        encounter_id = report_content.get('encounter_id', transcript_id)
        pdf_path = pdf_report_service.get_report_path(encounter_id, 'medical')
        
        success = pdf_report_service.generate_medical_report(report_content, pdf_path)
        
        if not success:
            return Response(
                {'error': 'Errore generazione PDF'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Restituisci path relativo per download
        relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
        
        return Response({
            'message': 'Report PDF generato con successo',
            'pdf_path': relative_path,
            'download_url': f'/media/{relative_path}',
            'transcript_id': transcript_id
        })
        
    except Exception as e:
        logger.error(f"Errore generazione PDF per transcript {transcript_id}: {e}")
        return Response(
            {'error': 'Errore generazione report PDF'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_pdf_report(request, transcript_id):
    """
    Endpoint per download diretto del report PDF
    """
    try:
        # Genera PDF se non esiste
        report_content = mongodb_service.generate_report_content(transcript_id)
        
        if not report_content:
            return HttpResponse("Report non trovato", status=404)
        
        encounter_id = report_content.get('encounter_id', transcript_id)
        pdf_path = pdf_report_service.get_report_path(encounter_id, 'medical')
        
        # Genera PDF se non esiste già
        if not os.path.exists(pdf_path):
            success = pdf_report_service.generate_medical_report(report_content, pdf_path)
            if not success:
                return HttpResponse("Errore generazione PDF", status=500)
        
        # Download del file
        response = FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf'
        )
        
        patient_name = f"{report_content.get('first_name', '')}{report_content.get('last_name', '')}".strip()
        filename = f"report_{patient_name}_{report_content.get('visit_date', '')}.pdf"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Errore download PDF per transcript {transcript_id}: {e}")
        return HttpResponse("Errore download PDF", status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transcript_details(request, transcript_id):
    """
    Endpoint per dettagli completi di un transcript
    """
    try:
        # Recupera da MongoDB
        report_content = mongodb_service.generate_report_content(transcript_id)
        
        if not report_content:
            return Response(
                {'error': 'Transcript non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'transcript_id': transcript_id,
            'transcript_data': report_content,
            'has_clinical_data': bool(report_content.get('first_name') or report_content.get('symptoms')),
            'visit_date': report_content.get('visit_date'),
            'patient_name': f"{report_content.get('first_name', '')} {report_content.get('last_name', '')}".strip()
        })
        
    except Exception as e:
        logger.error(f"Errore recupero dettagli transcript {transcript_id}: {e}")
        return Response(
            {'error': 'Errore recupero dettagli transcript'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )