import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'

const InterventionDetailModal = ({ intervention, show, onHide, onEdit }) => {
  
  const { data: details, isLoading } = useQuery({
    queryKey: ['intervention-details', intervention?.transcript_id],
    queryFn: () => medicalWorkflowAPI.getInterventionDetails(intervention.transcript_id),
    enabled: !!intervention && show
  })

  const handleDownloadPDF = async () => {
    try {
      // Usa fetch direttamente per accedere agli headers
      const response = await fetch(`/api/reports/${intervention.transcript_id}/download/`)
      
      if (!response.ok) {
        throw new Error('Errore nel download del PDF')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      // Estrai il nome del file dal header Content-Disposition se disponibile
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `Report_${intervention.patient_name}_${intervention.visit_date}.pdf`
      
      if (contentDisposition && contentDisposition.includes('filename=')) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Errore download PDF:', error)
      alert('Errore durante il download del PDF')
    }
  }

  const handleEditIntervention = () => {
    if (onEdit) {
      onEdit(intervention)
    }
    onHide()
  }

  const getTriageColor = (code) => {
    // Mapping per codici triage in italiano e inglese
    const colors = {
      // Italiano
      'bianco': 'secondary',
      'verde': 'success', 
      'giallo': 'warning',
      'rosso': 'danger',
      'nero': 'dark',
      // Inglese (legacy)
      'white': 'secondary',
      'green': 'success',
      'yellow': 'warning', 
      'red': 'danger',
      'black': 'dark'
    }
    return colors[code?.toLowerCase()] || 'secondary'
  }

  const getTriageIcon = (code) => {
    // Mapping per icone con supporto italiano e inglese
    const icons = {
      // Italiano
      'bianco': '⚪',
      'verde': '🟢',
      'giallo': '🟡', 
      'rosso': '🔴',
      'nero': '⚫',
      // Inglese (legacy)
      'white': '⚪',
      'green': '🟢',
      'yellow': '🟡',
      'red': '🔴',
      'black': '⚫'
    }
    return icons[code?.toLowerCase()] || '⚪'
  }

  const getTriageDisplayName = (code) => {
    // Mapping per nomi visualizzati sempre in italiano
    const displayNames = {
      // Italiano (mantieni)
      'bianco': 'BIANCO',
      'verde': 'VERDE',
      'giallo': 'GIALLO',
      'rosso': 'ROSSO', 
      'nero': 'NERO',
      // Inglese (converti in italiano)
      'white': 'BIANCO',
      'green': 'VERDE',
      'yellow': 'GIALLO',
      'red': 'ROSSO',
      'black': 'NERO'
    }
    return displayNames[code?.toLowerCase()] || code?.toUpperCase() || '-'
  }

  if (!show || !intervention) return null

  return (
    <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-clipboard-data me-2"></i>
              Dettagli Intervento
            </h5>
            <button type="button" className="btn-close" onClick={onHide}></button>
          </div>
          
          <div className="modal-body" style={{ padding: '20px' }}>
            {isLoading ? (
              <div className="text-center p-4">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Caricamento...</span>
                </div>
                <p className="mt-2">Caricamento dettagli...</p>
              </div>
            ) : (
              <div className="container-fluid">
                {/* Informazioni di base */}
                <div className="row mb-4">
                  <div className="col-12">
                    <div className="card border-primary">
                      <div className="card-header bg-primary text-white">
                        <h6 className="mb-0">
                          <i className="bi bi-info-circle me-2"></i>
                          Informazioni Intervento
                        </h6>
                      </div>
                      <div className="card-body">
                        <div className="row">
                          <div className="col-md-6">
                            <p><strong>Data/Ora:</strong> {intervention.visit_date} alle {intervention.visit_time}</p>
                            <p><strong>Paziente:</strong> {intervention.patient_name}</p>
                          </div>
                          <div className="col-md-6">
                            <p><strong>Stato:</strong> 
                              <span className={`badge ms-2 ${
                                intervention.status === 'In Attesa' ? 'bg-warning' : 
                                intervention.status === 'Completato' ? 'bg-success' : 
                                'bg-warning'
                              }`}>
                                {intervention.status}
                              </span>
                            </p>
                            <p><strong>Codice Triage:</strong> {
                              intervention.triage_code ? (
                                <span className={`badge ms-2 bg-${getTriageColor(intervention.triage_code)}`}>
                                  {getTriageIcon(intervention.triage_code)} {getTriageDisplayName(intervention.triage_code)}
                                </span>
                              ) : '-'
                            }</p>
                            <p><strong>Dati Clinici:</strong> {
                              intervention.has_clinical_data ? (
                                <span className="badge bg-success ms-2">
                                  <i className="bi bi-check-circle me-1"></i>
                                  Disponibili
                                </span>
                              ) : (
                                <span className="badge bg-warning ms-2">
                                  <i className="bi bi-exclamation-triangle me-1"></i>
                                  Non disponibili
                                </span>
                              )
                            }</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Trascrizione */}
                <div className="col-12 mb-4">
                  <div className="card">
                    <div className="card-header bg-info text-white">
                      <h6 className="mb-0">
                        <i className="bi bi-mic me-2"></i>
                        Trascrizione Audio
                      </h6>
                    </div>
                    <div className="card-body">
                      {details?.transcript_text ? (
                        <div className="transcript-container" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                          <p className="mb-0">{details.transcript_text}</p>
                        </div>
                      ) : (
                        <p className="text-muted mb-0">Trascrizione non disponibile</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Dati Clinici */}
                {details?.clinical_data && (
                  <div className="col-12 mb-4">
                    <div className="card">
                      <div className="card-header bg-success text-white">
                        <h6 className="mb-0">
                          <i className="bi bi-clipboard-heart me-2"></i>
                          Dati Clinici Estratti
                        </h6>
                      </div>
                      <div className="card-body">
                        <div className="row">
                          {details.clinical_data.patient_info && (
                            <div className="col-md-6 mb-3">
                              <h6>Informazioni Paziente</h6>
                              <ul className="list-unstyled">
                                {details.clinical_data.patient_info.first_name && (
                                  <li><strong>Nome:</strong> {details.clinical_data.patient_info.first_name}</li>
                                )}
                                {details.clinical_data.patient_info.last_name && (
                                  <li><strong>Cognome:</strong> {details.clinical_data.patient_info.last_name}</li>
                                )}
                                {details.clinical_data.patient_info.age && (
                                  <li><strong>Età:</strong> {details.clinical_data.patient_info.age}</li>
                                )}
                                {details.clinical_data.patient_info.gender && (
                                  <li><strong>Sesso:</strong> {details.clinical_data.patient_info.gender}</li>
                                )}
                                {details.clinical_data.patient_info.birth_date && (
                                  <li><strong>Data Nascita:</strong> {details.clinical_data.patient_info.birth_date}</li>
                                )}
                                {details.clinical_data.patient_info.phone && (
                                  <li><strong>Telefono:</strong> {details.clinical_data.patient_info.phone}</li>
                                )}
                                {details.clinical_data.patient_info.residence_city && (
                                  <li><strong>Città:</strong> {details.clinical_data.patient_info.residence_city}</li>
                                )}
                              </ul>
                            </div>
                          )}
                          
                          {details.clinical_data.vital_signs && (
                            <div className="col-md-6 mb-3">
                              <h6>Parametri Vitali</h6>
                              <ul className="list-unstyled">
                                {details.clinical_data.vital_signs.blood_pressure && (
                                  <li><strong>Pressione:</strong> {details.clinical_data.vital_signs.blood_pressure}</li>
                                )}
                                {details.clinical_data.vital_signs.heart_rate && (
                                  <li><strong>Freq. Cardiaca:</strong> {details.clinical_data.vital_signs.heart_rate}</li>
                                )}
                                {details.clinical_data.vital_signs.temperature && (
                                  <li><strong>Temperatura:</strong> {details.clinical_data.vital_signs.temperature}</li>
                                )}
                                {details.clinical_data.vital_signs.oxygen_saturation && (
                                  <li><strong>Saturazione O2:</strong> {details.clinical_data.vital_signs.oxygen_saturation}</li>
                                )}
                              </ul>
                            </div>
                          )}
                          
                          {details.clinical_data.clinical_assessment && (
                            <div className="col-12 mb-3">
                              <h6>Valutazione Clinica</h6>
                              <div className="row">
                                <div className="col-md-6">
                                  {details.clinical_data.clinical_assessment.symptoms && (
                                    <p><strong>Sintomi:</strong> {details.clinical_data.clinical_assessment.symptoms}</p>
                                  )}
                                  {details.clinical_data.clinical_assessment.diagnosis && (
                                    <p><strong>Diagnosi:</strong> {details.clinical_data.clinical_assessment.diagnosis}</p>
                                  )}
                                </div>
                                <div className="col-md-6">
                                  {details.clinical_data.clinical_assessment.treatment && (
                                    <p><strong>Trattamento:</strong> {details.clinical_data.clinical_assessment.treatment}</p>
                                  )}
                                  {details.clinical_data.clinical_assessment.medical_notes && (
                                    <p><strong>Note:</strong> {details.clinical_data.clinical_assessment.medical_notes}</p>
                                  )}
                                  {details.clinical_data.clinical_assessment.access_mode && (
                                    <p><strong>Modalità Accesso:</strong> {details.clinical_data.clinical_assessment.access_mode}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Pulsanti azione */}
                <div className="row mt-4">
                  <div className="col-12">
                    <div className="d-flex gap-2 justify-content-end">
                      {onEdit && (
                        <button 
                          className="btn btn-warning"
                          onClick={handleEditIntervention}
                        >
                          <i className="bi bi-pencil me-1"></i>
                          Modifica Intervento
                        </button>
                      )}
                      
                      <button 
                        className="btn btn-primary"
                        onClick={handleDownloadPDF}
                      >
                        <i className="bi bi-download me-1"></i>
                        Scarica PDF
                      </button>
                      
                      <button 
                        className="btn btn-secondary"
                        onClick={onHide}
                      >
                        Chiudi
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InterventionDetailModal