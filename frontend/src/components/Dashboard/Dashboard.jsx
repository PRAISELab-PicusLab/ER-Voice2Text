import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { medicalWorkflowAPI } from '../../services/api'
import { useAuthStore } from '../../services/authStore'
import PatientsList from './PatientsList'
import InterventionsList from './InterventionsList'

const Dashboard = () => {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('interventions')

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => medicalWorkflowAPI.getDashboardAnalytics(),
    refetchInterval: 30000,
  })

  const handleEditIntervention = (intervention) => {
    // Naviga alla pagina nuova emergenza con i dati precaricati
    navigate('/encounter/new', { 
      state: { 
        editMode: true, 
        interventionData: intervention 
      } 
    })
  }

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

  return (
    <div className="container-fluid py-2">
        <div className="row justify-content-center mb-4">
          <div className="col-12 col-md-10 col-lg-8 d-flex flex-column align-items-center text-center">
            <p className="text-danger mt-3 fs-5 fw-semibold">
              Registra subito una nuova emergenza!
            </p>
            <a 
              href="/encounter/new" 
              className="btn btn-danger btn-lg px-4 py-3 shadow-lg fs-3 fw-bold w-100 text-uppercase text-center"
              style={{ maxWidth: '480px', borderRadius: '1.5rem', letterSpacing: '0.04em' }}
            >
            <i className="bi bi-plus-circle-fill me-2"></i>
            NUOVA EMERGENZA
            </a>
            <small className="text-muted mt-2">Crea una nuova scheda di emergenza per un paziente</small>
          </div>
        </div>

        {/* Mobile-first statistics cards */}
      <div className="row mb-3 g-2">
        <div className="col-6 col-md-3">
          <div className="card bg-primary text-white h-100">
            <div className="card-body p-3">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="fw-bold mb-1">{analytics?.total_patients || 0}</h5>
                  <p className="mb-0 small">Pazienti</p>
                </div>
                <i className="bi bi-person-plus h4 mb-0"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-6 col-md-3">
          <div className="card bg-danger text-white h-100">
            <div className="card-body p-3">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="fw-bold mb-1">{analytics?.visits_today || 0}</h5>
                  <p className="mb-0 small">Emergenze Oggi</p>
                </div>
                <i className="bi bi-exclamation-triangle h4 mb-0"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-6 col-md-3">
          <div className="card bg-warning text-white h-100">
            <div className="card-body p-3">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="fw-bold mb-1">{analytics?.waiting_patients || 0}</h5>
                  <p className="mb-0 small">In Attesa</p>
                </div>
                <i className="bi bi-clock h4 mb-0"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-6 col-md-3">
          <div className="card bg-success text-white h-100">
            <div className="card-body p-3">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h5 className="fw-bold mb-1">{analytics?.completed_today || 0}</h5>
                  <p className="mb-0 small">Completate</p>
                </div>
                <i className="bi bi-check-circle h4 mb-0"></i>
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* Navigation tabs */}
      <div className="row mb-3">
        <div className="col">
          <ul className="nav nav-tabs">
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'interventions' ? 'active' : ''}`}
                onClick={() => setActiveTab('interventions')}
              >
                <i className="bi bi-clipboard-data me-2"></i>
                Tutti gli Interventi
              </button>
            </li>
            <li className="nav-item">
              <button 
                className={`nav-link ${activeTab === 'patients' ? 'active' : ''}`}
                onClick={() => setActiveTab('patients')}
              >
                <i className="bi bi-people me-2"></i>
                Pazienti
              </button>
            </li>
          </ul>
        </div>
      </div>

      {/* Main content based on active tab */}
      <div className="row">
        <div className="col">
          {activeTab === 'patients' ? <PatientsList /> : <InterventionsList onEditIntervention={handleEditIntervention} />}
        </div>
      </div>
      
    </div>
  )
}

export default Dashboard