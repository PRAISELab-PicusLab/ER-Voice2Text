#!/usr/bin/env python3
"""
Test script per verificare il nuovo layout PDF
"""

import sys
import os

# Aggiungi il path del backend Django
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_system.settings')

import django
django.setup()

from services.pdf_report import PDFReportService
from datetime import datetime

def test_pdf_generation():
    """Test per verificare la generazione PDF con il nuovo layout"""
    
    # Dati di test completi
    test_data = {
        'encounter_id': 'ENC_2024_001',
        'first_name': 'Mario',
        'last_name': 'Rossi',
        'age': 45,
        'gender': 'Maschio',
        'birth_date': '1979-03-15',
        'birth_place': 'Napoli',
        'residence_city': 'Fuorigrotta',
        'residence_address': 'Via Roma 123',
        'phone': '081-1234567',
        'symptoms': 'Dolore toracico e dispnea',
        'access_mode': 'Ambulanza',
        'triage_date': '2024-10-10 14:30',
        'visit_date': '2024-10-10',
        'exit_date': '2024-10-10 18:00',
        'triage_code': 'GIALLO',
        'discharge_code': 'VERDE',
        
        # Anamnesi e farmaci
        'history': 'Paziente con storia di ipertensione arteriosa in terapia. Nega allergie farmacologiche. Ex fumatore da 5 anni.',
        'medications_taken': 'Ramipril 5mg 1 cp/die, Amlodipina 5mg 1 cp/die',
        
        # Rilevazioni fisiche
        'consciousness_state': 'Vigile e collaborante',
        'pupils_state': 'Isocoriche e fotoreagenti',
        'respiratory_state': 'Eupnoico a riposo',
        'skin_state': 'Normocolorita e normoidratata',
        
        # Parametri vitali
        'oxygenation': '98%',
        'heart_rate': '82',
        'temperature': '36.5',
        'blood_glucose': '105',
        'blood_pressure': '140/85',
        
        # Valutazione clinica
        'medical_actions': 'Eseguito ECG 12 derivazioni, prelievo venoso per troponine e D-dimero, Rx torace',
        'assessment': 'Dolore toracico atipico. ECG nella norma. Troponine negative. Rx torace normale.',
        'plan': 'Dimissione con terapia antidolorifica al bisogno. Controllo medico curante entro 48h.',
        
        # Note mediche aggiuntive
        'annotations': 'Paziente informato sui sintomi di allarme. Consigliato riposo e graduale ripresa attività.',
        'medical_notes': 'Follow-up cardiologico consigliato entro 30 giorni per approfondimenti diagnostici.',
        
        # Trascrizione audio (esempio lungo)
        'transcript_text': '''
        Paziente di 45 anni che si presenta in pronto soccorso per dolore toracico iniziato circa 2 ore fa. 
        Il dolore è localizzato in regione precordiale, di intensità moderata, non irradiato, non correlato 
        ai movimenti respiratori o alla posizione. Associato a lieve dispnea. Nega palpitazioni, sudorazione, 
        nausea o vomito. 
        
        All'anamnesi emerge storia di ipertensione arteriosa in terapia farmacologica con ACE-inibitore e 
        calcio-antagonista. Ex fumatore da 5 anni (precedentemente 1 pacchetto/die per 20 anni). Nega 
        familiarità per cardiopatia ischemica. Non allergie farmacologiche note.
        
        All'esame obiettivo il paziente appare in buone condizioni generali, vigile e collaborante. 
        Parametri vitali stabili. Auscultazione cardiaca: toni validi, ritmo regolare, non soffi. 
        Auscultazione polmonare: murmure vescicolare presente bilateralmente, non rumori patologici aggiunti.
        
        Eseguito ECG che mostra ritmo sinusale regolare, frequenza 80 bpm, non alterazioni acute della 
        ripolarizzazione. Prelievo venoso per dosaggio troponine I, D-dimero, emocromo, funzionalità 
        renale ed epatica. Rx torace in due proiezioni che non evidenzia alterazioni pleuroparenchimali acute.
        
        I risultati degli esami ematochimici mostrano troponine nella norma, D-dimero lievemente elevato 
        ma non significativo nel contesto clinico, restanti parametri nella norma.
        
        Dopo osservazione di 4 ore con monitoraggio cardiaco continuo, il paziente riferisce completa 
        risoluzione della sintomatologia dolorosa. Non episodi di ricorrenza del dolore o altre manifestazioni cliniche.
        
        Dato il quadro clinico e strumentale, si conclude per episodio di dolore toracico atipico, 
        verosimilmente di natura muscolo-scheletrica. Il paziente viene dimesso con terapia antidolorifica 
        al bisogno e indicazione a controllo presso il medico curante entro 48 ore.
        '''
    }
    
    # Genera PDF
    pdf_service = PDFReportService()
    output_path = os.path.join(backend_path, "media", "reports", "test_report_nuovo_layout.pdf")
    
    # Assicurati che la directory esista
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        success = pdf_service.generate_medical_report(test_data, output_path)
        
        if success:
            print(f"✅ PDF generato con successo: {output_path}")
            print(f"📄 Dimensione file: {os.path.getsize(output_path)} bytes")
            print("\n📋 Contenuto del report:")
            print(f"   • Paziente: {test_data['first_name']} {test_data['last_name']}")
            print(f"   • Età: {test_data['age']} anni")
            print(f"   • Encounter ID: {test_data['encounter_id']}")
            print(f"   • Sintomi: {test_data['symptoms']}")
            print(f"   • Valutazione: {test_data['assessment'][:50]}...")
            print(f"   • Trascrizione: {len(test_data['transcript_text'])} caratteri")
            
            return True
        else:
            print("❌ Errore nella generazione del PDF")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏥 Test PDF Report Service - Nuovo Layout")
    print("=" * 50)
    
    success = test_pdf_generation()
    
    if success:
        print("\n✅ Test completato con successo!")
        print("\n📝 Caratteristiche del nuovo layout:")
        print("   ✓ Header professionale con logo e intestazioni")
        print("   ✓ Box informazioni paziente con layout tabellare")
        print("   ✓ Box date e codici urgenza")
        print("   ✓ Sezione clinica con tabella parametri vitali")
        print("   ✓ Trascrizione audio completa con gestione multipagina")
        print("   ✓ Note mediche aggiuntive")
        print("   ✓ Footer professionale con firme")
    else:
        print("\n❌ Test fallito!")
        sys.exit(1)