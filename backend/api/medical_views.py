"""
View API aggiuntive per il workflow medico completo
Gestisce la pipeline di trascrizione, estrazione entità e generazione report
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import FileResponse, HttpResponse
import os
import logging
import tempfile
from datetime import datetime, date

from core.models import Patient, Doctor, Encounter, AudioTranscript as DjangoAudioTranscript
from services.nvidia_nim import NVIDIANIMService
from services.whisper_realtime import whisper_realtime_service
from services.mongodb_service import mongodb_service
from services.pdf_report import pdf_report_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
            'whisper_available': whisper_realtime_service.is_available(),
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
@permission_classes([IsAuthenticated])
def patients_list(request):
    """
    Endpoint per lista pazienti con filtri
    """
    try:
        filter_type = request.GET.get('filter', 'all')  # all, waiting, completed
        
        # Recupera pazienti da MongoDB
        mongo_patients = mongodb_service.get_all_patients_summary()
        
        # Applica filtri
        if filter_type == 'waiting':
            mongo_patients = [p for p in mongo_patients if p['status'] == 'in_progress']
        elif filter_type == 'completed':
            mongo_patients = [p for p in mongo_patients if p['status'] == 'completed']
        
        # Arricchisci con dati Django se necessario
        enriched_patients = []
        for mongo_patient in mongo_patients:
            patient_data = mongo_patient.copy()
            
            # Cerca paziente Django corrispondente
            try:
                django_patient = Patient.objects.get(patient_id=mongo_patient['patient_id'])
                patient_data.update({
                    'fiscal_code': django_patient.fiscal_code,
                    'email': getattr(django_patient, 'email', ''),
                    'emergency_contact': django_patient.emergency_contact,
                    'allergies': django_patient.allergies,
                    'blood_type': django_patient.blood_type
                })
            except Patient.DoesNotExist:
                pass
            
            enriched_patients.append(patient_data)
        
        return Response({
            'patients': enriched_patients,
            'total_count': len(enriched_patients),
            'filter_applied': filter_type
        })
        
    except Exception as e:
        logger.error(f"Errore recupero lista pazienti: {e}")
        return Response(
            {'error': 'Errore recupero lista pazienti'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def process_audio_visit(request):
    """
    Endpoint per processare una nuova visita audio
    Pipeline completa: trascrizione -> estrazione entità -> salvataggio MongoDB
    """
    try:
        # Validazione input
        audio_file = request.FILES.get('audio_file')
        encounter_id = request.data.get('encounter_id')
        usage_mode = request.data.get('usage_mode', '')  # Checkup, Emergency, etc.
        
        if not audio_file or not encounter_id:
            return Response(
                {'error': 'audio_file e encounter_id sono richiesti'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Recupera encounter
        encounter = get_object_or_404(Encounter, encounter_id=encounter_id)
        
        # Salva file audio temporaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_audio_path = temp_file.name
        
        # Step 1: Trascrizione audio
        logger.info(f"Avvio trascrizione per encounter {encounter_id}")
        transcript_result = whisper_realtime_service.transcribe_audio_file(temp_audio_path)
        
        if 'error' in transcript_result:
            os.unlink(temp_audio_path)  # Cleanup
            return Response(
                {'error': f'Errore trascrizione: {transcript_result["error"]}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        transcript_text = transcript_result['text']
        logger.info(f"Trascrizione completata: {len(transcript_text)} caratteri")
        
        # Step 2: Estrazione entità cliniche
        logger.info(f"Avvio estrazione entità per encounter {encounter_id}")
        nvidia_service = NVIDIANIMService()
        clinical_data = nvidia_service.extract_clinical_entities(transcript_text, usage_mode)
        
        if 'error' in clinical_data:
            os.unlink(temp_audio_path)
            return Response(
                {'error': f'Errore estrazione entità: {clinical_data["error"]}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        logger.info(f"Estrazione entità completata")
        
        # Step 3: Salvataggio su MongoDB
        audio_file_path = f"audio/encounter_{encounter_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        final_audio_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
        os.makedirs(os.path.dirname(final_audio_path), exist_ok=True)
        os.rename(temp_audio_path, final_audio_path)
        
        transcript_id = mongodb_service.save_patient_visit(
            encounter_id=encounter_id,
            patient_id=str(encounter.patient.patient_id),
            doctor_id=str(encounter.doctor.doctor_id),
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
        
        return Response({
            'message': 'Visita processata con successo',
            'transcript_id': transcript_id,
            'encounter_id': encounter_id,
            'transcript_length': len(transcript_text),
            'entities_extracted': len(clinical_data.get('extracted_data', {})),
            'validation_errors': clinical_data.get('validation_errors', [])
        })
        
    except Exception as e:
        logger.error(f"Errore processing visita audio: {e}")
        return Response(
            {'error': 'Errore interno processing visita'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verifica che l'encounter esista
            encounter = get_object_or_404(Encounter, encounter_id=encounter_id)
            
            # Avvia il servizio di trascrizione
            transcription_service = TranscriptionService()
            transcript = transcription_service.transcribe_audio_file(
                audio_file=audio_file,
                encounter_id=encounter_id,
                language=language
            )
            
            # Serializza e restituisci il risultato
            serializer = self.get_serializer(transcript)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Errore durante trascrizione: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_audio(self, request, pk=None):
        """
        Download del file audio originale
        """
        try:
            transcript = self.get_object()
            
            if not transcript.audio_file:
                raise Http404("File audio non trovato")
            
            response = HttpResponse(
                transcript.audio_file.read(), 
                content_type='audio/mpeg'
            )
            response['Content-Disposition'] = f'attachment; filename="audio_{transcript.transcript_id}.mp3"'
            return response
            
        except Exception as e:
            logger.error(f"Errore download audio: {e}")
            raise Http404("File non trovato")

class ClinicalDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire i dati clinici estratti
    """
    queryset = ClinicalData.objects.all()
    serializer_class = ClinicalDataSerializer
    
    @action(detail=False, methods=['post'], url_path='extract-from-transcript')
    def extract_from_transcript(self, request):
        """
        Estrae dati clinici da una trascrizione esistente
        """
        try:
            transcript_id = request.data.get('transcript_id')
            
            if not transcript_id:
                return Response(
                    {'error': 'transcript_id è richiesto'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Ottieni la trascrizione
            transcript = get_object_or_404(AudioTranscript, transcript_id=transcript_id)
            
            # Verifica che la trascrizione sia completata
            if transcript.status != 'completed':
                return Response(
                    {'error': 'La trascrizione deve essere completata'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Avvia l'estrazione
            extraction_service = ClinicalExtractionService()
            clinical_data = extraction_service.extract_clinical_data(transcript)
            
            # Serializza e restituisci il risultato
            serializer = self.get_serializer(clinical_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Errore durante estrazione: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def structured_data(self, request, pk=None):
        """
        Restituisce i dati estratti in formato strutturato
        """
        try:
            clinical_data = self.get_object()
            return Response(clinical_data.extracted_data)
            
        except Exception as e:
            logger.error(f"Errore lettura dati: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClinicalReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestire i report clinici
    """
    queryset = ClinicalReport.objects.all()
    serializer_class = ClinicalReportSerializer
    
    @action(detail=False, methods=['post'], url_path='generate-from-data')
    def generate_from_data(self, request):
        """
        Genera un report PDF da dati clinici estratti
        """
        try:
            clinical_data_id = request.data.get('clinical_data_id')
            
            if not clinical_data_id:
                return Response(
                    {'error': 'clinical_data_id è richiesto'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Ottieni i dati clinici
            clinical_data = get_object_or_404(ClinicalData, data_id=clinical_data_id)
            
            # Verifica che l'estrazione sia completata
            if clinical_data.status != 'completed':
                return Response(
                    {'error': 'L\'estrazione dei dati deve essere completata'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Avvia la generazione del report
            report_service = ReportGenerationService()
            report = report_service.generate_clinical_report(clinical_data)
            
            # Serializza e restituisci il risultato
            serializer = self.get_serializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Errore durante generazione report: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """
        Download del report PDF
        """
        try:
            report = self.get_object()
            
            if not report.pdf_file:
                raise Http404("File PDF non trovato")
            
            response = HttpResponse(
                report.pdf_file.read(), 
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="report_{report.report_id}.pdf"'
            return response
            
        except Exception as e:
            logger.error(f"Errore download PDF: {e}")
            raise Http404("File non trovato")

class MedicalWorkflowViewSet(viewsets.ViewSet):
    """
    ViewSet per gestire il workflow medico completo
    """
    
    @action(detail=False, methods=['post'], url_path='complete-workflow')
    def complete_workflow(self, request):
        """
        Esegue il workflow completo: trascrizione -> estrazione -> report
        """
        try:
            # Validazione parametri
            encounter_id = request.data.get('encounter_id')
            audio_file = request.FILES.get('audio_file')
            language = request.data.get('language', 'it')
            
            if not encounter_id or not audio_file:
                return Response(
                    {'error': 'encounter_id e audio_file sono richiesti'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Step 1: Trascrizione
            transcription_service = TranscriptionService()
            transcript = transcription_service.transcribe_audio_file(
                audio_file=audio_file,
                encounter_id=encounter_id,
                language=language
            )
            
            # Step 2: Estrazione dati clinici
            extraction_service = ClinicalExtractionService()
            clinical_data = extraction_service.extract_clinical_data(transcript)
            
            # Step 3: Generazione report
            report_service = ReportGenerationService()
            report = report_service.generate_clinical_report(clinical_data)
            
            # Prepara risposta completa
            response_data = {
                'transcript': AudioTranscriptSerializer(transcript).data,
                'clinical_data': ClinicalDataSerializer(clinical_data).data,
                'report': ClinicalReportSerializer(report).data,
                'workflow_status': 'completed'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Errore workflow completo: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='workflow-status/(?P<encounter_id>[^/.]+)')
    def workflow_status(self, request, encounter_id=None):
        """
        Verifica lo stato del workflow per un encounter
        """
        try:
            encounter = get_object_or_404(Encounter, encounter_id=encounter_id)
            
            # Cerca trascrizioni
            transcripts = AudioTranscript.objects.filter(encounter=encounter)
            
            # Cerca dati clinici (attraverso la relazione transcript)
            clinical_data_list = ClinicalData.objects.filter(transcript__encounter=encounter)
            
            # Cerca report
            reports = ClinicalReport.objects.filter(encounter=encounter)
            
            status_data = {
                'encounter_id': encounter_id,
                'transcripts': [
                    {
                        'id': t.transcript_id,
                        'status': t.status,
                        'confidence': t.confidence_score,
                        'duration': t.audio_duration
                    } for t in transcripts
                ],
                'clinical_data': [
                    {
                        'id': cd.id,
                        'status': 'completed' if cd.validated else 'processing',
                        'confidence': cd.confidence_score,
                        'extracted_at': cd.extracted_at
                    } for cd in clinical_data_list
                ],
                'reports': [
                    {
                        'id': r.report_id,
                        'status': 'completed' if r.is_finalized else 'processing',
                        'created_at': r.created_at,
                        'finalized_at': r.finalized_at
                    } for r in reports
                ]
            }
            
            return Response(status_data)
            
        except Exception as e:
            logger.error(f"Errore verifica stato: {e}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )