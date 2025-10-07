/**
 * Pagina di login AGID compliant
 */

import React, { useState } from 'react'
import { useAuthStore } from '@services/authStore'

const LoginPage = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  const { login, loading, error } = useAuthStore()

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(credentials)
    } catch (err) {
      console.error('Login failed:', err)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setCredentials(prev => ({ ...prev, [name]: value }))
  }

  return (
    <div className="min-vh-100 d-flex align-items-center bg-light">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-md-6 col-lg-4">
            {/* Header */}
            <div className="text-center mb-4">
              <div className="mb-3">
                <i className="bi bi-hospital display-1 text-primary"></i>
              </div>
              <h1 className="h3 fw-bold text-primary">Sistema ER Voice2Text</h1>
              <p className="text-muted">Accesso riservato al personale medico</p>
            </div>

            {/* Form Login */}
            <div className="card border-0 shadow">
              <div className="card-body p-4">
                <form onSubmit={handleSubmit}>
                  {error && (
                    <div className="alert alert-danger" role="alert">
                      <i className="bi bi-exclamation-triangle me-2"></i>
                      {error}
                    </div>
                  )}

                  <div className="mb-3">
                    <label htmlFor="username" className="form-label fw-semibold">
                      Username
                    </label>
                    <input
                      type="text"
                      className="form-control form-control-lg"
                      id="username"
                      name="username"
                      value={credentials.username}
                      onChange={handleChange}
                      required
                      autoComplete="username"
                      placeholder="Inserisci il tuo username"
                    />
                  </div>

                  <div className="mb-4">
                    <label htmlFor="password" className="form-label fw-semibold">
                      Password
                    </label>
                    <input
                      type="password"
                      className="form-control form-control-lg"
                      id="password"
                      name="password"
                      value={credentials.password}
                      onChange={handleChange}
                      required
                      autoComplete="current-password"
                      placeholder="Inserisci la tua password"
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary btn-lg w-100"
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Accesso in corso...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-box-arrow-in-right me-2"></i>
                        Accedi
                      </>
                    )}
                  </button>
                </form>

                {/* Info Demo */}
                <div className="mt-4 p-3 bg-light rounded">
                  <h6 className="fw-semibold text-primary">Demo Credentials</h6>
                  <small className="text-muted">
                    Username: <code>demo</code><br />
                    Password: <code>demo123</code>
                  </small>
                </div>
              </div>
            </div>

            {/* Footer conformità */}
            <div className="text-center mt-4">
              <small className="text-muted">
                Sistema conforme alle linee guida AGID per l'accessibilità
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage