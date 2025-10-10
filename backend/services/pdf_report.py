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
        Genera report medico PDF seguendo il layout professionale
        con gestione multipagina e trascrizione completa
        
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
            line_height = 16
            
            # Genera prima pagina
            y = self._draw_full_header(c, report_data, width, height)
            y = self._draw_patient_info_detailed(c, report_data, margin_x, y, width, line_height)
            y = self._draw_dates_urgency_box(c, report_data, margin_x, y, width, line_height)
            y = self._draw_clinical_detailed(c, report_data, margin_x, y, width, line_height)
            
            # Controlla se serve nuova pagina per trascrizione e note
            if y < 200:  # Poco spazio rimanente
                c.showPage()  # Nuova pagina
                y = height - 80
            
            # Trascrizione audio completa
            if report_data.get('transcript_text'):
                y = self._draw_transcript_full(c, report_data, margin_x, y, width, line_height)
            
            # Note mediche aggiuntive
            if report_data.get('medical_notes') or report_data.get('annotations'):
                y = self._draw_medical_notes(c, report_data, margin_x, y, width, line_height)
            
            # Footer professionale
            self._draw_professional_footer(c, report_data, width, height)
            
            c.save()
            logger.info(f"Report PDF generato: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore generazione PDF: {e}")
            return False
    
    def _draw_full_header(self, c, data, width, height):
        """Disegna l'intestazione completa seguendo il layout del report.py"""
        # Header lines principali
        lines = [
            "USL FUORIGROTTA - Azienda Sanitaria",
            "Nuovo ospedale di Fuorigrotta S. Diego Armando", 
            "Unità operativa Medicina d'Urgenza Pronto Soccorso",
            "Responsabile Dott. Antonio Conte"
        ]
        
        lines2 = [
            "PRONTO SOCCORSO",
            "___________________________",
            "                           ",
        ]
        
        y = 750  # Punto di partenza verticale
        
        # Box informazioni ospedale (angolo destro)
        box_width = 200
        box_height = 100
        box_x = width - box_width
        box_y = height - box_height - 40
        
        lines0 = [
            "Sede Legale",
            "A.O.R.N. D.Armando", 
            "Via Claudio, 21",
            "80125 NAPOLI",
            "1234567890123456"
        ]
        
        c.setFont("Helvetica", 8)
        start_y = box_y + box_height - 10
        
        for line in lines0:
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
        
        # Prima lista intestazioni (centrate)
        c.setFont("Helvetica", 9)
        for line in lines:
            text_width = c.stringWidth(line, "Helvetica", 9)
            x_position = (width - text_width) / 2
            c.drawString(x_position, y, line)
            y -= 12
        
        # Seconda lista grassetto
        c.setFont("Helvetica-Bold", 9)
        for line in lines2:
            text_width = c.stringWidth(line, "Helvetica-Bold", 9)
            x_position = (width - text_width) / 2
            c.drawString(x_position, y, line)
            y -= 12
        
        # Titolo principale
        c.setFont("Helvetica-Bold", 11)
        title_text = "RELAZIONE CLINICA"
        text_width = c.stringWidth(title_text, "Helvetica-Bold", 11)
        x_position = (width - text_width) / 2
        c.drawString(x_position, y, title_text)
        
        # Data e numero verbale
        triage_date = data.get("visit_date", "")
        try:
            if triage_date:
                date_obj = datetime.strptime(str(triage_date), "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
            else:
                formatted_date = datetime.now().strftime("%d/%m/%Y")
        except:
            formatted_date = datetime.now().strftime("%d/%m/%Y")
        
        encounter_id = data.get("encounter_id", "")
        
        c.setFont("Helvetica", 9)
        c.drawString(50, y-12, f"Fuorigrotta, lì: {formatted_date}")
        c.setFont("Helvetica-Bold", 9)
        text_width = c.stringWidth(f"N.VERBALE: {encounter_id}", "Helvetica-Bold", 9)
        c.drawString(width - 50 - text_width, y-12, f"N.VERBALE: {encounter_id}")
        
        return y - 30
    
    def _draw_patient_info_detailed(self, c, data, x, y, width, line_height):
        """Disegna informazioni paziente con box secondo layout report.py"""
        
        def safe_get(data, key):
            value = data.get(key, "")
            if isinstance(value, list):
                return str(value[0]) if value else ""
            return str(value)
        
        # Box dati anagrafici
        box_x = x
        box_y = y - 90
        box_width = width - 2 * x
        box_height = 64
        
        c.rect(box_x, box_y, box_width, box_height, stroke=1)
        
        # Colonne per allineamento
        col1 = box_x + 10
        col2 = box_x + box_width / 3 + 20
        col3 = box_x + 2 * box_width / 3
        
        font_size = 10
        c.setFont("Helvetica", font_size)
        text_y = box_y + box_height - 14
        
        # Estrai dati
        nome = safe_get(data, "first_name")
        cognome = safe_get(data, "last_name")
        sesso_raw = safe_get(data, "gender")
        sesso = "F" if sesso_raw and sesso_raw.lower().startswith("f") else ("M" if sesso_raw else "")
        residence_city = safe_get(data, "residence_city")
        eta = safe_get(data, "age")
        data_nascita = safe_get(data, "birth_date")
        indirizzo = safe_get(data, "residence_address")
        telefono = safe_get(data, "phone")
        birth_place = safe_get(data, "birth_place")
        sintomi = safe_get(data, "symptoms")
        access_mode = safe_get(data, "access_mode")
        
        # Riga 1: Assistito/a | Sesso | Età
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col1, text_y, "Assistito/a")
        c.setFont("Helvetica", font_size)
        c.drawString(col1 + 70, text_y, f"{cognome} {nome}")
        
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col2, text_y, "Sesso")
        c.setFont("Helvetica", font_size)
        c.drawString(col2 + 60, text_y, sesso)
        
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col3, text_y, "Età")
        c.setFont("Helvetica", font_size)
        c.drawString(col3 + 25, text_y, str(eta))
        
        text_y -= 14
        
        # Riga 2: Data e luogo di nascita
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col1, text_y, "Nato/a il")
        c.setFont("Helvetica", font_size)
        c.drawString(col1 + 70, text_y, str(data_nascita))
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col2, text_y, "a")
        c.setFont("Helvetica", font_size)
        c.drawString(col2 + 60, text_y, str(birth_place))
        
        text_y -= 14
        
        # Riga 3: Residenza e Indirizzo
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col1, text_y, "Residenza")
        c.setFont("Helvetica", font_size)
        c.drawString(col1 + 70, text_y, str(residence_city))
        
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col2, text_y, "Indirizzo")
        c.setFont("Helvetica", font_size)
        c.drawString(col2 + 60, text_y, str(indirizzo))
        
        text_y -= 14
        
        # Riga 4: Telefono
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col1, text_y, "Telefono")
        c.setFont("Helvetica", font_size)
        c.drawString(col1 + 70, text_y, str(telefono))
        
        # Aggiorna y per contenuto successivo
        y = box_y - 20
        
        # Motivo e modalità accesso
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col1, y, "Motivo Accesso:")
        c.setFont("Helvetica", font_size)
        c.drawString(col1 + 100, y, str(sintomi))
        
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(col1, y-12, "Modalità Accesso:")
        c.setFont("Helvetica", font_size)
        c.drawString(col1 + 100, y-12, str(access_mode))
        
        return y - 30
    
    def _draw_dates_urgency_box(self, c, data, x, y, width, line_height):
        """Disegna box con date e codici urgenza"""
        
        def safe_get(data, key):
            value = data.get(key, "")
            if isinstance(value, list):
                return str(value[0]) if value else ""
            return str(value)
        
        # Box date e urgenze
        box2_x = 50
        box2_y = y - 80
        box2_width = width - 2 * 50
        box2_height = 35
        
        c.rect(box2_x, box2_y, box2_width, box2_height)
        
        label_font = "Helvetica-Bold"
        value_font = "Helvetica"
        font_size = 10
        
        # Dati
        data_triage = safe_get(data, "triage_date")
        data_visita = safe_get(data, "visit_date")
        data_uscita = safe_get(data, "exit_date")
        urgenza_triage = safe_get(data, "triage_code")
        urgenza_dimissione = safe_get(data, "discharge_code")
        
        # Coordinate (3 colonne per riga)
        col1 = box2_x + 10
        col2 = box2_x + box2_width / 3
        col3 = box2_x + 2 * box2_width / 3
        row1_y = box2_y + box2_height - 15
        row2_y = row1_y - 12
        
        # RIGA 1
        c.setFont(label_font, font_size)
        c.drawString(col1, row1_y, "Data triage:")
        c.setFont(value_font, font_size)
        c.drawString(col1 + 70, row1_y, str(data_triage))
        
        c.setFont(label_font, font_size)
        c.drawString(col2, row1_y, "Data visita:")
        c.setFont(value_font, font_size)
        c.drawString(col2 + 65, row1_y, str(data_visita))
        
        c.setFont(label_font, font_size)
        c.drawString(col3, row1_y, "Data uscita:")
        c.setFont(value_font, font_size)
        c.drawString(col3 + 65, row1_y, str(data_uscita))
        
        # RIGA 2
        c.setFont(label_font, font_size)
        c.drawString(col1, row2_y, "Urgenza triage:")
        c.setFont(value_font, font_size)
        c.drawString(col1 + 85, row2_y, str(urgenza_triage))
        
        c.setFont(label_font, font_size)
        c.drawString(col3, row2_y, "Urgenza dimissione:")
        c.setFont(value_font, font_size)
        c.drawString(col3 + 65, row2_y, str(urgenza_dimissione))
        
        return box2_y - 20
    
    def _draw_clinical_detailed(self, c, data, x, y, width, line_height):
        """Disegna valutazione clinica completa con tabella parametri vitali"""
        
        def safe_get(data, key):
            value = data.get(key, "")
            if isinstance(value, list):
                return str(value[0]) if value else ""
            return str(value)
        
        font_size = 10
        
        # Anamnesi
        history = safe_get(data, "history")
        medications_taken = safe_get(data, "medications_taken")
        
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(50, y, "Anamnesi:")
        c.setFont("Helvetica", font_size)
        y -= 12
        c.drawString(150, y, str(history))
        y -= 12
        c.drawString(150, y, str(medications_taken))
        y -= 24
        
        # Rilevazioni fisiche
        consciousness_state = safe_get(data, "consciousness_state")
        respiratory_state = safe_get(data, "respiratory_state")
        skin_state = safe_get(data, "skin_state")
        pupils_state = safe_get(data, "pupils_state")
        
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(50, y, "Rilevazioni:")
        y -= 12
        
        c.setFont("Helvetica", font_size)
        c.drawString(150, y, "- coscienza:")
        c.drawString(250, y, str(consciousness_state))
        y -= 12
        
        c.drawString(150, y, "- pupille:")
        c.drawString(250, y, str(pupils_state))
        y -= 12
        
        c.drawString(150, y, "- respiro:")
        c.drawString(250, y, str(respiratory_state))
        y -= 12
        
        c.drawString(150, y, "- cute:")
        c.drawString(250, y, str(skin_state))
        y -= 24
        
        # Tabella parametri vitali
        table_data = [
            ["SpO2", "FC (bpm)", "Temp (°C)", "Glic (Mg/dl)", "PA (mmHg)"],
            [
                safe_get(data, "oxygenation"),
                safe_get(data, "heart_rate"),
                safe_get(data, "temperature"),
                safe_get(data, "blood_glucose"),
                safe_get(data, "blood_pressure")
            ]
        ]
        
        # Calcola larghezze colonna
        available_width = width - 2 * 50
        num_columns = len(table_data[0])
        col_widths = [available_width / num_columns] * num_columns
        
        # Crea tabella
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        # Disegna tabella
        table_width, table_height = table.wrap(available_width, 100)
        table.drawOn(c, 50, y - 40)
        y -= 64  # Spazio per tabella
        
        # Azioni mediche
        medical_actions = safe_get(data, "medical_actions")
        c.setFont("Helvetica", font_size)
        c.drawString(50, y, str(medical_actions))
        y -= 24
        
        # Valutazione
        assessment = safe_get(data, "assessment")
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(50, y, "Valutazione:")
        c.setFont("Helvetica", font_size)
        y -= 12
        c.drawString(150, y, str(assessment))
        y -= 24
        
        # Piano terapeutico
        plan = safe_get(data, "plan")
        c.setFont("Helvetica-Bold", font_size)
        c.drawString(50, y, "Piano:")
        y -= 12
        c.setFont("Helvetica", font_size)
        c.drawString(150, y, str(plan))
        y -= 24
        
        return y
    
    def _draw_transcript_full(self, c, data, x, y, width, line_height):
        """Disegna trascrizione audio completa con gestione multipagina"""
        transcript = data.get('transcript_text', '')
        if not transcript:
            return y
        
        from reportlab.lib.pagesizes import letter
        page_width, page_height = letter
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, "TRASCRIZIONE AUDIO COMPLETA")
        y -= line_height * 2
        
        c.setFont("Helvetica", 9)
        
        # Testo trascrizione con wrapping
        max_width = width - 2*x
        text_lines = self._get_wrapped_lines(c, transcript, max_width, "Helvetica", 9)
        
        for line in text_lines:
            # Controlla se serve nuova pagina
            if y < 100:  # Poco spazio rimanente
                c.showPage()  # Nuova pagina
                y = page_height - 80  # Reset posizione
                
                # Header semplificato per pagina successiva
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x, y, "TRASCRIZIONE AUDIO (continua)")
                y -= 30
                c.setFont("Helvetica", 9)
            
            c.drawString(x + 10, y, line)
            y -= 12
        
        return y - 20
    
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
    
    def _draw_medical_notes(self, c, data, x, y, width, line_height):
        """Disegna note mediche aggiuntive e prescrizioni"""
        
        def safe_get(data, key):
            value = data.get(key, "")
            if isinstance(value, list):
                return str(value[0]) if value else ""
            return str(value)
        
        # Note e prescrizioni
        annotations = safe_get(data, "annotations")
        medical_notes = safe_get(data, "medical_notes")
        
        font_size = 10
        
        if annotations or medical_notes:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y, "NOTE E PRESCRIZIONI MEDICHE")
            y -= line_height * 2
            
            c.setFont("Helvetica-Bold", font_size)
            c.drawString(x, y, "Note e Prescrizioni:")
            c.setFont("Helvetica", font_size)
            y -= 12
            
            # Combina tutte le note
            all_notes = []
            if annotations:
                all_notes.append(f"Annotazioni: {annotations}")
            if medical_notes:
                all_notes.append(f"Note mediche: {medical_notes}")
            
            # Disegna note con wrapping
            for note in all_notes:
                text_lines = self._get_wrapped_lines(c, note, width - x - 60, "Helvetica", font_size)
                for line in text_lines:
                    # Controlla se serve nuova pagina
                    if y < 100:
                        c.showPage()
                        y = 750  # Reset posizione
                        c.setFont("Helvetica-Bold", 10)
                        c.drawString(x, y, "NOTE MEDICHE (continua)")
                        y -= 30
                        c.setFont("Helvetica", font_size)
                    
                    c.drawString(x + 15, y, line)
                    y -= line_height
                y -= 5  # Spazio tra note diverse
        
        return y - 20
    
    def _get_wrapped_lines(self, c, text, max_width, font_name, font_size):
        """Restituisce lista di righe con text wrapping ottimizzato"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _draw_professional_footer(self, c, data, width, height):
        """Disegna footer professionale seguendo il layout report.py"""
        footer_y = 80
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, footer_y + 35, "Dichiara di aver preso visione di quanto sopra, e di essere stato informato in modo comprensibile sulle proprie")
        c.drawString(50, footer_y + 25, "condizioni di salute, sulla terapia proposta e sui rischi connessi")
        
        # Etichette firme equidistanti
        sign_labels = ["Firma dell'accompagnatore", "Firma del paziente", "Il medico dimettente"]
        positions = [width * 0.2, width * 0.5, width * 0.8]
        
        c.setFont("Helvetica", 9)
        for text, x in zip(sign_labels, positions):
            c.drawCentredString(x, footer_y, text)
        
        # Linee firma sotto
        signature_lines = ["_________________________", "_________________________", "_________________________"]
        for line, x in zip(signature_lines, positions):
            c.drawCentredString(x, footer_y - 20, line)
    
    def get_report_path(self, encounter_id: str, report_type: str = "medical", 
                       patient_name: str = "", visit_date: str = "") -> str:
        """
        Genera il path per salvare il report PDF con nome strutturato
        
        Args:
            encounter_id: ID encounter
            report_type: Tipo di report
            patient_name: Nome del paziente per il filename
            visit_date: Data della visita per il filename
            
        Returns:
            Path completo del file PDF
        """
        # Pulisci il nome del paziente per il filename
        clean_name = ""
        if patient_name:
            # Rimuovi caratteri non validi per filename
            import re
            clean_name = re.sub(r'[^\w\s-]', '', patient_name).strip()
            clean_name = re.sub(r'[-\s]+', '_', clean_name)
        
        # Pulisci la data per il filename
        clean_date = ""
        if visit_date:
            # Rimuovi caratteri non validi
            clean_date = re.sub(r'[^\d]', '', visit_date)
        
        # Costruisci il nome del file
        if clean_name and clean_date:
            filename = f"Report_{clean_name}_{clean_date}.pdf"
        elif clean_name:
            filename = f"Report_{clean_name}_{encounter_id}.pdf"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report_type}_{encounter_id}_{timestamp}.pdf"
        
        reports_dir = os.path.join(self.media_root, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        return os.path.join(reports_dir, filename)


# Istanza singleton del servizio
pdf_report_service = PDFReportService()