/**
 * Layout principale AGID compliant con navigazione
 */

import React from 'react'
import { useAuthStore } from '@services/authStore'

const Layout = ({ children }) => {
  const { user, logout } = useAuthStore()

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div className="min-vh-100 w-100">
      {/* Header AGID */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container-fluid">
          <a className="navbar-brand fw-bold" href="/">
            <i className="bi bi-hospital me-2"></i>
            Sistema ER Voice2Text
          </a>
          
          {/* Navigation Links */}
          <div className="navbar-nav me-auto">
            <a className="nav-link" href="/dashboard">
              <i className="bi bi-speedometer2 me-1"></i>
              Dashboard
            </a>
            <a className="nav-link" href="/test-workflow">
              <i className="bi bi-gear me-1"></i>
              Test Workflow
            </a>
          </div>
          
          <div className="navbar-nav ms-auto">
            <div className="nav-item dropdown">
              <a
                className="nav-link dropdown-toggle"
                href="#"
                role="button"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                <i className="bi bi-person-circle me-1"></i>
                {user?.get_full_name || user?.username}
              </a>
              <ul className="dropdown-menu">
                <li>
                  <span className="dropdown-item-text">
                    {user?.specialization} - {user?.department}
                  </span>
                </li>
                <li><hr className="dropdown-divider" /></li>
                <li>
                  <button 
                    className="dropdown-item"
                    onClick={handleLogout}
                  >
                    <i className="bi bi-box-arrow-right me-2"></i>
                    Logout
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content w-100">
        {children}
      </main>

      {/* Footer AGID */}
      <footer className="bg-light border-top mt-auto py-3 w-100">
        <div className="container-fluid">
          <div className="row">
            <div className="col-md-6">
              <small className="text-muted">
                © 2025 Sistema Sanitario - Conforme AGID
              </small>
            </div>
            <div className="col-md-6 text-end">
              <small className="text-muted">
                Versione 1.0.0 | Privacy | Accessibilità
              </small>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout