# Sistema Medico Unificato - Voice2Care

Sistema unificato per la gestione di cartelle cliniche nel Pronto Soccorso con trascrizione automatica vocale e intelligence artificiale.

## 🏥 Caratteristiche

- **Autenticazione sicura** per medici del Pronto Soccorso
- **Dashboard tempo reale** per gestione pazienti ed episodi
- **Registrazione vocale** e trascrizione automatica
- **Estrazione automatica** di dati clinici strutturati
- **Generazione report** PDF automatizzata
- **API REST** complete per integrazione

## 🚀 Tecnologie

### Backend
- **Django 4.2.7** con Django REST Framework
- **SQLite** database (facilmente migrabile a PostgreSQL)
- **Python 3.9+** con supporto ML/AI

### Frontend
- **React 18** con Vite
- **Bootstrap Italia** per UI/UX conforme
- **React Query** per state management API
- **React Router** per navigazione

## 📁 Struttura del Progetto

```
unified-medical-system/
├── backend/                    # Django Backend
│   ├── medical_system/        # Configurazione principale
│   │   ├── settings.py        # Configurazioni unificate
│   │   ├── urls.py           # URL routing principale
│   │   └── auth_views.py     # Autenticazione centralizzata
│   ├── core/                 # Modelli core del sistema
│   │   ├── models.py         # Doctor, Patient, Encounter
│   │   └── migrations/       # Migrazioni database
│   ├── api/                  # API REST
│   │   ├── views.py          # ViewSets API
│   │   ├── serializers.py    # Serializers unificati
│   │   └── urls.py          # URL API
│   ├── manage.py            # Django CLI
│   └── requirements.txt     # Dipendenze Python
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/       # Componenti React
│   │   │   ├── Auth/        # Login/Logout
│   │   │   ├── Dashboard/   # Dashboard principale
│   │   │   ├── Encounter/   # Gestione episodi
│   │   │   ├── Layout/      # Layout e navigazione
│   │   │   ├── Audio/       # Registrazione vocale
│   │   │   ├── Clinical/    # Editor dati clinici
│   │   │   └── Report/      # Anteprima report
│   │   ├── services/        # API client e stores
│   │   ├── App.jsx         # Componente principale
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Dipendenze Node.js
│   └── vite.config.js      # Configurazione Vite
│
└── README.md               # Questa documentazione
```

## ⚙️ Setup e Installazione

### Prerequisiti
- Python 3.9+
- Node.js 18+
- Git

### 🚀 AVVIO RAPIDO

#### ⚡ Metodo 1: Script automatico (Windows)
```bash
# Doppio click su START.bat oppure esegui:
START.bat
```

#### ⚡ Metodo 2: Setup manuale

**1. Clone del repository**
```bash
git clone <repository-url>
cd unified-medical-system
```

**2. Setup Backend**
```bash
cd backend

# Crea ambiente virtuale
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Installa dipendenze
pip install -r requirements.txt

# Esegui migrazioni
python manage.py migrate

# Crea superuser per admin
python manage.py createsuperuser

# Avvia server
python manage.py runserver
```

Il backend sarà disponibile su `http://localhost:8000`

**3. Setup Frontend**
```bash
cd frontend

# Installa dipendenze
npm install

# Avvia development server
npm run dev
```

Il frontend sarà disponibile su `http://localhost:5173`

### 🔗 Collegamenti Rapidi
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/
- **Admin Django**: http://localhost:8000/admin/

## 🔑 Autenticazione

Il sistema utilizza autenticazione personalizzata per medici:

### Endpoint API
- `POST /auth/login/` - Login medico
- `POST /auth/logout/` - Logout
- `GET /health/` - Health check

### Credenziali di test
Usa l'admin Django per creare utenti Doctor o usa:
```bash
python manage.py shell
from core.models import Doctor
doctor = Doctor.objects.create_user(
    username='dr.smith',
    password='password123',
    first_name='John',
    last_name='Smith',
    specialization='Emergency Medicine',
    department='Pronto Soccorso',
    is_emergency_doctor=True
)
```

## 📊 Modelli Dati

### Doctor
- ID medico univoco
- Dati anagrafici e credenziali
- Specializzazione e dipartimento
- Flag pronto soccorso

### Patient  
- ID paziente univoco
- Dati anagrafici completi
- Codice fiscale
- Contatti emergenza

### Encounter
- ID episodio univoco
- Associazione paziente-medico
- Data/ora ammissione e dimissione
- Priorità triage e stato
- Motivo principale accesso

## 🔧 API REST

### Endpoints principali
- `/api/doctors/` - Gestione medici
- `/api/patients/` - Gestione pazienti  
- `/api/encounters/` - Gestione episodi
- `/api/encounters/{id}/audio/` - Upload audio
- `/api/encounters/{id}/transcript/` - Trascrizione
- `/api/encounters/{id}/report/` - Generazione report

### Documentazione API
Accedi a `/api/docs/` per documentazione interattiva Swagger

## 🏃‍♂️ Comandi Utili

### Backend
```bash
# Test
python manage.py test

# Shell Django
python manage.py shell

# Colleziona file statici
python manage.py collectstatic

# Reset database (sviluppo)
rm db.sqlite3
python manage.py migrate
```

### Frontend
```bash
# Build produzione
npm run build

# Preview build
npm run preview

# Lint
npm run lint
```

## 🛠️ Sviluppo

### Aggiungere nuove funzionalità
1. **Backend**: Crea modelli in `core/models.py`, serializers in `api/serializers.py`, views in `api/views.py`
2. **Frontend**: Crea componenti in `src/components/`, servizi in `src/services/`
3. **Database**: Crea migrazioni con `python manage.py makemigrations`

### Testing
- Backend: Django Test Framework
- Frontend: Vitest + React Testing Library

### Configurazione CORS
Per sviluppo, CORS è configurato per accettare localhost. In produzione, aggiorna `CORS_ALLOWED_ORIGINS` in `settings.py`.

## 📝 Note Tecniche

- **CSRF disabilitato** per API REST (solo sviluppo)
- **Debug mode attivo** (ricorda di disabilitare in produzione)  
- **SQLite database** (migrabile a PostgreSQL per produzione)
- **File media** salvati in `/media/` (configurare storage per produzione)

## 🚀 Deploy Produzione

1. Imposta `DEBUG = False` in settings.py
2. Configura database PostgreSQL
3. Imposta variabili ambiente per secrets
4. Configura server web (nginx + gunicorn)
5. Abilita HTTPS e CSP headers
6. Configura monitoring e logging

## 🤝 Contribuire

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/nome-funzionalità`)
3. Commit modifiche (`git commit -am 'Aggiungi nuova funzionalità'`)
4. Push branch (`git push origin feature/nome-funzionalità`)
5. Crea Pull Request

## 📄 Licenza

Questo progetto è proprietario - tutti i diritti riservati.

## 📞 Supporto

Per supporto tecnico o domande:
- Email: [inserire email]
- Issues: [inserire URL repository]
- Documentazione: [inserire URL docs]

---

**Sistema Voice2Care** - Innovazione digitale per il Pronto Soccorso 🏥