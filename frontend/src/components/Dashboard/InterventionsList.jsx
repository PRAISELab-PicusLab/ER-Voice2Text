import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'
import InterventionDetailModal from './InterventionDetailModal'

const InterventionsList = ({ onEditIntervention }) => {
  const [selectedIntervention, setSelectedIntervention] = useState(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [interventionToDelete, setInterventionToDelete] = useState(null)
  
  // Stati per i messaggi di notifica
  const [showNotificationModal, setShowNotificationModal] = useState(false)
  const [notificationMessage, setNotificationMessage] = useState('')
  const [notificationType, setNotificationType] = useState('success') // 'success' | 'error'
  
  // Stati per i filtri
  const [filters, setFilters] = useState({
    status: '',
    patientName: '',
    dateFrom: '',
    dateTo: ''
  })
  const [showFilters, setShowFilters] = useState(true)

  const { data: interventionsData, isLoading, error, refetch } = useQuery({
    queryKey: ['all-interventions'],
    queryFn: () => medicalWorkflowAPI.getAllInterventions(),
    refetchInterval: 30000,
  })

  const handleEditIntervention = (intervention) => {
    if (onEditIntervention) {
      onEditIntervention(intervention)
    }
  }

  // Funzione helper per mostrare notifiche
  const showNotification = (message, type = 'success') => {
    setNotificationMessage(message)
    setNotificationType(type)
    setShowNotificationModal(true)
  }

  const handleDeleteIntervention = (transcriptId) => {
    setInterventionToDelete(transcriptId)
    setShowDeleteModal(true)
  }

  const confirmDeleteIntervention = async () => {
    try {
      await medicalWorkflowAPI.deleteIntervention(interventionToDelete)
      // Aggiorna la lista dopo l'eliminazione
      refetch()
      setShowDeleteModal(false)
      setInterventionToDelete(null)
      showNotification('Intervento eliminato con successo', 'success')
    } catch (error) {
      console.error('Errore eliminazione intervento:', error)
      setShowDeleteModal(false)
      setInterventionToDelete(null)
      showNotification('Errore durante l\'eliminazione dell\'intervento', 'error')
    }
  }

  // Funzione per filtrare gli interventi
  const getFilteredInterventions = () => {
    if (!interventionsData?.interventions) return []
    
    return interventionsData.interventions.filter(intervention => {
      // Filtro per stato
      if (filters.status && intervention.status !== filters.status) {
        return false
      }
      
      // Filtro per nome paziente
      if (filters.patientName && !intervention.patient_name.toLowerCase().includes(filters.patientName.toLowerCase())) {
        return false
      }
      
      // Filtro per data (from)
      if (filters.dateFrom) {
        const interventionDate = new Date(intervention.created_at)
        const fromDate = new Date(filters.dateFrom)
        if (interventionDate < fromDate) {
          return false
        }
      }
      
      // Filtro per data (to)
      if (filters.dateTo) {
        const interventionDate = new Date(intervention.created_at)
        const toDate = new Date(filters.dateTo)
        toDate.setHours(23, 59, 59, 999) // Include tutto il giorno
        if (interventionDate > toDate) {
          return false
        }
      }
      
      return true
    })
  }

  // Funzione per resettare i filtri
  const resetFilters = () => {
    setFilters({
      status: '',
      patientName: '',
      dateFrom: '',
      dateTo: ''
    })
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

  const handleViewDetails = (intervention) => {
    setSelectedIntervention(intervention)
    setShowDetailModal(true)
  }

  const handleDownloadPDF = async (transcriptId) => {
    try {
      // Usa fetch direttamente per accedere agli headers
      const response = await fetch(`/api/reports/${transcriptId}/download/`)
      
      if (!response.ok) {
        throw new Error('Errore nel download del PDF')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      
      // Estrai il nome del file dal header Content-Disposition se disponibile
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `report_${transcriptId}.pdf`
      
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
      showNotification('Errore durante il download del PDF', 'error')
    }
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="card-body text-center p-5">
          <div className="spinner-border text-primary mb-3" role="status">
            <span className="visually-hidden">Caricamento...</span>
          </div>
          <h5 className="text-muted">Caricamento interventi...</h5>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="alert alert-danger">
            <h5 className="alert-heading">Errore</h5>
            <p className="mb-0">Impossibile caricare la lista degli interventi. {error.message}</p>
            <hr />
            <button className="btn btn-outline-danger" onClick={() => refetch()}>
              <i className="bi bi-arrow-clockwise me-2"></i>
              Riprova
            </button>
          </div>
        </div>
      </div>
    )
  }

  const interventions = getFilteredInterventions()

  return (
    <>
      <div className="card">
        <div className="card-header bg-light">
          <div className="d-flex justify-content-between align-items-center">
            <h4 className="card-title mb-0">
              <i className="bi bi-list-ul me-2"></i>
              Tutti gli Interventi
            </h4>
            <div className="d-flex gap-2 align-items-center">
              <span className="badge bg-primary fs-6">
                {interventions.length} interventi
              </span>
              <button 
                className="btn btn-outline-primary btn-sm"
                onClick={() => refetch()}
                title="Aggiorna lista interventi"
              >
                <i className="bi bi-arrow-clockwise me-1"></i>
                Aggiorna
              </button>
            </div>
          </div>
          
          {/* Header filtri con toggle */}
          <div className="d-flex justify-content-between align-items-center mt-3">
            <h6 className="mb-0 text-muted">
              <i className="bi bi-funnel me-2"></i>
              Filtri di Ricerca
              {!showFilters && <small className="text-warning ms-2">(nascosti)</small>}
            </h6>
            <button
              className="btn btn-link btn-sm text-muted text-decoration-none p-0"
              onClick={() => setShowFilters(!showFilters)}
              title={showFilters ? "Nascondi filtri" : "Mostra filtri"}
            >
              <i className={`bi ${showFilters ? 'bi-chevron-up' : 'bi-chevron-down'}`}></i>
            </button>
          </div>
        </div>
        
        {/* Sezione filtri */}
        <div 
          className="card-body border-bottom border-light"
          style={{
            maxHeight: showFilters ? '500px' : '0px',
            overflow: 'hidden',
            opacity: showFilters ? 1 : 0,
            transform: showFilters ? 'translateY(0)' : 'translateY(-10px)',
            transition: 'max-height 0.4s ease-in-out, opacity 0.3s ease-in-out 0.1s, transform 0.3s ease-in-out 0.1s, padding 0.3s ease-in-out',
            paddingTop: showFilters ? '1rem' : '0',
            paddingBottom: showFilters ? '1rem' : '0'
          }}
        >
          <div className="row g-3">
            <div className="col-md-3">
              <label className="form-label small fw-bold">Stato Intervento</label>
              <select 
                className="form-select"
                value={filters.status}
                onChange={(e) => setFilters({...filters, status: e.target.value})}
              >
                <option value="">Tutti gli stati</option>
                <option value="In Attesa">In Attesa</option>
                <option value="Completato">Completato</option>
              </select>
            </div>
            
            <div className="col-md-3">
              <label className="form-label small fw-bold">Nome Paziente</label>
              <input 
                type="text"
                className="form-control"
                placeholder="Cerca per nome..."
                value={filters.patientName}
                onChange={(e) => setFilters({...filters, patientName: e.target.value})}
              />
            </div>
            
            <div className="col-md-2">
              <label className="form-label small fw-bold">Data Da</label>
              <input 
                type="date"
                className="form-control"
                value={filters.dateFrom}
                onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
              />
            </div>
            
            <div className="col-md-2">
              <label className="form-label small fw-bold">Data A</label>
              <input 
                type="date"
                className="form-control"
                value={filters.dateTo}
                onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
              />
            </div>
            
            <div className="col-md-2" style={{ display: 'flex', alignItems: 'end', padding: '10px' }}>
              <button 
                className="btn btn-danger"
                onClick={resetFilters}
                title="Reset filtri"
              >
                <i className="bi bi-x-circle me-1"></i>
                Reset
              </button>
            </div>
          </div>
        </div>
        
        <div className="card-body p-0">
          {interventions.length === 0 ? (
            <div className="text-center p-5">
              <i className="bi bi-inbox text-muted" style={{ fontSize: '3rem' }}></i>
              <h5 className="text-muted mt-3">Nessun intervento trovato</h5>
              <p className="text-muted">Non ci sono ancora interventi registrati nel sistema.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Data/Ora</th>
                    <th>Paziente</th>
                    <th>Triage</th>
                    <th>Sintomi</th>
                    <th>Stato</th>
                    <th>Dati Clinici</th>
                    <th className="text-end">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {interventions.map((intervention) => (
                    <tr key={intervention.transcript_id}>
                      <td>
                        <div className="fw-bold">{intervention.visit_date}</div>
                        <small className="text-muted">{intervention.visit_time}</small>
                      </td>
                      <td>
                        <div className="fw-bold">{intervention.patient_name}</div>
                      </td>
                      <td>
                        {intervention.triage_code ? (
                          <span className={`badge bg-${getTriageColor(intervention.triage_code)}`}>
                            {getTriageIcon(intervention.triage_code)} {intervention.triage_code.toUpperCase()}
                          </span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td>
                        <div 
                          className="text-truncate" 
                          style={{ maxWidth: '200px' }}
                          title={intervention.symptoms}
                        >
                          {intervention.symptoms || '-'}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${
                          intervention.status === 'Completato' ? 'bg-success' : 'bg-warning'
                        }`}>
                          {intervention.status}
                        </span>
                      </td>
                      <td>
                        {intervention.has_clinical_data ? (
                          <span className="badge bg-success">
                            <i className="bi bi-check-circle me-1"></i>
                            Disponibili
                          </span>
                        ) : (
                          <span className="badge bg-warning">
                            <i className="bi bi-exclamation-triangle me-1"></i>
                            Mancanti
                          </span>
                        )}
                      </td>
                      <td className="text-end">
                        <div className="btn-group" role="group">
                          <button
                            className="btn btn-outline-primary btn-sm"
                            onClick={() => handleViewDetails(intervention)}
                            title="Visualizza dettagli"
                          >
                            <i className="bi bi-eye"></i>
                          </button>
                          <button
                            className="btn btn-outline-success btn-sm"
                            onClick={() => handleDownloadPDF(intervention.transcript_id)}
                            title="Scarica PDF"
                            disabled={!intervention.has_clinical_data}
                          >
                            <i className="bi bi-download"></i>
                          </button>
                          <button
                            className="btn btn-outline-danger btn-sm"
                            onClick={() => handleDeleteIntervention(intervention.transcript_id)}
                            title="Elimina intervento"
                          >
                            <i className="bi bi-trash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal dettagli intervento */}
      {selectedIntervention && (
        <InterventionDetailModal
          intervention={selectedIntervention}
          show={showDetailModal}
          onHide={() => {
            setShowDetailModal(false)
            setSelectedIntervention(null)
          }}
          onEdit={handleEditIntervention}
        />
      )}

      {/* Modal conferma eliminazione */}
      {showDeleteModal && (
        <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-exclamation-triangle-fill text-warning me-2"></i>
                  Conferma Eliminazione
                </h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => {
                    setShowDeleteModal(false)
                    setInterventionToDelete(null)
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <p className="mb-3">
                  Sei sicuro di voler eliminare questo intervento?
                </p>
                <div className="alert alert-danger">
                  <i className="bi bi-warning me-2"></i>
                  <strong>Attenzione:</strong> Questa azione non può essere annullata. 
                  Tutti i dati associati a questo intervento verranno eliminati definitivamente.
                </div>
              </div>
              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowDeleteModal(false)
                    setInterventionToDelete(null)
                  }}
                >
                  Annulla
                </button>
                <button 
                  type="button" 
                  className="btn btn-danger"
                  onClick={confirmDeleteIntervention}
                >
                  <i className="bi bi-trash me-1"></i>
                  Elimina Definitivamente
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal notifiche */}
      {showNotificationModal && (
        <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className={`modal-header ${notificationType === 'success' ? 'bg-success' : 'bg-danger'} text-white`}>
                <h5 className="modal-title">
                  <i className={`bi ${notificationType === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill'} me-2`}></i>
                  {notificationType === 'success' ? 'Operazione Completata' : 'Errore'}
                </h5>
                <button 
                  type="button" 
                  className="btn-close btn-close-white" 
                  onClick={() => setShowNotificationModal(false)}
                ></button>
              </div>
              <div className="modal-body">
                <div className={`alert ${notificationType === 'success' ? 'alert-success' : 'alert-danger'} mb-0`}>
                  <i className={`bi ${notificationType === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'} me-2`}></i>
                  {notificationMessage}
                </div>
              </div>
              <div className="modal-footer">
                <button 
                  type="button" 
                  className={`btn ${notificationType === 'success' ? 'btn-success' : 'btn-danger'}`}
                  onClick={() => setShowNotificationModal(false)}
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default InterventionsList