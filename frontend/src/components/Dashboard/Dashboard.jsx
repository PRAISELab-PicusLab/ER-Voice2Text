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
    <div className="container-fluid py-4">
      <div className="row mb-4">
        <div className="col">
          <h1 className="h2 fw-bold text-primary">
            <i className="bi bi-speedometer2 me-2"></i>
            Dashboard Pronto Soccorso
          </h1>
          <p className="text-muted">
            Benvenuto, {user?.get_full_name} - {user?.department}
          </p>
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-3">
          <div className="card bg-primary text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="fw-bold">{analytics?.total_patients || 0}</h4>
                  <p className="mb-0">Pazienti Totali</p>
                </div>
                <i className="bi bi-person-plus display-6"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-md-3">
          <div className="card bg-success text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="fw-bold">{analytics?.visits_today || 0}</h4>
                  <p className="mb-0">Visite Oggi</p>
                </div>
                <i className="bi bi-calendar-check display-6"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-md-3">
          <div className="card bg-warning text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="fw-bold">{analytics?.waiting_patients || 0}</h4>
                  <p className="mb-0">In Attesa</p>
                </div>
                <i className="bi bi-clock display-6"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-md-3">
          <div className="card bg-info text-white">
            <div className="card-body">
              <div className="d-flex justify-content-between">
                <div>
                  <h4 className="fw-bold">{analytics?.completed_today || 0}</h4>
                  <p className="mb-0">Completate Oggi</p>
                </div>
                <i className="bi bi-check-circle display-6"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">
                <i className="bi bi-gear me-2"></i>
                Stato Servizi
              </h5>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-md-3">
                  <div className="d-flex align-items-center">
                    <i className={`bi bi-circle-fill me-2 ${analytics?.mongodb_connected ? 'text-success' : 'text-danger'}`}></i>
                    <span>MongoDB</span>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="d-flex align-items-center">
                    <i className={`bi bi-circle-fill me-2 ${analytics?.whisper_available ? 'text-success' : 'text-warning'}`}></i>
                    <span>Whisper AI</span>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="d-flex align-items-center">
                    <i className={`bi bi-circle-fill me-2 ${analytics?.nvidia_nim_available ? 'text-success' : 'text-warning'}`}></i>
                    <span>NVIDIA NIM</span>
                  </div>
                </div>
                <div className="col-md-3">
                  <small className="text-muted">
                    Ultimo aggiornamento: {analytics?.last_updated ? new Date(analytics.last_updated).toLocaleTimeString() : 'N/D'}
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col">
          <PatientsList />
        </div>
      </div>
    </div>
  )
}

export default Dashboard