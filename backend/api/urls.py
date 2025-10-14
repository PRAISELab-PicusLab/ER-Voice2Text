"""
API URLs configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .medical_workflow_views import (
    dashboard_analytics,
    patients_list,
    process_audio_visit,
    patient_visit_history,
    update_patient_data,
    generate_pdf_report,
    download_pdf_report,
    transcript_details,
    extract_clinical_data_llm,
    update_clinical_data,
    all_interventions_list,
    intervention_details,
    resume_intervention,
    delete_intervention,
    calculate_codice_fiscale,
    get_extraction_methods
)

router = DefaultRouter()
router.register(r'doctors', views.DoctorViewSet)
router.register(r'patients', views.PatientViewSet)
router.register(r'encounters', views.EncounterViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    
    # Medical workflow endpoints
    path('dashboard/analytics/', dashboard_analytics, name='dashboard-analytics'),
    path('workflow/patients/list/', patients_list, name='patients-list'),
    path('visits/process-audio/', process_audio_visit, name='process-audio-visit'),
    path('patients/<str:patient_id>/visits/', patient_visit_history, name='patient-visit-history'),
    path('patients/<str:patient_id>/update/', update_patient_data, name='update-patient-data'),
    path('reports/<str:transcript_id>/generate/', generate_pdf_report, name='generate-pdf-report'),
    path('reports/<str:transcript_id>/download/', download_pdf_report, name='download-pdf-report'),
    path('transcripts/<str:transcript_id>/details/', transcript_details, name='transcript-details'),
    path('transcripts/<str:transcript_id>/extract_clinical_data/', extract_clinical_data_llm, name='extract-clinical-data-llm'),
    path('transcripts/<str:transcript_id>/update_clinical_data/', update_clinical_data, name='update-clinical-data'),
    path('interventions/list/', all_interventions_list, name='all-interventions-list'),
    path('interventions/<str:transcript_id>/details/', intervention_details, name='intervention-details'),
    path('interventions/<str:transcript_id>/resume/', resume_intervention, name='resume-intervention'),
    path('interventions/<str:transcript_id>/delete/', delete_intervention, name='delete-intervention'),
    path('utils/calculate-codice-fiscale/', calculate_codice_fiscale, name='calculate-codice-fiscale'),
    path('extraction/methods/', get_extraction_methods, name='get-extraction-methods'),
]