import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
// import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

// Bootstrap Italia CSS
import 'bootstrap-italia/dist/css/bootstrap-italia.min.css'
import 'bootstrap-italia/dist/js/bootstrap-italia.min.js'

// Components
import Layout from '@components/Layout/Layout'
import LoginPage from '@components/Auth/LoginPage'
import Dashboard from '@components/Dashboard/Dashboard'
import EncounterDetail from '@components/Encounter/EncounterDetail'
import AudioRecording from '@components/Audio/AudioRecording'
import ClinicalEditor from '@components/Clinical/ClinicalEditor'
import ReportPreview from '@components/Report/ReportPreview'
import NewEmergencyPage from '@components/Emergency/NewEmergencyPage'

// Hooks
import { useAuthStore } from '@services/authStore'

// CSS Custom per AGID
import './App.css'

// QueryClient configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minuti
    },
  },
})

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          {!isAuthenticated ? (
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          ) : (
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/encounter/new" element={<NewEmergencyPage />} />
                <Route path="/encounter/:id" element={<EncounterDetail />} />
                <Route path="/encounter/:id/audio" element={<AudioRecording />} />
                <Route path="/encounter/:id/clinical" element={<ClinicalEditor />} />
                <Route path="/encounter/:id/report" element={<ReportPreview />} />
                <Route path="/login" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Layout>
          )}
        </div>
      </Router>
      {/* {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />} */}
    </QueryClientProvider>
  )
}

export default App
