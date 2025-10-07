"""
Management command per creare dati demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from core.models import Doctor, Patient, Encounter
from datetime import datetime, timedelta
import uuid

class Command(BaseCommand):
    help = 'Crea dati demo per testing'

    def handle(self, *args, **options):
        # Crea medico demo
        doctor, created = Doctor.objects.get_or_create(
            username='demo.doctor',
            defaults={
                'password': make_password('demo123'),
                'first_name': 'Mario',
                'last_name': 'Rossi',
                'email': 'mario.rossi@ospedale.it',
                'specialization': 'Medicina d\'Emergenza',
                'department': 'Pronto Soccorso',
                'license_number': '12345',
                'is_emergency_doctor': True,
                'is_staff': True,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✅ Medico demo creato: {doctor.username}')
        else:
            self.stdout.write(f'ℹ️  Medico demo già esistente: {doctor.username}')
        
        # Crea paziente demo
        patient, created = Patient.objects.get_or_create(
            fiscal_code='RSSMRA85M01H501Z',
            defaults={
                'first_name': 'Giuseppe',
                'last_name': 'Verdi',
                'date_of_birth': datetime(1985, 8, 1).date(),
                'place_of_birth': 'Roma',
                'gender': 'M',
                'phone': '+39 123 456 7890',
                'weight': 75.0,
                'height': 175.0
            }
        )
        
        if created:
            self.stdout.write(f'✅ Paziente demo creato: {patient.get_full_name()}')
        else:
            self.stdout.write(f'ℹ️  Paziente demo già esistente: {patient.get_full_name()}')
        
        # Crea encounter demo
        encounter, created = Encounter.objects.get_or_create(
            patient=patient,
            doctor=doctor,
            status='in_progress',
            defaults={
                'chief_complaint': 'Dolore toracico',
                'triage_priority': 'yellow',
                'admission_time': datetime.now() - timedelta(hours=1)
            }
        )
        
        if created:
            self.stdout.write(f'✅ Encounter demo creato: {encounter.encounter_id}')
        else:
            self.stdout.write(f'ℹ️  Encounter demo già esistente: {encounter.encounter_id}')
        
        self.stdout.write('\n🎉 Setup dati demo completato!')
        self.stdout.write(f'👤 Login: demo.doctor / demo123')
