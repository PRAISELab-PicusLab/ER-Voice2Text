/**
 * Pagina completa per Nuova Emergenza
 * Gestisce tutto il flusso: registrazione in tempo reale, trascrizione, modifica, PDF, estrazione dati
 */

import React, { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { medicalWorkflowAPI, transcriptsAPI } from '../../services/api'
import { useNavigate, useLocation } from 'react-router-dom'

const NewEmergencyPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)
  const timerRef = useRef(null)

  // Dati del paziente se provenienti dalla lista pazienti
  const patientFromRoute = location.state?.patient
  const isEmergency = location.state?.isEmergency || true
  
  // Modalità edit se proveniente da modifica intervento
  const editMode = location.state?.editMode || false
  const interventionData = location.state?.interventionData

  // Stati principali
  const [currentStep, setCurrentStep] = useState(
    editMode ? 'editing' : 'setup'
  ) // setup, recording, transcribing, editing, extraction, completed
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState(null)
  
  // Dati del workflow
  const [transcriptText, setTranscriptText] = useState('')
  const [editedTranscript, setEditedTranscript] = useState('')
  const [extractedData, setExtractedData] = useState(null)
  const [pdfUrl, setPdfUrl] = useState('')
  const [transcriptId, setTranscriptId] = useState('')
  
  // Dati iniziali emergenza
  const [emergencyData, setEmergencyData] = useState({
    sintomi_principali: '',
    codice_triage: 'bianco',
    note_triage: ''
  })

  // Stato per animazione transcribing dinamica
  const [transcribingMessage, setTranscribingMessage] = useState(0)

  // Messaggi onesti per transcribing - riflettono il processo reale
  const transcribingMessages = [
    {
      icon: 'bi bi-mic text-primary',
      title: 'Audio Ricevuto',
      subtitle: 'Registrazione acquisita correttamente.'
    },
    {
      icon: 'bi bi-cpu text-primary',
      title: 'Elaborazione Vocale',
      subtitle: 'Analisi e conversione audio in testo.'
    },
    {
      icon: 'bi bi-file-earmark-text text-primary',
      title: 'Trascrizione in corso',
      subtitle: 'Testo estratto dall\'audio registrato.'
    }
  ]

  // Timer per cambiare messaggi durante transcribing - più lento per contesto medico
  useEffect(() => {
    if (currentStep === 'transcribing') {
      const interval = setInterval(() => {
        setTranscribingMessage(prev => (prev + 1) % transcribingMessages.length)
      }, 4000) // Cambia ogni 4 secondi per permettere lettura attenta
      
      return () => clearInterval(interval)
    }
  }, [currentStep])

  // Carica dati intervento in modalità edit
  useEffect(() => {
    if (editMode && interventionData) {
      // Carica i dati dell'intervento esistente
      setTranscriptId(interventionData.transcript_id)
      
      // Carica la trascrizione esistente
      medicalWorkflowAPI.getInterventionDetails(interventionData.transcript_id)
        .then(details => {
          if (details.transcript_text) {
            setTranscriptText(details.transcript_text)
            setEditedTranscript(details.transcript_text)
          }
          if (details.clinical_data) {
            const clinicalData = details.clinical_data
            // Se il triage_code non è presente nei dati clinici ma c'è in emergencyData, usalo
            if (!clinicalData.triage_code && emergencyData.codice_triage) {
              clinicalData.triage_code = emergencyData.codice_triage
            }
            setExtractedData({ extracted_data: clinicalData })
          }
        })
        .catch(error => {
          console.error('Errore caricamento dati intervento:', error)
        })
    }
  }, [editMode, interventionData, emergencyData.codice_triage])

  // Mutation per processare l'audio completo
  const processAudioMutation = useMutation({
    mutationFn: async (audioBlob) => {
      const formData = new FormData()
      formData.append('audio_file', audioBlob)
      formData.append('sintomi_principali', emergencyData.sintomi_principali)
      formData.append('codice_triage', emergencyData.codice_triage)
      formData.append('note_triage', emergencyData.note_triage)
      
      // Se c'è un paziente selezionato, aggiungi i suoi dati
      if (patientFromRoute) {
        formData.append('patient_id', patientFromRoute.patient_id)
      }
      
      return medicalWorkflowAPI.processAudioVisit(formData)
    },
    onSuccess: (data) => {
      setTranscriptText(data.transcript)
      setEditedTranscript(data.transcript)
      setTranscriptId(data.transcript_id)
      setCurrentStep('editing')
    },
    onError: (error) => {
      console.error('Errore processing audio:', error)
      setCurrentStep('setup')
    }
  })

  // Mutation per estrazione dati LLM dal transcript modificato
  const extractDataMutation = useMutation({
    mutationFn: async (editedTranscript) => {
      return medicalWorkflowAPI.extractClinicalData(transcriptId, editedTranscript)
    },
    onSuccess: (data) => {
      // Se il triage_code non è presente nei dati estratti, usa quello da emergencyData
      if (data.extracted_data && !data.extracted_data.triage_code && emergencyData.codice_triage) {
        data.extracted_data.triage_code = emergencyData.codice_triage
      }
      setExtractedData(data)
      setCurrentStep('extraction')
    },
    onError: (error) => {
      console.error('Errore estrazione dati:', error)
    }
  })

  // Mutation per generare PDF
  const generatePDFMutation = useMutation({
    mutationFn: async (transcriptId) => {
      return medicalWorkflowAPI.generatePDFReport(transcriptId)
    },
    onSuccess: (data) => {
      setPdfUrl(data.download_url)
      setCurrentStep('completed')
    },
    onError: (error) => {
      console.error('Errore generazione PDF:', error)
    }
  })

  // Mutation per aggiornare i dati clinici estratti
  const updateClinicalDataMutation = useMutation({
    mutationFn: async ({ transcriptId, clinicalData }) => {
      return transcriptsAPI.updateClinicalData(transcriptId, clinicalData)
    },
    onSuccess: (data) => {
      console.log('Dati clinici aggiornati con successo:', data)
      // Dopo aver salvato i dati, genera il PDF
      generatePDFMutation.mutate(transcriptId)
    },
    onError: (error) => {
      console.error('Errore aggiornamento dati clinici:', error)
      alert('Errore durante il salvataggio delle modifiche. Riprova.')
    }
  })

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      })
      
      streamRef.current = stream
      audioChunksRef.current = []

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        setAudioBlob(audioBlob)
        setCurrentStep('transcribing')
        processAudioMutation.mutate(audioBlob)
      }

      mediaRecorder.start(100) // Chunk ogni 100ms per monitoraggio real-time
      setIsRecording(true)
      setCurrentStep('recording')
      
      // Timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
    } catch (error) {
      console.error('Errore accesso microfono:', error)
      alert('Errore accesso microfono. Controlla i permessi.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      clearInterval(timerRef.current)
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }

  const handleEmergencyDataChange = (e) => {
    const { name, value } = e.target
    setEmergencyData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleTranscriptEdit = (e) => {
    setEditedTranscript(e.target.value)
  }

  const handleGenerateLLMExtraction = () => {
    if (transcriptId || editedTranscript) {
      extractDataMutation.mutate(editedTranscript)
    }
  }

  const handleGeneratePDF = () => {
    if (transcriptId && extractedData?.extracted_data) {
      // Prima salva le modifiche ai dati estratti, poi genera il PDF
      updateClinicalDataMutation.mutate({
        transcriptId,
        clinicalData: extractedData.extracted_data
      })
    }
  }

  const handleExtractedDataChange = (field, value) => {
    setExtractedData(prev => ({
      ...prev,
      extracted_data: {
        ...prev.extracted_data,
        [field]: value
      }
    }))
  }

  const handleCalculateCodiceFiscale = async () => {
    if (!extractedData?.extracted_data) {
      alert('Nessun dato estratto disponibile per il calcolo del codice fiscale.')
      return
    }
    
    const data = extractedData.extracted_data
    if (!data.first_name || !data.last_name || !data.birth_date || !data.gender || !data.birth_place) {
      alert('Per calcolare il codice fiscale sono necessari: Nome, Cognome, Data di nascita, Sesso e Luogo di nascita.')
      return
    }

    try {
      const response = await medicalWorkflowAPI.calculateCodiceFiscale({
        first_name: data.first_name,
        last_name: data.last_name,
        birth_date: data.birth_date,
        gender: data.gender,
        birth_place: data.birth_place
      })
      
      if (response.codice_fiscale) {
        handleExtractedDataChange('codice_fiscale', response.codice_fiscale)
        // alert(`Codice fiscale calcolato: ${response.codice_fiscale}`)
      }
    } catch (error) {
      console.error('Errore calcolo codice fiscale:', error)
      alert('Errore durante il calcolo del codice fiscale. Riprova.')
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getTriageColor = (code) => {
    const colors = {
      bianco: 'secondary',
      verde: 'success',
      giallo: 'warning',
      rosso: 'danger'
    }
    return colors[code] || 'secondary'
  }

  const getTriageIcon = (code) => {
    const icons = {
      bianco: '⚪',
      verde: '🟢',
      giallo: '🟡',
      rosso: '🔴'
    }
    return icons[code] || '⚪'
  }

  return (
    <div className="container-fluid py-2 emergency-page">
      {/* Header fisso */}
      <div className="row mb-4">
        <div className="col">
          <div className="d-flex justify-content-between align-items-center">
            <h1 className="h2 fw-bold text-danger mb-0">
              <i className="bi bi-mic me-2"></i>
              NUOVA EMERGENZA
            </h1>
            <button 
              className="btn btn-outline-secondary"
              onClick={() => navigate('/dashboard')}
            >
              <i className="bi bi-arrow-left me-2"></i>
              Torna alla Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Progress indicator responsive */}
      <div className="row mb-4">
        <div className="col">
          <div className="progress mb-3" style={{ height: '10px' }}>
            <div 
              className="progress-bar bg-danger" 
              style={{ 
                width: `${
                  currentStep === 'setup' ? 0 :
                  currentStep === 'recording' ? 20 :
                  currentStep === 'transcribing' ? 40 :
                  currentStep === 'editing' ? 60 :
                  currentStep === 'extraction' ? 80 : 100
                }%`
              }}
            ></div>
          </div>
          <div className="d-flex justify-content-between small text-muted">
            <span 
              className={`cursor-pointer ${currentStep === 'setup' ? 'text-danger fw-bold' : ''}`}
              onClick={() => setCurrentStep('setup')}
              style={{ cursor: 'pointer' }}
            >
              Setup
            </span>
            <span 
              className={`cursor-pointer ${currentStep === 'recording' ? 'text-danger fw-bold' : ''}`}
              onClick={() => currentStep !== 'recording' && setCurrentStep('recording')}
              style={{ cursor: currentStep !== 'recording' ? 'pointer' : 'not-allowed' }}
            >
              Registrazione
            </span>
            <span 
              className={`cursor-pointer ${currentStep === 'transcribing' ? 'text-danger fw-bold' : ''}`}
              onClick={() => currentStep !== 'transcribing' && transcriptText && setCurrentStep('transcribing')}
              style={{ cursor: (currentStep !== 'transcribing' && transcriptText) ? 'pointer' : 'not-allowed' }}
            >
              Trascrizione
            </span>
            <span 
              className={`cursor-pointer ${currentStep === 'editing' ? 'text-danger fw-bold' : ''}`}
              onClick={() => transcriptText && setCurrentStep('editing')}
              style={{ cursor: transcriptText ? 'pointer' : 'not-allowed' }}
            >
              Modifica
            </span>
            <span 
              className={`cursor-pointer ${currentStep === 'extraction' ? 'text-danger fw-bold' : ''}`}
              onClick={() => extractedData && setCurrentStep('extraction')}
              style={{ cursor: extractedData ? 'pointer' : 'not-allowed' }}
            >
              Estrazione
            </span>
            <span 
              className={`cursor-pointer ${currentStep === 'completed' ? 'text-success fw-bold' : ''}`}
              onClick={() => pdfUrl && setCurrentStep('completed')}
              style={{ cursor: pdfUrl ? 'pointer' : 'not-allowed' }}
            >
              Completato
            </span>
          </div>
          
          {/* Mobile: vertical step indicator */}
          <div className="d-md-none text-center">
            <div className="d-flex justify-content-center align-items-center gap-2 mb-2">
              <span className={`badge ${currentStep === 'setup' ? 'bg-danger' : 'bg-secondary'}`}>1</span>
              <span className={`badge ${currentStep === 'recording' ? 'bg-danger' : 'bg-secondary'}`}>2</span>
              <span className={`badge ${currentStep === 'transcribing' ? 'bg-danger' : 'bg-secondary'}`}>3</span>
              <span className={`badge ${currentStep === 'editing' ? 'bg-danger' : 'bg-secondary'}`}>4</span>
              <span className={`badge ${currentStep === 'extraction' ? 'bg-danger' : 'bg-secondary'}`}>5</span>
              <span className={`badge ${currentStep === 'completed' ? 'bg-success' : 'bg-secondary'}`}>✓</span>
            </div>
            <small className="text-muted">
              {currentStep === 'setup' && 'Configurazione iniziale'}
              {currentStep === 'recording' && 'Registrazione audio'}
              {currentStep === 'transcribing' && 'Elaborazione trascrizione'}
              {currentStep === 'editing' && 'Revisione testo'}
              {currentStep === 'extraction' && 'Estrazione dati clinici'}
              {currentStep === 'completed' && 'Completato'}
            </small>
          </div>
        </div>
      </div>

      {/* STEP 1: Setup iniziale */}
      {currentStep === 'setup' && (
        <div className="row justify-content-center">
          <div className="col-12 col-lg-8">
            <div className="card border-danger">
              <div className="card-header bg-danger bg-opacity-10">
                <h3 className="card-title text-danger mb-0">
                  <i className="bi bi-clipboard-data me-2"></i>
                  Dati Iniziali Emergenza
                </h3>
              </div>
              <div className="card-body p-3 p-md-4">
                {/* Sintomi principali - sempre full width */}
                <div className="row mb-4">
                  <div className="col-12">
                    <label className="form-label fw-bold text-danger fs-5">Sintomi Principali</label>
                    <textarea
                      className="form-control form-control-lg border-danger"
                      name="sintomi_principali"
                      rows="4"
                      value={emergencyData.sintomi_principali}
                      onChange={handleEmergencyDataChange}
                      placeholder="Descrivi brevemente i sintomi principali del paziente..."
                      style={{ fontSize: '1.1rem' }}
                    />
                  </div>
                </div>

                {/* Triage e Note - responsive */}
                <div className="row mb-4 gy-3">
                  <div className="col-12 col-sm-6">
                    <label className="form-label fw-bold text-danger">Codice Triage</label>
                    <select
                      className="form-select form-select-lg border-danger"
                      name="codice_triage"
                      value={emergencyData.codice_triage}
                      onChange={handleEmergencyDataChange}
                      style={{ fontSize: '1.1rem' }}
                    >
                      <option value="bianco">⚪ Bianco - Non urgente</option>
                      <option value="verde">🟢 Verde - Urgenza minore</option>
                      <option value="giallo">🟡 Giallo - Urgenza</option>
                      <option value="rosso">🔴 Rosso - Emergenza</option>
                    </select>
                  </div>
                  <div className="col-12 col-sm-6">
                    <label className="form-label fw-bold text-danger">Note Triage</label>
                    <textarea
                      className="form-control form-control-lg border-danger"
                      name="note_triage"
                      rows="4"
                      value={emergencyData.note_triage}
                      onChange={handleEmergencyDataChange}
                      placeholder="Note aggiuntive sul triage..."
                      style={{ fontSize: '1.1rem' }}
                    />
                  </div>
                </div>

                {/* Pulsante registrazione - sempre centrato */}
                <div className="text-center">
                  <button 
                    className="btn btn-danger btn-lg px-4 py-3 fs-4 fw-bold shadow w-100 w-md-auto"
                    onClick={startRecording}
                    style={{ borderRadius: '1.5rem', letterSpacing: '0.04em', minHeight: '60px' }}
                  >
                    <i className="bi bi-mic-fill me-2"></i>
                    <span className="d-none d-sm-inline">INIZIA REGISTRAZIONE</span>
                    <span className="d-sm-none">REGISTRA</span>
                  </button>
                  <p className="text-danger mt-3 fs-6 fs-md-5">
                    Premi per iniziare la registrazione audio dell'emergenza
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: Registrazione in corso */}
      {currentStep === 'recording' && (
        <div className="row justify-content-center">
          <div className="col-12 col-lg-6">
            <div className="card border-danger text-center shadow-sm medical-processing-card">
              <div className="card-body p-4">
                {/* Icona registrazione professionale */}
                <div className="mb-3">
                  <i className="bi bi-mic-fill display-4 text-danger mb-3"
                     style={{ fontSize: '2.5rem' }}></i>
                </div>

                {/* Titolo professionale */}
                <h5 className="text-danger fw-semibold mb-2" style={{ fontSize: '1.1rem' }}>
                  Registrazione Audio Attiva
                </h5>

                {/* Sottotitolo con timer integrato */}
                <p className="text-muted mb-4" style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>
                  <strong className="text-danger medical-timer" style={{ fontSize: '1.5rem' }}>
                    {formatTime(recordingTime)}
                  </strong><br />
                  Durata registrazione • Parla chiaramente nel microfono
                </p>

                {/* Badge triage essenziale */}
                <div className="mb-3">
                  <span className={`badge fs-6 px-3 py-2 medical-triage-badge ${getTriageColor(emergencyData.codice_triage) === 'secondary' ? 'text-dark' : 'text-dark'}`}
                        style={{
                          backgroundColor: getTriageColor(emergencyData.codice_triage) === 'secondary' ? '#f8f9fa' : undefined,
                          borderColor: getTriageColor(emergencyData.codice_triage) === 'secondary' ? '#dee2e6' : undefined
                        }}>
                    <span className="me-2" style={{ fontSize: '1.2em' }}>{getTriageIcon(emergencyData.codice_triage)}</span>
                    Triage: <strong>{emergencyData.codice_triage.toUpperCase()}</strong>
                  </span>
                </div>

                {/* Pulsante stop prominente */}
                <div className="d-grid gap-2">
                  <button
                    className="btn btn-dark btn-lg px-4 py-3 fw-semibold shadow-sm emergency-btn"
                    onClick={stopRecording}
                    style={{
                      borderRadius: '0.75rem',
                      fontSize: '1.1rem',
                      minHeight: '50px'
                    }}
                  >
                    <i className="bi bi-stop-circle-fill me-2"></i>
                    TERMINA REGISTRAZIONE
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Trascrizione in corso - DESIGN PROFESSIONALE MEDICO */}
      {currentStep === 'transcribing' && (
        <div className="row justify-content-center">
          <div className="col-12 col-lg-6">
            <div className="card border-primary text-center shadow-sm medical-processing-card">
              <div className="card-body p-4">
                {/* Icona professionale */}
                <div className="mb-3">
                  <i className={`${transcribingMessages[transcribingMessage].icon} display-4 text-primary mb-3`}
                     style={{ fontSize: '2.5rem' }}></i>
                </div>

                {/* Titolo professionale */}
                <h5 className="text-primary fw-semibold mb-2" style={{ fontSize: '1.1rem' }}>
                  {transcribingMessages[transcribingMessage].title}
                </h5>

                {/* Sottotitolo tecnico */}
                <p className="text-muted mb-4" style={{ fontSize: '0.95rem', lineHeight: '1.5' }}>
                  {transcribingMessages[transcribingMessage].subtitle}
                </p>

                {/* Progress bar dinamica con effetto caricamento */}
                <div className="progress mb-3 dynamic-progress-container" style={{ height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                  <div className="progress-bar bg-primary dynamic-progress-bar"
                       style={{
                         backgroundColor: '#0066CC',
                         borderRadius: '4px'
                       }}></div>
                </div>

                {/* Indicatore fasi reali */}
                <div className="d-flex justify-content-center align-items-center gap-2 mb-3">
                  {transcribingMessages.map((_, index) => (
                    <div
                      key={index}
                      className={`rounded-circle ${index === transcribingMessage ? 'bg-primary' : 'bg-light border'}`}
                      style={{
                        width: '8px',
                        height: '8px',
                        transition: 'all 0.3s ease'
                      }}
                    ></div>
                  ))}
                </div>

                {/* Tempo stimato professionale */}
                <div className="text-center">
                  <small className="text-muted fw-medium">
                    <i className="bi bi-clock-history me-1"></i>
                    Elaborazione automatica • Attendere
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 4: Modifica trascrizione */}
      {currentStep === 'editing' && (
        <div className="row">
          <div className="col">
            <div className="card border-success">
              <div className="card-header bg-success bg-opacity-10">
                <h3 className="card-title text-success mb-0">
                  <i className="bi bi-file-text me-2"></i>
                  Trascrizione Completata - Revisiona e Modifica
                </h3>
              </div>
              <div className="card-body p-3 p-md-4">
                <div className="alert alert-success mb-4">
                  <i className="bi bi-check-circle me-2"></i>
                  <span className="fw-semibold">Trascrizione completata!</span> Puoi modificare il testo prima di estrarre i dati clinici.
                </div>

                {/* Editor trascrizione */}
                <div className="mb-4">
                  <label className="form-label fw-bold fs-5 text-success mb-3">
                    <i className="bi bi-file-text me-2"></i>
                    Trascrizione Audio:
                  </label>
                  <textarea
                    className="form-control border-success transcript-editor"
                    rows="10"
                    value={editedTranscript}
                    onChange={handleTranscriptEdit}
                    placeholder="La trascrizione apparirà qui..."
                  />
                  <div className="form-text mt-2 d-flex justify-content-between">
                    <span>Caratteri: <strong>{editedTranscript.length}</strong></span>
                    <span>Parole: <strong>{editedTranscript.split(/\s+/).filter(w => w).length}</strong></span>
                  </div>
                </div>

                {/* Pulsante estrazione - responsive */}
                <div className="text-center">
                  <div className="d-grid gap-2 d-md-flex justify-content-md-center">
                    <button 
                      className="btn btn-success btn-lg px-4 py-3 fs-5 fw-bold shadow emergency-btn"
                      onClick={handleGenerateLLMExtraction}
                      disabled={extractDataMutation.isPending}
                    >
                      {extractDataMutation.isPending ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          <span className="d-none d-sm-inline">Estraendo dati...</span>
                          <span className="d-sm-none">Elaborando...</span>
                        </>
                      ) : (
                        <>
                          <i className="bi bi-cpu me-2"></i>
                          <span className="d-none d-sm-inline">ESTRAI DATI CLINICI</span>
                          <span className="d-sm-none">ESTRAI DATI</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 5: Estrazione dati e form autocompletato */}
      {currentStep === 'extraction' && extractedData && (
        <div className="row">
          <div className="col-12">
            <div className="card border-primary">
              <div className="card-header bg-primary bg-opacity-10">
                <h4 className="card-title text-primary mb-0">
                  <i className="bi bi-cpu me-2"></i>
                  Dati Clinici Estratti - Verifica e Modifica
                </h4>
              </div>
              <div className="card-body p-4">
                {/* Informazioni sui risultati dell'estrazione */}
                <div className="row mb-4">
                  <div className="col-12">
                    <div className="alert alert-info">
                      <h5 className="alert-heading">
                        Risultati Estrazione AI
                      </h5>
                      {extractedData.validation_errors && extractedData.validation_errors.length > 0 && (
                        <div className="mt-2">
                          <strong>Avvisi di validazione:</strong>
                          <ul className="mb-0">
                            {extractedData.validation_errors.map((error, index) => (
                              <li key={index}>{error}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {extractedData.llm_fallback && (
                        <p className="mb-0 text-warning">
                          <i className="bi bi-exclamation-triangle me-1"></i>
                          <strong>Modalità fallback attivata:</strong> {extractedData.llm_warnings?.join(', ')}
                        </p>
                      )}
                      <p className="mb-0 text-muted">
                        <i className="bi bi-lightbulb me-1"></i>
                        L'AI ha estratto automaticamente i dati clinici dalla trascrizione. Verifica l'accuratezza e modifica se necessario.
                      </p>
                    </div>
                  </div>
                </div>

                {extractedData.extracted_data && (
                  <>
                    {/* Dati del paziente */}
                    <div className="row mb-4">
                      <div className="col-12">
                        <h5 className="text-primary mb-3">
                          <i className="bi bi-person me-2"></i>
                          Informazioni Paziente
                        </h5>
                        <div className="row g-3">
                          <div className="col-md-4">
                            <label className="form-label fw-bold">Nome:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.first_name || ''}
                              onChange={(e) => handleExtractedDataChange('first_name', e.target.value)}
                            />
                          </div>
                          <div className="col-md-4">
                            <label className="form-label fw-bold">Cognome:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.last_name || ''}
                              onChange={(e) => handleExtractedDataChange('last_name', e.target.value)}
                            />
                          </div>
                          <div className="col-md-4">
                            <label className="form-label fw-bold">Età:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.age || ''}
                              onChange={(e) => handleExtractedDataChange('age', e.target.value)}
                            />
                          </div>
                          <div className="col-md-12">
                            <label className="form-label fw-bold">Codice Fiscale: <span className="text-danger">*</span></label>
                            <div className="input-group">
                              <input
                                type="text"
                                className="form-control text-uppercase"
                                placeholder="RSSMRA80A01H501Z"
                                maxLength="16"
                                value={extractedData.extracted_data.codice_fiscale || ''}
                                onChange={(e) => handleExtractedDataChange('codice_fiscale', e.target.value.toUpperCase())}
                                style={{ fontFamily: 'monospace' }}
                              />
                              <button
                                type="button"
                                className="btn btn-outline-primary"
                                onClick={handleCalculateCodiceFiscale}
                                title="Calcola automaticamente"
                              >
                                <i className="bi bi-calculator"></i>
                              </button>
                            </div>
                            <small className="text-muted">Obbligatorio - 16 caratteri alfanumerici</small>
                          </div>
                          <div className="col-md-4">
                            <label className="form-label fw-bold">Data Nascita:</label>
                            <input
                              type="date"
                              className="form-control"
                              value={extractedData.extracted_data.birth_date || ''}
                              onChange={(e) => handleExtractedDataChange('birth_date', e.target.value)}
                            />
                          </div>
                          <div className="col-md-4">
                            <label className="form-label fw-bold">Luogo Nascita:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.birth_place || ''}
                              onChange={(e) => handleExtractedDataChange('birth_place', e.target.value)}
                            />
                          </div>
                          <div className="col-md-4">
                            <label className="form-label fw-bold">Sesso:</label>
                            <select
                              className="form-select"
                              value={extractedData.extracted_data.gender || ''}
                              onChange={(e) => handleExtractedDataChange('gender', e.target.value)}
                            >
                              <option value="">Seleziona</option>
                              <option value="M">Maschio</option>
                              <option value="F">Femmina</option>
                              <option value="O">Altro</option>
                            </select>
                          </div>
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Telefono:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.phone || ''}
                              onChange={(e) => handleExtractedDataChange('phone', e.target.value)}
                            />
                          </div>
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Città Residenza:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.residence_city || ''}
                              onChange={(e) => handleExtractedDataChange('residence_city', e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Parametri vitali */}
                    <div className="row mb-4">
                      <div className="col-12">
                        <h5 className="text-success mb-3">
                          <i className="bi bi-heart-pulse me-2"></i>
                          Parametri Vitali
                        </h5>
                        <div className="row g-3">
                          <div className="col-md-3">
                            <label className="form-label fw-bold">Pressione Arteriosa:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.blood_pressure || ''}
                              onChange={(e) => handleExtractedDataChange('blood_pressure', e.target.value)}
                              placeholder="es. 120/80"
                            />
                          </div>
                          <div className="col-md-3">
                            <label className="form-label fw-bold">Frequenza Cardiaca:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.heart_rate || ''}
                              onChange={(e) => handleExtractedDataChange('heart_rate', e.target.value)}
                              placeholder="bpm"
                            />
                          </div>
                          <div className="col-md-3">
                            <label className="form-label fw-bold">Temperatura:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.temperature || ''}
                              onChange={(e) => handleExtractedDataChange('temperature', e.target.value)}
                              placeholder="°C"
                            />
                          </div>
                          <div className="col-md-3">
                            <label className="form-label fw-bold">Saturazione O2:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.oxygen_saturation || ''}
                              onChange={(e) => handleExtractedDataChange('oxygen_saturation', e.target.value)}
                              placeholder="%"
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Informazioni cliniche */}
                    <div className="row mb-4">
                      <div className="col-12">
                        <h5 className="text-warning mb-3">
                          <i className="bi bi-clipboard-pulse me-2"></i>
                          Informazioni Cliniche
                        </h5>
                        <div className="row g-3">
                          <div className="col-12">
                            <label className="form-label fw-bold">Sintomi:</label>
                            <textarea
                              className="form-control"
                              rows="3"
                              value={extractedData.extracted_data.symptoms || ''}
                              onChange={(e) => handleExtractedDataChange('symptoms', e.target.value)}
                            />
                          </div>
                          <div className="col-12">
                            <label className="form-label fw-bold">Diagnosi Differenziale:</label>
                            <textarea
                              className="form-control"
                              rows="3"
                              value={extractedData.extracted_data.diagnosis || ''}
                              onChange={(e) => handleExtractedDataChange('diagnosis', e.target.value)}
                            />
                          </div>
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Codice Triage:</label>
                            <select
                              className="form-select"
                              value={extractedData.extracted_data.triage_code || emergencyData.codice_triage || ''}
                              onChange={(e) => handleExtractedDataChange('triage_code', e.target.value)}
                            >
                              <option value="">Seleziona</option>
                              <option value="bianco">⚪ Bianco - Non Urgente</option>
                              <option value="verde">🟢 Verde - Poco Urgente</option>
                              <option value="giallo">🟡 Giallo - Urgente</option>
                              <option value="rosso">🔴 Rosso - Molto Urgente</option>
                            </select>
                            {!extractedData.extracted_data.triage_code && emergencyData.codice_triage && (
                              <div className="form-text text-info">
                                <i className="bi bi-info-circle me-1"></i>
                                Codice ereditato dai dati iniziali dell'emergenza
                              </div>
                            )}
                          </div>
                          <div className="col-md-6">
                            <label className="form-label fw-bold">Modalità Accesso:</label>
                            <input
                              type="text"
                              className="form-control"
                              value={extractedData.extracted_data.access_mode || ''}
                              onChange={(e) => handleExtractedDataChange('access_mode', e.target.value)}
                              placeholder="es. Ambulanza, Autonomo"
                            />
                          </div>
                          <div className="col-12">
                            <label className="form-label fw-bold">Note Mediche:</label>
                            <textarea
                              className="form-control"
                              rows="4"
                              value={extractedData.extracted_data.medical_notes || ''}
                              onChange={(e) => handleExtractedDataChange('medical_notes', e.target.value)}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}

                {/* Pulsante generazione PDF - responsive */}
                <div className="text-center mt-4">
                  <div className="d-grid gap-2 d-md-flex justify-content-md-center">
                    <button 
                      className="btn btn-primary btn-lg px-4 py-3 fs-5 fw-bold shadow emergency-btn"
                      onClick={handleGeneratePDF}
                      disabled={updateClinicalDataMutation.isPending || generatePDFMutation.isPending}
                    >
                      {updateClinicalDataMutation.isPending || generatePDFMutation.isPending ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          <span className="d-none d-sm-inline">
                            {updateClinicalDataMutation.isPending ? 'Salvando modifiche...' : 'Generando PDF...'}
                          </span>
                          <span className="d-sm-none">
                            {updateClinicalDataMutation.isPending ? 'Salvando...' : 'PDF...'}
                          </span>
                        </>
                      ) : (
                        <>
                          <i className="bi bi-file-pdf me-2"></i>
                          <span className="d-none d-sm-inline">GENERA REPORT PDF</span>
                          <span className="d-sm-none">PDF</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="mt-3">
                    <small className="text-muted">
                      <i className="bi bi-info-circle me-1"></i>
                      Le modifiche ai dati verranno salvate automaticamente prima della generazione del PDF
                    </small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 6: Completato */}
      {currentStep === 'completed' && (
        <div className="row justify-content-center">
          <div className="col-12 col-lg-6">
            <div className="card border-success text-center shadow-lg completion-card">
              <div className="card-body p-4 p-md-5">
                <div className="mb-4">
                  <i className="bi bi-check-circle text-success" style={{ fontSize: '4rem' }}></i>
                </div>
                <h2 className="text-success fw-bold mb-3">EMERGENZA COMPLETATA</h2>
                <p className="fs-6 fs-md-5 text-muted mb-4">
                  La registrazione è stata elaborata con successo. Il report PDF è disponibile per il download.
                </p>

                {/* Bottoni azione - responsive */}
                <div className="d-grid gap-2 d-md-flex justify-content-md-center flex-wrap">
                  <button 
                    className="btn btn-danger btn-lg px-3 py-2 emergency-btn"
                    onClick={() => window.location.reload()}
                  >
                    <i className="bi bi-plus-circle me-2"></i>
                    <span className="d-none d-sm-inline">Nuova Emergenza</span>
                    <span className="d-sm-none">Nuova</span>
                  </button>
                  
                  <button 
                    className="btn btn-primary btn-lg px-3 py-2 emergency-btn"
                    onClick={() => navigate('/dashboard')}
                  >
                    <i className="bi bi-house me-2"></i>
                    <span className="d-none d-sm-inline">Dashboard</span>
                    <span className="d-sm-none">Home</span>
                  </button>
                  
                  {pdfUrl && (
                    <a 
                      href={`http://localhost:8000${pdfUrl}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-success btn-lg px-3 py-2 emergency-btn"
                    >
                      <i className="bi bi-download me-2"></i>
                      <span className="d-none d-sm-inline">Scarica PDF</span>
                      <span className="d-sm-none">PDF</span>
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default NewEmergencyPage