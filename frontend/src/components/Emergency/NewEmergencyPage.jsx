/**
 * Pagina completa per Nuova Emergenza
 * Gestisce tutto il flusso: registrazione in tempo reale, trascrizione, modifica, PDF, estrazione dati
 */

import React, { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'
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
    codice_triage: 'white',
    note_triage: ''
  })

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

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
            setExtractedData({ extracted_data: details.clinical_data })
          }
        })
        .catch(error => {
          console.error('Errore caricamento dati intervento:', error)
        })
    }
  }, [editMode, interventionData])

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
    if (transcriptId && editedTranscript) {
      extractDataMutation.mutate(editedTranscript)
    }
  }

  const handleGeneratePDF = () => {
    if (transcriptId) {
      generatePDFMutation.mutate(transcriptId)
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

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getTriageColor = (code) => {
    const colors = {
      white: 'secondary',
      green: 'success',
      yellow: 'warning',
      red: 'danger',
      black: 'dark'
    }
    return colors[code] || 'secondary'
  }

  const getTriageIcon = (code) => {
    const icons = {
      white: '⚪',
      green: '🟢',
      yellow: '🟡',
      red: '🔴',
      black: '⚫'
    }
    return icons[code] || '⚪'
  }

  return (
    <div className="container-fluid py-2">
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

      {/* Progress indicator */}
      <div className="row mb-4">
        <div className="col">
          <div className="progress mb-3" style={{ height: '8px' }}>
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
              <div className="card-body p-4">
                <div className="row mb-4">
                  <div className="col-12 col-md-6 mb-3">
                    <label className="form-label fw-bold text-danger">Sintomi Principali</label>
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
                  <div className="col-6 col-md-3 mb-3">
                    <label className="form-label fw-bold text-danger">Codice Triage</label>
                    <select
                      className="form-select form-select-lg border-danger"
                      name="codice_triage"
                      value={emergencyData.codice_triage}
                      onChange={handleEmergencyDataChange}
                      style={{ fontSize: '1.1rem' }}
                    >
                      <option value="white">⚪ Bianco</option>
                      <option value="green">🟢 Verde</option>
                      <option value="yellow">🟡 Giallo</option>
                      <option value="red">🔴 Rosso</option>
                      <option value="black">⚫ Nero</option>
                    </select>
                  </div>
                  <div className="col-6 col-md-3 mb-3">
                    <label className="form-label fw-bold text-danger">Note Triage</label>
                    <textarea
                      className="form-control form-control-lg border-danger"
                      name="note_triage"
                      rows="4"
                      value={emergencyData.note_triage}
                      onChange={handleEmergencyDataChange}
                      placeholder="Note aggiuntive..."
                      style={{ fontSize: '1.1rem' }}
                    />
                  </div>
                </div>

                <div className="text-center">
                  <button 
                    className="btn btn-danger btn-lg px-5 py-3 fs-3 fw-bold shadow"
                    onClick={startRecording}
                    style={{ borderRadius: '1.5rem', letterSpacing: '0.04em' }}
                  >
                    <i className="bi bi-mic-fill me-2"></i>
                    INIZIA REGISTRAZIONE
                  </button>
                  <p className="text-danger mt-3 fs-5">
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
            <div className="card border-danger text-center">
              <div className="card-body p-5">
                <div className="mb-4">
                  <div className="display-1 text-danger mb-3">
                    <i className="bi bi-record-circle-fill"></i>
                  </div>
                  <h2 className="text-danger fw-bold">REGISTRAZIONE IN CORSO</h2>
                  <h1 className="font-monospace text-danger" style={{ fontSize: '3rem' }}>
                    {formatTime(recordingTime)}
                  </h1>
                </div>

                <div className="mb-4">
                  <span className={`badge bg-${getTriageColor(emergencyData.codice_triage)} fs-4 px-4 py-2`}>
                    {getTriageIcon(emergencyData.codice_triage)} Triage: {emergencyData.codice_triage.toUpperCase()}
                  </span>
                </div>

                <button 
                  className="btn btn-dark btn-lg px-5 py-3 fs-3 fw-bold shadow"
                  onClick={stopRecording}
                  style={{ borderRadius: '1.5rem', letterSpacing: '0.04em' }}
                >
                  <i className="bi bi-stop-fill me-2"></i>
                  TERMINA REGISTRAZIONE
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STEP 3: Trascrizione in corso */}
      {currentStep === 'transcribing' && (
        <div className="row justify-content-center">
          <div className="col-12 col-lg-6">
            <div className="card border-primary text-center">
              <div className="card-body p-5">
                <div className="spinner-border text-primary mb-3" style={{ width: '4rem', height: '4rem' }}>
                  <span className="visually-hidden">Elaborazione...</span>
                </div>
                <h3 className="text-primary mb-3">Elaborazione in corso...</h3>
                <p className="fs-5 text-muted mb-4">
                  Stiamo trascrivendo l'audio e estraendo i dati clinici utilizzando l'AI
                </p>
                <div className="progress" style={{ height: '12px' }}>
                  <div className="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                       style={{ width: '100%' }}></div>
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
              <div className="card-body p-4">
                <div className="alert alert-success mb-4">
                  <i className="bi bi-check-circle me-2"></i>
                  Trascrizione completata! Puoi modificare il testo prima di estrarre i dati clinici.
                </div>

                <div className="mb-4">
                  <label className="form-label fw-bold fs-5">Trascrizione Audio:</label>
                  <textarea
                    className="form-control border-success"
                    rows="12"
                    value={editedTranscript}
                    onChange={handleTranscriptEdit}
                    style={{ fontSize: '1.1rem', lineHeight: '1.6' }}
                    placeholder="La trascrizione apparirà qui..."
                  />
                  <div className="form-text">
                    Caratteri: {editedTranscript.length} | Parole: {editedTranscript.split(/\s+/).filter(w => w).length}
                  </div>
                </div>

                <div className="text-center">
                  <button 
                    className="btn btn-success btn-lg px-4 py-3 fs-4 fw-bold shadow me-3"
                    onClick={handleGenerateLLMExtraction}
                    disabled={extractDataMutation.isPending}
                    style={{ borderRadius: '1.2rem' }}
                  >
                    {extractDataMutation.isPending ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Estraendo dati...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-cpu me-2"></i>
                        ESTRAI DATI CLINICI
                      </>
                    )}
                  </button>
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
                        <i className="bi bi-info-circle me-2"></i>
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
                              value={extractedData.extracted_data.triage_code || ''}
                              onChange={(e) => handleExtractedDataChange('triage_code', e.target.value)}
                            >
                              <option value="">Seleziona</option>
                              <option value="white">⚪ Bianco - Non Urgente</option>
                              <option value="green">🟢 Verde - Poco Urgente</option>
                              <option value="yellow">🟡 Giallo - Urgente</option>
                              <option value="red">🔴 Rosso - Molto Urgente</option>
                              <option value="black">⚫ Nero - Critico</option>
                            </select>
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

                <div className="text-center mt-4">
                  <button 
                    className="btn btn-primary btn-lg px-4 py-3 fs-5 fw-bold shadow"
                    onClick={handleGeneratePDF}
                    disabled={generatePDFMutation.isPending}
                    style={{ borderRadius: '1.2rem' }}
                  >
                    {generatePDFMutation.isPending ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Generando PDF...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-file-pdf me-2"></i>
                        GENERA REPORT PDF
                      </>
                    )}
                  </button>
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
            <div className="card border-success text-center">
              <div className="card-body p-5">
                <div className="mb-4">
                  <i className="bi bi-check-circle text-success" style={{ fontSize: '5rem' }}></i>
                </div>
                <h2 className="text-success fw-bold mb-3">EMERGENZA COMPLETATA</h2>
                <p className="fs-5 text-muted mb-4">
                  La registrazione è stata elaborata con successo. Il report PDF è disponibile per il download.
                </p>

                <div className="d-flex justify-content-center gap-3 flex-wrap">
                  <button 
                    className="btn btn-danger btn-lg px-4 py-3"
                    onClick={() => window.location.reload()}
                    style={{ borderRadius: '1.2rem' }}
                  >
                    <i className="bi bi-plus-circle me-2"></i>
                    Nuova Emergenza
                  </button>
                  <button 
                    className="btn btn-primary btn-lg px-4 py-3"
                    onClick={() => navigate('/dashboard')}
                    style={{ borderRadius: '1.2rem' }}
                  >
                    <i className="bi bi-house me-2"></i>
                    Dashboard
                  </button>
                  {pdfUrl && (
                    <a 
                      href={`http://localhost:8000${pdfUrl}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-success btn-lg px-4 py-3"
                      style={{ borderRadius: '1.2rem' }}
                    >
                      <i className="bi bi-download me-2"></i>
                      Scarica PDF
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