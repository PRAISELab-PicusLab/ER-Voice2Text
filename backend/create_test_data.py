#!/usr/bin/env python
"""
Script per creare dati di test nel sistema medico
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_system.settings')
django.setup()

from core.models import Doctor, Patient
from datetime import date

def create_test_data():
    """Crea dati di test per il sistema"""
    
    # Crea un dottore di test se non esiste
    doctor, created = Doctor.objects.get_or_create(
        username='mario.rossi',
        defaults={
            'first_name': 'Mario',
            'last_name': 'Rossi',
            'email': 'mario.rossi@ospedale.it',
            'specialization': 'Medicina d\'Emergenza',
            'department': 'Pronto Soccorso',
            'license_number': 'OM123456',
            'is_emergency_doctor': True
        }
    )
    
    if created:
        print(f"✅ Creato dottore: {doctor.get_full_name()}")
    else:
        print(f"ℹ️  Dottore già esistente: {doctor.get_full_name()}")
    
    # Crea pazienti di test
    test_patients = [
        {
            'fiscal_code': 'RSSMRA80A01H501X',
            'first_name': 'Maria',
            'last_name': 'Rossi',
            'date_of_birth': date(1980, 1, 1),
            'place_of_birth': 'Milano',
            'gender': 'F',
            'phone': '+39 333 111 2222',
            'emergency_contact': 'Giuseppe Rossi - +39 333 111 2223',
            'allergies': 'Penicillina',
            'blood_type': 'A+'
        },
        {
            'fiscal_code': 'VRDDLC75B02H501Y',
            'first_name': 'Luca',
            'last_name': 'Verdi',
            'date_of_birth': date(1975, 2, 2),
            'place_of_birth': 'Roma',
            'gender': 'M',
            'phone': '+39 333 222 3333',
            'emergency_contact': 'Anna Verdi - +39 333 222 3334',
            'allergies': 'Nessuna allergia nota',
            'blood_type': 'B-'
        },
        {
            'fiscal_code': 'BLNGLR90C03H501Z',
            'first_name': 'Giulia',
            'last_name': 'Bianchi',
            'date_of_birth': date(1990, 3, 3),
            'place_of_birth': 'Napoli',
            'gender': 'F',
            'phone': '+39 333 333 4444',
            'emergency_contact': 'Marco Bianchi - +39 333 333 4445',
            'allergies': 'Lattosio',
            'blood_type': 'O+'
        }
    ]
    
    for patient_data in test_patients:
        patient, created = Patient.objects.get_or_create(
            fiscal_code=patient_data['fiscal_code'],
            defaults=patient_data
        )
        
        if created:
            print(f"✅ Creato paziente: {patient.get_full_name()} ({patient.fiscal_code})")
        else:
            print(f"ℹ️  Paziente già esistente: {patient.get_full_name()} ({patient.fiscal_code})")
    
    print(f"\n📊 Totale dottori: {Doctor.objects.count()}")
    print(f"📊 Totale pazienti: {Patient.objects.count()}")
    print("✅ Dati di test creati con successo!")

if __name__ == '__main__':
    create_test_data()