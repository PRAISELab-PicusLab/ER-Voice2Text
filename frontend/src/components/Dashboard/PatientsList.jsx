/**import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'
import PatientModal from './PatientModal'
import VisitHistoryModal from './VisitHistoryModal'
import AudioRecordingModal from './AudioRecordingModal' Componente per gestione lista pazienti con nuove funzionalità
 */

import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '@services/api'
import PatientModal from './PatientModal'
import VisitHistoryModal from './VisitHistoryModal'
import AudioRecordingModal from './AudioRecordingModal'

const PatientsList = () => {
  const [filter, setFilter] = useState('all') // all, waiting, completed
  const [selectedPatient, setSelectedPatient] = useState(null)
  const [showPatientModal, setShowPatientModal] = useState(false)
  const [showVisitHistory, setShowVisitHistory] = useState(false)
  const [showAudioRecording, setShowAudioRecording] = useState(false)
  const [showNewVisitModal, setShowNewVisitModal] = useState(false)
  
  const queryClient = useQueryClient()

  // Query per lista pazienti
  const { data: patients, isLoading } = useQuery({
    queryKey: ['patients-list', filter],
    queryFn: () => medicalWorkflowAPI.getPatientsList(filter),
    refetchInterval: 30000,
  })

  const handlePatientAction = (patient, action) => {
    setSelectedPatient(patient)
    
    switch (action) {
      case 'new-emergency':
        setShowAudioRecording(true)
        break
      case 'edit-data':
        setShowPatientModal(true)
        break
      case 'view-history':
        setShowVisitHistory(true)
        break
      default:
        break
    }
  }

  const handleNewEmergency = () => {
    setSelectedPatient(null)
    setShowNewVisitModal(true)
  }

  const closeModals = () => {
    setSelectedPatient(null)
    setShowPatientModal(false)
    setShowVisitHistory(false)
    setShowAudioRecording(false)
    setShowNewVisitModal(false)
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      'in_progress': { class: 'bg-warning', text: 'In Corso' },
      'completed': { class: 'bg-success', text: 'Completato' }
    }
    
    const config = statusConfig[status] || { class: 'bg-secondary', text: status }
    return (
      <span className={`badge ${config.class}`}>
        {config.text}
      </span>
    )
  }

  const getTriageColor = (code) => {
    const colors = {
      white: 'light',
      green: 'success',
      yellow: 'warning',
      red: 'danger',
      black: 'dark'
    }
    return colors[code] || 'secondary'
  }

  return (
    <div className="card">
      {/* Mobile-optimized header */}
      <div className="card-header">
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-start align-items-md-center gap-2">
          <h5 className="card-title mb-0">
            <i className="bi bi-people me-2"></i>
            Pazienti
          </h5>
          
          {/* Mobile-first filter buttons */}
          <div className="d-flex flex-wrap gap-1">
            <button 
              className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-outline-primary'}`}
              onClick={() => setFilter('all')}
            >
              Tutti ({patients?.total_count || 0})
            </button>
            <button 
              className={`btn btn-sm ${filter === 'waiting' ? 'btn-warning' : 'btn-outline-warning'}`}
              onClick={() => setFilter('waiting')}
            >
              <i className="bi bi-clock me-1"></i>
              Attesa
            </button>
            <button 
              className={`btn btn-sm ${filter === 'completed' ? 'btn-success' : 'btn-outline-success'}`}
              onClick={() => setFilter('completed')}
            >
              <i className="bi bi-check-circle me-1"></i>
              Completati
            </button>
          </div>
        </div>
      </div>
      
      <div className="card-body">
        {isLoading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Caricamento...</span>
            </div>
          </div>
        ) : patients?.patients?.length > 0 ? (
          <>
            {/* Desktop table view */}
            <div className="table-responsive d-none d-md-block">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Paziente</th>
                    <th>Età</th>
                    <th>Contatti</th>
                    <th>Ultima Emergenza</th>
                    <th>Stato</th>
                    <th>Emergenze Totali</th>
                    <th>Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.patients.map((patient) => (
                    <tr key={patient.patient_id}>
                      <td>
                        <div>
                          <strong>{patient.first_name} {patient.last_name}</strong>
                          {patient.fiscal_code && (
                            <div><small className="text-muted">CF: {patient.fiscal_code}</small></div>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="text-muted">{patient.age ? `${patient.age} anni` : '-'}</span>
                        <div><small className="text-muted">{patient.gender === 'M' ? 'M' : patient.gender === 'F' ? 'F' : patient.gender}</small></div>
                      </td>
                      <td>
                        <div>
                          {patient.phone && <div><i className="bi bi-telephone me-1"></i><small>{patient.phone}</small></div>}
                          {patient.residence_city && <div><i className="bi bi-geo-alt me-1"></i><small>{patient.residence_city}</small></div>}
                        </div>
                      </td>
                      <td>
                        <small className="text-muted">
                          {patient.last_visit_date ? new Date(patient.last_visit_date).toLocaleDateString('it-IT') : 'Mai'}
                        </small>
                        {patient.last_triage_code && (
                          <div><span className={`badge bg-${getTriageColor(patient.last_triage_code)} badge-sm`}>{patient.last_triage_code.toUpperCase()}</span></div>
                        )}
                      </td>
                      <td>{getStatusBadge(patient.status)}</td>
                      <td><span className="badge bg-info">{patient.total_visits || 0}</span></td>
                      <td>
                        <div className="btn-group btn-group-sm">
                          <button className="btn btn-outline-danger" title="Nuova emergenza" onClick={() => handlePatientAction(patient, 'new-emergency')}>
                            <i className="bi bi-mic"></i>
                          </button>
                          <button className="btn btn-outline-secondary" title="Modifica dati" onClick={() => handlePatientAction(patient, 'edit-data')}>
                            <i className="bi bi-pencil"></i>
                          </button>
                          <button className="btn btn-outline-info" title="Cronologia" onClick={() => handlePatientAction(patient, 'view-history')}>
                            <i className="bi bi-clock-history"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile card view */}
            <div className="d-md-none">
              {patients.patients.map((patient) => (
                <div key={`mobile-${patient.patient_id}`} className="card mb-2 shadow-sm">
                  <div className="card-body p-3">
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="flex-grow-1">
                        <h6 className="card-title mb-1 fw-bold">{patient.first_name} {patient.last_name}</h6>
                        <p className="text-muted small mb-1">{patient.age ? `${patient.age} anni` : '-'} • {patient.residence_city || 'N/D'}</p>
                        <p className="text-muted small mb-0">
                          Ultima emergenza: {patient.last_visit_date ? new Date(patient.last_visit_date).toLocaleDateString('it-IT') : 'Mai'}
                        </p>
                        {patient.last_triage_code && (
                          <span className={`badge bg-${getTriageColor(patient.last_triage_code)} mt-1`}>
                            {patient.last_triage_code.toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div className="d-flex flex-column gap-1">
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={() => handlePatientAction(patient, 'new-emergency')}
                          style={{ minWidth: '80px' }}
                        >
                          <i className="bi bi-mic me-1"></i>
                          Emergenza
                        </button>
                        <button 
                          className="btn btn-outline-secondary btn-sm"
                          onClick={() => handlePatientAction(patient, 'edit-data')}
                          style={{ minWidth: '80px' }}
                        >
                          <i className="bi bi-pencil me-1"></i>
                          Modifica
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-4">
            <i className="bi bi-people display-1 text-muted"></i>
            <h5 className="text-muted mt-3">Nessun paziente trovato</h5>
            <p className="text-muted">
              {filter === 'all' ? 
                'Non ci sono pazienti nel sistema.' :
                `Non ci sono pazienti con stato "${filter}".`
              }
            </p>
            <button 
              className="btn btn-danger btn-lg"
              onClick={handleNewEmergency}
            >
              <i className="bi bi-plus-lg me-2"></i>
              Registra Prima Emergenza
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      {showPatientModal && selectedPatient && (
        <PatientModal 
          patient={selectedPatient}
          isOpen={showPatientModal}
          onClose={closeModals}
          onSaved={() => {
            queryClient.invalidateQueries(['patients-list'])
            closeModals()
          }}
        />
      )}

      {showVisitHistory && selectedPatient && (
        <VisitHistoryModal 
          patient={selectedPatient}
          isOpen={showVisitHistory}
          onClose={closeModals}
        />
      )}

      {(showAudioRecording || showNewVisitModal) && (
        <AudioRecordingModal 
          patient={selectedPatient}
          isOpen={showAudioRecording || showNewVisitModal}
          onClose={closeModals}
          onCompleted={() => {
            queryClient.invalidateQueries(['patients-list'])
            queryClient.invalidateQueries(['dashboard-analytics'])
            closeModals()
          }}
        />
      )}
    </div>
  )
}

export default PatientsList