"""
Servizio per la generazione di report clinici in PDF (versione semplificata)
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
import tempfile
from core.models import ClinicalData, ClinicalReport
import logging

logger = logging.getLogger(__name__)

class ReportGenerationService:
    """
    Servizio per la generazione di report clinici in formato PDF
    """
    
    def __init__(self):
        """
        Inizializza il servizio di generazione report
        """
        pass

    def generate_clinical_report(self, clinical_data: ClinicalData) -> ClinicalReport:
        """
        Genera un report clinico PDF da dati clinici strutturati
        
        Args:
            clinical_data: Oggetto ClinicalData con dati estratti
            
        Returns:
            ClinicalReport: Oggetto con report generato
        """
        try:
            # Crea record di report
            report = ClinicalReport.objects.create(
                clinical_data=clinical_data,
                encounter=clinical_data.transcript.encounter
            )
            
            # Per ora genera un semplice file di testo
            text_content = self._generate_text_report(clinical_data)
            
            # Salva il file (per ora come .txt invece di .pdf)
            report.pdf_file.save(
                f"report_{report.report_id}.txt",
                ContentFile(text_content.encode('utf-8')),
                save=True
            )
            
            # Aggiorna stato
            report.is_finalized = True
            report.finalized_at = timezone.now()
            report.save()
            
            logger.info(f"Report generato con successo: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Errore durante la generazione del report: {e}")
            if 'report' in locals():
                # Il modello ClinicalReport non ha campi per gestire errori
                # Possiamo lasciare is_finalized = False
                pass
            raise

    def _generate_text_report(self, clinical_data: ClinicalData) -> str:
        """
        Genera un report in formato testo
        """
        encounter = clinical_data.transcript.encounter
        
        # Debug: log dei tipi di dati
        logger.debug(f"vital_signs type: {type(clinical_data.vital_signs)}, value: {clinical_data.vital_signs}")
        logger.debug(f"physical_examination type: {type(clinical_data.physical_examination)}, value: {clinical_data.physical_examination}")
        
        # Costruiamo un dizionario con i dati clinici dai campi del modello
        data = {
            'informazioni_paziente': {
                'nome_completo': clinical_data.patient_name or '',
                'età': clinical_data.patient_age or '',
                'sesso': clinical_data.patient_gender or ''
            },
            'parametri_vitali': clinical_data.vital_signs or {},
            'motivo_accesso': clinical_data.chief_complaint or '',
            'storia_clinica': clinical_data.history_present_illness or '',
            'anamnesi_patologica': clinical_data.past_medical_history or [],
            'farmaci': clinical_data.medications or [],
            'allergie': clinical_data.allergies or [],
            'esame_obiettivo': clinical_data.physical_examination or {},
            'valutazione': clinical_data.assessment or '',
            'diagnosi': clinical_data.diagnosis or [],
            'piano_terapeutico': clinical_data.treatment_plan or ''
        }
        
        report_lines = [
            "=" * 60,
            "REPORT CLINICO",
            "=" * 60,
            "",
            f"ID Encounter: {encounter.encounter_id}",
            f"Data: {encounter.admission_time.strftime('%d/%m/%Y %H:%M')}",
            f"Medico: {encounter.doctor.get_full_name() if encounter.doctor else 'N/A'}",
            f"Paziente: {encounter.patient.get_full_name() if encounter.patient else 'N/A'}",
            f"Priorità Triage: {encounter.get_triage_priority_display()}",
            f"Motivo accesso: {encounter.chief_complaint}",
            "",
            "-" * 60,
            "INFORMAZIONI PAZIENTE",
            "-" * 60,
        ]
        
        patient_info = data.get('informazioni_paziente', {})
        if patient_info and isinstance(patient_info, dict):
            for key, value in patient_info.items():
                if value:
                    display_key = key.replace('_', ' ').title()
                    report_lines.append(f"{display_key}: {value}")
        elif patient_info and isinstance(patient_info, str):
            report_lines.append(patient_info)
        
        report_lines.extend([
            "",
            "-" * 60,
            "PARAMETRI VITALI",
            "-" * 60,
        ])
        
        vitals = data.get('parametri_vitali', {})
        if vitals and isinstance(vitals, dict):
            for key, value in vitals.items():
                if value:
                    display_key = key.replace('_', ' ').title()
                    report_lines.append(f"{display_key}: {value}")
        elif vitals and isinstance(vitals, list):
            for i, vital in enumerate(vitals, 1):
                report_lines.append(f"{i}. {vital}")
        elif vitals and isinstance(vitals, str):
            report_lines.append(vitals)
        
        # Anamnesi e storia clinica
        if data.get('motivo_accesso'):
            report_lines.extend([
                "",
                "-" * 60,
                "MOTIVO DELL'ACCESSO",
                "-" * 60,
                data['motivo_accesso']
            ])

        if data.get('storia_clinica'):
            report_lines.extend([
                "",
                "-" * 60,
                "STORIA DELLA MALATTIA ATTUALE",
                "-" * 60,
                data['storia_clinica']
            ])

        # Anamnesi patologica remota
        past_history = data.get('anamnesi_patologica', [])
        if past_history:
            report_lines.extend([
                "",
                "-" * 60,
                "ANAMNESI PATOLOGICA REMOTA",
                "-" * 60,
            ])
            for i, item in enumerate(past_history, 1):
                report_lines.append(f"{i}. {item}")
        
        # Farmaci
        medications = data.get('farmaci', [])
        if medications:
            report_lines.extend([
                "",
                "-" * 60,
                "TERAPIE IN CORSO",
                "-" * 60,
            ])
            for i, med in enumerate(medications, 1):
                report_lines.append(f"{i}. {med}")
        
        # Allergie
        allergies = data.get('allergie', [])
        if allergies:
            report_lines.extend([
                "",
                "-" * 60,
                "ALLERGIE",
                "-" * 60,
            ])
            for i, allergy in enumerate(allergies, 1):
                report_lines.append(f"{i}. {allergy}")

        # Esame obiettivo
        exam = data.get('esame_obiettivo', {})
        if exam:
            report_lines.extend([
                "",
                "-" * 60,
                "ESAME OBIETTIVO",
                "-" * 60,
            ])
            if isinstance(exam, dict):
                for key, value in exam.items():
                    if value:
                        display_key = key.replace('_', ' ').title()
                        report_lines.append(f"{display_key}: {value}")
            elif isinstance(exam, list):
                for i, item in enumerate(exam, 1):
                    report_lines.append(f"{i}. {item}")
            elif isinstance(exam, str):
                report_lines.append(exam)
        
        # Diagnosi
        diagnoses = data.get('diagnosi', [])
        if diagnoses:
            report_lines.extend([
                "",
                "-" * 60,
                "DIAGNOSI",
                "-" * 60,
            ])
            for i, diagnosis in enumerate(diagnoses, 1):
                report_lines.append(f"{i}. {diagnosis}")

        # Valutazione
        if data.get('valutazione'):
            report_lines.extend([
                "",
                "-" * 60,
                "VALUTAZIONE CLINICA",
                "-" * 60,
                data['valutazione']
            ])

        # Piano terapeutico
        if data.get('piano_terapeutico'):
            report_lines.extend([
                "",
                "-" * 60,
                "PIANO TERAPEUTICO",
                "-" * 60,
                data['piano_terapeutico']
            ])
        
        # Informazioni tecniche
        report_lines.extend([
            "",
            "-" * 60,
            "INFORMAZIONI TECNICHE",
            "-" * 60,
            f"Data Generazione: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"ID Trascrizione: {clinical_data.transcript.transcript_id}",
            f"Confidenza Trascrizione: {clinical_data.transcript.confidence_score * 100:.1f}%" if clinical_data.transcript.confidence_score else "N/A",
            f"Confidenza Estrazione: {clinical_data.confidence_score * 100:.1f}%" if clinical_data.confidence_score else "N/A",
            f"Durata Audio: {clinical_data.transcript.audio_duration:.1f} secondi" if clinical_data.transcript.audio_duration else "Durata Audio: N/A",
            "",
            "DISCLAIMER:",
            "Questo report è stato generato automaticamente da un sistema di trascrizione",
            "e analisi del linguaggio naturale. Le informazioni contenute devono essere",
            "verificate e validate da personale medico qualificato prima di qualsiasi",
            "utilizzo clinico.",
            "",
            "=" * 60,
        ])
        
        return "\n".join(report_lines)