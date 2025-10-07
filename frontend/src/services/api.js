/**
 * API Service per comunicazione con backend Django
 * Gestisce autenticazione, endpoints REST e WebSocket
 */

import axios from 'axios'

// Configurazione base Axios
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 secondi
})

// Interceptor per autenticazione JWT
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor per gestione refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// Authentication endpoints
export const authAPI = {
  login: async (credentials) => {
    // Usa l'endpoint diretto che bypassa CSRF
    const response = await apiClient.post('/auth/login/', credentials)
    const { access, refresh, user } = response.data
    
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    
    return { user, access, refresh }
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout/')
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me/')
    return response.data
  },
}

// Patients endpoints
export const patientsAPI = {
  list: async (params = {}) => {
    const response = await apiClient.get('/api/patients/', { params })
    return response.data
  },

  get: async (id) => {
    const response = await apiClient.get(`/patients/${id}/`)
    return response.data
  },

  create: async (data) => {
    const response = await apiClient.post('/patients/', data)
    return response.data
  },

  update: async (id, data) => {
    const response = await apiClient.put(`/patients/${id}/`, data)
    return response.data
  },

  getEncounters: async (id) => {
    const response = await apiClient.get(`/patients/${id}/encounters/`)
    return response.data
  },
}

// Encounters endpoints
export const encountersAPI = {
  list: async (params = {}) => {
    const response = await apiClient.get('/api/encounters/', { params })
    return response.data
  },

  get: async (id) => {
    const response = await apiClient.get(`/api/encounters/${id}/`)
    return response.data
  },

  create: async (data) => {
    const response = await apiClient.post('/api/encounters/', data)
    return response.data
  },

  update: async (id, data) => {
    const response = await apiClient.put(`/api/encounters/${id}/`, data)
    return response.data
  },

  startAudioSession: async (id) => {
    const response = await apiClient.post(`/encounters/${id}/start_audio_session/`)
    return response.data
  },

  getTranscripts: async (id) => {
    const response = await apiClient.get(`/encounters/${id}/transcripts/`)
    return response.data
  },
}

// Audio Transcripts endpoints
export const transcriptsAPI = {
  list: async (params = {}) => {
    const response = await apiClient.get('/transcripts/', { params })
    return response.data
  },

  get: async (id) => {
    const response = await apiClient.get(`/transcripts/${id}/`)
    return response.data
  },

  uploadAudio: async (id, audioFile, engine = 'whisper') => {
    const formData = new FormData()
    formData.append('audio', audioFile)
    formData.append('engine', engine)

    const response = await apiClient.post(`/transcripts/${id}/upload_audio/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        console.log(`Upload progress: ${percentCompleted}%`)
      },
    })
    return response.data
  },

  extractClinicalData: async (id) => {
    const response = await apiClient.post(`/transcripts/${id}/extract_clinical_data/`)
    return response.data
  },

  updateClinicalData: async (id, clinicalData) => {
    const response = await apiClient.patch(`/transcripts/${id}/update_clinical_data/`, {
      clinical_data: clinicalData,
    })
    return response.data
  },

  generateReport: async (id, template = 'er_standard') => {
    const response = await apiClient.post(`/transcripts/${id}/generate_report/`, {
      template,
    })
    return response.data
  },
}

// Doctors endpoints
export const doctorsAPI = {
  list: async (params = {}) => {
    const response = await apiClient.get('/doctors/', { params })
    return response.data
  },

  get: async (id) => {
    const response = await apiClient.get(`/doctors/${id}/`)
    return response.data
  },

  getActiveEncounters: async (id) => {
    const response = await apiClient.get(`/doctors/${id}/active_encounters/`)
    return response.data
  },
}

// WebSocket service per streaming STT
export class STTWebSocketService {
  constructor() {
    this.ws = null
    this.isConnected = false
    this.listeners = new Map()
  }

  connect(transcriptId) {
    const wsUrl = `${import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'}/ws/stt/${transcriptId}/`
    
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnected = true
        console.log('STT WebSocket connected')
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.emit('message', data)

          // Emit specific event types
          if (data.type) {
            this.emit(data.type, data)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('STT WebSocket error:', error)
        this.emit('error', error)
        reject(error)
      }

      this.ws.onclose = () => {
        this.isConnected = false
        console.log('STT WebSocket disconnected')
        this.emit('disconnect')
      }
    })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.isConnected = false
    }
  }

  sendAudioChunk(audioBlob) {
    if (this.ws && this.isConnected) {
      this.ws.send(audioBlob)
    }
  }

  sendCommand(command, data = {}) {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify({ command, ...data }))
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data))
    }
  }
}

// Error handling utility
export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        return { message: 'Dati non validi', details: data }
      case 401:
        return { message: 'Non autorizzato', details: 'Effettua il login' }
      case 403:
        return { message: 'Accesso negato', details: data }
      case 404:
        return { message: 'Risorsa non trovata', details: data }
      case 500:
        return { message: 'Errore interno del server', details: 'Riprova più tardi' }
      default:
        return { message: 'Errore sconosciuto', details: data }
    }
  } else if (error.request) {
    // Network error
    return { message: 'Errore di connessione', details: 'Verifica la connessione internet' }
  } else {
    // Other error
    return { message: 'Errore', details: error.message }
  }
}

// File upload utility
export const uploadFile = async (url, file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  return apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percentCompleted)
      }
    },
  })
}

// Medical Workflow endpoints
export const medicalWorkflowAPI = {
  // Workflow completo in una chiamata
  completeWorkflow: async (encounterId, audioFile, language = 'it') => {
    const formData = new FormData()
    formData.append('encounter_id', encounterId)
    formData.append('audio_file', audioFile)
    formData.append('language', language)

    const response = await apiClient.post('/api/medical-workflow/complete-workflow/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minuti per workflow completo
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        console.log(`Upload progress: ${percentCompleted}%`)
      },
    })
    return response.data
  },

  // Stato del workflow per encounter
  getWorkflowStatus: async (encounterId) => {
    const response = await apiClient.get(`/api/medical-workflow/workflow-status/${encounterId}/`)
    return response.data
  },

  // Solo trascrizione
  uploadAndTranscribe: async (encounterId, audioFile, language = 'it') => {
    const formData = new FormData()
    formData.append('encounter_id', encounterId)
    formData.append('audio_file', audioFile)
    formData.append('language', language)

    const response = await apiClient.post('/api/transcripts/upload-and-transcribe/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    })
    return response.data
  },

  // Solo estrazione dati clinici
  extractFromTranscript: async (transcriptId) => {
    const response = await apiClient.post('/api/clinical-data/extract-from-transcript/', {
      transcript_id: transcriptId
    })
    return response.data
  },

  // Solo generazione report
  generateFromData: async (clinicalDataId) => {
    const response = await apiClient.post('/api/reports/generate-from-data/', {
      clinical_data_id: clinicalDataId
    })
    return response.data
  },

  // Download report
  downloadReport: async (reportId) => {
    const response = await apiClient.get(`/api/reports/${reportId}/download_pdf/`, {
      responseType: 'blob'
    })
    return response.data
  },

  // Download audio originale
  downloadAudio: async (transcriptId) => {
    const response = await apiClient.get(`/api/transcripts/${transcriptId}/download_audio/`, {
      responseType: 'blob'
    })
    return response.data
  },

  // Statistiche dashboard
  getStats: async () => {
    const [transcripts, clinicalData, reports] = await Promise.all([
      apiClient.get('/api/transcripts/'),
      apiClient.get('/api/clinical-data/'),
      apiClient.get('/api/reports/')
    ])
    
    return {
      transcripts: transcripts.data,
      clinicalData: clinicalData.data,
      reports: reports.data
    }
  },

  // Dashboard analytics con MongoDB
  getDashboardAnalytics: async () => {
    const response = await apiClient.get('/api/dashboard/analytics/')
    return response.data
  },

  // Lista pazienti con filtri
  getPatientsList: async (filter = 'all') => {
    const response = await apiClient.get('/api/patients/list/', {
      params: { filter }
    })
    return response.data
  },

  // Processo visita audio completa con FormData
  processAudioVisit: async (formData) => {
    const response = await apiClient.post('/api/visits/process-audio/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minuti per processing completo
    })
    return response.data
  },

  // Processo visita audio completa (metodo legacy)
  processAudioVisitLegacy: async (encounterId, audioFile, usageMode = '') => {
    const formData = new FormData()
    formData.append('encounter_id', encounterId)
    formData.append('audio_file', audioFile)
    formData.append('usage_mode', usageMode)

    const response = await apiClient.post('/api/visits/process-audio/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minuti per processing completo
    })
    return response.data
  },

  // Cronologia visite paziente
  getPatientVisitHistory: async (patientId) => {
    const response = await apiClient.get(`/api/patients/${patientId}/visits/`)
    return response.data
  },

  // Aggiorna dati paziente
  updatePatientData: async (patientId, data) => {
    const response = await apiClient.put(`/api/patients/${patientId}/update/`, data)
    return response.data
  },

  // Genera report PDF
  generatePDFReport: async (transcriptId) => {
    const response = await apiClient.post(`/api/reports/${transcriptId}/generate/`)
    return response.data
  },

  // Download report PDF
  downloadPDFReport: async (transcriptId) => {
    const response = await apiClient.get(`/api/reports/${transcriptId}/download/`, {
      responseType: 'blob'
    })
    return response.data
  },

  // Dettagli transcript
  getTranscriptDetails: async (transcriptId) => {
    const response = await apiClient.get(`/api/transcripts/${transcriptId}/details/`)
    return response.data
  }
}

export default apiClient