"""
Servizio MongoDB per gestione dati pazienti e visite
Basato sulla logica del Project 2
"""

import os
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from mongoengine import connect, disconnect
from django.conf import settings

from core.mongodb_models import (
    AudioTranscript, 
    ClinicalReport, 
    MedicalPatientData,
    VitalSigns,
    ClinicalAssessment,
    ClinicalData
)

logger = logging.getLogger(__name__)


class MongoDBService:
    """
    Servizio per gestione dati MongoDB
    """
    
    def __init__(self):
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Connessione a MongoDB"""
        try:
            mongodb_uri = getattr(settings, 'MONGODB_URL', None)
            if not mongodb_uri:
                logger.error("MONGODB_URL non configurata nelle Django settings")
                return
            
            # Disconnetti connessioni esistenti
            disconnect()
            
            # Connetti a MongoDB
            connect(host=mongodb_uri, alias='default')
            self.connected = True
            logger.info(f"Connessione MongoDB stabilita: {mongodb_uri}")
            
        except Exception as e:
            logger.error(f"Errore connessione MongoDB: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Verifica connessione MongoDB"""
        return self.connected
    
    def save_patient_visit(self, encounter_id: str, patient_id: str, doctor_id: str, 
                          audio_file_path: str, transcript_text: str, 
                          clinical_data: Dict[str, Any]) -> Optional[str]:
        """
        Salva una nuova visita paziente con audio e dati clinici
        
        Args:
            encounter_id: ID encounter Django
            patient_id: ID paziente Django
            doctor_id: ID medico Django
            audio_file_path: Path file audio
            transcript_text: Testo trascrizione
            clinical_data: Dati clinici estratti
            
        Returns:
            ID del transcript MongoDB creato
        """
        if not self.connected:
            logger.error("MongoDB non connesso")
            return None
        
        try:
            # Crea documento AudioTranscript
            transcript_doc = AudioTranscript()
            transcript_doc.encounter_id = encounter_id
            transcript_doc.patient_id = patient_id
            transcript_doc.doctor_id = doctor_id
            transcript_doc.audio_file_path = audio_file_path
            transcript_doc.full_transcript = transcript_text
            transcript_doc.processing_status = 'extracted'
            
            # Popola dati clinici
            if clinical_data:
                clinical_doc = ClinicalData()
                
                # Dati paziente
                if clinical_data.get('extracted_data'):
                    extracted = clinical_data['extracted_data']
                    
                    patient_data = MedicalPatientData()
                    patient_data.first_name = extracted.get('first_name', '')
                    patient_data.last_name = extracted.get('last_name', '')
                    # Gestisci età come int
                    age_value = extracted.get('age')
                    if age_value and age_value != '':
                        try:
                            patient_data.age = int(age_value)
                        except (ValueError, TypeError):
                            patient_data.age = None
                    else:
                        patient_data.age = None
                    patient_data.gender = extracted.get('gender', '')
                    patient_data.birth_date = extracted.get('birth_date', '')
                    patient_data.birth_place = extracted.get('birth_place', '')
                    patient_data.residence_city = extracted.get('residence_city', '')
                    patient_data.residence_address = extracted.get('residence_address', '')
                    patient_data.phone = extracted.get('phone', '')
                    patient_data.access_mode = extracted.get('access_mode', '')
                    
                    # Parametri vitali
                    vital_signs = VitalSigns()
                    vital_signs.heart_rate = extracted.get('heart_rate', '')
                    vital_signs.blood_pressure = extracted.get('blood_pressure', '')
                    # Gestisci temperatura come float
                    temp_value = extracted.get('temperature')
                    if temp_value and temp_value != '':
                        try:
                            vital_signs.temperature = float(temp_value)
                        except (ValueError, TypeError):
                            vital_signs.temperature = None
                    else:
                        vital_signs.temperature = None
                    vital_signs.oxygenation = extracted.get('oxygenation', '')
                    vital_signs.blood_glucose = extracted.get('blood_glucose', '')
                    
                    # Valutazione clinica
                    assessment = ClinicalAssessment()
                    assessment.skin_state = extracted.get('skin_state', '')
                    assessment.consciousness_state = extracted.get('consciousness_state', '')
                    assessment.pupils_state = extracted.get('pupils_state', '')
                    assessment.respiratory_state = extracted.get('respiratory_state', '')
                    assessment.history = extracted.get('history', '')
                    assessment.medications_taken = extracted.get('medications_taken', '')
                    assessment.symptoms = extracted.get('symptoms', '')
                    assessment.medical_actions = extracted.get('medical_actions', '')
                    assessment.assessment = extracted.get('assessment', '')
                    assessment.plan = extracted.get('plan', '')
                    assessment.triage_code = extracted.get('triage_code', '')
                    
                    # Assembla dati clinici
                    clinical_doc.patient_data = patient_data
                    clinical_doc.vital_signs = vital_signs
                    clinical_doc.clinical_assessment = assessment
                
                # Metadati estrazione
                clinical_doc.llm_model_used = clinical_data.get('llm_model', '')
                clinical_doc.confidence_score = clinical_data.get('confidence_score', 0.0)
                clinical_doc.validation_errors = clinical_data.get('validation_errors', [])
                clinical_doc.extraction_timestamp = datetime.utcnow()
                
                transcript_doc.clinical_data = clinical_doc
                transcript_doc.extraction_completed_at = datetime.utcnow()
            
            # Salva documento
            transcript_doc.save()
            
            logger.info(f"Visita salvata: {transcript_doc.transcript_id}")
            return transcript_doc.transcript_id
            
        except Exception as e:
            logger.error(f"Errore salvataggio visita: {e}")
            return None
    
    def get_patient_visits(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Recupera tutte le visite di un paziente
        
        Args:
            patient_id: ID paziente Django
            
        Returns:
            Lista delle visite del paziente
        """
        if not self.connected:
            return []
        
        try:
            visits = AudioTranscript.objects(patient_id=patient_id).order_by('-created_at')
            
            visits_data = []
            for visit in visits:
                visit_data = {
                    'transcript_id': visit.transcript_id,
                    'encounter_id': visit.encounter_id,
                    'created_at': visit.created_at.isoformat(),
                    'status': visit.processing_status,
                    'duration': visit.duration_seconds,
                    'has_clinical_data': visit.clinical_data is not None,
                    'transcript_text': visit.full_transcript[:200] + '...' if len(visit.full_transcript or '') > 200 else visit.full_transcript
                }
                
                # Aggiungi dati clinici se presenti
                if visit.clinical_data and visit.clinical_data.patient_data:
                    patient_data = visit.clinical_data.patient_data
                    visit_data['patient_name'] = f"{patient_data.first_name} {patient_data.last_name}".strip()
                    visit_data['patient_age'] = patient_data.age
                    visit_data['triage_code'] = visit.clinical_data.clinical_assessment.triage_code if visit.clinical_data.clinical_assessment else ''
                
                visits_data.append(visit_data)
            
            return visits_data
            
        except Exception as e:
            logger.error(f"Errore recupero visite paziente: {e}")
            return []
    
    def get_all_patients_summary(self) -> List[Dict[str, Any]]:
        """
        Recupera summary di tutti i pazienti con le loro ultime visite
        
        Returns:
            Lista di pazienti con dati aggregati
        """
        if not self.connected:
            return []
        
        try:
            # Recupera tutti i transcript raggruppati per patient_id
            pipeline = [
                {
                    "$sort": {"patient_id": 1, "created_at": -1}
                },
                {
                    "$group": {
                        "_id": "$patient_id",
                        "latest_visit": {"$first": "$$ROOT"},
                        "total_visits": {"$sum": 1},
                        "last_visit_date": {"$first": "$created_at"}
                    }
                }
            ]
            
            results = AudioTranscript.objects.aggregate(pipeline)
            
            patients_data = []
            for result in results:
                latest_visit = result['latest_visit']
                
                patient_data = {
                    'patient_id': result['_id'],
                    'total_visits': result['total_visits'],
                    'last_visit_date': result['last_visit_date'].isoformat(),
                    'last_encounter_id': latest_visit.get('encounter_id'),
                    'last_transcript_id': latest_visit.get('transcript_id'),
                    'status': 'completed' if latest_visit.get('processing_status') in ['extracted', 'validated'] else 'in_progress'
                }
                
                # Dati anagrafica dall'ultima visita
                if (latest_visit.get('clinical_data') and 
                    latest_visit['clinical_data'].get('patient_data')):
                    
                    pd = latest_visit['clinical_data']['patient_data']
                    patient_data.update({
                        'first_name': pd.get('first_name', ''),
                        'last_name': pd.get('last_name', ''),
                        'age': pd.get('age'),
                        'gender': pd.get('gender', ''),
                        'phone': pd.get('phone', ''),
                        'residence_city': pd.get('residence_city', '')
                    })
                
                # Ultimo triage
                if (latest_visit.get('clinical_data') and 
                    latest_visit['clinical_data'].get('clinical_assessment')):
                    
                    ca = latest_visit['clinical_data']['clinical_assessment']
                    patient_data['last_triage_code'] = ca.get('triage_code', '')
                
                patients_data.append(patient_data)
            
            return patients_data
            
        except Exception as e:
            logger.error(f"Errore recupero summary pazienti: {e}")
            return []
    
    def get_visits_today(self) -> int:
        """
        Conta le visite di oggi
        """
        if not self.connected:
            return 0
        
        try:
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = datetime.combine(date.today(), datetime.max.time())
            
            count = AudioTranscript.objects(
                created_at__gte=today_start,
                created_at__lte=today_end
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Errore conteggio visite oggi: {e}")
            return 0
    
    def get_waiting_patients_count(self) -> int:
        """
        Conta pazienti in attesa (visite non completate)
        """
        if not self.connected:
            return 0
        
        try:
            count = AudioTranscript.objects(
                processing_status__in=['pending', 'transcribing', 'transcribed', 'extracting']
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Errore conteggio pazienti in attesa: {e}")
            return 0
    
    def update_patient_data(self, patient_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Aggiorna i dati anagrafici di un paziente nell'ultima visita
        
        Args:
            patient_id: ID paziente Django
            updated_data: Dati aggiornati
            
        Returns:
            True se aggiornamento riuscito
        """
        if not self.connected:
            return False
        
        try:
            # Trova l'ultima visita del paziente
            latest_visit = AudioTranscript.objects(patient_id=patient_id).order_by('-created_at').first()
            
            if not latest_visit:
                logger.warning(f"Nessuna visita trovata per paziente {patient_id}")
                return False
            
            # Aggiorna dati paziente
            if not latest_visit.clinical_data:
                latest_visit.clinical_data = ClinicalData()
            
            if not latest_visit.clinical_data.patient_data:
                latest_visit.clinical_data.patient_data = MedicalPatientData()
            
            pd = latest_visit.clinical_data.patient_data
            
            # Aggiorna campi specificati
            for field, value in updated_data.items():
                if hasattr(pd, field):
                    setattr(pd, field, value)
            
            # Salva modifiche
            latest_visit.save()
            
            logger.info(f"Dati paziente {patient_id} aggiornati")
            return True
            
        except Exception as e:
            logger.error(f"Errore aggiornamento dati paziente: {e}")
            return False
    
    def generate_report_content(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """
        Genera il contenuto per il report PDF
        
        Args:
            transcript_id: ID transcript MongoDB
            
        Returns:
            Dizionario con contenuto strutturato per PDF
        """
        if not self.connected:
            return None
        
        try:
            transcript = AudioTranscript.objects(transcript_id=transcript_id).first()
            
            if not transcript or not transcript.clinical_data:
                logger.warning(f"Transcript {transcript_id} non trovato o senza dati clinici")
                return None
            
            cd = transcript.clinical_data
            pd = cd.patient_data if cd.patient_data else MedicalPatientData()
            vs = cd.vital_signs if cd.vital_signs else VitalSigns()
            ca = cd.clinical_assessment if cd.clinical_assessment else ClinicalAssessment()
            
            # Struttura dati per PDF seguendo il format del Project 2
            report_content = {
                # Anagrafica
                'first_name': pd.first_name or '',
                'last_name': pd.last_name or '',
                'age': pd.age or '',
                'gender': pd.gender or '',
                'birth_date': pd.birth_date or '',
                'birth_place': pd.birth_place or '',
                'residence_city': pd.residence_city or '',
                'residence_address': pd.residence_address or '',
                'phone': pd.phone or '',
                'access_mode': pd.access_mode or '',
                
                # Parametri vitali
                'heart_rate': vs.heart_rate or '',
                'blood_pressure': vs.blood_pressure or '',
                'temperature': vs.temperature or '',
                'oxygenation': vs.oxygenation or '',
                'blood_glucose': vs.blood_glucose or '',
                
                # Valutazione clinica
                'skin_state': ca.skin_state or '',
                'consciousness_state': ca.consciousness_state or '',
                'pupils_state': ca.pupils_state or '',
                'respiratory_state': ca.respiratory_state or '',
                'history': ca.history or '',
                'medications_taken': ca.medications_taken or '',
                'symptoms': ca.symptoms or '',
                'medical_actions': ca.medical_actions or '',
                'assessment': ca.assessment or '',
                'plan': ca.plan or '',
                'triage_code': ca.triage_code or '',
                
                # Metadati
                'visit_date': transcript.created_at.strftime('%d/%m/%Y'),
                'visit_time': transcript.created_at.strftime('%H:%M'),
                'transcript_text': transcript.full_transcript or '',
                'doctor_id': transcript.doctor_id,
                'encounter_id': transcript.encounter_id
            }
            
            return report_content
            
        except Exception as e:
            logger.error(f"Errore generazione contenuto report: {e}")
            return None
    
    def update_transcript_text(self, transcript_id: str, new_text: str) -> bool:
        """
        Aggiorna il testo della trascrizione
        """
        try:
            transcript = AudioTranscript.objects(transcript_id=transcript_id).first()
            if transcript:
                transcript.full_transcript = new_text
                transcript.save()
                logger.info(f"Transcript {transcript_id} aggiornato con nuovo testo")
                return True
            else:
                logger.warning(f"Transcript {transcript_id} non trovato per aggiornamento testo")
                return False
        except Exception as e:
            logger.error(f"Errore aggiornamento testo transcript {transcript_id}: {e}")
            return False
    
    def update_clinical_data(self, transcript_id: str, clinical_dict: Dict[str, Any]) -> bool:
        """
        Aggiorna i dati clinici associati al transcript
        """
        try:
            # Aggiorna i dati del paziente
            transcript = AudioTranscript.objects(transcript_id=transcript_id).first()
            if not transcript:
                logger.warning(f"Transcript {transcript_id} non trovato per aggiornamento dati clinici")
                return False
            
            # Aggiorna MedicalPatientData
            patient_data = MedicalPatientData.objects(transcript=transcript).first()
            if not patient_data:
                patient_data = MedicalPatientData(transcript=transcript)
            
            patient_data.first_name = clinical_dict.get('first_name', '')
            patient_data.last_name = clinical_dict.get('last_name', '')
            patient_data.birth_date = clinical_dict.get('birth_date', '')
            patient_data.gender = clinical_dict.get('gender', '')
            patient_data.save()
            
            # Aggiorna ClinicalAssessment
            clinical_assessment = ClinicalAssessment.objects(transcript=transcript).first()
            if not clinical_assessment:
                clinical_assessment = ClinicalAssessment(transcript=transcript)
            
            clinical_assessment.symptoms = clinical_dict.get('symptoms', '')
            clinical_assessment.assessment = clinical_dict.get('diagnosis', '')
            clinical_assessment.save()
            
            logger.info(f"Dati clinici aggiornati per transcript {transcript_id}")
            return True
            
        except Exception as e:
            logger.error(f"Errore aggiornamento dati clinici per transcript {transcript_id}: {e}")
            return False


# Istanza singleton del servizio
mongodb_service = MongoDBService()