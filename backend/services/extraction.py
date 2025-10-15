"""
Service for extracting clinical data using LLM
"""

import json
import re
from typing import Dict, List, Optional, Any
from core.models import AudioTranscript, ClinicalData
import logging

logger = logging.getLogger(__name__)


class ClinicalExtractionService:
    """
    Service for extracting structured clinical data from transcripts
    """
    
    def __init__(self):
        """
        Initialize the extraction service
        """
        # Template for extraction based on reference projects
        self.extraction_template = {
            "informazioni_paziente": {
                "nome": "",
                "cognome": "",
                "data_nascita": "",
                "codice_fiscale": "",
                "sesso": "",
                "età": ""
            },
            "parametri_vitali": {
                "pressione_arteriosa": "",
                "frequenza_cardiaca": "",
                "temperatura": "",
                "saturazione_ossigeno": "",
                "frequenza_respiratoria": ""
            },
            "sintomi": [],
            "esami_clinici": [],
            "diagnosi": [],
            "terapie": [],
            "allergie": [],
            "storia_clinica": "",
            "note_mediche": "",
            "priorità_triage": ""
        }

    def extract_clinical_data(self, transcript: AudioTranscript) -> ClinicalData:
        """
        Extract structured clinical data from a transcript

        :param transcript: AudioTranscript object to process
        :type transcript: AudioTranscript
        :returns: ClinicalData: Object with extracted clinical data
        :rtype: ClinicalData
        :raises Exception: If extraction fails
        """
        try:
            # Crea record di dati clinici
            clinical_data = ClinicalData.objects.create(
                transcript=transcript
            )
            
            # Estrai i dati dal testo
            text = transcript.transcript_text
            extracted_data = self._extract_structured_data(text)
            
            # Popola i campi del modello con i dati estratti
            self._populate_clinical_data_fields(clinical_data, extracted_data)
            
            # Calcola confidence score
            clinical_data.confidence_score = self._calculate_extraction_confidence(extracted_data)
            clinical_data.save()
            
            logger.info(f"Estrazione completata per clinical_data {clinical_data.id}")
            return clinical_data
            
        except Exception as e:
            logger.error(f"Errore durante l'estrazione: {e}")
            if 'clinical_data' in locals():
                # Non possiamo impostare un campo 'status' che non esiste
                # Invece, possiamo eliminare il record parziale o lasciarlo incompleto
                pass
            raise

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from text using regex patterns and heuristic logic
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: Dictionary with extracted data
        :rtype: Dict[str, Any]
        """
        data = self.extraction_template.copy()
        
        # Estrazione informazioni paziente
        data["informazioni_paziente"] = self._extract_patient_info(text)
        
        # Estrazione parametri vitali
        data["parametri_vitali"] = self._extract_vital_signs(text)
        
        # Estrazione sintomi
        data["sintomi"] = self._extract_symptoms(text)
        
        # Estrazione esami
        data["esami_clinici"] = self._extract_clinical_tests(text)
        
        # Estrazione diagnosi
        data["diagnosi"] = self._extract_diagnoses(text)
        
        # Estrazione terapie
        data["terapie"] = self._extract_therapies(text)
        
        # Estrazione allergie
        data["allergie"] = self._extract_allergies(text)
        
        # Estrazione storia clinica
        data["storia_clinica"] = self._extract_medical_history(text)
        
        # Estrazione note mediche
        data["note_mediche"] = self._extract_medical_notes(text)
        
        # Determinazione priorità triage
        data["priorità_triage"] = self._determine_triage_priority(data)
        
        return data

    def _extract_patient_info(self, text: str) -> Dict[str, str]:
        """
        Extract patient information
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: Dictionary with patient information
        :rtype: Dict[str, str]
        """
        info = {}
        
        # Nome e cognome
        name_patterns = [
            r"il\s+paziente\s+(\w+)\s+(\w+)",
            r"la\s+paziente\s+(\w+)\s+(\w+)",
            r"signor[ea]?\s+(\w+)\s+(\w+)",
            r"nome\s*:\s*(\w+)\s+(\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["nome"] = match.group(1)
                info["cognome"] = match.group(2)
                break
        
        # Età
        age_match = re.search(r"(\d{1,3})\s*anni?", text, re.IGNORECASE)
        if age_match:
            info["età"] = age_match.group(1)
        
        # Sesso
        if re.search(r"\b(maschio|uomo|signore?)\b", text, re.IGNORECASE):
            info["sesso"] = "M"
        elif re.search(r"\b(femmina|donna|signora)\b", text, re.IGNORECASE):
            info["sesso"] = "F"
        
        return info

    def _extract_vital_signs(self, text: str) -> Dict[str, str]:
        """
        Extract vital signs
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: Dictionary with vital signs
        :rtype: Dict[str, str]
        """
        vitals = {}
        
        # Pressione arteriosa
        bp_patterns = [
            r"pressione\s*(?:arteriosa)?\s*(?:è|di)?\s*(\d{2,3})/(\d{2,3})",
            r"(\d{2,3})/(\d{2,3})\s*mmHg",
            r"(\d{2,3})\s*su\s*(\d{2,3})"
        ]
        
        for pattern in bp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vitals["pressione_arteriosa"] = f"{match.group(1)}/{match.group(2)} mmHg"
                break
        
        # Frequenza cardiaca
        hr_patterns = [
            r"frequenza\s*cardiaca\s*(?:è|di)?\s*(\d{2,3})",
            r"(\d{2,3})\s*bpm",
            r"battiti\s*(?:al\s*minuto)?\s*(\d{2,3})"
        ]
        
        for pattern in hr_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vitals["frequenza_cardiaca"] = f"{match.group(1)} bpm"
                break
        
        # Temperatura
        temp_patterns = [
            r"temperatura\s*(?:corporea)?\s*(?:è|di)?\s*(\d{2,3}(?:\.\d)?)\s*°?C?",
            r"febbre\s*(?:a)?\s*(\d{2,3}(?:\.\d)?)\s*°?C?"
        ]
        
        for pattern in temp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vitals["temperatura"] = f"{match.group(1)}°C"
                break
        
        # Saturazione ossigeno
        sat_patterns = [
            r"saturazione\s*(?:ossigeno)?\s*(?:è|di)?\s*(\d{2,3})%?",
            r"SpO2\s*(\d{2,3})%?"
        ]
        
        for pattern in sat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vitals["saturazione_ossigeno"] = f"{match.group(1)}%"
                break
        
        return vitals

    def _extract_symptoms(self, text: str) -> List[str]:
        """
        Extract symptoms from text
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: List of symptoms
        :rtype: List[str]
        """
        symptoms = []
        
        symptom_patterns = [
            r"dolore\s+(?:al|alla|ai|alle)\s+(\w+)",
            r"sintomi?\s*(?:di|sono|è|include)?\s*([^.]+)",
            r"si\s+presenta\s+con\s+([^.]+)",
            r"lamenta\s+([^.]+)",
            r"accusa\s+([^.]+)"
        ]
        
        for pattern in symptom_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                symptom = match.group(1).strip()
                if len(symptom) > 3 and symptom not in symptoms:
                    symptoms.append(symptom)
        
        return symptoms

    def _extract_clinical_tests(self, text: str) -> List[str]:
        """
        Extract clinical tests
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: List of clinical tests
        :rtype: List[str]
        """
        tests = []
        
        test_patterns = [
            r"esame\s+(?:del|della|dei|delle)?\s*(\w+)",
            r"analisi\s+(?:del|della|dei|delle)?\s*(\w+)",
            r"radiografia\s+(?:del|della|dei|delle)?\s*(\w+)",
            r"ecografia\s+(?:del|della|dei|delle)?\s*(\w+)",
            r"TAC\s+(?:del|della|dei|delle)?\s*(\w+)",
            r"risonanza\s+(?:del|della|dei|delle)?\s*(\w+)"
        ]
        
        for pattern in test_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                test = f"{match.group(0)}"
                if test not in tests:
                    tests.append(test)
        
        return tests

    def _extract_diagnoses(self, text: str) -> List[str]:
        """
        Extract diagnoses from text
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: List of diagnoses
        :rtype: List[str]
        """
        diagnoses = []
        
        diagnosis_patterns = [
            r"diagnosi\s*(?:è|di)?\s*([^.]+)",
            r"diagnosticato\s+(?:con)?\s*([^.]+)",
            r"presenta\s+(?:una|un)?\s*([^.]+)",
            r"sospetto\s+(?:di)?\s*([^.]+)"
        ]
        
        for pattern in diagnosis_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                diagnosis = match.group(1).strip()
                if len(diagnosis) > 3 and diagnosis not in diagnoses:
                    diagnoses.append(diagnosis)
        
        return diagnoses

    def _extract_therapies(self, text: str) -> List[str]:
        """
        Extract therapies and medications from text
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: List of therapies/medications
        :rtype: List[str]
        """
        therapies = []
        
        therapy_patterns = [
            r"terapia\s+(?:con)?\s*([^.]+)",
            r"farmaco\s*([^.]+)",
            r"prescri(?:tto|zione)\s*([^.]+)",
            r"somministrar[eio]\s*([^.]+)",
            r"assumere\s*([^.]+)"
        ]
        
        for pattern in therapy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                therapy = match.group(1).strip()
                if len(therapy) > 3 and therapy not in therapies:
                    therapies.append(therapy)
        
        return therapies

    def _extract_allergies(self, text: str) -> List[str]:
        """
        Extract allergies from text
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: List of allergies
        :rtype: List[str]
        """
        allergies = []
        
        allergy_patterns = [
            r"allergi[ca]?\s+(?:a|al|alla|ai|alle)?\s*([^.]+)",
            r"intolleranz[ea]\s+(?:a|al|alla|ai|alle)?\s*([^.]+)",
            r"reazion[ei]\s+avvers[ea]\s+(?:a|al|alla|ai|alle)?\s*([^.]+)"
        ]
        
        for pattern in allergy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                allergy = match.group(1).strip()
                if len(allergy) > 2 and allergy not in allergies:
                    allergies.append(allergy)
        
        return allergies

    def _extract_medical_history(self, text: str) -> str:
        """
        Extract medical history from text
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: Medical history as a string
        :rtype: str
        """
        history_patterns = [
            r"storia\s+clinic[a]?\s*:?\s*([^.]+)",
            r"anamnesi\s*:?\s*([^.]+)",
            r"precedenti\s+(?:medici|clinici)\s*:?\s*([^.]+)"
        ]
        
        for pattern in history_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""

    def _extract_medical_notes(self, text: str) -> str:
        """
        Extract general medical notes from text
        
        :param text: Transcript text to analyze
        :type text: str
        :returns: Medical notes as a string
        :rtype: str
        """
        # Rimuovi parti già estratte e mantieni il resto come note
        cleaned_text = text
        
        # Rimuovi pattern già estratti
        patterns_to_remove = [
            r"pressione\s*(?:arteriosa)?\s*(?:è|di)?\s*\d{2,3}/\d{2,3}",
            r"frequenza\s*cardiaca\s*(?:è|di)?\s*\d{2,3}",
            r"temperatura\s*(?:corporea)?\s*(?:è|di)?\s*\d{2,3}(?:\.\d)?°?C?"
        ]
        
        for pattern in patterns_to_remove:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)
        
        return cleaned_text.strip()

    def _determine_triage_priority(self, data: Dict[str, Any]) -> str:
        """
        Determine triage priority based on extracted data
        
        :param data: Extracted clinical data
        :type data: Dict[str, Any]
        :returns: Triage priority level ("ALTA", "MEDIA", "BASSA")
        :rtype: str
        """
        # Logica di priorità basata sui sintomi e parametri vitali
        vitals = data.get("parametri_vitali", {})
        symptoms = data.get("sintomi", [])
        
        # Priorità ALTA se ci sono parametri vitali critici
        if vitals.get("pressione_arteriosa"):
            bp = vitals["pressione_arteriosa"]
            bp_match = re.search(r"(\d+)/(\d+)", bp)
            if bp_match:
                systolic = int(bp_match.group(1))
                diastolic = int(bp_match.group(2))
                if systolic > 180 or diastolic > 110 or systolic < 90:
                    return "ALTA"
        
        if vitals.get("frequenza_cardiaca"):
            hr_match = re.search(r"(\d+)", vitals["frequenza_cardiaca"])
            if hr_match:
                hr = int(hr_match.group(1))
                if hr > 120 or hr < 50:
                    return "ALTA"
        
        # Priorità ALTA per sintomi critici
        critical_symptoms = ["dolore toracico", "difficoltà respiratoria", "perdita coscienza"]
        for symptom in symptoms:
            for critical in critical_symptoms:
                if critical.lower() in symptom.lower():
                    return "ALTA"
        
        # Priorità MEDIA per sintomi moderati
        moderate_symptoms = ["dolore", "febbre", "nausea"]
        for symptom in symptoms:
            for moderate in moderate_symptoms:
                if moderate.lower() in symptom.lower():
                    return "MEDIA"
        
        return "BASSA"

    def _calculate_extraction_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calculate a confidence score for the extraction
        
        :param data: Extracted clinical data
        :type data: Dict[str, Any]
        :returns: Confidence score between 0.0 and 1.0
        :rtype: float
        """
        total_fields = 0
        filled_fields = 0
        
        for section, content in data.items():
            if isinstance(content, dict):
                for field, value in content.items():
                    total_fields += 1
                    if value and value.strip():
                        filled_fields += 1
            elif isinstance(content, list):
                total_fields += 1
                if content:
                    filled_fields += 1
            elif isinstance(content, str):
                total_fields += 1
                if content and content.strip():
                    filled_fields += 1
        
        if total_fields == 0:
            return 0.0
        
        return filled_fields / total_fields

    def _populate_clinical_data_fields(self, clinical_data: ClinicalData, extracted_data: Dict[str, Any]) -> None:
        """
        Populate the ClinicalData model fields with extracted data
        
        :param clinical_data: ClinicalData object to populate
        :type clinical_data: ClinicalData
        :param extracted_data: Dictionary with extracted clinical data
        :type extracted_data: Dict[str, Any]
        :returns: None
        :rtype: None
        """
        try:
            # Informazioni paziente
            patient_info = extracted_data.get("informazioni_paziente", {})
            clinical_data.patient_name = f"{patient_info.get('nome', '')} {patient_info.get('cognome', '')}".strip()
            
            if patient_info.get('età'):
                try:
                    clinical_data.patient_age = int(patient_info['età'])
                except (ValueError, TypeError):
                    pass
            
            clinical_data.patient_gender = patient_info.get('sesso', '')
            
            # Anamnesi
            clinical_data.chief_complaint = extracted_data.get("sintomi_principali", "")
            clinical_data.history_present_illness = extracted_data.get("storia_clinica", "")
            
            # Liste JSON
            clinical_data.past_medical_history = extracted_data.get("storia_medica", [])
            clinical_data.medications = extracted_data.get("terapie", [])
            clinical_data.allergies = extracted_data.get("allergie", [])
            clinical_data.diagnosis = extracted_data.get("diagnosi", [])
            
            # Parametri vitali e esame obiettivo
            clinical_data.vital_signs = extracted_data.get("parametri_vitali", {})
            clinical_data.physical_examination = extracted_data.get("esami_clinici", {})
            
            # Valutazione e piano
            clinical_data.assessment = extracted_data.get("note_mediche", "")
            clinical_data.treatment_plan = extracted_data.get("piano_terapeutico", "")
            
        except Exception as e:
            logger.error(f"Errore nel popolare i campi di ClinicalData: {e}")
            # Non sollevare l'errore, continua con i campi che siamo riusciti a popolare