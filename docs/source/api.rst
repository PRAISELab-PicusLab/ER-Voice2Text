api package
===========

.. automodule:: api
   :members:
   :undoc-members:
   :show-inheritance:

Submodules
----------

api.admin module
----------------

.. automodule:: api.admin
   :members:
   :undoc-members:
   :show-inheritance:

api.apps module
---------------

.. automodule:: api.apps
   :members:
   :undoc-members:
   :show-inheritance:

api.medical\_workflow\_views module
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

All functions are decorated with ``@api_view`` and use REST Framework serializers for data validation and serialization.

api.models module
-----------------

.. automodule:: api.models
   :members:
   :undoc-members:
   :show-inheritance:

api.serializers module
----------------------

.. automodule:: api.serializers
   :members:
   :undoc-members:
   :show-inheritance:

api.tests module
----------------

.. automodule:: api.tests
   :members:
   :undoc-members:
   :show-inheritance:

api.urls module
---------------

.. automodule:: api.urls
   :members:
   :undoc-members:
   :show-inheritance:

api.views module
----------------

.. automodule:: api.views
   :members:
   :undoc-members:
   :show-inheritance:
