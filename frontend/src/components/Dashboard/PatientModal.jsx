import React, { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'

const PatientModal = ({ 
  isOpen, 
  onClose, 
  patient = null, 
  mode = 'create' // 'create' o 'edit'
}) => {
  const queryClient = useQueryClient()
  
  const [formData, setFormData] = useState({
    codice_fiscale: patient?.codice_fiscale || '',
    nome: patient?.nome || '',
    cognome: patient?.cognome || '',
    data_nascita: patient?.data_nascita || '',
    sesso: patient?.sesso || '',
    telefono: patient?.telefono || '',
    indirizzo: patient?.indirizzo || '',
    codice_triage: patient?.codice_triage || 'white',
    note_triage: patient?.note_triage || ''
  })

  const [errors, setErrors] = useState({})

  const createPatientMutation = useMutation({
    mutationFn: (data) => medicalWorkflowAPI.createPatient(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['patients'])
      onClose()
      setFormData({
        codice_fiscale: '',
        nome: '',
        cognome: '',
        data_nascita: '',
        sesso: '',
        telefono: '',
        indirizzo: '',
        codice_triage: 'white',
        note_triage: ''
      })
    },
    onError: (error) => {
      setErrors(error.response?.data || { general: 'Errore durante la creazione' })
    }
  })

  const updatePatientMutation = useMutation({
    mutationFn: (data) => medicalWorkflowAPI.updatePatient(patient.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['patients'])
      onClose()
    },
    onError: (error) => {
      setErrors(error.response?.data || { general: 'Errore durante l\'aggiornamento' })
    }
  })

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Rimuovi errore per questo campo
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.codice_fiscale) newErrors.codice_fiscale = 'Codice fiscale richiesto'
    if (!formData.nome) newErrors.nome = 'Nome richiesto'
    if (!formData.cognome) newErrors.cognome = 'Cognome richiesto'
    if (!formData.data_nascita) newErrors.data_nascita = 'Data di nascita richiesta'
    if (!formData.sesso) newErrors.sesso = 'Sesso richiesto'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!validateForm()) return

    if (mode === 'create') {
      createPatientMutation.mutate(formData)
    } else {
      updatePatientMutation.mutate(formData)
    }
  }

  const getTriageColorClass = (code) => {
    const colors = {
      white: 'secondary',
      green: 'success', 
      yellow: 'warning',
      red: 'danger',
      black: 'dark'
    }
    return colors[code] || 'secondary'
  }

  if (!isOpen) return null

  const isLoading = createPatientMutation.isPending || updatePatientMutation.isPending

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              <i className={`bi ${mode === 'create' ? 'bi-person-plus' : 'bi-person-gear'} me-2`}></i>
              {mode === 'create' ? 'Nuovo Paziente' : 'Modifica Paziente'}
            </h5>
            <button 
              type="button" 
              className="btn-close" 
              onClick={onClose}
              disabled={isLoading}
            ></button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="modal-body">
              {errors.general && (
                <div className="alert alert-danger">
                  <i className="bi bi-exclamation-triangle me-2"></i>
                  {errors.general}
                </div>
              )}

              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="codice_fiscale" className="form-label">
                      Codice Fiscale *
                    </label>
                    <input
                      type="text"
                      className={`form-control ${errors.codice_fiscale ? 'is-invalid' : ''}`}
                      id="codice_fiscale"
                      name="codice_fiscale"
                      value={formData.codice_fiscale}
                      onChange={handleInputChange}
                      maxLength="16"
                      style={{ textTransform: 'uppercase' }}
                    />
                    {errors.codice_fiscale && (
                      <div className="invalid-feedback">{errors.codice_fiscale}</div>
                    )}
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="sesso" className="form-label">
                      Sesso *
                    </label>
                    <select
                      className={`form-select ${errors.sesso ? 'is-invalid' : ''}`}
                      id="sesso"
                      name="sesso"
                      value={formData.sesso}
                      onChange={handleInputChange}
                    >
                      <option value="">Seleziona...</option>
                      <option value="M">Maschio</option>
                      <option value="F">Femmina</option>
                    </select>
                    {errors.sesso && (
                      <div className="invalid-feedback">{errors.sesso}</div>
                    )}
                  </div>
                </div>
              </div>

              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="nome" className="form-label">
                      Nome *
                    </label>
                    <input
                      type="text"
                      className={`form-control ${errors.nome ? 'is-invalid' : ''}`}
                      id="nome"
                      name="nome"
                      value={formData.nome}
                      onChange={handleInputChange}
                    />
                    {errors.nome && (
                      <div className="invalid-feedback">{errors.nome}</div>
                    )}
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="cognome" className="form-label">
                      Cognome *
                    </label>
                    <input
                      type="text"
                      className={`form-control ${errors.cognome ? 'is-invalid' : ''}`}
                      id="cognome"
                      name="cognome"
                      value={formData.cognome}
                      onChange={handleInputChange}
                    />
                    {errors.cognome && (
                      <div className="invalid-feedback">{errors.cognome}</div>
                    )}
                  </div>
                </div>
              </div>

              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="data_nascita" className="form-label">
                      Data di Nascita *
                    </label>
                    <input
                      type="date"
                      className={`form-control ${errors.data_nascita ? 'is-invalid' : ''}`}
                      id="data_nascita"
                      name="data_nascita"
                      value={formData.data_nascita}
                      onChange={handleInputChange}
                    />
                    {errors.data_nascita && (
                      <div className="invalid-feedback">{errors.data_nascita}</div>
                    )}
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="telefono" className="form-label">
                      Telefono
                    </label>
                    <input
                      type="tel"
                      className="form-control"
                      id="telefono"
                      name="telefono"
                      value={formData.telefono}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
              </div>

              <div className="mb-3">
                <label htmlFor="indirizzo" className="form-label">
                  Indirizzo
                </label>
                <input
                  type="text"
                  className="form-control"
                  id="indirizzo"
                  name="indirizzo"
                  value={formData.indirizzo}
                  onChange={handleInputChange}
                />
              </div>

              <div className="row">
                <div className="col-md-6">
                  <div className="mb-3">
                    <label htmlFor="codice_triage" className="form-label">
                      Codice Triage
                    </label>
                    <select
                      className="form-select"
                      id="codice_triage"
                      name="codice_triage"
                      value={formData.codice_triage}
                      onChange={handleInputChange}
                    >
                      <option value="white">⚪ Bianco - Non urgente</option>
                      <option value="green">🟢 Verde - Poco urgente</option>
                      <option value="yellow">🟡 Giallo - Urgente</option>
                      <option value="red">🔴 Rosso - Molto urgente</option>
                      <option value="black">⚫ Nero - Critico</option>
                    </select>
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="mb-3">
                    <span className={`badge bg-${getTriageColorClass(formData.codice_triage)} fs-6`}>
                      Priorità: {formData.codice_triage.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mb-3">
                <label htmlFor="note_triage" className="form-label">
                  Note Triage
                </label>
                <textarea
                  className="form-control"
                  id="note_triage"
                  name="note_triage"
                  rows="3"
                  value={formData.note_triage}
                  onChange={handleInputChange}
                  placeholder="Note aggiuntive per il triage..."
                ></textarea>
              </div>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={onClose}
                disabled={isLoading}
              >
                Annulla
              </button>
              <button 
                type="submit" 
                className={`btn btn-${mode === 'create' ? 'primary' : 'success'}`}
                disabled={isLoading}
              >
                {isLoading && <span className="spinner-border spinner-border-sm me-2"></span>}
                {mode === 'create' ? 'Crea Paziente' : 'Salva Modifiche'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default PatientModal