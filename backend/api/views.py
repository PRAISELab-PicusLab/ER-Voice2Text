"""
Views API per il sistema medico unificato
Endpoints REST per gestione pazienti, medici ed episodi
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
import logging

from core.models import Patient, Doctor, Encounter
from .serializers import *

logger = logging.getLogger(__name__)


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione medici
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    @action(detail=True, methods=['get'])
    def encounters(self, request, pk=None):
        """Ottieni tutti gli encounter di un medico"""
        doctor = self.get_object()
        encounters = Encounter.objects.filter(doctor=doctor)
        serializer = EncounterSerializer(encounters, many=True)
        return Response(serializer.data)


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione pazienti
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    @action(detail=True, methods=['get'])
    def encounters(self, request, pk=None):
        """Ottieni tutti gli encounter di un paziente"""
        patient = self.get_object()
        encounters = Encounter.objects.filter(patient=patient)
        serializer = EncounterSerializer(encounters, many=True)
        return Response(serializer.data)


class EncounterViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione encounters di Pronto Soccorso
    """
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer
    ordering_fields = ['admission_time', 'triage_priority']
    ordering = ['-admission_time']


class TranscribeAudioView(APIView):
    """
    Endpoint per trascrizione audio
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = TranscribeAudioSerializer(data=request.data)
        if serializer.is_valid():
            # Logica di trascrizione audio (da implementare)
            return Response({
                'message': 'Audio ricevuto per trascrizione',
                'data': serializer.validated_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProcessClinicalDataView(APIView):
    """
    Endpoint per processamento dati clinici
    """
    def post(self, request, format=None):
        serializer = ProcessClinicalDataSerializer(data=request.data)
        if serializer.is_valid():
            # Logica di processamento dati clinici (da implementare)
            return Response({
                'message': 'Dati clinici processati',
                'data': serializer.validated_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateReportView(APIView):
    """
    Endpoint per generazione report PDF
    """
    def post(self, request, format=None):
        serializer = GenerateReportSerializer(data=request.data)
        if serializer.is_valid():
            # Logica di generazione report (da implementare)
            return Response({
                'message': 'Report generato',
                'data': serializer.validated_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)