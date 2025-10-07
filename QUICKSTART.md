# GUIDA RAPIDA - Come Eseguire il Sistema

## 🚀 Avvio Rapido

### 1. Setup Automatico
```bash
cd unified-medical-system
python setup.py
```

### 2. Avvio Backend Django
```bash
cd backend
.venv\Scripts\activate
python manage.py runserver
```
**🌐 Backend disponibile su: http://localhost:8000**

### 3. Avvio Frontend React
```bash
# Nuovo terminale
cd frontend  
npm run dev
```
**🌐 Frontend disponibile su: http://localhost:3000**

## 👤 Accesso al Sistema

### Credenziali Demo
- **Username:** `demo.doctor`
- **Password:** `demo123`

### URL Principali
- **Frontend:** http://localhost:3000
- **API Backend:** http://localhost:8000/api
- **Admin Django:** http://localhost:8000/admin

## 🛠️ Componenti Disponibili

### ✅ Funzionanti
- ✅ **Login AGID-compliant**
- ✅ **Dashboard Pronto Soccorso**  
- ✅ **Gestione Encounters**
- ✅ **API REST complete**
- ✅ **Autenticazione JWT**
- ✅ **Styling Bootstrap Italia**

### 🔄 In Sviluppo
- 🔄 **Registrazione Audio STT**
- 🔄 **Editor Dati Clinici**
- 🔄 **Generazione PDF Report**
- 🔄 **Pipeline NLP/LLM**

## 📁 Struttura Implementata

```
unified-medical-system/
├── backend/                    # ✅ Django REST API
│   ├── core/                  # ✅ Modelli base
│   ├── stt/                   # ✅ Engine STT 
│   ├── api/                   # ✅ Endpoints REST
│   └── manage.py              # ✅ Django management
├── frontend/                   # ✅ React + Vite
│   ├── src/components/        # ✅ Componenti UI
│   ├── src/services/          # ✅ API client
│   └── package.json           # ✅ Dipendenze
└── docker-compose.yml         # ✅ Container setup
```

## 🔧 Troubleshooting

### Errore "Module not found"
```bash
cd backend
.venv\Scripts\pip install -r requirements.txt
```

### Errore Frontend Dependencies
```bash
cd frontend
npm install
```

### Reset Database
```bash
cd backend
del db.sqlite3
python manage.py migrate
python manage.py create_demo_data
```

## 🎯 Prossimi Passi

1. **Completa componenti STT** (Task 7)
2. **Implementa PDF reports** (Task 8)  
3. **Test con dataset medico reale**
4. **Deploy production con Docker**

## 📞 Support

Per problemi o domande:
- Controlla logs Django: `backend/logs/`
- Controlla console browser per frontend
- Verifica variabili ambiente `.env`