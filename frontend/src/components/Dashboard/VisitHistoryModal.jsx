import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'

const VisitHistoryModal = ({ isOpen, onClose, patient }) => {
  const { data: visitHistory, isLoading } = useQuery({
    queryKey: ['patient-visits', patient?.id],
    queryFn: () => medicalWorkflowAPI.getPatientVisitHistory(patient.id),
    enabled: isOpen && !!patient?.id,
  })

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('it-IT')
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      'in_progress': { class: 'warning', text: 'In Corso', icon: 'clock' },
      'completed': { class: 'success', text: 'Completata', icon: 'check-circle' },
      'cancelled': { class: 'danger', text: 'Annullata', icon: 'x-circle' }
    }
    const config = statusConfig[status] || { class: 'secondary', text: status, icon: 'info-circle' }
    
    return (
      <span className={`badge bg-${config.class}`}>
        <i className={`bi bi-${config.icon} me-1`}></i>
        {config.text}
      </span>
    )
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

  const downloadReport = async (visitId) => {
    try {
      const response = await medicalWorkflowAPI.downloadReport(visitId)
      // Crea un link per il download
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `report_visita_${visitId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Errore durante il download:', error)
      alert('Errore durante il download del report')
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-clock-history me-2"></i>
              Cronologia Visite - {patient?.nome} {patient?.cognome}
            </h5>
            <button 
              type="button" 
              className="btn-close" 
              onClick={onClose}
            ></button>
          </div>

          <div className="modal-body">
            {/* Info Paziente */}
            <div className="card mb-4">
              <div className="card-body">
                <div className="row">
                  <div className="col-md-3">
                    <strong>Codice Fiscale:</strong><br />
                    {patient?.codice_fiscale}
                  </div>
                  <div className="col-md-3">
                    <strong>Data di Nascita:</strong><br />
                    {patient?.data_nascita}
                  </div>
                  <div className="col-md-3">
                    <strong>Sesso:</strong><br />
                    {patient?.sesso}
                  </div>
                  <div className="col-md-3">
                    <strong>Telefono:</strong><br />
                    {patient?.telefono || 'N/D'}
                  </div>
                </div>
              </div>
            </div>

            {/* Lista Visite */}
            {isLoading ? (
              <div className="text-center py-4">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Caricamento...</span>
                </div>
                <p className="mt-2">Caricamento cronologia visite...</p>
              </div>
            ) : visitHistory?.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-inbox display-1 text-muted"></i>
                <h5 className="text-muted mt-3">Nessuna visita registrata</h5>
                <p className="text-muted">Questo paziente non ha ancora visite registrate nel sistema.</p>
              </div>
            ) : (
              <div className="timeline">
                {visitHistory?.map((visit, index) => (
                  <div key={visit.id} className="card mb-3">
                    <div className="card-header d-flex justify-content-between align-items-center">
                      <div>
                        <h6 className="mb-1">
                          <i className="bi bi-calendar3 me-2"></i>
                          Visita del {formatDate(visit.data_visita)}
                        </h6>
                        <div className="d-flex gap-2 align-items-center">
                          {getStatusBadge(visit.stato)}
                          <span className={`badge bg-${getTriageColor(visit.codice_triage)}`}>
                            Triage: {visit.codice_triage?.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div>
                        {visit.stato === 'completed' && visit.report_generato && (
                          <button
                            className="btn btn-outline-primary btn-sm me-2"
                            onClick={() => downloadReport(visit.id)}
                          >
                            <i className="bi bi-download me-1"></i>
                            Report PDF
                          </button>
                        )}
                        <small className="text-muted">
                          ID: {visit.id}
                        </small>
                      </div>
                    </div>

                    <div className="card-body">
                      {/* Sintomi e Note Triage */}
                      {visit.sintomi_principali && (
                        <div className="row mb-3">
                          <div className="col-md-6">
                            <strong>Sintomi Principali:</strong>
                            <p className="mb-1">{visit.sintomi_principali}</p>
                          </div>
                          <div className="col-md-6">
                            <strong>Note Triage:</strong>
                            <p className="mb-1">{visit.note_triage || 'Nessuna nota'}</p>
                          </div>
                        </div>
                      )}

                      {/* Dati Clinici */}
                      {visit.dati_clinici && (
                        <div className="mb-3">
                          <strong>Dati Clinici Estratti:</strong>
                          <div className="row mt-2">
                            {visit.dati_clinici.diagnosi && (
                              <div className="col-md-6">
                                <small className="text-muted">Diagnosi:</small><br />
                                <span className="badge bg-info">{visit.dati_clinici.diagnosi}</span>
                              </div>
                            )}
                            {visit.dati_clinici.terapia && (
                              <div className="col-md-6">
                                <small className="text-muted">Terapia:</small><br />
                                <span className="badge bg-success">{visit.dati_clinici.terapia}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Audio Transcript */}
                      {visit.audio_transcript && (
                        <div className="mb-3">
                          <strong>Trascrizione Audio:</strong>
                          <div className="bg-light p-3 rounded mt-2" style={{ maxHeight: '150px', overflowY: 'auto' }}>
                            <small>{visit.audio_transcript}</small>
                          </div>
                        </div>
                      )}

                      {/* Metadati Visita */}
                      <div className="row text-muted small">
                        <div className="col-md-4">
                          <i className="bi bi-stopwatch me-1"></i>
                          Durata: {visit.durata_minuti ? `${visit.durata_minuti} min` : 'N/D'}
                        </div>
                        <div className="col-md-4">
                          <i className="bi bi-person-badge me-1"></i>
                          Medico: {visit.medico_responsabile || 'N/D'}
                        </div>
                        <div className="col-md-4">
                          <i className="bi bi-clock me-1"></i>
                          Ultimo aggiornamento: {formatDate(visit.updated_at)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={onClose}
            >
              Chiudi
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VisitHistoryModal