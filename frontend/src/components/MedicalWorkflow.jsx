import React, { useState } from 'react';

const steps = [
  'Upload Audio',
  'Trascrizione',
  'Estrazione Dati',
  'Generazione Report'
];

const MedicalWorkflow = ({ encounterId }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validazione file audio
      const allowedTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg'];
      if (!allowedTypes.includes(file.type)) {
        setError('Formato file non supportato. Utilizzare MP3, WAV o OGG.');
        return;
      }
      
      if (file.size > 50 * 1024 * 1024) { // 50MB limit
        setError('File troppo grande. Limite massimo: 50MB.');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      setActiveStep(1);
    }
  };

  const handleProcessWorkflow = async () => {
    if (!selectedFile || !encounterId) {
      setError('File audio ed Encounter ID sono richiesti.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Crea FormData per upload
      const formData = new FormData();
      formData.append('encounter_id', encounterId);
      formData.append('audio_file', selectedFile);
      formData.append('language', 'it');

      // Simula il progresso attraverso i passi
      setActiveStep(1);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setActiveStep(2);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setActiveStep(3);

      // Chiamata API per workflow completo
      const response = await fetch('/api/medical-workflow/complete-workflow/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}` // Se usi autenticazione JWT
        }
      });

      if (!response.ok) {
        throw new Error(`Errore HTTP: ${response.status}`);
      }

      const data = await response.json();
      setResult(data);
      setActiveStep(4);
      
    } catch (err) {
      console.error('Errore workflow:', err);
      setError(`Errore durante il processing: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!result?.report?.report_id) return;

    try {
      const response = await fetch(`/api/reports/${result.report.report_id}/download_pdf/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Errore download report');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `report_${result.report.report_id}.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      setError(`Errore download: ${err.message}`);
    }
  };

  const resetWorkflow = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setLoading(false);
  };

  return (
    <div className="container-fluid">
      <div className="card shadow">
        <div className="card-header bg-primary text-white">
          <h5 className="card-title mb-0">
            🏥 Workflow Medico - Trascrizione e Report
          </h5>
        </div>
        <div className="card-body">
          
          {/* Progress Stepper */}
          <div className="row mb-4">
            <div className="col-12">
              <div className="progress-container">
                <div className="d-flex justify-content-between">
                  {steps.map((step, index) => (
                    <div key={index} className="text-center flex-fill">
                      <div className={`rounded-circle mx-auto mb-2 d-flex align-items-center justify-content-center ${
                        index <= activeStep ? 'bg-success text-white' : 'bg-light text-muted'
                      }`} style={{ width: '40px', height: '40px' }}>
                        {index + 1}
                      </div>
                      <small className={index <= activeStep ? 'text-success fw-bold' : 'text-muted'}>
                        {step}
                      </small>
                    </div>
                  ))}
                </div>
                <div className="progress mt-3" style={{ height: '4px' }}>
                  <div 
                    className="progress-bar bg-success" 
                    style={{ width: `${((activeStep) / (steps.length - 1)) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Progress bar durante il loading */}
          {loading && (
            <div className="mb-3">
              <div className="progress">
                <div className="progress-bar progress-bar-striped progress-bar-animated" 
                     style={{ width: '100%' }}>
                </div>
              </div>
              <small className="text-muted mt-1 d-block">
                Processing in corso... Step {activeStep} di {steps.length}
              </small>
            </div>
          )}

          {/* Messaggi di errore */}
          {error && (
            <div className="alert alert-danger" role="alert">
              <i className="bi bi-exclamation-triangle me-2"></i>
              {error}
            </div>
          )}

          {/* Step 1: Upload File */}
          {activeStep === 0 && (
            <div className="text-center py-5">
              <i className="bi bi-mic display-1 text-primary mb-3"></i>
              <h4>Seleziona file audio per la trascrizione</h4>
              <p className="text-muted mb-4">
                Formati supportati: MP3, WAV, OGG (max 50MB)
              </p>
              <label className="btn btn-primary btn-lg">
                <i className="bi bi-cloud-upload me-2"></i>
                Carica File Audio
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          )}

          {/* Step 2-4: Processing */}
          {activeStep > 0 && activeStep < 4 && (
            <div className="text-center py-4">
              {selectedFile && (
                <div className="alert alert-info mb-3">
                  <i className="bi bi-file-earmark-music me-2"></i>
                  File selezionato: <strong>{selectedFile.name}</strong>
                </div>
              )}
              
              {activeStep === 1 && !loading && (
                <button
                  type="button"
                  className="btn btn-success btn-lg"
                  onClick={handleProcessWorkflow}
                >
                  <i className="bi bi-play-circle me-2"></i>
                  Avvia Processing Completo
                </button>
              )}
            </div>
          )}

          {/* Step 4: Risultati */}
          {activeStep === 4 && result && (
            <div className="mt-3">
              <div className="alert alert-success" role="alert">
                <i className="bi bi-check-circle me-2"></i>
                <strong>🎉 Workflow completato con successo!</strong>
              </div>

              {/* Risultati trascrizione */}
              <div className="card mb-3">
                <div className="card-header">
                  <h6 className="mb-0">📝 Trascrizione</h6>
                </div>
                <div className="card-body">
                  <div className="row">
                    <div className="col-md-4">
                      <small className="text-muted">ID:</small><br/>
                      <code>{result.transcript?.transcript_id}</code>
                    </div>
                    <div className="col-md-4">
                      <small className="text-muted">Confidenza:</small><br/>
                      <span className="badge bg-info">
                        {(result.transcript?.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="col-md-4">
                      <small className="text-muted">Durata:</small><br/>
                      {result.transcript?.audio_duration?.toFixed(1)}s
                    </div>
                  </div>
                </div>
              </div>

              {/* Risultati estrazione */}
              <div className="card mb-3">
                <div className="card-header">
                  <h6 className="mb-0">🔍 Dati Clinici Estratti</h6>
                </div>
                <div className="card-body">
                  <div className="row">
                    <div className="col-md-6">
                      <small className="text-muted">ID:</small><br/>
                      <code>{result.clinical_data?.data_id}</code>
                    </div>
                    <div className="col-md-6">
                      <small className="text-muted">Confidenza:</small><br/>
                      <span className="badge bg-info">
                        {(result.clinical_data?.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  
                  {/* Anteprima dati estratti */}
                  {result.clinical_data?.extracted_data && (
                    <div className="mt-3">
                      <small className="text-muted">Anteprima dati estratti:</small>
                      <pre className="bg-light p-2 rounded mt-1" style={{ fontSize: '0.8rem', maxHeight: '200px', overflow: 'auto' }}>
                        {JSON.stringify(result.clinical_data.extracted_data, null, 2).slice(0, 500)}...
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Risultati report */}
              <div className="card mb-3">
                <div className="card-header">
                  <h6 className="mb-0">📄 Report Generato</h6>
                </div>
                <div className="card-body">
                  <small className="text-muted">ID:</small><br/>
                  <code className="mb-3 d-block">{result.report?.report_id}</code>
                  
                  <button
                    type="button"
                    className="btn btn-outline-primary me-2"
                    onClick={handleDownloadReport}
                  >
                    <i className="bi bi-download me-2"></i>
                    Scarica Report
                  </button>
                </div>
              </div>

              {/* Pulsante reset */}
              <div className="text-center mt-4">
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={resetWorkflow}
                >
                  <i className="bi bi-arrow-clockwise me-2"></i>
                  Nuovo Workflow
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MedicalWorkflow;