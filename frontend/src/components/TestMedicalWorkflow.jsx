/**
 * Pagina di test per il workflow medico completo
 */

import React, { useState } from 'react';
import MedicalWorkflow from './MedicalWorkflow';

const TestMedicalWorkflow = () => {
  const [encounterId, setEncounterId] = useState('');
  const [testMode, setTestMode] = useState(false);

  const handleStartTest = () => {
    if (!encounterId.trim()) {
      alert('Inserisci un ID Encounter valido per iniziare il test');
      return;
    }
    setTestMode(true);
  };

  const handleResetTest = () => {
    setTestMode(false);
    setEncounterId('');
  };

  // Genera un ID encounter di esempio
  const generateSampleId = () => {
    const sampleId = `ENC_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setEncounterId(sampleId);
  };

  return (
    <div className="container-fluid py-4">
      <div className="row">
        <div className="col-12">
          <h1 className="display-5">🧪 Test Medical Workflow</h1>
          <p className="lead text-muted">
            Testa il sistema completo di trascrizione audio, estrazione dati clinici e generazione report
          </p>
        </div>
      </div>

      {!testMode ? (
        <div className="row">
          <div className="col-lg-8 mx-auto">
            <div className="card shadow">
              <div className="card-header bg-info text-white">
                <h5 className="card-title mb-0">Configurazione Test</h5>
              </div>
              <div className="card-body">
                
                <div className="alert alert-info">
                  <h6 className="alert-heading">Prima di iniziare:</h6>
                  <ul className="mb-0">
                    <li>Assicurati che il backend Django sia in esecuzione su <code>http://127.0.0.1:8000</code></li>
                    <li>Verifica di avere un file audio di prova (MP3, WAV, OGG)</li>
                    <li>Il file audio dovrebbe contenere una registrazione medica in italiano</li>
                  </ul>
                </div>

                <div className="mb-4">
                  <h6>Encounter ID</h6>
                  <div className="input-group">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Inserisci un ID encounter o genera uno di esempio"
                      value={encounterId}
                      onChange={(e) => setEncounterId(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={generateSampleId}
                      className="btn btn-outline-secondary"
                    >
                      Genera ID
                    </button>
                    <button
                      type="button"
                      onClick={handleStartTest}
                      className="btn btn-primary"
                      disabled={!encounterId.trim()}
                    >
                      Inizia Test
                    </button>
                  </div>
                  <small className="form-text text-muted">
                    L'ID encounter identifica il caso clinico specifico
                  </small>
                </div>

                <div className="alert alert-warning">
                  <h6 className="alert-heading">Note importanti:</h6>
                  <ul className="mb-0">
                    <li>Questo è un ambiente di test - non utilizzare dati medici reali</li>
                    <li>I modelli AI potrebbero richiedere del tempo per il primo caricamento</li>
                    <li>Assicurati di avere una connessione stabile durante il processing</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="row">
          <div className="col-12">
            {/* Info encounter */}
            <div className="alert alert-primary d-flex justify-content-between align-items-center">
              <div>
                <h6 className="mb-0">🏥 Test in corso per Encounter: <code>{encounterId}</code></h6>
              </div>
              <button
                type="button"
                onClick={handleResetTest}
                className="btn btn-outline-primary btn-sm"
              >
                ← Cambia Encounter
              </button>
            </div>

            {/* Componente workflow */}
            <MedicalWorkflow encounterId={encounterId} />
          </div>
        </div>
      )}

      {/* Informazioni API */}
      <div className="row mt-5">
        <div className="col-12">
          <div className="card">
            <div className="card-header bg-light">
              <h6 className="card-title mb-0">📡 Endpoint API Disponibili</h6>
            </div>
            <div className="card-body">
              <div className="row">
                <div className="col-md-6">
                  <ul className="list-unstyled">
                    <li><code>POST /api/medical-workflow/complete-workflow/</code><br/>
                        <small className="text-muted">Workflow completo</small></li>
                    <li><code>POST /api/transcripts/upload-and-transcribe/</code><br/>
                        <small className="text-muted">Solo trascrizione</small></li>
                    <li><code>POST /api/clinical-data/extract-from-transcript/</code><br/>
                        <small className="text-muted">Solo estrazione</small></li>
                  </ul>
                </div>
                <div className="col-md-6">
                  <ul className="list-unstyled">
                    <li><code>POST /api/reports/generate-from-data/</code><br/>
                        <small className="text-muted">Solo report</small></li>
                    <li><code>GET /api/medical-workflow/workflow-status/{'{encounter_id}'}/</code><br/>
                        <small className="text-muted">Stato workflow</small></li>
                  </ul>
                </div>
              </div>
              
              <div className="alert alert-info mt-3">
                <strong>Esempio file audio di test:</strong><br/>
                Registra una breve frase come: "Il paziente Mario Rossi di 45 anni presenta dolore toracico, 
                pressione arteriosa 140/90, frequenza cardiaca 85 battiti al minuto, temperatura 37.2 gradi."
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestMedicalWorkflow;