/**
 * Modal per creazione nuovo episodio di cura
 */

import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { encountersAPI, patientsAPI } from '@services/api'

const NewEncounterModal = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient()
  
  const [formData, setFormData] = useState({
    // Dati paziente
    patient_first_name: '',
    patient_last_name: '',
    patient_date_of_birth: '',
    patient_fiscal_code: '',
    patient_gender: 'M',
    patient_phone: '',
    
    // Dati encounter
    chief_complaint: '',
    triage_priority: 'green',
    admission_time: new Date().toISOString().slice(0, 16), // YYYY-MM-DDTHH:mm
  })

  const [errors, setErrors] = useState({})

  // Mutation per creare nuovo encounter
  const createEncounterMutation = useMutation({
    mutationFn: (data) => encountersAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['encounters'])
      onClose()
      setFormData({
        patient_first_name: '',
        patient_last_name: '',
        patient_date_of_birth: '',
        patient_fiscal_code: '',
        patient_gender: 'M',
        patient_phone: '',
        chief_complaint: '',
        triage_priority: 'green',
        admission_time: new Date().toISOString().slice(0, 16),
      })
      setErrors({})
    },
    onError: (error) => {
      setErrors(error.response?.data || { general: 'Errore durante la creazione' })
    }
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    
    // Rimuovi errore del campo se presente
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }))
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    createEncounterMutation.mutate(formData)
  }

  const getTriageLabel = (priority) => {
    const labels = {
      white: 'Codice Bianco',
      green: 'Codice Verde', 
      yellow: 'Codice Giallo',
      red: 'Codice Rosso',
      black: 'Codice Nero'
    }
    return labels[priority] || priority
  }

  if (!isOpen) return null

  return (
    <div className="modal fade show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className="bi bi-plus-circle me-2"></i>
              Nuovo Episodio di Cura
            </h5>
            <button 
              type="button" 
              className="btn-close" 
              onClick={onClose}
            ></button>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {errors.general && (
                <div className="alert alert-danger">
                  {errors.general}
                </div>
              )}

              <div className="row">
                {/* Dati Paziente */}
                <div className="col-md-6">
                  <h6 className="fw-bold mb-3">
                    <i className="bi bi-person me-2"></i>
                    Dati Paziente
                  </h6>
                  
                  <div className="mb-3">
                    <label className="form-label">Nome *</label>
                    <input
                      type="text"
                      className={`form-control ${errors.patient_first_name ? 'is-invalid' : ''}`}
                      name="patient_first_name"
                      value={formData.patient_first_name}
                      onChange={handleChange}
                      required
                    />
                    {errors.patient_first_name && (
                      <div className="invalid-feedback">{errors.patient_first_name}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Cognome *</label>
                    <input
                      type="text"
                      className={`form-control ${errors.patient_last_name ? 'is-invalid' : ''}`}
                      name="patient_last_name"
                      value={formData.patient_last_name}
                      onChange={handleChange}
                      required
                    />
                    {errors.patient_last_name && (
                      <div className="invalid-feedback">{errors.patient_last_name}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Data di Nascita *</label>
                    <input
                      type="date"
                      className={`form-control ${errors.patient_date_of_birth ? 'is-invalid' : ''}`}
                      name="patient_date_of_birth"
                      value={formData.patient_date_of_birth}
                      onChange={handleChange}
                      required
                    />
                    {errors.patient_date_of_birth && (
                      <div className="invalid-feedback">{errors.patient_date_of_birth}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Codice Fiscale</label>
                    <input
                      type="text"
                      className={`form-control ${errors.patient_fiscal_code ? 'is-invalid' : ''}`}
                      name="patient_fiscal_code"
                      value={formData.patient_fiscal_code}
                      onChange={handleChange}
                      maxLength="16"
                    />
                    {errors.patient_fiscal_code && (
                      <div className="invalid-feedback">{errors.patient_fiscal_code}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Sesso *</label>
                    <select
                      className={`form-select ${errors.patient_gender ? 'is-invalid' : ''}`}
                      name="patient_gender"
                      value={formData.patient_gender}
                      onChange={handleChange}
                      required
                    >
                      <option value="M">Maschio</option>
                      <option value="F">Femmina</option>
                      <option value="O">Altro</option>
                    </select>
                    {errors.patient_gender && (
                      <div className="invalid-feedback">{errors.patient_gender}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Telefono</label>
                    <input
                      type="tel"
                      className={`form-control ${errors.patient_phone ? 'is-invalid' : ''}`}
                      name="patient_phone"
                      value={formData.patient_phone}
                      onChange={handleChange}
                    />
                    {errors.patient_phone && (
                      <div className="invalid-feedback">{errors.patient_phone}</div>
                    )}
                  </div>
                </div>

                {/* Dati Episodio */}
                <div className="col-md-6">
                  <h6 className="fw-bold mb-3">
                    <i className="bi bi-clipboard-heart me-2"></i>
                    Dati Episodio
                  </h6>

                  <div className="mb-3">
                    <label className="form-label">Motivo Accesso *</label>
                    <textarea
                      className={`form-control ${errors.chief_complaint ? 'is-invalid' : ''}`}
                      name="chief_complaint"
                      value={formData.chief_complaint}
                      onChange={handleChange}
                      rows="3"
                      placeholder="Descrivi il motivo dell'accesso in pronto soccorso..."
                      required
                    ></textarea>
                    {errors.chief_complaint && (
                      <div className="invalid-feedback">{errors.chief_complaint}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Priorità Triage *</label>
                    <select
                      className={`form-select ${errors.triage_priority ? 'is-invalid' : ''}`}
                      name="triage_priority"
                      value={formData.triage_priority}
                      onChange={handleChange}
                      required
                    >
                      <option value="white">Codice Bianco - Non urgente</option>
                      <option value="green">Codice Verde - Poco urgente</option>
                      <option value="yellow">Codice Giallo - Urgente</option>
                      <option value="red">Codice Rosso - Molto urgente</option>
                      <option value="black">Codice Nero - Emergenza</option>
                    </select>
                    {errors.triage_priority && (
                      <div className="invalid-feedback">{errors.triage_priority}</div>
                    )}
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Orario Ammissione *</label>
                    <input
                      type="datetime-local"
                      className={`form-control ${errors.admission_time ? 'is-invalid' : ''}`}
                      name="admission_time"
                      value={formData.admission_time}
                      onChange={handleChange}
                      required
                    />
                    {errors.admission_time && (
                      <div className="invalid-feedback">{errors.admission_time}</div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={onClose}
                disabled={createEncounterMutation.isLoading}
              >
                Annulla
              </button>
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={createEncounterMutation.isLoading}
              >
                {createEncounterMutation.isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Creazione...
                  </>
                ) : (
                  <>
                    <i className="bi bi-check-lg me-1"></i>
                    Crea Episodio
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default NewEncounterModal