import os
import logging
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from django.conf import settings

logger = logging.getLogger(__name__)

class PDFReportService:
    """
    Servizio migliorato per generazione report PDF medico d'urgenza
    - layout professionale
    - dinamico (adatta spazio testo)
    - più leggibile e ben distanziato
    """

    def __init__(self):
        self.media_root = getattr(settings, "MEDIA_ROOT", "/tmp")
        self.logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo2.jpg")

        self.page_size = A4
        self.margin_x = 25 * mm
        self.margin_y = 25 * mm
        self.styles = getSampleStyleSheet()

        # Stili personalizzati
        self.styles.add(ParagraphStyle(name="SectionTitle", fontSize=11, leading=14,
                                       textColor=colors.HexColor("#003366"), spaceAfter=8, spaceBefore=12, 
                                       fontName="Helvetica-Bold"))
        self.styles.add(ParagraphStyle(name="NormalText", fontSize=10, leading=13,
                                       fontName="Helvetica"))
        self.styles.add(ParagraphStyle(name="BoldLabel", fontSize=10, fontName="Helvetica-Bold"))

    def generate_medical_report(self, report_data: Dict[str, Any], output_path: str) -> bool:
        try:
            c = canvas.Canvas(output_path, pagesize=self.page_size)
            width, height = self.page_size

            y = height - self.margin_y
            y = self._draw_header(c, report_data, width, height, y)
            y -= 25  # Spazio aumentato dopo header

            # Sezioni dinamiche
            y = self._section_patient_info(c, report_data, width, y)
            y = self._section_dates_info(c, report_data, width, y)
            y = self._section_clinical_info(c, report_data, width, y)

            # Trascrizione (se presente)
            transcript_text = report_data.get("transcript_text", "").strip()
            if transcript_text:
                if y < 200:
                    c.showPage()
                    y = height - self.margin_y
                y = self._section_transcript(c, transcript_text, width, y)

            # Footer firme migliorato
            self._draw_footer(c, width)

            c.save()
            logger.info(f"Report PDF generato con successo: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Errore generazione PDF: {e}")
            import traceback; traceback.print_exc()
            return False

    # --------------------------------------------------------
    # INTESTAZIONE
    # --------------------------------------------------------
    def _draw_header(self, c, data, width, height, y):
        try:
            # Logo
            if os.path.exists(self.logo_path):
                c.drawImage(self.logo_path, self.margin_x, height - 70, width=50, height=50, preserveAspectRatio=True)

            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(width / 2, height - 50, "A.O.R.N. S. DIEGO ARMANDO - FUORIGROTTA")
            c.setFont("Helvetica", 9)
            c.drawCentredString(width / 2, height - 65, "Unità Operativa Medicina d’Urgenza e Pronto Soccorso")

            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(width / 2, height - 90, "REFERTO MEDICO DI PRONTO SOCCORSO")

            visit_date = data.get("visit_date", datetime.now().strftime("%d/%m/%Y"))
            c.setFont("Helvetica", 9)
            c.drawString(self.margin_x, height - 110, f"Data visita: {visit_date}")

            encounter_id = data.get("encounter_id", "N/D")
            c.drawRightString(width - self.margin_x, height - 110, f"N. Verbale: {encounter_id}")
            return height - 125
        except Exception:
            return y - 30

    # --------------------------------------------------------
    # SEZIONI PRINCIPALI
    # --------------------------------------------------------
    def _section_patient_info(self, c, data, width, y):
        if y < 150:  # Se poco spazio, nuova pagina
            c.showPage()
            y = self.page_size[1] - self.margin_y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.margin_x, y, "DATI ANAGRAFICI ASSISTITO")
        y -= 20  # Spazio aumentato
        c.line(self.margin_x, y, width - self.margin_x, y)
        y -= 25  # Spazio aumentato

        text = (
            f"<b>Nome:</b> {data.get('first_name', '')}  <b>Cognome:</b> {data.get('last_name', '')} "
            f"<b>Codice Fiscale:</b> {data.get('codice_fiscale', '')}<br/>"
            f"<b>Sesso:</b> {data.get('gender', '')} "
            f"<b>Età:</b> {data.get('age', '')}<br/>"
            f"<b>Data di nascita:</b> {data.get('birth_date', '')} "
            f" - <b>Luogo di nascita:</b> {data.get('birth_place', '')}<br/>"
            f"<b>Città di residenza:</b> {data.get('residence_city', '')} "
            f" - <b>Indirizzo di residenza:</b> {data.get('residence_address', '')}<br/>"
            f"<b>Telefono:</b> {data.get('phone', '')}<br/><br/>"
            f"<b>Motivo Accesso:</b> {data.get('symptoms', '')}<br/>"
            f"<b>Modalità Accesso:</b> {data.get('access_mode', '')}"
        )

        p = Paragraph(text, self.styles["NormalText"])
        y = self._draw_paragraph(c, p, width, y)
        return y - 35  # Spazio aumentato tra sezioni

    def _section_dates_info(self, c, data, width, y):
        if y < 120:  # Se poco spazio, nuova pagina
            c.showPage()
            y = self.page_size[1] - self.margin_y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.margin_x, y, "DATE E URGENZA")
        y -= 20  # Spazio aumentato
        c.line(self.margin_x, y, width - self.margin_x, y)
        y -= 25  # Spazio aumentato

        table_data = [
            ["Data Triage", "Data Visita", "Data Uscita", "Urgenza Triage", "Urgenza Dimissione"],
            [
                data.get("triage_date", ""),
                data.get("visit_date", ""),
                data.get("exit_date", ""),
                data.get("triage_code", ""),
                data.get("discharge_code", "")
            ]
        ]

        col_width = (width - 2 * self.margin_x) / len(table_data[0])
        table = Table(table_data, colWidths=[col_width] * len(table_data[0]))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 9)
        ]))
        table.wrapOn(c, width, y)
        table_height = table._height
        table.drawOn(c, self.margin_x, y - table_height)
        return y - table_height - 40  # Spazio aumentato

    def _section_clinical_info(self, c, data, width, y):
        sections = [
            ("ANAMNESI", f"{data.get('history', '')}<br/>{data.get('medications_taken', '')}"),
            ("ESAME OBIETTIVO", 
             f"<b>Stato di coscienza:</b> {data.get('consciousness_state', '')}<br/>"
             f"<b>Pupille:</b> {data.get('pupils_state', '')}<br/>"
             f"<b>Apparato respiratorio:</b> {data.get('respiratory_state', '')}<br/>"
             f"<b> Cute e mucose:</b> {data.get('skin_state', '')}"),
            ("PARAMETRI VITALI", ""),
        ]

        for title, text in sections:
            if y < 150:  # Controllo pagina per ogni sezione
                c.showPage()
                y = self.page_size[1] - self.margin_y
            c.setFont("Helvetica-Bold", 11)
            c.drawString(self.margin_x, y, title)
            y -= 20  # Spazio aumentato
            c.line(self.margin_x, y, width - self.margin_x, y)
            y -= 25  # Spazio aumentato

            if text:
                p = Paragraph(text, self.styles["NormalText"])
                y = self._draw_paragraph(c, p, width, y)
                y -= 20  # Spazio aumentato

            # Parametri vitali come tabella
            if title == "PARAMETRI VITALI":
                table_data = [
                    ["SpO₂", "FC (bpm)", "Temp (°C)", "Glic (mg/dl)", "PA (mmHg)"],
                    [
                        data.get("oxygenation", ""),
                        data.get("heart_rate", ""),
                        data.get("temperature", ""),
                        data.get("blood_glucose", ""),
                        data.get("blood_pressure", "")
                    ]
                ]
                col_width = (width - 2 * self.margin_x) / 5
                table = Table(table_data, colWidths=[col_width]*5)
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                ]))
                table.wrapOn(c, width, y)
                table_height = table._height
                table.drawOn(c, self.margin_x, y - table_height)
                y -= table_height + 35  # Spazio aumentato

        # Diagnosi, terapia, note, prognosi
        for section_name, key in [
            ("DIAGNOSI", "assessment"),
            ("TERAPIA", "plan"),
            ("NOTE E PRESCRIZIONI", "annotations"),
            ("PROGNOSI", "prognosis")
        ]:
            value = data.get(key)
            if value:
                if y < 120:  # Controllo pagina
                    c.showPage()
                    y = self.page_size[1] - self.margin_y
                c.setFont("Helvetica-Bold", 11)
                c.drawString(self.margin_x, y, section_name)
                y -= 20  # Spazio aumentato
                c.line(self.margin_x, y, width - self.margin_x, y)
                y -= 25  # Spazio aumentato
                p = Paragraph(str(value), self.styles["NormalText"])
                y = self._draw_paragraph(c, p, width, y)
                y -= 35  # Spazio aumentato tra sezioni

        return y

    # --------------------------------------------------------
    # TRASCRIZIONE
    # --------------------------------------------------------
    def _section_transcript(self, c, transcript, width, y):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(self.margin_x, y, "TRASCRIZIONE AUDIO")
        y -= 20  # Spazio aumentato
        c.line(self.margin_x, y, width - self.margin_x, y)
        y -= 25  # Spazio aumentato

        p = Paragraph(transcript.replace("\n", "<br/>"), self.styles["NormalText"])
        y = self._draw_paragraph(c, p, width, y)
        return y - 40  # Spazio aumentato

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------
    def _draw_footer(self, c, width):
        footer_y = 140  # Spazio aumentato ulteriormente per le firme
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.margin_x, footer_y + 55, "CONSENSO INFORMATO")
        c.setFont("Helvetica", 9)
        c.drawString(self.margin_x, footer_y + 43,
                     "Il paziente dichiara di essere stato informato sulle proprie condizioni e terapie proposte.")
        c.drawString(self.margin_x, footer_y + 30,
                     "Firma del paziente / Legale rappresentante:")
        c.line(self.margin_x, footer_y + 25, self.margin_x + 120, footer_y + 25)
        c.drawString(self.margin_x, footer_y + 15, "Data: ____/____/________")

        # Firma medico con più spazio verticale
        c.drawString(width - 200, footer_y + 30, "Firma del medico:")
        c.line(width - 200, footer_y + 25, width - 50, footer_y + 25)
        c.drawString(width - 200, footer_y + 15, "Dott. ________________________")
        c.drawString(width - 200, footer_y + 5, "Data: ____/____/________")

    # --------------------------------------------------------
    # HELPER
    # --------------------------------------------------------
    def _draw_paragraph(self, c, paragraph, width, y):
        """Renderizza un paragrafo e restituisce nuova Y"""
        available_width = width - 2 * self.margin_x
        _, h = paragraph.wrap(available_width, y)
        paragraph.drawOn(c, self.margin_x, y - h)
        return y - h

    def get_report_path(self, encounter_id: str, report_type: str = "medical",
                        patient_name: str = "", visit_date: str = "") -> str:
        import re
        clean_name = re.sub(r"[^\w\s-]", "", patient_name or "").strip()
        clean_name = re.sub(r"[-\s]+", "_", clean_name)
        filename = f"Report_{clean_name}_{encounter_id}.pdf" if clean_name else f"report_{report_type}_{encounter_id}_{datetime.now():%Y%m%d_%H%M%S}.pdf"
        reports_dir = os.path.join(self.media_root, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        return os.path.join(reports_dir, filename)

pdf_report_service = PDFReportService()
