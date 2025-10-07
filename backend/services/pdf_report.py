"""
Servizio per generazione report PDF 
Basato sulla logica del Project 2 con stesso layout e struttura
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader
from django.conf import settings

logger = logging.getLogger(__name__)


class PDFReportService:
    """
    Servizio per generazione report PDF medici
    """
    
    def __init__(self):
        self.media_root = getattr(settings, 'MEDIA_ROOT', '/tmp')
        self.logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo2.jpg")
    
    def generate_medical_report(self, report_data: Dict[str, Any], output_path: str) -> bool:
        """
        Genera report medico PDF seguendo il layout del Project 2
        
        Args:
            report_data: Dati clinici strutturati
            output_path: Path del file PDF da generare
            
        Returns:
            True se generazione riuscita
        """
        try:
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            margin_x = 50
            margin_y = 50
            right_margin = width - 50
            line_height = 16
            
            # Genera intestazione
            self._draw_header(c, width, height)
            
            # Posizione iniziale per contenuto
            y = height - 180
            
            # Informazioni paziente
            y = self._draw_patient_info(c, report_data, margin_x, y, width, line_height)
            
            # Parametri vitali
            y = self._draw_vital_signs(c, report_data, margin_x, y, width, line_height)
            
            # Valutazione clinica
            y = self._draw_clinical_assessment(c, report_data, margin_x, y, width, line_height)
            
            # Trascrizione (se presente)
            if report_data.get('transcript_text'):
                y = self._draw_transcript(c, report_data, margin_x, y, width, line_height)
            
            # Footer
            self._draw_footer(c, report_data, width, height)
            
            c.save()
            logger.info(f"Report PDF generato: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore generazione PDF: {e}")
            return False
    
    def _draw_header(self, c, width, height):
        """Disegna l'intestazione del report"""
        # Box informazioni ospedale (angolo destro)
        box_width = 200
        box_height = 100
        box_x = width - box_width - 50
        box_y = height - box_height - 40
        
        # Testo sede legale
        lines_sede = [
            "Sede Legale",
            "A.O.R.N. D.Armando", 
            "Via Claudio, 21",
            "80125 NAPOLI",
            "1234567890123456"
        ]
        
        c.setFont("Helvetica", 8)
        start_y = box_y + box_height - 10
        
        for line in lines_sede:
            text_width = c.stringWidth(line, "Helvetica", 8)
            x_position = box_x + (box_width - text_width) / 2
            c.drawString(x_position, start_y, line)
            start_y -= 10
        
        # Logo ospedale
        logo_x = 80
        logo_y = height - 40 - 40
        logo_width = 50
        logo_height = 50
        
        if os.path.exists(self.logo_path):
            c.drawImage(self.logo_path, logo_x, logo_y, width=logo_width, height=logo_height)
        
        # Testo sotto logo
        center_x = logo_x + logo_width / 2
        text_start_y = logo_y - 4
        
        c.setFont("Helvetica-Bold", 9)
        text = "S. Diego Armando"
        text_width = c.stringWidth(text, "Helvetica-Bold", 9)
        c.drawString(center_x - text_width / 2, text_start_y, text)
        
        c.setFont("Helvetica", 6)
        text2 = "AZIENDA OSPEDALIERA"
        text_width2 = c.stringWidth(text2, "Helvetica", 6)
        c.drawString(center_x - text_width2 / 2, text_start_y - 8, text2)
        
        text3 = "DI RILIEVO NAZIONALE"
        text_width3 = c.stringWidth(text3, "Helvetica", 6)
        c.drawString(center_x - text_width3 / 2, text_start_y - 16, text3)
        
        # Intestazioni principali
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 120, "USL FUORIGROTTA - Azienda Sanitaria")
        c.drawString(50, height - 140, "Nuovo ospedale di Fuorigrotta S. Diego Armando")
        c.drawString(50, height - 160, "Unità operativa Medicina d'Urgenza Pronto Soccorso")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 175, "Responsabile Dott. Antonio Conte")
    
    def _draw_patient_info(self, c, data, x, y, width, line_height):
        """Disegna informazioni paziente"""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "INFORMAZIONI PAZIENTE")
        y -= line_height * 2
        
        c.setFont("Helvetica", 10)
        
        # Prima colonna
        fields_left = [
            ("Nome:", data.get('first_name', '')),
            ("Cognome:", data.get('last_name', '')),
            ("Età:", str(data.get('age', ''))),
            ("Sesso:", data.get('gender', '')),
            ("Data nascita:", data.get('birth_date', '')),
            ("Luogo nascita:", data.get('birth_place', ''))
        ]
        
        # Seconda colonna
        fields_right = [
            ("Città residenza:", data.get('residence_city', '')),
            ("Indirizzo:", data.get('residence_address', '')),
            ("Telefono:", data.get('phone', '')),
            ("Modalità accesso:", data.get('access_mode', '')),
            ("Codice triage:", data.get('triage_code', '')),
            ("Data visita:", data.get('visit_date', ''))
        ]
        
        # Disegna campi in due colonne
        col_width = (width - 2*x) / 2
        
        for i, ((label_l, value_l), (label_r, value_r)) in enumerate(zip(fields_left, fields_right)):
            current_y = y - i * line_height
            
            # Colonna sinistra
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, current_y, label_l)
            c.setFont("Helvetica", 10)
            c.drawString(x + 80, current_y, str(value_l))
            
            # Colonna destra
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x + col_width, current_y, label_r)
            c.setFont("Helvetica", 10)
            c.drawString(x + col_width + 100, current_y, str(value_r))
        
        return y - len(fields_left) * line_height - 20
    
    def _draw_vital_signs(self, c, data, x, y, width, line_height):
        """Disegna parametri vitali"""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "PARAMETRI VITALI")
        y -= line_height * 2
        
        c.setFont("Helvetica", 10)
        
        vital_fields = [
            ("Frequenza cardiaca:", data.get('heart_rate', '')),
            ("Pressione arteriosa:", data.get('blood_pressure', '')),
            ("Temperatura:", f"{data.get('temperature', '')}°C" if data.get('temperature') else ''),
            ("Saturazione O2:", data.get('oxygenation', '')),
            ("Glicemia:", data.get('blood_glucose', ''))
        ]
        
        for i, (label, value) in enumerate(vital_fields):
            current_y = y - i * line_height
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, current_y, label)
            c.setFont("Helvetica", 10)
            c.drawString(x + 130, current_y, str(value))
        
        return y - len(vital_fields) * line_height - 20
    
    def _draw_clinical_assessment(self, c, data, x, y, width, line_height):
        """Disegna valutazione clinica"""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "VALUTAZIONE CLINICA")
        y -= line_height * 2
        
        c.setFont("Helvetica", 10)
        
        # Stato fisico
        physical_fields = [
            ("Stato cute:", data.get('skin_state', '')),
            ("Stato coscienza:", data.get('consciousness_state', '')),
            ("Stato pupille:", data.get('pupils_state', '')),
            ("Stato respiratorio:", data.get('respiratory_state', ''))
        ]
        
        for i, (label, value) in enumerate(physical_fields):
            current_y = y - i * line_height
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, current_y, label)
            c.setFont("Helvetica", 10)
            c.drawString(x + 120, current_y, str(value))
        
        y -= len(physical_fields) * line_height + 10
        
        # Campi testuali
        text_fields = [
            ("ANAMNESI:", data.get('history', '')),
            ("FARMACI:", data.get('medications_taken', '')),
            ("SINTOMI:", data.get('symptoms', '')),
            ("AZIONI MEDICHE:", data.get('medical_actions', '')),
            ("VALUTAZIONE:", data.get('assessment', '')),
            ("PIANO TERAPEUTICO:", data.get('plan', ''))
        ]
        
        for label, text in text_fields:
            if text:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x, y, label)
                y -= line_height
                
                # Gestisce testo lungo con wrap
                c.setFont("Helvetica", 9)
                self._draw_wrapped_text(c, str(text), x + 10, y, width - x - 60, line_height)
                lines_count = len(str(text)) // 80 + 1
                y -= lines_count * line_height + 5
        
        return y - 20
    
    def _draw_transcript(self, c, data, x, y, width, line_height):
        """Disegna trascrizione"""
        transcript = data.get('transcript_text', '')
        if not transcript:
            return y
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "TRASCRIZIONE AUDIO")
        y -= line_height * 2
        
        c.setFont("Helvetica", 8)
        
        # Testo trascrizione con wrapping
        max_width = width - 2*x
        self._draw_wrapped_text(c, transcript, x, y, max_width, line_height - 2)
        
        # Calcola spazio utilizzato
        lines_count = len(transcript) // 100 + 1
        return y - lines_count * (line_height - 2) - 20
    
    def _draw_wrapped_text(self, c, text, x, y, max_width, line_height):
        """Disegna testo con wrapping automatico"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if c.stringWidth(test_line, "Helvetica", 8) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            c.drawString(x, y - i * line_height, line)
    
    def _draw_footer(self, c, data, width, height):
        """Disegna footer del report"""
        footer_y = 50
        
        c.setFont("Helvetica", 8)
        c.drawString(50, footer_y, f"Report generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}")
        
        # Firma medico
        c.drawString(width - 200, footer_y + 20, "Firma del medico")
        c.drawString(width - 200, footer_y, "_" * 30)
    
    def get_report_path(self, encounter_id: str, report_type: str = "medical") -> str:
        """
        Genera il path per salvare il report PDF
        
        Args:
            encounter_id: ID encounter
            report_type: Tipo di report
            
        Returns:
            Path completo del file PDF
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report_type}_{encounter_id}_{timestamp}.pdf"
        
        reports_dir = os.path.join(self.media_root, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        return os.path.join(reports_dir, filename)


# Istanza singleton del servizio
pdf_report_service = PDFReportService()