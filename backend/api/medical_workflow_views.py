"""
View API aggiuntive per il workflow medico completo
Gestisce la pipeline di trascrizione, estrazione entità e generazione report
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, AllowAny
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
    Pipeline: trascrizione -> salvataggio MongoDB (senza estrazione automatica)
    L'estrazione verrà fatta separatamente quando l'utente preme il bottone
    """
    temp_audio_path: Optional[str] = None

    try:
        # Validazione input
        audio_file = request.FILES.get('audio_file')
        raw_patient_id = request.data.get('patient_id')
        sintomi_principali = request.data.get('sintomi_principali', '')
        codice_triage = (request.data.get('codice_triage') or '').strip().lower() or 'white'
        note_triage = request.data.get('note_triage', '')

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

        # Step 1: SOLO Trascrizione audio (senza estrazione automatica)
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

        # Crea paziente temporaneo se necessario
        if not patient:
            timestamp_suffix = datetime.now().strftime('%Y%m%d%H%M%S')
            patient = Patient.objects.create(
                first_name='Paziente',
                last_name=f'Anonimo {timestamp_suffix}',
                date_of_birth=date.today(),
                place_of_birth='Sconosciuto',
                gender='O'
            )
            patient_created = True
            logger.info(f"Creato paziente temporaneo {patient.patient_id}")

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
            codice_triage = 'white'

        chief_complaint = sintomi_principali.strip() or 'Visita registrata tramite audio'

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

        # Salva SOLO la trascrizione su MongoDB (con dati iniziali del triage)
        transcript_id = mongodb_service.save_patient_visit_transcript_only(
            encounter_id=encounter_id,
            patient_id=str(patient.patient_id),
            doctor_id=str(doctor.doctor_id),
            audio_file_path=audio_file_path,
            transcript_text=transcript_text,
            triage_code=codice_triage,
            symptoms=sintomi_principali,
            triage_notes=note_triage
        )

        if not transcript_id:
            return Response(
                {'error': 'Errore salvataggio su MongoDB'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"Trascrizione salvata con transcript_id: {transcript_id}")

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
            'message': 'Trascrizione completata con successo',
            'transcript_id': transcript_id,
            'encounter_id': encounter_id,
            'transcript': transcript_text,
            'transcript_length': len(transcript_text),
            'patient_created': patient_created,
            'patient': patient_payload,
            'needs_extraction': True  # Indica che l'estrazione deve essere fatta separatamente
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
def generate_pdf_report(request, transcript_id):
    """
    Endpoint per generare report PDF da transcript MongoDB
    """
    try:
        logger.info(f"Generazione PDF richiesta per transcript_id: {transcript_id}")
        
        # Recupera contenuto report da MongoDB
        report_content = mongodb_service.generate_report_content(transcript_id)
        
        if not report_content:
            logger.error(f"Report content non trovato per transcript_id: {transcript_id}")
            return Response(
                {'error': 'Transcript non trovato o dati insufficienti'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"Report content recuperato per transcript_id: {transcript_id}")
        
        # Estrai informazioni paziente per nome file PDF
        patient_name = ""
        visit_date = ""
        
        try:
            # Cerca informazioni paziente nel contenuto del report
            if 'patient_info' in report_content and report_content['patient_info']:
                first_name = report_content['patient_info'].get('first_name', '')
                last_name = report_content['patient_info'].get('last_name', '')
                if first_name and last_name:
                    patient_name = f"{first_name}_{last_name}"
                elif first_name or last_name:
                    patient_name = first_name or last_name
                
                visit_date = report_content['patient_info'].get('visit_date', '')
        except Exception as e:
            logger.warning(f"Errore estrazione dati paziente per filename: {e}")
        
        # Genera PDF con nome strutturato
        encounter_id = report_content.get('encounter_id', transcript_id)
        pdf_path = pdf_report_service.get_report_path(encounter_id, 'medical', patient_name, visit_date)
        
        logger.info(f"Generando PDF in: {pdf_path}")
        
        success = pdf_report_service.generate_medical_report(report_content, pdf_path)
        
        if not success:
            logger.error(f"Errore generazione PDF per transcript_id: {transcript_id}")
            return Response(
                {'error': 'Errore generazione PDF'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"PDF generato con successo per transcript_id: {transcript_id}")
        
        # Restituisci path relativo per download
        relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
        
        return Response({
            'message': 'Report PDF generato con successo',
            'pdf_path': relative_path,
            'download_url': f'/media/{relative_path}',
            'transcript_id': transcript_id
        })
        
    except Exception as e:
        logger.error(f"Errore generazione PDF per transcript {transcript_id}: {e}", exc_info=True)
        return Response(
            {'error': 'Errore generazione report PDF'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def download_pdf_report(request, transcript_id):
    """
    Endpoint per download diretto del report PDF
    """
    try:
        logger.info(f"Download PDF richiesto per transcript_id: {transcript_id}")
        
        # Genera PDF se non esiste
        report_content = mongodb_service.generate_report_content(transcript_id)
        
        if not report_content:
            logger.error(f"Report content non trovato per transcript_id: {transcript_id}")
            return HttpResponse("Report non trovato", status=404)
        
        logger.info(f"Report content trovato per transcript_id: {transcript_id}")
        
        # Estrai informazioni paziente per nome file PDF
        patient_name = ""
        visit_date = ""
        
        try:
            # Cerca informazioni paziente nel contenuto del report
            if 'patient_info' in report_content and report_content['patient_info']:
                first_name = report_content['patient_info'].get('first_name', '')
                last_name = report_content['patient_info'].get('last_name', '')
                if first_name and last_name:
                    patient_name = f"{first_name}_{last_name}"
                elif first_name or last_name:
                    patient_name = first_name or last_name
                
                visit_date = report_content['patient_info'].get('visit_date', '')
        except Exception as e:
            logger.warning(f"Errore estrazione dati paziente per filename: {e}")
        
        encounter_id = report_content.get('encounter_id', transcript_id)
        pdf_path = pdf_report_service.get_report_path(encounter_id, 'medical', patient_name, visit_date)
        
        logger.info(f"PDF path: {pdf_path}")
        
        # Genera PDF se non esiste già
        if not os.path.exists(pdf_path):
            logger.info(f"PDF non esiste, generando: {pdf_path}")
            success = pdf_report_service.generate_medical_report(report_content, pdf_path)
            if not success:
                logger.error(f"Errore generazione PDF per transcript_id: {transcript_id}")
                return HttpResponse("Errore generazione PDF", status=500)
            logger.info(f"PDF generato con successo: {pdf_path}")
        else:
            logger.info(f"PDF già esistente: {pdf_path}")
        
        # Download del file
        response = FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf'
        )
        
        # Usa il nome del file già generato dal servizio PDF
        filename = os.path.basename(pdf_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF download completato per transcript_id: {transcript_id}")
        return response
        
    except Exception as e:
        logger.error(f"Errore download PDF per transcript {transcript_id}: {e}", exc_info=True)
        return HttpResponse("Errore download PDF", status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
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


@api_view(['POST'])
@permission_classes([AllowAny])
def extract_clinical_data_llm(request, transcript_id):
    """
    Endpoint per estrazione dati clinici LLM con transcript modificato
    """
    try:
        # Recupera i dati da MongoDB
        from services.mongodb_service import mongodb_service
        
        transcript_data = mongodb_service.get_visit_data(transcript_id)
        
        if not transcript_data:
            return Response(
                {'error': 'Transcript non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verifica se è fornito un transcript modificato
        updated_transcript = request.data.get('transcript_text')
        if updated_transcript:
            # Aggiorna il transcript in MongoDB con il testo modificato
            success = mongodb_service.update_transcript_text(transcript_id, updated_transcript)
            if success:
                transcript_data['transcript_text'] = updated_transcript
                logger.info(f"Transcript {transcript_id} aggiornato con testo modificato")
            else:
                logger.warning(f"Errore aggiornamento transcript {transcript_id}")
        
        # Usa il testo della trascrizione (modificato o originale)
        transcript_text = transcript_data.get('transcript_text', '')
        
        if not transcript_text.strip():
            return Response(
                {'error': 'Nessun testo di trascrizione disponibile per l\'estrazione'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Avvia l'estrazione con NVIDIA NIM usando il testo corretto
        nvidia_service = NVIDIANIMService()
        usage_mode = 'Emergency'  # Default per emergenze
        clinical_data = nvidia_service.extract_clinical_entities(transcript_text, usage_mode)
        
        if not clinical_data:
            return Response(
                {'error': 'Errore durante estrazione entità cliniche'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        extracted_data = clinical_data.get('extracted_data', {}) or {}
        
        # Aggiorna MongoDB con i dati estratti
        update_success = mongodb_service.update_clinical_data(transcript_id, extracted_data)
        
        if not update_success:
            logger.warning(f"Errore aggiornamento dati clinici per transcript {transcript_id}")
        
        logger.info(f"Estrazione LLM completata per transcript {transcript_id}")
        
        return Response({
            'transcript_id': transcript_id,
            'extracted_data': extracted_data,
            'clinical_data': clinical_data,
            'validation_errors': clinical_data.get('validation_errors', []),
            'llm_fallback': clinical_data.get('fallback', False),
            'llm_warnings': clinical_data.get('warnings', []),
            'transcript_updated': bool(updated_transcript),
            'data_saved': update_success,
            'status': 'completed'
        })
        
    except Exception as e:
        logger.error(f"Errore estrazione LLM per transcript {transcript_id}: {e}")
        return Response(
            {'error': f'Errore durante estrazione LLM: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def all_interventions_list(request):
    """
    Endpoint per ottenere lista di tutti gli interventi/visite da MongoDB
    """
    try:
        # Recupera tutti i transcript da MongoDB
        all_visits = mongodb_service.get_all_visits_summary()
        
        return Response({
            'interventions': all_visits,
            'total_count': len(all_visits)
        })
        
    except Exception as e:
        logger.error(f"Errore recupero lista interventi: {e}")
        return Response(
            {'error': 'Errore recupero lista interventi'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def intervention_details(request, transcript_id):
    """
    Endpoint per ottenere dettagli completi di un intervento
    """
    try:
        logger.info(f"Richiesta dettagli per intervento: {transcript_id}")
        
        # Recupera dettagli da MongoDB
        visit_data = mongodb_service.get_visit_data(transcript_id)
        
        if not visit_data:
            logger.warning(f"Intervento {transcript_id} non trovato in MongoDB")
            return Response(
                {'error': 'Intervento non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"Dati visita recuperati per {transcript_id}: status={visit_data.get('processing_status')}")
        
        # Recupera anche i dati per il report se disponibili
        report_content = mongodb_service.generate_report_content(transcript_id)
        
        # Determina se l'intervento può essere ripreso
        processing_status = visit_data.get('processing_status', 'unknown')
        can_resume = processing_status in ['transcribed', 'in_progress']
        
        # Determina il prossimo step se può essere ripreso
        next_step = None
        if can_resume:
            if processing_status == 'transcribed':
                next_step = 'editing'  # L'utente deve rivedere/modificare la trascrizione
            elif processing_status == 'in_progress':
                next_step = 'transcribing'  # La trascrizione è ancora in corso
        
        response_data = {
            'transcript_id': transcript_id,
            'visit_data': visit_data,
            'clinical_data': visit_data.get('clinical_data', {}),  # Aggiungi questo per compatibilità frontend
            'report_content': report_content,
            'has_clinical_data': bool(visit_data.get('clinical_data')),
            'transcript_text': visit_data.get('transcript_text', ''),
            'processing_status': processing_status,
            'can_resume': can_resume,
            'next_step': next_step,
            'encounter_id': visit_data.get('encounter_id'),
            'patient_id': visit_data.get('patient_id'),
        }
        
        logger.info(f"Risposta preparata per {transcript_id}: can_resume={can_resume}, next_step={next_step}")
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Errore recupero dettagli intervento {transcript_id}: {e}")
        return Response(
            {'error': 'Errore recupero dettagli intervento'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def resume_intervention(request, transcript_id):
    """
    Endpoint per riprendere un intervento incompleto
    Restituisce i dati necessari per riprendere il workflow
    """
    try:
        logger.info(f"Richiesta ripresa intervento: {transcript_id}")
        
        # Recupera dati dell'intervento
        visit_data = mongodb_service.get_visit_data(transcript_id)
        
        if not visit_data:
            return Response(
                {'error': 'Intervento non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        processing_status = visit_data.get('processing_status', 'unknown')
        
        # Verifica se può essere ripreso
        if processing_status not in ['transcribed', 'in_progress']:
            return Response(
                {'error': 'Questo intervento non può essere ripreso', 'status': processing_status}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepara i dati per riprendere il workflow
        resume_data = {
            'transcript_id': transcript_id,
            'encounter_id': visit_data.get('encounter_id'),
            'patient_id': visit_data.get('patient_id'),
            'transcript_text': visit_data.get('transcript_text', ''),
            'processing_status': processing_status,
            'current_step': 'editing' if processing_status == 'transcribed' else 'transcribing',
            'needs_extraction': processing_status == 'transcribed',
            'created_at': visit_data.get('created_at')
        }
        
        # Se ci sono già dati clinici estratti, includili
        if visit_data.get('clinical_data'):
            resume_data['existing_clinical_data'] = visit_data['clinical_data']
            resume_data['has_clinical_data'] = True
        else:
            resume_data['has_clinical_data'] = False
        
        logger.info(f"Dati preparati per ripresa intervento {transcript_id}: step={resume_data['current_step']}")
        
        return Response(resume_data)
        
    except Exception as e:
        logger.error(f"Errore ripresa intervento {transcript_id}: {e}")
        return Response(
            {'error': 'Errore durante ripresa intervento'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_intervention(request, transcript_id):
    """
    Endpoint per eliminare un intervento/visita
    """
    try:
        logger.info(f"Richiesta eliminazione intervento: {transcript_id}")
        
        # Elimina da MongoDB
        success = mongodb_service.delete_visit(transcript_id)
        
        if not success:
            logger.error(f"Intervento non trovato per eliminazione: {transcript_id}")
            return Response(
                {'error': 'Intervento non trovato'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        logger.info(f"Intervento eliminato con successo: {transcript_id}")
        return Response({'message': 'Intervento eliminato con successo'})
        
    except Exception as e:
        logger.error(f"Errore eliminazione intervento {transcript_id}: {e}", exc_info=True)
        return Response(
            {'error': 'Errore durante eliminazione'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )