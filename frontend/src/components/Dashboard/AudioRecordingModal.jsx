import React, { useState, useRef, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'

const AudioRecordingModal = ({ isOpen, onClose, patient, onCompleted }) => {
  const queryClient = useQueryClient()
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)

  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState(null)
  const [transcription, setTranscription] = useState('')
  const [clinicalData, setClinicalData] = useState(null)
  const [resultPatient, setResultPatient] = useState(null)
  const [step, setStep] = useState('record') // 'record', 'transcribing', 'processing', 'review'
  const activePatient = resultPatient || patient || {}
  const patientId = activePatient?.patient_id || activePatient?.patientId || activePatient?.id || activePatient?.id_patient || null
  const patientFirstName = activePatient?.nome || activePatient?.first_name || ''
  const patientLastName = activePatient?.cognome || activePatient?.last_name || ''
  const patientDisplayName = `${patientFirstName} ${patientLastName}`.trim() || 'Paziente non selezionato'
  const patientFiscalCode = activePatient?.codice_fiscale || activePatient?.fiscal_code || ''
  const patientBirthDate = activePatient?.data_nascita || activePatient?.date_of_birth || ''
  const defaultTriageCode = activePatient?.codice_triage || activePatient?.last_triage_code || 'white'
  const [visitData, setVisitData] = useState({
    sintomi_principali: '',
    codice_triage: defaultTriageCode,
    note_triage: ''
  })

  const timerRef = useRef(null)

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

  useEffect(() => {
    setVisitData(prev => ({
      ...prev,
      codice_triage: defaultTriageCode
    }))
  }, [defaultTriageCode])

  // Mutation per processare l'audio
  const processAudioMutation = useMutation({
    mutationFn: async (audioData) => {
      const formData = new FormData()
      formData.append('audio_file', audioData.blob)
      if (patientId) {
        formData.append('patient_id', patientId)
      }
      formData.append('sintomi_principali', visitData.sintomi_principali)
      formData.append('codice_triage', visitData.codice_triage)
      formData.append('note_triage', visitData.note_triage)
      
      return medicalWorkflowAPI.processAudioVisit(formData)
    },
    onSuccess: (data) => {
      setTranscription(data.transcript || '')
      setClinicalData(data.clinical_data || null)
      setResultPatient(data.patient || null)
      setStep('review')
      queryClient.invalidateQueries({ queryKey: ['patients-list'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-analytics'] })
      // NON chiamare onCompleted qui - lascia che l'utente veda i risultati prima
    },
    onError: (error) => {
      console.error('Errore processing audio:', error)
      const errorMessage = error?.response?.data?.error || error?.message || 'Errore durante l\'elaborazione dell\'audio'
      alert(errorMessage)
      setStep('record')
    }
  })

  // Funzione per gestire il download del PDF
  const handleDownloadPDF = async () => {
    try {
      const transcriptId = processAudioMutation.data?.transcript_id
      if (!transcriptId) {
        alert('Errore: ID trascrizione non disponibile')
        return
      }

      // Prima genera il PDF
      await medicalWorkflowAPI.generatePDFReport(transcriptId)
      
      // Poi scaricalo
      const blob = await medicalWorkflowAPI.downloadPDFReport(transcriptId)
      
      // Crea URL per il download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `report_${transcriptId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
    } catch (error) {
      console.error('Errore nel download PDF:', error)
      alert('Errore durante il download del PDF: ' + (error.message || 'Errore sconosciuto'))
    }
  }

  // Funzione per gestire la chiusura del modal
  const handleClose = () => {
    // Chiama onCompleted solo quando l'utente chiude effettivamente il modal
    if (step === 'review' && onCompleted) {
      onCompleted({
        transcriptId: processAudioMutation.data?.transcript_id,
        encounterId: processAudioMutation.data?.encounter_id,
        patient: processAudioMutation.data?.patient || resultPatient,
        raw: processAudioMutation.data
      })
    }
    onClose()
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        setAudioBlob(audioBlob)
        setStep('transcribing')
        
        // Invia l'audio per la trascrizione e analisi
        processAudioMutation.mutate({ blob: audioBlob })
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      // Timer per il tempo di registrazione
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

    } catch (error) {
      console.error('Errore accesso microfono:', error)
      alert('Errore nell\'accesso al microfono. Verifica i permessi del browser.')
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

  const resetRecording = () => {
    setAudioBlob(null)
    setTranscription('')
    setClinicalData(null)
    setStep('record')
    setRecordingTime(0)
    setVisitData({
      sintomi_principali: '',
      codice_triage: defaultTriageCode,
      note_triage: ''
    })
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleVisitDataChange = (e) => {
    const { name, value } = e.target
    setVisitData(prev => ({
      ...prev,
      [name]: value
    }))
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

  if (!isOpen) return null

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header flex-column flex-md-row align-items-start align-items-md-center bg-danger bg-opacity-10 border-0" style={{borderRadius: '1.2rem 1.2rem 0 0'}}>
            <div className="d-flex flex-column flex-md-row align-items-start align-items-md-center w-100">
              <h2 className="modal-title text-danger fw-bold d-flex align-items-center mb-2 mb-md-0" style={{fontSize: '2rem', letterSpacing: '0.01em'}}>
                <i className="bi bi-mic me-2 fs-1"></i>
                NUOVA EMERGENZA
              </h2>
              <span className="badge bg-secondary ms-md-3 fs-6 px-3 py-2">{patientDisplayName}</span>
            </div>
            <button 
              type="button" 
              className="btn-close ms-auto mt-2 mt-md-0" 
              onClick={handleClose}
              disabled={isRecording || processAudioMutation.isPending}
              aria-label="Chiudi"
            ></button>
          </div>

          <div className="modal-body">
            {/* Info Paziente */}
            <div className="card mb-4 border-0 bg-light shadow-sm">
              <div className="card-body p-3 p-md-4">
                <div className="row gy-2 gx-3 align-items-center">
                  <div className="col-12 col-md-3">
                    <strong>Paziente:</strong><br />
                    {patientDisplayName}
                  </div>
                  <div className="col-6 col-md-3">
                    <strong>Codice Fiscale:</strong><br />
                    {patientFiscalCode || 'N/D'}
                  </div>
                  <div className="col-6 col-md-3">
                    <strong>Data di Nascita:</strong><br />
                    {patientBirthDate || 'N/D'}
                  </div>
                  <div className="col-12 col-md-3 text-md-end mt-2 mt-md-0">
                    <span className={`badge bg-${getTriageColor(visitData.codice_triage)} fs-6 px-3 py-2`} style={{fontSize: '1.1rem'}}>
                      {getTriageIcon(visitData.codice_triage)} Triage: {visitData.codice_triage?.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {step === 'record' && (
              <div>
                {/* Dati pre-visita */}
                <div className="row mb-4 gy-3 flex-column flex-md-row">
                  {!patientId && (
                    <div className="col-12">
                      <div className="alert alert-info d-flex align-items-center" role="alert">
                        <i className="bi bi-info-circle me-2"></i>
                        <span>
                          Verrà creato automaticamente un nuovo paziente utilizzando i dati estratti dalla registrazione.
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="col-12 col-md-6">
                    <label htmlFor="sintomi_principali" className="form-label fw-bold text-danger">
                      Sintomi Principali
                    </label>
                    <textarea
                      className="form-control form-control-lg border-danger border-2"
                      id="sintomi_principali"
                      name="sintomi_principali"
                      rows="3"
                      value={visitData.sintomi_principali}
                      onChange={handleVisitDataChange}
                      placeholder="Descrizione breve dei sintomi principali..."
                      style={{fontSize: '1.1rem'}}
                    ></textarea>
                  </div>
                  <div className="col-6 col-md-3">
                    <label htmlFor="codice_triage" className="form-label fw-bold text-danger">
                      Codice Triage
                    </label>
                    <select
                      className="form-select form-select-lg border-danger border-2"
                      id="codice_triage"
                      name="codice_triage"
                      value={visitData.codice_triage}
                      onChange={handleVisitDataChange}
                      style={{fontSize: '1.1rem'}}
                    >
                      <option value="white">⚪ Bianco</option>
                      <option value="green">🟢 Verde</option>
                      <option value="yellow">🟡 Giallo</option>
                      <option value="red">🔴 Rosso</option>
                      <option value="black">⚫ Nero</option>
                    </select>
                  </div>
                  <div className="col-6 col-md-3">
                    <label htmlFor="note_triage" className="form-label fw-bold text-danger">
                      Note Triage
                    </label>
                    <textarea
                      className="form-control form-control-lg border-danger border-2"
                      id="note_triage"
                      name="note_triage"
                      rows="3"
                      value={visitData.note_triage}
                      onChange={handleVisitDataChange}
                      placeholder="Note aggiuntive..."
                      style={{fontSize: '1.1rem'}}
                    ></textarea>
                  </div>
                </div>

                {/* Controlli Registrazione */}
                <div className="text-center mt-3">
                  {!isRecording ? (
                    <div>
                      <button 
                        className="btn btn-danger btn-lg px-5 py-3 fs-3 fw-bold shadow"
                        onClick={startRecording}
                        style={{borderRadius: '1.5rem', letterSpacing: '0.04em'}}
                      >
                        <i className="bi bi-mic-fill me-2"></i>
                        INIZIA REGISTRAZIONE
                      </button>
                      <p className="text-danger mt-3 fs-5 fw-semibold">
                        Premi per iniziare la registrazione della visita/emergenza
                      </p>
                    </div>
                  ) : (
                    <div>
                      <div className="mb-3">
                        <div className="display-4 text-danger">
                          <i className="bi bi-record-circle-fill"></i>
                        </div>
                        <h3 className="text-danger">Registrazione in corso...</h3>
                        <h2 className="font-monospace">{formatTime(recordingTime)}</h2>
                      </div>
                      <div className="mb-4">
                        <span className={`badge bg-${getTriageColor(visitData.codice_triage)} fs-4 px-4 py-2`}>
                          {getTriageIcon(visitData.codice_triage)} Triage: {visitData.codice_triage?.toUpperCase()}
                        </span>
                      </div>
                      <button 
                        className="btn btn-dark btn-lg px-5 py-3 fs-3 fw-bold shadow"
                        onClick={stopRecording}
                        style={{borderRadius: '1.5rem', letterSpacing: '0.04em'}}
                      >
                        <i className="bi bi-stop-fill me-2"></i>
                        TERMINA REGISTRAZIONE
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {step === 'transcribing' && (
              <div className="text-center py-4">
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
            )}

            {step === 'review' && (
              <div>
                <div className="alert alert-success">
                  <i className="bi bi-check-circle me-2"></i>
                  Elaborazione completata! Revisa i dati estratti prima di salvare.
                </div>

                {clinicalData?.fallback && (
                  <div className="alert alert-warning">
                    <i className="bi bi-exclamation-triangle me-2"></i>
                    Il servizio di estrazione avanzata non è disponibile, sono stati utilizzati dati generici.
                    {clinicalData?.warnings?.length > 0 && (
                      <ul className="mt-2 mb-0">
                        {clinicalData.warnings.map((warning, index) => (
                          <li key={index} className="small">{warning}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Trascrizione */}
                <div className="card mb-3 border-success">
                  <div className="card-header bg-success bg-opacity-10">
                    <h5 className="mb-0 fw-bold text-success">
                      <i className="bi bi-file-text me-2"></i>
                      Trascrizione Audio Whisper AI
                    </h5>
                  </div>
                  <div className="card-body">
                    <div className="bg-light p-4 rounded border" style={{ 
                      maxHeight: '300px', 
                      overflowY: 'auto',
                      fontSize: '1.1rem',
                      lineHeight: '1.6',
                      fontFamily: 'Georgia, serif'
                    }}>
                      {transcription ? (
                        <div>
                          <p className="mb-0" style={{ textAlign: 'justify' }}>
                            {transcription}
                          </p>
                          <hr className="my-3" />
                          <small className="text-muted d-flex align-items-center justify-content-between">
                            <span>
                              <i className="bi bi-robot me-1"></i>
                              Trascritto automaticamente con AI Whisper
                            </span>
                            <span>
                              Caratteri: {transcription.length} | Parole: {transcription.split(/\s+/).filter(w => w).length}
                            </span>
                          </small>
                        </div>
                      ) : (
                        <div className="text-center text-muted">
                          <i className="bi bi-hourglass-split me-2"></i>
                          Trascrizione in elaborazione...
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Dati Clinici Estratti */}
                {clinicalData && (
                  <div className="card mb-3">
                    <div className="card-header">
                      <h6 className="mb-0">
                        <i className="bi bi-cpu me-2"></i>
                        Dati Clinici Estratti dall'AI
                      </h6>
                    </div>
                    <div className="card-body">
                      <div className="row">
                        {clinicalData.diagnosi && (
                          <div className="col-md-6 mb-2">
                            <strong>Diagnosi:</strong><br />
                            <span className="badge bg-info fs-6">{clinicalData.diagnosi}</span>
                          </div>
                        )}
                        {clinicalData.terapia && (
                          <div className="col-md-6 mb-2">
                            <strong>Terapia:</strong><br />
                            <span className="badge bg-success fs-6">{clinicalData.terapia}</span>
                          </div>
                        )}
                        {clinicalData.sintomi && (
                          <div className="col-md-6 mb-2">
                            <strong>Sintomi:</strong><br />
                            <span className="badge bg-warning fs-6">{clinicalData.sintomi}</span>
                          </div>
                        )}
                        {clinicalData.esami && (
                          <div className="col-md-6 mb-2">
                            <strong>Esami:</strong><br />
                            <span className="badge bg-secondary fs-6">{clinicalData.esami}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Sezione Download PDF */}
                <div className="card mb-3 border-primary">
                  <div className="card-header bg-primary bg-opacity-10">
                    <h6 className="mb-0 fw-bold text-primary">
                      <i className="bi bi-file-earmark-pdf me-2"></i>
                      Report PDF
                    </h6>
                  </div>
                  <div className="card-body text-center">
                    <p className="text-muted mb-3">
                      Scarica il report PDF completo della visita con tutti i dati clinici estratti
                    </p>
                    <button 
                      className="btn btn-primary btn-lg px-4 py-2"
                      onClick={handleDownloadPDF}
                      disabled={!processAudioMutation.data?.transcript_id}
                    >
                      <i className="bi bi-download me-2"></i>
                      Scarica Report PDF
                    </button>
                  </div>
                </div>

                <div className="text-center">
                  <p className="text-success">
                    <i className="bi bi-check-circle me-2"></i>
                    Visita salvata con successo! Puoi scaricare il report PDF e chiudere il modal.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            {step === 'record' && !isRecording && (
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={handleClose}
              >
                Annulla
              </button>
            )}
            
            {step === 'record' && audioBlob && (
              <button 
                type="button" 
                className="btn btn-warning" 
                onClick={resetRecording}
              >
                <i className="bi bi-arrow-clockwise me-2"></i>
                Registra di Nuovo
              </button>
            )}

            {step === 'review' && (
              <>
                <button 
                  type="button" 
                  className="btn btn-warning btn-lg px-4 py-3" 
                  onClick={resetRecording}
                  style={{borderRadius: '1.2rem'}}
                >
                  <i className="bi bi-arrow-clockwise me-2"></i>
                  Nuova Registrazione
                </button>
                <button 
                  type="button" 
                  className="btn btn-success btn-lg px-4 py-3" 
                  onClick={handleClose}
                  style={{borderRadius: '1.2rem'}}
                >
                  <i className="bi bi-check-lg me-2"></i>
                  Completa Visita
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AudioRecordingModal