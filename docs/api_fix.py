#!/usr/bin/env python3
"""
Script to automatically fix api.rst file to include proper medical_workflow_views documentation
This ensures the API functions are visible in the generated documentation
"""

import os
import re

def fix_api_rst():
    """Fix the api.rst file to include proper medical_workflow_views documentation"""
    
    api_rst_path = os.path.join("source", "api.rst")
    
    if not os.path.exists(api_rst_path):
        print("Warning: api.rst file not found")
        return False
    
    # Read the current content
    with open(api_rst_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the pattern to match the basic medical_workflow_views section
    pattern = r'api\.medical\\\_workflow\\\_views module\n-----------------------------------\n\n\.\. automodule:: api\.medical_workflow_views\n   :members:\n   :undoc-members:\n   :show-inheritance:'
    
    # Define the replacement with detailed documentation
    replacement = '''api.medical\\\_workflow\\\_views module
-----------------------------------

.. automodule:: api.medical_workflow_views
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: AllowAny,Any,Dict,DjangoAudioTranscript,Doctor,Encounter,FileResponse,FormParser,HttpResponse,JSONParser,MultiPartParser,NVIDIANIMService,Optional,Patient,Response,Tuple,api_view,clinical_extraction_service,date,datetime,get_object_or_404,get_pdf_report_service,logger,logging,mongodb_service,os,parse_date,parser_classes,pdf_report_service,permission_classes,settings,status,tempfile,whisper_service

API Endpoints Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the following API functions for the medical workflow:

**Patient Management**

- ``patients_list()`` - List of patients
- ``patient_visit_history()`` - Patient visit history
- ``update_patient_data()`` - Update patient data

**Audio Workflow and Transcription**

- ``process_audio_visit()`` - Audio processing and transcription
- ``extract_clinical_data_llm()`` - Clinical data extraction with LLM
- ``transcript_details()`` - Transcription details

**Report Generation**

- ``generate_pdf_report()`` - PDF report generation
- ``download_pdf_report()`` - Download generated report

**Analytics and Dashboard**

- ``dashboard_analytics()`` - Analytics data for dashboard
- ``all_interventions_list()`` - List all interventions
- ``intervention_details()`` - Specific intervention details

**Clinical Data Management**

- ``update_clinical_data()`` - Update extracted clinical data
- ``get_extraction_methods()`` - Available extraction methods

All functions are decorated with ``@api_view`` and use REST Framework serializers for data validation and serialization.'''
    
    # Check if the pattern exists and replace it
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        
        # Write the updated content back
        with open(api_rst_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ Applied medical_workflow_views documentation fix to api.rst")
        return True
    else:
        print("ℹ medical_workflow_views section already properly configured or not found")
        return False

if __name__ == "__main__":
    fix_api_rst()