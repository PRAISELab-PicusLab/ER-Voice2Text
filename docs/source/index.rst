Documentazione ER-Voice2Text
============================

**ER-Voice2Text** è un sistema avanzato per la gestione dei flussi di lavoro medici in Pronto Soccorso,
che integra trascrizione vocale automatica, estrazione di entità cliniche e generazione di report medici.

Panoramica del Sistema
======================

Il sistema è composto da:

* **Backend Django**: API REST per la gestione dei dati medici
* **Servizi AI**: Integrazione con NVIDIA NIM e modelli Whisper per trascrizione e analisi
* **Database**: SQLite per dati relazionali, MongoDB per trascrizioni e analisi
* **Frontend React**: Interfaccia utente per medici e operatori sanitari

Caratteristiche Principali
==========================

* **Trascrizione Audio Real-time**: Utilizzo di Whisper per trascrizione accurata
* **Estrazione Entità Cliniche**: LLM e NER per identificazione automatica di dati clinici
* **Workflow Medico Completo**: Dalla registrazione audio al report PDF finale
* **Autenticazione Medica**: Sistema di login per operatori sanitari
* **Dashboard Analytics**: Statistiche e visualizzazioni per l'analisi dei dati

Architettura del Backend
========================

Il backend è organizzato nei seguenti moduli:

.. toctree::
   :maxdepth: 2
   :caption: Moduli Backend:

   core
   api
   services
   medical_system
   auth_views
   manage

Modelli Django
==============

Il sistema utilizza modelli Django per la gestione di:

* **Doctor**: Gestione dei medici e specializzazioni
* **Patient**: Anagrafica e dati clinici pazienti
* **Encounter**: Episodi di cura in Pronto Soccorso
* **AudioTranscript**: Trascrizioni audio con metadati
* **ClinicalData**: Dati clinici estratti dalle trascrizioni
* **ClinicalReport**: Report medici finalizzati

Servizi AI e Integrazione
==========================

Il sistema integra diversi servizi per l'analisi intelligente:

* **NVIDIA NIM**: Large Language Model per estrazione entità cliniche
* **Whisper**: Trascrizione speech-to-text ad alta precisione
* **Text2NER**: Named Entity Recognition per analisi testuale
* **MongoDB**: Storage per trascrizioni e dati non strutturati

API Reference
=============

.. toctree::
   :maxdepth: 3
   :caption: API e Moduli:

   modules

Configurazione e Deploy
=======================

Per informazioni su installazione, configurazione e deployment, 
consultare il README del progetto e la documentazione di setup.

Indici e Tabelle
================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
