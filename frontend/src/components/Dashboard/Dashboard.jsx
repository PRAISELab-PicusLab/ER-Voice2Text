import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { medicalWorkflowAPI } from '../../services/api'
import { useAuthStore } from '../../services/authStore'
import PatientsList from './PatientsList'

const Dashboard = () => {
  const { user } = useAuthStore()

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => medicalWorkflowAPI.getDashboardAnalytics(),
    refetchInterval: 30000,
  })

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

      {/* Messaggio e pulsante Nuova Emergenza centrale */}
      <div className="row justify-content-center mb-4">
        <div className="col-12 col-md-10 col-lg-8 d-flex flex-column align-items-center">
          <div className="alert alert-warning text-center w-100 mb-3 p-3 fs-5 fw-semibold" style={{borderRadius: '1.5rem'}}>
            <span className="text-danger">AZIONE RAPIDA:</span> Premi il pulsante qui sotto per registrare subito una nuova emergenza!
          </div>
          <a 
            href="/encounter/new" 
            className="btn btn-danger btn-lg px-4 py-3 shadow-lg fs-3 fw-bold w-100 text-uppercase text-center"
            style={{ maxWidth: '480px', borderRadius: '1.5rem', letterSpacing: '0.04em' }}
          >
            <i className="bi bi-plus-circle-fill me-2"></i>
            NUOVA EMERGENZA
          </a>
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


      {/* Patients list - main content */}
      <div className="row">
        <div className="col">
          <PatientsList />
        </div>
      </div>
      
    </div>
  )
}

export default Dashboard