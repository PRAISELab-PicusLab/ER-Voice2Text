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
    
    def save_patient_visit_transcript_only(self, encounter_id: str, patient_id: str, doctor_id: str, 
                                          audio_file_path: str, transcript_text: str, 
                                          triage_code: str = None, symptoms: str = None, 
                                          triage_notes: str = None) -> Optional[str]:
        """
        Salva una nuova visita paziente con SOLO trascrizione (senza dati clinici estratti)
        
        Args:
            encounter_id: ID encounter Django
            patient_id: ID paziente Django
            doctor_id: ID medico Django
            audio_file_path: Path file audio
            transcript_text: Testo trascrizione
            triage_code: Codice triage (white, green, yellow, red, black)
            symptoms: Sintomi principali
            triage_notes: Note del triage
            
        Returns:
            ID del transcript MongoDB creato
        """
        if not self.connected:
            logger.error("MongoDB non connesso")
            return None
        
        try:
            # Crea documento AudioTranscript con dati iniziali del triage
            transcript_doc = AudioTranscript()
            transcript_doc.encounter_id = encounter_id
            transcript_doc.patient_id = patient_id
            transcript_doc.doctor_id = doctor_id
            transcript_doc.audio_file_path = audio_file_path
            transcript_doc.full_transcript = transcript_text
            transcript_doc.processing_status = 'transcribed'  # Solo trascritto, non estratto
            
            # Se abbiamo dati iniziali del triage, crea una struttura clinica di base
            if triage_code or symptoms or triage_notes:
                clinical_data = ClinicalData()
                
                # Crea assessment con i dati iniziali del triage
                clinical_assessment = ClinicalAssessment()
                if triage_code:
                    clinical_assessment.triage_code = triage_code
                if symptoms:
                    clinical_assessment.symptoms = symptoms
                if triage_notes:
                    clinical_assessment.history = triage_notes  # Salva le note nei dati storici
                
                clinical_data.clinical_assessment = clinical_assessment
                transcript_doc.clinical_data = clinical_data
            else:
                transcript_doc.clinical_data = None  # Nessun dato clinico inizialmente
            
            # Salva il documento
            transcript_doc.save()
            
            logger.info(f"Transcript salvato con ID: {transcript_doc.transcript_id}, triage: {triage_code}")
            return str(transcript_doc.transcript_id)
            
        except Exception as e:
            logger.error(f"Errore salvataggio transcript: {e}")
            return None
    
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
                    patient_data.codice_fiscale = extracted.get('codice_fiscale', '')
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
        Conta TUTTE le emergenze di oggi (create oggi, sia completate che in corso)
        """
        if not self.connected:
            return 0
        
        try:
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_end = datetime.combine(date.today(), datetime.max.time())
            
            # Conta TUTTE le visite create oggi
            count = AudioTranscript.objects(
                created_at__gte=today_start,
                created_at__lte=today_end
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Errore conteggio emergenze oggi: {e}")
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
    
    def get_completed_visits_today(self) -> int:
        """
        Conta TUTTE le visite completate (con status 'extracted' o 'validated')
        """
        if not self.connected:
            return 0

        try:
            # Conta TUTTE le visite completate, non solo quelle di oggi
            count = AudioTranscript.objects(
                processing_status__in=['extracted', 'validated']
            ).count()

            return count

        except Exception as e:
            logger.error(f"Errore conteggio visite completate: {e}")
            return 0
    
    def get_unique_patients(self) -> List[Dict[str, Any]]:
        """
        Recupera lista di pazienti unici raggruppati per codice fiscale da tutti gli interventi
        """
        if not self.connected:
            return []
        
        try:
            # Recupera tutti i transcript con dati clinici
            transcripts = AudioTranscript.objects(clinical_data__exists=True).only(
                'transcript_id', 'clinical_data', 'created_at', 'processing_status'
            )
            
            # Raggruppa per codice fiscale
            patients_dict = {}
            
            for transcript in transcripts:
                if not transcript.clinical_data or not transcript.clinical_data.patient_data:
                    continue
                
                pd = transcript.clinical_data.patient_data
                codice_fiscale = pd.codice_fiscale
                
                # Salta se non c'è codice fiscale
                if not codice_fiscale:
                    continue
                
                # Se il paziente non esiste ancora nel dizionario, crealo
                if codice_fiscale not in patients_dict:
                    patients_dict[codice_fiscale] = {
                        'patient_id': codice_fiscale,  # Usa codice fiscale come ID unico
                        'fiscal_code': codice_fiscale,
                        'codice_fiscale': codice_fiscale,
                        'first_name': pd.first_name or '',
                        'last_name': pd.last_name or '',
                        'age': pd.age or '',
                        'gender': pd.gender or '',
                        'phone': pd.phone or '',
                        'residence_city': pd.residence_city or '',
                        'residence_address': pd.residence_address or '',
                        'total_visits': 0,
                        'last_visit_date': None,
                        'last_triage_code': '',
                        'status': 'completed',  # Default status
                        'interventions': []  # Lista degli ID interventi
                    }
                
                patient = patients_dict[codice_fiscale]
                
                # Aggiorna statistiche visite
                patient['total_visits'] += 1
                patient['interventions'].append(transcript.transcript_id)
                
                # Aggiorna ultima visita se questa è più recente
                if (not patient['last_visit_date'] or 
                    transcript.created_at > patient['last_visit_date']):
                    patient['last_visit_date'] = transcript.created_at
                    
                    # Aggiorna ultimo codice triage se disponibile
                    if (transcript.clinical_data.clinical_assessment and 
                        transcript.clinical_data.clinical_assessment.triage_code):
                        patient['last_triage_code'] = transcript.clinical_data.clinical_assessment.triage_code
                
                # Aggiorna status in base all'ultimo processing_status
                if transcript.processing_status == 'in_progress':
                    patient['status'] = 'in_progress'
                elif patient['status'] != 'in_progress':  # Non sovrascrive in_progress
                    patient['status'] = 'completed' if transcript.processing_status == 'extracted' else 'waiting'
            
            # Converti in lista e formatta date
            patients_list = []
            for patient in patients_dict.values():
                if patient['last_visit_date']:
                    patient['last_visit_date'] = patient['last_visit_date'].isoformat()
                patients_list.append(patient)
            
            # Ordina per cognome, nome
            patients_list.sort(key=lambda p: (p.get('last_name', ''), p.get('first_name', '')))
            
            return patients_list
            
        except Exception as e:
            logger.error(f"Errore recupero pazienti unici: {e}")
            return []
    
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
                'codice_fiscale': pd.codice_fiscale or '',
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
            transcript = AudioTranscript.objects(transcript_id=transcript_id).first()
            if not transcript:
                logger.warning(f"Transcript {transcript_id} non trovato per aggiornamento dati clinici")
                return False
            
            # Crea o aggiorna i dati clinici completi
            if not transcript.clinical_data:
                transcript.clinical_data = ClinicalData()
            
            cd = transcript.clinical_data
            
            # Aggiorna dati paziente
            if not cd.patient_data:
                cd.patient_data = MedicalPatientData()
            
            pd = cd.patient_data
            
            # Funzione helper per gestire valori sicuri (inclusi array)
            def safe_str(value):
                if isinstance(value, list):
                    # Se è un array, prendi il primo elemento se disponibile
                    return str(value[0]) if value and len(value) > 0 else ''
                return str(value) if value is not None else ''
            
            # Aggiorna i campi del paziente con gestione sicura
            pd.first_name = safe_str(clinical_dict.get('first_name', ''))
            pd.last_name = safe_str(clinical_dict.get('last_name', ''))
            
            # Per il codice fiscale, preserva quello esistente se il nuovo è vuoto
            new_codice_fiscale = safe_str(clinical_dict.get('codice_fiscale', ''))
            existing_codice_fiscale = pd.codice_fiscale or ''
            
            if new_codice_fiscale.strip():  # Solo se il nuovo valore non è vuoto
                pd.codice_fiscale = new_codice_fiscale
            # Altrimenti mantieni quello esistente (non sovrascrivere con stringa vuota)
            
            pd.birth_date = safe_str(clinical_dict.get('birth_date', ''))
            pd.birth_place = safe_str(clinical_dict.get('birth_place', ''))
            pd.gender = safe_str(clinical_dict.get('gender', ''))
            pd.phone = safe_str(clinical_dict.get('phone', ''))
            pd.residence_city = safe_str(clinical_dict.get('residence_city', ''))
            pd.residence_address = safe_str(clinical_dict.get('residence_address', ''))
            pd.access_mode = safe_str(clinical_dict.get('access_mode', ''))
            
            # Gestisci età come int
            age_value = clinical_dict.get('age')
            if age_value and age_value != '':
                try:
                    if isinstance(age_value, list) and age_value:
                        age_value = age_value[0]
                    pd.age = int(age_value)
                except (ValueError, TypeError):
                    pd.age = None
            
            # Aggiorna parametri vitali con gestione sicura
            if not cd.vital_signs:
                cd.vital_signs = VitalSigns()
            
            vs = cd.vital_signs
            # I vital signs devono essere stringhe, non array
            vs.heart_rate = safe_str(clinical_dict.get('heart_rate', ''))
            vs.blood_pressure = safe_str(clinical_dict.get('blood_pressure', ''))
            vs.oxygenation = safe_str(clinical_dict.get('oxygen_saturation', ''))
            vs.blood_glucose = safe_str(clinical_dict.get('blood_glucose', ''))
            
            # Gestisci temperatura come float
            temp_value = clinical_dict.get('temperature')
            if temp_value and temp_value != '':
                try:
                    if isinstance(temp_value, list) and temp_value:
                        temp_value = temp_value[0]
                    vs.temperature = float(temp_value)
                except (ValueError, TypeError):
                    vs.temperature = None
            
            # Aggiorna valutazione clinica con gestione sicura
            if not cd.clinical_assessment:
                cd.clinical_assessment = ClinicalAssessment()
            
            ca = cd.clinical_assessment
            ca.symptoms = safe_str(clinical_dict.get('symptoms', ''))
            ca.assessment = safe_str(clinical_dict.get('diagnosis', ''))
            ca.triage_code = safe_str(clinical_dict.get('triage_code', ''))
            ca.skin_state = safe_str(clinical_dict.get('skin_state', ''))
            ca.consciousness_state = safe_str(clinical_dict.get('consciousness_state', ''))
            ca.pupils_state = safe_str(clinical_dict.get('pupils_state', ''))
            ca.respiratory_state = safe_str(clinical_dict.get('respiratory_state', ''))
            ca.history = safe_str(clinical_dict.get('history', ''))
            ca.medications_taken = safe_str(clinical_dict.get('medications_taken', ''))
            ca.medical_actions = safe_str(clinical_dict.get('medical_actions', ''))
            ca.plan = safe_str(clinical_dict.get('plan', ''))
            
            # Aggiorna metadati
            cd.extraction_timestamp = datetime.utcnow()
            cd.is_validated = True  # Consideralo validato visto che viene dall'interfaccia
            
            # Aggiorna status transcript
            transcript.processing_status = 'extracted'
            transcript.save()
            
            logger.info(f"Dati clinici aggiornati con successo per transcript {transcript_id}")
            return True
            
        except Exception as e:
            logger.error(f"Errore aggiornamento dati clinici per transcript {transcript_id}: {e}")
            logger.error(f"Dati ricevuti: {clinical_dict}")
            logger.error(f"Traceback completo: ", exc_info=True)
            return False
    
    def get_all_visits_summary(self) -> List[Dict[str, Any]]:
        """
        Recupera una lista riassuntiva di tutte le visite/interventi
        
        Returns:
            Lista di dizionari con informazioni riassuntive
        """
        if not self.connected:
            return []
        
        try:
            transcripts = AudioTranscript.objects().order_by('-created_at')
            
            visits_summary = []
            for transcript in transcripts:
                cd = transcript.clinical_data if transcript.clinical_data else None
                pd = cd.patient_data if cd and cd.patient_data else None
                ca = cd.clinical_assessment if cd and cd.clinical_assessment else None
                
                # Mapping degli stati per il frontend
                status_mapping = {
                    'pending': 'In Attesa',
                    'transcribing': 'In Attesa', 
                    'transcribed': 'In Attesa',
                    'extracting': 'In Attesa',
                    'extracted': 'Completato',
                    'validated': 'Completato',
                    'error': 'In Attesa',
                    'processed': 'Completato'
                }
                
                raw_status = transcript.processing_status or 'processed'
                display_status = status_mapping.get(raw_status, 'In Attesa')
                
                visit_info = {
                    'transcript_id': transcript.transcript_id,
                    'encounter_id': transcript.encounter_id,
                    'patient_id': transcript.patient_id,
                    'doctor_id': transcript.doctor_id,
                    'visit_date': transcript.created_at.strftime('%d/%m/%Y'),
                    'visit_time': transcript.created_at.strftime('%H:%M'),
                    'patient_name': f"{pd.first_name or ''} {pd.last_name or ''}".strip() if pd else 'Paziente Anonimo',
                    'fiscal_code': pd.codice_fiscale if pd else '',  # Per compatibilità filtri
                    'codice_fiscale': pd.codice_fiscale if pd else '',  # Per visualizzazione
                    'triage_code': ca.triage_code if ca else '',
                    'symptoms': ca.symptoms[:100] + '...' if ca and ca.symptoms and len(ca.symptoms) > 100 else (ca.symptoms if ca else ''),
                    'status': display_status,
                    'raw_status': raw_status,  # Mantieni lo stato originale per debug
                    'has_clinical_data': bool(cd),
                    'created_at': transcript.created_at.isoformat()
                }
                
                visits_summary.append(visit_info)
            
            return visits_summary
            
        except Exception as e:
            logger.error(f"Errore recupero lista visite: {e}")
            return []
    
    def get_visit_data(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera i dati completi di una visita/transcript
        
        Args:
            transcript_id: ID del transcript
            
        Returns:
            Dizionario con i dati della visita o None se non trovato
        """
        if not self.connected:
            return None
        
        try:
            transcript = AudioTranscript.objects(transcript_id=transcript_id).first()
            
            if not transcript:
                logger.warning(f"Transcript {transcript_id} non trovato")
                return None
            
            cd = transcript.clinical_data if transcript.clinical_data else None
            pd = cd.patient_data if cd and cd.patient_data else None
            vs = cd.vital_signs if cd and cd.vital_signs else None
            ca = cd.clinical_assessment if cd and cd.clinical_assessment else None
            
            visit_data = {
                'transcript_id': transcript.transcript_id,
                'encounter_id': transcript.encounter_id,
                'patient_id': transcript.patient_id,
                'doctor_id': transcript.doctor_id,
                'audio_file_path': transcript.audio_file_path,
                'transcript_text': transcript.full_transcript,
                'processing_status': transcript.processing_status,
                'created_at': transcript.created_at.isoformat(),
                'has_clinical_data': bool(cd),
                'clinical_data': {}
            }
            
            # Aggiungi dati clinici se presenti
            if cd:
                clinical_data = {}
                
                if pd:
                    clinical_data['patient_data'] = {
                        'first_name': pd.first_name or '',
                        'last_name': pd.last_name or '',
                        'codice_fiscale': pd.codice_fiscale or '',
                        'age': pd.age or '',
                        'gender': pd.gender or '',
                        'birth_date': pd.birth_date or '',
                        'birth_place': pd.birth_place or '',
                        'residence_city': pd.residence_city or '',
                        'residence_address': pd.residence_address or '',
                        'phone': pd.phone or '',
                        'access_mode': pd.access_mode or ''
                    }
                
                if vs:
                    clinical_data['vital_signs'] = {
                        'heart_rate': vs.heart_rate or '',
                        'blood_pressure': vs.blood_pressure or '',
                        'temperature': vs.temperature or '',
                        'oxygen_saturation': vs.oxygenation or '',  # mapping per compatibilità frontend
                        'oxygenation': vs.oxygenation or '',
                        'blood_glucose': vs.blood_glucose or ''
                    }
                
                if ca:
                    clinical_data['clinical_assessment'] = {
                        'symptoms': ca.symptoms or '',
                        'diagnosis': ca.assessment or '',  # mapping per compatibilità frontend
                        'assessment': ca.assessment or '',
                        'treatment': ca.medical_actions or '',  # mapping per compatibilità frontend
                        'medical_notes': ca.plan or '',  # mapping per compatibilità frontend
                        'triage_code': ca.triage_code or '',
                        'skin_state': ca.skin_state or '',
                        'consciousness_state': ca.consciousness_state or '',
                        'pupils_state': ca.pupils_state or '',
                        'respiratory_state': ca.respiratory_state or '',
                        'history': ca.history or '',
                        'medications_taken': ca.medications_taken or '',
                        'medical_actions': ca.medical_actions or '',
                        'plan': ca.plan or ''
                    }
                
                visit_data['clinical_data'] = clinical_data
            
            return visit_data
            
        except Exception as e:
            logger.error(f"Errore recupero dati visita {transcript_id}: {e}")
            return None

    def delete_visit(self, transcript_id: str) -> bool:
        """
        Elimina una visita da MongoDB
        
        Args:
            transcript_id: ID del transcript da eliminare
            
        Returns:
            True se eliminazione riuscita, False altrimenti
        """
        if not self.connected:
            return False
        
        try:
            # Trova il transcript
            transcript = AudioTranscript.objects(transcript_id=transcript_id).first()
            
            if not transcript:
                logger.warning(f"Transcript non trovato per eliminazione: {transcript_id}")
                return False
            
            # Elimina eventuali report clinici associati
            ClinicalReport.objects(transcript_id=transcript_id).delete()
            
            # Elimina il transcript (i dati clinici embedded vengono eliminati automaticamente)
            transcript.delete()
            
            logger.info(f"Visita eliminata con successo: {transcript_id}")
            return True
            
        except Exception as e:
            logger.error(f"Errore eliminazione visita {transcript_id}: {e}")
            return False


# Istanza singleton del servizio
mongodb_service = MongoDBService()