/**
 * Modal per visualizzare dettagli dell'encounter con informazioni workflow
 */

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { encountersAPI, medicalWorkflowAPI } from '@services/api'

const EncounterDetailModal = ({ isOpen, onClose, encounterId }) => {
  // Query per dettagli encounter
  const { data: encounter, isLoading: encounterLoading } = useQuery({
    queryKey: ['encounter', encounterId],
    queryFn: () => encountersAPI.getById(encounterId),
    enabled: !!encounterId && isOpen,
  })

  // Query per stato workflow
  const { data: workflowStatus, isLoading: workflowLoading } = useQuery({
    queryKey: ['workflow-status', encounterId],
    queryFn: () => medicalWorkflowAPI.getWorkflowStatus(encounterId),
    enabled: !!encounterId && isOpen,
    retry: false,
  })

  if (!isOpen) return null

  const handleDownloadReport = async (reportId) => {
    try {
      await medicalWorkflowAPI.downloadReport(reportId)
    } catch (error) {
      console.error('Errore durante il download del report:', error)
    }
  }

  return (
    <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-person-badge me-2"></i>
              Dettagli Episodio di Cura
            </h5>
            <button
              type="button"
              className="btn-close"
              onClick={onClose}
            ></button>
          </div>

          <div className="modal-body">
            {encounterLoading ? (
              <div className="text-center py-4">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Caricamento...</span>
                </div>
              </div>
            ) : encounter ? (
              <div className="row">
                {/* Informazioni Paziente */}
                <div className="col-md-6">
                  <div className="card mb-3">
                    <div className="card-header">
                      <h6 className="card-title mb-0">
                        <i className="bi bi-person me-2"></i>
                        Informazioni Paziente
                      </h6>
                    </div>
                    <div className="card-body">
                      <p><strong>Nome:</strong> {encounter.patient_name}</p>
                      <p><strong>Data di Nascita:</strong> {
                        encounter.patient_date_of_birth 
                          ? new Date(encounter.patient_date_of_birth).toLocaleDateString('it-IT')
                          : 'N/A'
                      }</p>
                      <p><strong>Codice Fiscale:</strong> {encounter.patient_fiscal_code || 'N/A'}</p>
                      <p><strong>Sesso:</strong> {encounter.patient_gender === 'M' ? 'Maschio' : 'Femmina'}</p>
                      <p><strong>Telefono:</strong> {encounter.patient_phone || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                {/* Informazioni Encounter */}
                <div className="col-md-6">
                  <div className="card mb-3">
                    <div className="card-header">
                      <h6 className="card-title mb-0">
                        <i className="bi bi-hospital me-2"></i>
                        Informazioni Episodio
                      </h6>
                    </div>
                    <div className="card-body">
                      <p><strong>ID Episodio:</strong> {encounter.encounter_id}</p>
                      <p><strong>Motivo dell'accesso:</strong> {encounter.chief_complaint}</p>
                      <p><strong>Priorità Triage:</strong> 
                        <span className={`badge bg-${getTriageColor(encounter.triage_priority)} ms-2`}>
                          {encounter.triage_priority.toUpperCase()}
                        </span>
                      </p>
                      <p><strong>Orario ammissione:</strong> {
                        new Date(encounter.admission_time).toLocaleString('it-IT')
                      }</p>
                      <p><strong>Stato:</strong> 
                        <span className={`badge bg-${encounter.status === 'in_progress' ? 'warning' : 'success'} ms-2`}>
                          {encounter.status === 'in_progress' ? 'In Corso' : 'Completato'}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>

                {/* Stato Workflow */}
                <div className="col-12">
                  <div className="card">
                    <div className="card-header">
                      <h6 className="card-title mb-0">
                        <i className="bi bi-diagram-3 me-2"></i>
                        Stato Workflow Medico
                      </h6>
                    </div>
                    <div className="card-body">
                      {workflowLoading ? (
                        <div className="text-center py-2">
                          <div className="spinner-border spinner-border-sm text-secondary" role="status"></div>
                        </div>
                      ) : workflowStatus ? (
                        <div className="row">
                          {/* Trascrizioni */}
                          <div className="col-md-4">
                            <h6 className="text-primary">
                              <i className="bi bi-mic me-1"></i>
                              Trascrizioni ({workflowStatus.transcripts.length})
                            </h6>
                            {workflowStatus.transcripts.length > 0 ? (
                              workflowStatus.transcripts.map((transcript, index) => (
                                <div key={transcript.id} className="mb-2">
                                  <div className="d-flex justify-content-between align-items-center">
                                    <small>Audio {index + 1}</small>
                                    <span className={`badge bg-${
                                      transcript.status === 'completed' ? 'success' : 
                                      transcript.status === 'processing' ? 'warning' : 'secondary'
                                    }`}>
                                      {transcript.status === 'completed' ? 'Completata' : 
                                       transcript.status === 'processing' ? 'In Corso' : 'In Attesa'}
                                    </span>
                                  </div>
                                  {transcript.confidence_score && (
                                    <div className="progress mt-1" style={{height: '4px'}}>
                                      <div 
                                        className="progress-bar bg-info" 
                                        style={{width: `${transcript.confidence_score * 100}%`}}
                                      ></div>
                                    </div>
                                  )}
                                </div>
                              ))
                            ) : (
                              <p className="text-muted small">Nessuna trascrizione</p>
                            )}
                          </div>

                          {/* Dati Clinici */}
                          <div className="col-md-4">
                            <h6 className="text-warning">
                              <i className="bi bi-clipboard-data me-1"></i>
                              Dati Clinici ({workflowStatus.clinical_data.length})
                            </h6>
                            {workflowStatus.clinical_data.length > 0 ? (
                              workflowStatus.clinical_data.map((data, index) => (
                                <div key={data.id} className="mb-2">
                                  <div className="d-flex justify-content-between align-items-center">
                                    <small>Estrazione {index + 1}</small>
                                    <span className={`badge bg-${
                                      data.status === 'completed' ? 'success' : 
                                      data.status === 'processing' ? 'warning' : 'secondary'
                                    }`}>
                                      {data.status === 'completed' ? 'Completata' : 
                                       data.status === 'processing' ? 'In Corso' : 'In Attesa'}
                                    </span>
                                  </div>
                                </div>
                              ))
                            ) : (
                              <p className="text-muted small">Nessun dato estratto</p>
                            )}
                          </div>

                          {/* Report */}
                          <div className="col-md-4">
                            <h6 className="text-success">
                              <i className="bi bi-file-earmark-text me-1"></i>
                              Report ({workflowStatus.reports.length})
                            </h6>
                            {workflowStatus.reports.length > 0 ? (
                              workflowStatus.reports.map((report, index) => (
                                <div key={report.id} className="mb-2">
                                  <div className="d-flex justify-content-between align-items-center">
                                    <small>Report {index + 1}</small>
                                    <div>
                                      <span className={`badge bg-${
                                        report.status === 'completed' ? 'success' : 
                                        report.status === 'processing' ? 'warning' : 'secondary'
                                      } me-1`}>
                                        {report.status === 'completed' ? 'Completato' : 
                                         report.status === 'processing' ? 'In Corso' : 'In Attesa'}
                                      </span>
                                      {report.status === 'completed' && (
                                        <button
                                          className="btn btn-outline-primary btn-sm"
                                          onClick={() => handleDownloadReport(report.id)}
                                          title="Scarica Report"
                                        >
                                          <i className="bi bi-download"></i>
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))
                            ) : (
                              <p className="text-muted small">Nessun report generato</p>
                            )}
                          </div>
                        </div>
                      ) : (
                        <p className="text-muted">Nessun workflow avviato per questo episodio</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="alert alert-danger">
                Errore durante il caricamento dei dettagli dell'episodio
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

// Utility function (da spostare in un file utils se necessario)
const getTriageColor = (priority) => {
  const colors = {
    white: 'light',
    green: 'success',
    yellow: 'warning', 
    red: 'danger',
    black: 'dark'
  }
  return colors[priority] || 'secondary'
}

export default EncounterDetailModal