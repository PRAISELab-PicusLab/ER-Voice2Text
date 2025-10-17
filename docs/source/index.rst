ER-Voice2Text Documentation
============================

**ER-Voice2Text** is an advanced system for managing medical workflows in Emergency Departments,
integrating automatic voice transcription, clinical entity extraction, and medical report generation.

System Overview
===============

The system consists of:

* **Django Backend**: REST API for medical data management
* **AI Services**: Integration with NVIDIA NIM and Whisper models for transcription and analysis
* **Database**: SQLite for relational data, MongoDB for transcriptions and analysis
* **React Frontend**: User interface for doctors and healthcare operators

Key Features
============

* **Real-time Audio Transcription**: Using Whisper for accurate transcription
* **Clinical Entity Extraction**: LLM and NER for automatic identification of clinical data
* **Complete Medical Workflow**: From audio recording to final PDF report
* **Medical Authentication**: Login system for healthcare operators
* **Analytics Dashboard**: Statistics and visualizations for data analysis

Backend Architecture
====================

The backend is organized in the following modules:

.. toctree::
   :maxdepth: 2
   :caption: Backend Modules:

   core
   api
   services
   medical_system
   auth_views
   manage

Django Models
=============

The system uses Django models for managing:

* **Doctor**: Management of doctors and specializations
* **Patient**: Patient registry and clinical data  
* **Encounter**: Emergency Department care episodes
* **AudioTranscript**: Audio transcriptions with metadata
* **ClinicalData**: Clinical data extracted from transcriptions
* **ClinicalReport**: Finalized medical reports

AI Services and Integration
===========================

The system integrates several services for intelligent analysis:

* **NVIDIA NIM**: Large Language Model for clinical entity extraction
* **Whisper**: High-precision speech-to-text transcription
* **Text2NER**: Named Entity Recognition for textual analysis  
* **MongoDB**: Storage for transcriptions and unstructured data

Configuration and Deployment
=============================

For information on installation, configuration and deployment, 
consult the project README and setup documentation.

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
