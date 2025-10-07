"""
Servizio per la generazione di report clinici in PDF
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
        self.styles = None
        
    def _load_reportlab(self):
        """
        Carica ReportLab solo quando necessario (lazy loading)
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            self.reportlab_modules = {
                'colors': colors,
                'A4': A4,
                'SimpleDocTemplate': SimpleDocDocument,
                'Table': Table,
                'TableStyle': TableStyle,
                'Paragraph': Paragraph,
                'Spacer': Spacer,
                'getSampleStyleSheet': getSampleStyleSheet,
                'ParagraphStyle': ParagraphStyle,
                'inch': inch,
                'TA_CENTER': TA_CENTER,
                'TA_LEFT': TA_LEFT,
                'TA_JUSTIFY': TA_JUSTIFY
            }
            
            if self.styles is None:
                self.styles = getSampleStyleSheet()
                self._setup_custom_styles()
            
            return True
            
        except ImportError:
            logger.error("ReportLab non installato. Installa con: pip install reportlab")
            return False
        except Exception as e:
            logger.error(f"Errore nel caricamento di ReportLab: {e}")
            return False

    def _setup_custom_styles(self):
        """
        Configura stili personalizzati per il PDF
        """
        # Stile titolo principale
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Stile sezione
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceBefore=15,
            spaceAfter=10,
            leftIndent=0
        ))
        
        # Stile sottosezione
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.black,
            spaceBefore=10,
            spaceAfter=5
        ))

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
                encounter=clinical_data.encounter,
                status='generating'
            )
            
            # Genera il PDF
            pdf_content = self._generate_pdf_content(clinical_data)
            
            # Salva il file PDF
            report.pdf_file.save(
                f"report_{report.report_id}.pdf",
                ContentFile(pdf_content),
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

    def _generate_pdf_content(self, clinical_data: ClinicalData) -> bytes:
        """
        Genera il contenuto PDF del report
        """
        # Crea un file temporaneo per il PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            try:
                # Crea il documento PDF
                doc = SimpleDocTemplate(
                    temp_file.name,
                    pagesize=A4,
                    rightMargin=72,
                    leftMargin=72,
                    topMargin=72,
                    bottomMargin=18
                )
                
                # Costruisci il contenuto
                story = []
                
                # Header del report
                story.extend(self._build_header(clinical_data))
                
                # Informazioni paziente
                story.extend(self._build_patient_info(clinical_data.extracted_data))
                
                # Parametri vitali
                story.extend(self._build_vital_signs(clinical_data.extracted_data))
                
                # Sintomi e diagnosi
                story.extend(self._build_symptoms_diagnosis(clinical_data.extracted_data))
                
                # Esami e terapie
                story.extend(self._build_tests_therapies(clinical_data.extracted_data))
                
                # Note mediche
                story.extend(self._build_medical_notes(clinical_data.extracted_data))
                
                # Footer
                story.extend(self._build_footer(clinical_data))
                
                # Genera il PDF
                doc.build(story)
                
                # Leggi il contenuto del file
                with open(temp_file.name, 'rb') as pdf_file:
                    return pdf_file.read()
                    
            finally:
                # Pulisci il file temporaneo
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def _build_header(self, clinical_data: ClinicalData) -> list:
        """
        Costruisce l'header del report
        """
        story = []
        
        # Titolo principale
        title = Paragraph("REPORT CLINICO", self.styles['MainTitle'])
        story.append(title)
        
        # Informazioni generali
        encounter = clinical_data.encounter
        info_data = [
            ['ID Encounter:', encounter.encounter_id],
            ['Data:', encounter.timestamp.strftime("%d/%m/%Y %H:%M")],
            ['Medico:', encounter.doctor.get_full_name() if encounter.doctor else 'N/A'],
            ['Tipo:', encounter.encounter_type],
            ['Priorità Triage:', clinical_data.extracted_data.get('priorità_triage', 'N/A')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Spacer(1, 20))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        return story

    def _build_patient_info(self, data: Dict[str, Any]) -> list:
        """
        Costruisce la sezione informazioni paziente
        """
        story = []
        
        patient_info = data.get('informazioni_paziente', {})
        if not any(patient_info.values()):
            return story
        
        # Titolo sezione
        story.append(Paragraph("INFORMAZIONI PAZIENTE", self.styles['SectionHeader']))
        
        # Tabella informazioni
        patient_data = []
        for key, value in patient_info.items():
            if value:
                display_key = key.replace('_', ' ').title()
                patient_data.append([display_key + ':', str(value)])
        
        if patient_data:
            patient_table = Table(patient_data, colWidths=[2*inch, 3*inch])
            patient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(patient_table)
            story.append(Spacer(1, 15))
        
        return story

    def _build_vital_signs(self, data: Dict[str, Any]) -> list:
        """
        Costruisce la sezione parametri vitali
        """
        story = []
        
        vitals = data.get('parametri_vitali', {})
        if not any(vitals.values()):
            return story
        
        # Titolo sezione
        story.append(Paragraph("PARAMETRI VITALI", self.styles['SectionHeader']))
        
        # Tabella parametri vitali
        vitals_data = []
        for key, value in vitals.items():
            if value:
                display_key = key.replace('_', ' ').title()
                vitals_data.append([display_key + ':', str(value)])
        
        if vitals_data:
            vitals_table = Table(vitals_data, colWidths=[2.5*inch, 2.5*inch])
            vitals_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(vitals_table)
            story.append(Spacer(1, 15))
        
        return story

    def _build_symptoms_diagnosis(self, data: Dict[str, Any]) -> list:
        """
        Costruisce la sezione sintomi e diagnosi
        """
        story = []
        
        # Sintomi
        symptoms = data.get('sintomi', [])
        if symptoms:
            story.append(Paragraph("SINTOMI", self.styles['SectionHeader']))
            for i, symptom in enumerate(symptoms, 1):
                story.append(Paragraph(f"{i}. {symptom}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Diagnosi
        diagnoses = data.get('diagnosi', [])
        if diagnoses:
            story.append(Paragraph("DIAGNOSI", self.styles['SectionHeader']))
            for i, diagnosis in enumerate(diagnoses, 1):
                story.append(Paragraph(f"{i}. {diagnosis}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        return story

    def _build_tests_therapies(self, data: Dict[str, Any]) -> list:
        """
        Costruisce la sezione esami e terapie
        """
        story = []
        
        # Esami clinici
        tests = data.get('esami_clinici', [])
        if tests:
            story.append(Paragraph("ESAMI CLINICI", self.styles['SectionHeader']))
            for i, test in enumerate(tests, 1):
                story.append(Paragraph(f"{i}. {test}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Terapie
        therapies = data.get('terapie', [])
        if therapies:
            story.append(Paragraph("TERAPIE PRESCRITTE", self.styles['SectionHeader']))
            for i, therapy in enumerate(therapies, 1):
                story.append(Paragraph(f"{i}. {therapy}", self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Allergie
        allergies = data.get('allergie', [])
        if allergies:
            story.append(Paragraph("ALLERGIE", self.styles['SectionHeader']))
            for i, allergy in enumerate(allergies, 1):
                story.append(Paragraph(f"{i}. {allergy}", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        return story

    def _build_medical_notes(self, data: Dict[str, Any]) -> list:
        """
        Costruisce la sezione note mediche
        """
        story = []
        
        # Storia clinica
        history = data.get('storia_clinica', '')
        if history:
            story.append(Paragraph("STORIA CLINICA", self.styles['SectionHeader']))
            story.append(Paragraph(history, self.styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Note mediche
        notes = data.get('note_mediche', '')
        if notes:
            story.append(Paragraph("NOTE MEDICHE", self.styles['SectionHeader']))
            story.append(Paragraph(notes, self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        return story

    def _build_footer(self, clinical_data: ClinicalData) -> list:
        """
        Costruisce il footer del report
        """
        story = []
        
        # Informazioni tecniche
        story.append(Spacer(1, 30))
        story.append(Paragraph("INFORMAZIONI TECNICHE", self.styles['SectionHeader']))
        
        tech_data = [
            ['Data Generazione:', datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
            ['ID Trascrizione:', str(clinical_data.transcript.transcript_id)],
            ['Confidenza Trascrizione:', f"{clinical_data.transcript.confidence_score:.2%}"],
            ['Confidenza Estrazione:', f"{clinical_data.confidence_score:.2%}"],
            ['Durata Audio:', f"{clinical_data.transcript.audio_duration:.1f} secondi" if clinical_data.transcript.audio_duration else 'N/A']
        ]
        
        tech_table = Table(tech_data, colWidths=[2.5*inch, 2.5*inch])
        tech_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tech_table)
        
        # Disclaimer
        disclaimer = """
        <b>DISCLAIMER:</b> Questo report è stato generato automaticamente da un sistema di trascrizione 
        e analisi del linguaggio naturale. Le informazioni contenute devono essere verificate 
        e validate da personale medico qualificato prima di qualsiasi utilizzo clinico.
        """
        
        story.append(Spacer(1, 20))
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return story