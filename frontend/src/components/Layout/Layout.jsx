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
      {/* Mobile-first header for emergency medical use */}
      <nav className="navbar navbar-light bg-white shadow-sm py-1">
        <div className="container-fluid d-flex align-items-center justify-content-between px-2" style={{minHeight: '60px'}}>
          {/* Hamburger menu sempre visibile */}
          <button
            className="btn btn-link ms-0 me-2 header-icon-btn"
            type="button"
            data-bs-toggle="offcanvas"
            data-bs-target="#mobileMenu"
            aria-controls="mobileMenu"
            style={{ minWidth: '44px', minHeight: '44px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#dc3545' }}
          >
            <i className="bi bi-list fs-3"></i>
          </button>

          {/* Logo centrale */}
          <a className="navbar-brand fw-bold text-primary d-flex align-items-center justify-content-center mx-auto px-2" href="/" style={{fontSize: '1.3rem', flex: 1, textAlign: 'center'}}>
            <i className="bi bi-hospital me-2 fs-3"></i>
            ER Voice2Text
          </a>

          {/* User menu (dx) */}
          <div className="dropdown ms-2" style={{minWidth: '44px'}}>
            <button
              className="btn btn-link dropdown-toggle d-flex align-items-center justify-content-center header-icon-btn"
              type="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
              style={{ minWidth: '44px', minHeight: '44px', padding: 0, color: '#dc3545' }}
            >
              <i className="bi bi-person-circle fs-4"></i>
            </button>
            <ul className="dropdown-menu dropdown-menu-end mt-2" style={{minWidth: '200px'}}>
              <li>
                <span className="dropdown-item-text small">
                  {user?.get_full_name || user?.username}<br/>
                  {user?.specialization} - {user?.department}
                </span>
              </li>
              <li><hr className="dropdown-divider" /></li>
              <li>
                <button className="dropdown-item" onClick={handleLogout}>
                  <i className="bi bi-box-arrow-right me-2"></i>
                  Logout
                </button>
              </li>
            </ul>
          </div>
      {/* Stile custom per header icon btn */}
      <style>{`
        .header-icon-btn {
          border: none !important;
          box-shadow: none !important;
          color: #dc3545 !important;
        }
        .header-icon-btn:focus, .header-icon-btn:active {
          border: 2px solid #dc3545 !important;
          background: #fff !important;
          outline: none !important;
        }
      `}</style>
        </div>
      </nav>

      {/* Mobile offcanvas menu */}
      <div className="offcanvas offcanvas-start" tabIndex={-1} id="mobileMenu">
        <div className="offcanvas-header">
          <h5 className="offcanvas-title">Menu</h5>
          <button type="button" className="btn-close" data-bs-dismiss="offcanvas"></button>
        </div>
        <div className="offcanvas-body">
          <ul className="nav nav-pills flex-column">
            <li className="nav-item mb-2">
              <a className="nav-link" href="/dashboard">
                <i className="bi bi-speedometer2 me-2"></i>Dashboard
              </a>
            </li>
            <li className="nav-item mb-2">
              <a className="nav-link" href="/encounter/new">
                <i className="bi bi-plus-circle me-2"></i>Nuova Emergenza
              </a>
            </li>
          </ul>
        </div>
      </div>

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