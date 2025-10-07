/**
 * Modal per avviare rapidamente il workflow completo per un encounter
 */

import React, { useState, useRef } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '@services/api'

const QuickWorkflowModal = ({ isOpen, onClose, encounter }) => {
  const queryClient = useQueryClient()
  const fileInputRef = useRef(null)
  
  const [selectedFile, setSelectedFile] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState({
    transcription: false,
    extraction: false,
    report: false
  })
  const [results, setResults] = useState({
    transcriptId: null,
    clinicalDataId: null,
    reportId: null
  })

  // Reset stato quando si apre/chiude il modal
  React.useEffect(() => {
    if (isOpen) {
      setSelectedFile(null)
      setIsProcessing(false)
      setProgress({ transcription: false, extraction: false, report: false })
      setResults({ transcriptId: null, clinicalDataId: null, reportId: null })
    }
  }, [isOpen])

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleCompleteWorkflow = async () => {
    if (!selectedFile || !encounter) return

    setIsProcessing(true)
    
    try {
      // Avvia il workflow completo
      setProgress({ transcription: true, extraction: false, report: false })
      
      const response = await medicalWorkflowAPI.completeWorkflow(
        encounter.encounter_id,
        selectedFile
      )
      
      setProgress({ transcription: true, extraction: true, report: false })
      
      // Simula il progresso per l'estrazione
      setTimeout(() => {
        setProgress({ transcription: true, extraction: true, report: true })
        setResults({
          transcriptId: response.transcript_id,
          clinicalDataId: response.clinical_data_id,
          reportId: response.report_id
        })
        
        // Aggiorna le query
        queryClient.invalidateQueries(['workflow-status', encounter.encounter_id])
        queryClient.invalidateQueries(['workflow-stats'])
        
        setIsProcessing(false)
      }, 2000)
      
    } catch (error) {
      console.error('Errore durante il workflow:', error)
      setIsProcessing(false)
      // TODO: gestire errore con toast/alert
    }
  }

  const handleDownloadReport = async () => {
    if (results.reportId) {
      try {
        await medicalWorkflowAPI.downloadReport(results.reportId)
      } catch (error) {
        console.error('Errore durante il download:', error)
      }
    }
  }

  const handleClose = () => {
    if (!isProcessing) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-lightning-charge me-2"></i>
              Workflow Rapido - {encounter?.patient_name}
            </h5>
            {!isProcessing && (
              <button
                type="button"
                className="btn-close"
                onClick={handleClose}
              ></button>
            )}
          </div>

          <div className="modal-body">
            {!isProcessing && !results.reportId ? (
              // Fase di selezione file
              <div>
                <p className="text-muted mb-3">
                  Seleziona un file audio per avviare automaticamente trascrizione, 
                  estrazione dati clinici e generazione report.
                </p>
                
                <div className="mb-3">
                  <label className="form-label">File Audio</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="form-control"
                    accept="audio/*"
                    onChange={handleFileSelect}
                  />
                  <div className="form-text">
                    Formati supportati: MP3, WAV, M4A, OGG
                  </div>
                </div>

                {selectedFile && (
                  <div className="alert alert-info">
                    <strong>File selezionato:</strong> {selectedFile.name}
                    <br />
                    <strong>Dimensione:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                )}
              </div>
            ) : isProcessing ? (
              // Fase di processing
              <div>
                <p className="text-muted mb-3">
                  Elaborazione in corso... Questo potrebbe richiedere alcuni minuti.
                </p>
                
                <div className="mb-3">
                  <div className="d-flex align-items-center mb-2">
                    <i className={`bi bi-mic me-2 ${progress.transcription ? 'text-success' : 'text-muted'}`}></i>
                    <span className={progress.transcription ? 'text-success' : 'text-muted'}>
                      Trascrizione Audio
                    </span>
                    {progress.transcription && <i className="bi bi-check-lg text-success ms-auto"></i>}
                  </div>
                  
                  <div className="d-flex align-items-center mb-2">
                    <i className={`bi bi-clipboard-data me-2 ${progress.extraction ? 'text-success' : 'text-muted'}`}></i>
                    <span className={progress.extraction ? 'text-success' : 'text-muted'}>
                      Estrazione Dati Clinici
                    </span>
                    {progress.extraction && <i className="bi bi-check-lg text-success ms-auto"></i>}
                  </div>
                  
                  <div className="d-flex align-items-center mb-2">
                    <i className={`bi bi-file-earmark-text me-2 ${progress.report ? 'text-success' : 'text-muted'}`}></i>
                    <span className={progress.report ? 'text-success' : 'text-muted'}>
                      Generazione Report
                    </span>
                    {progress.report && <i className="bi bi-check-lg text-success ms-auto"></i>}
                  </div>
                </div>

                <div className="progress">
                  <div 
                    className="progress-bar progress-bar-striped progress-bar-animated" 
                    style={{
                      width: `${
                        progress.transcription && progress.extraction && progress.report ? 100 :
                        progress.transcription && progress.extraction ? 66 :
                        progress.transcription ? 33 : 0
                      }%`
                    }}
                  ></div>
                </div>
              </div>
            ) : (
              // Fase completata
              <div>
                <div className="alert alert-success">
                  <i className="bi bi-check-circle me-2"></i>
                  <strong>Workflow completato con successo!</strong>
                </div>
                
                <p className="text-muted">
                  Il workflow è stato completato per l'episodio <strong>{encounter?.encounter_id}</strong>.
                  Il report è pronto per il download.
                </p>
                
                <div className="d-grid gap-2">
                  <button
                    className="btn btn-primary"
                    onClick={handleDownloadReport}
                  >
                    <i className="bi bi-download me-2"></i>
                    Scarica Report PDF
                  </button>
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            {!isProcessing && !results.reportId ? (
              <>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleClose}
                >
                  Annulla
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleCompleteWorkflow}
                  disabled={!selectedFile}
                >
                  <i className="bi bi-play-fill me-1"></i>
                  Avvia Workflow
                </button>
              </>
            ) : !isProcessing ? (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleClose}
              >
                Chiudi
              </button>
            ) : (
              <button
                type="button"
                className="btn btn-secondary"
                disabled
              >
                <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                Elaborazione in corso...
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default QuickWorkflowModal