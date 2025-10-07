#!/usr/bin/env python
"""
Script per verificare ID pazienti
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_system.settings')
django.setup()

from core.models import Patient

def list_patients():
    """Lista tutti i pazienti"""
    print("Pazienti disponibili:")
    for patient in Patient.objects.all():
        print(f"UUID: {patient.patient_id}")
        print(f"Nome: {patient.get_full_name()}")
        print(f"CF: {patient.fiscal_code}")
        print("---")

if __name__ == '__main__':
    list_patients()