# ER-Voice2Text - Unified Medical System

Unified system for managing clinical records in the Emergency Department with automatic voice transcription and artificial intelligence.

## 📚 Documentation

**📖 [Complete documentation available here](https://praiselab-picuslab.github.io/ER-Voice2Text/)**

The documentation includes:
- Complete API Reference
- Developer Guide
- System Architecture
- Usage Examples

---

## 🏥 Features

- **Secure authentication** for Emergency Department doctors
- **Real-time dashboard** for patient and episode management
- **Voice recording** and automatic transcription
- **Automatic extraction** of structured clinical data
- **Automated PDF report** generation
- **Complete REST APIs** for integration

## 🚀 Technologies

### Backend
- **Django 4.2.7** with Django REST Framework
- **SQLite** database (easily migrable to PostgreSQL)
- **Python 3.9+** with ML/AI support

### Frontend
- **React 18** with Vite
- **Bootstrap Italia** for compliant UI/UX
- **React Query** for API state management
- **React Router** for navigation

### AI Services
- **NVIDIA NIM** for clinical entity extraction
- **Whisper** for speech-to-text transcription
- **MongoDB** for unstructured data storage
- **Named Entity Recognition** for medical text analysis

## 📁 Project Structure

```
ER-Voice2Text/
├── backend/                    # Django Backend
│   ├── medical_system/        # Main configuration
│   │   ├── settings.py        # Unified configurations
│   │   ├── urls.py           # Main URL routing
│   │   └── wsgi.py           # WSGI application
│   ├── core/                 # Core system models
│   │   ├── models.py         # Doctor, Patient, Encounter
│   │   ├── mongodb_models.py # MongoDB models for AI data
│   │   └── migrations/       # Database migrations
│   ├── api/                  # REST API
│   │   ├── views.py          # API ViewSets
│   │   ├── medical_workflow_views.py # Medical workflow endpoints
│   │   ├── serializers.py    # Unified serializers
│   │   └── urls.py          # API URLs
│   ├── services/             # AI and Integration Services
│   │   ├── whisper_service.py    # Audio transcription
│   │   ├── nvidia_nim.py         # LLM clinical extraction
│   │   ├── clinical_extraction.py # Clinical data processing
│   │   ├── pdf_report.py         # PDF report generation
│   │   └── mongodb_service.py    # MongoDB integration
│   ├── auth_views.py        # Centralized authentication
│   ├── manage.py            # Django CLI
│   └── requirements.txt     # Python dependencies
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Auth/        # Login/Logout
│   │   │   ├── Dashboard/   # Main dashboard
│   │   │   ├── Encounter/   # Episode management
│   │   │   ├── Layout/      # Layout and navigation
│   │   │   ├── Audio/       # Voice recording
│   │   │   ├── Clinical/    # Clinical data editor
│   │   │   └── Report/      # Report preview
│   │   ├── services/        # API client and stores
│   │   ├── App.jsx         # Main component
│   │   └── main.jsx        # Entry point
│   ├── package.json        # Node.js dependencies
│   └── vite.config.js      # Vite configuration
│
├── docs/                     # Technical Documentation
│   ├── source/              # Sphinx documentation source
│   ├── build/html/          # Generated HTML documentation
│   ├── generate_docs.bat    # Documentation generation script
│   └── README.md           # Documentation guide
│
└── README.md               # This documentation
```

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git

### 🚀 QUICK START

#### ⚡ Method 1: Automatic script (Windows)
```bash
# Double click on START.bat or run:
START.bat
```

#### ⚡ Method 2: Manual setup

**1. Repository clone**
```bash
git clone <repository-url>
cd ER-Voice2Text
```

**2. Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser

# Start server
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

**3. Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 🔗 Quick Links
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/

### 🤖 AI Services Configuration

#### NVIDIA NIM (Optional)
For enhanced clinical entity extraction:
```bash
# Set environment variables in backend/.env
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=openai/gpt-oss-20b
```

#### MongoDB (Optional)
For advanced analytics and unstructured data:
```bash
# Set environment variable
MONGODB_URL=mongodb://localhost:27017/medical_system
```

The system works with fallback modes if these services are not configured.
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

## 🔑 Authentication

The system uses custom authentication for doctors:

### API Endpoints
- `POST /auth/login/` - Doctor login
- `POST /auth/logout/` - Logout
- `GET /health/` - Health check

### Test Credentials
Use Django admin to create Doctor users or use:
```bash
python manage.py shell
from core.models import Doctor
doctor = Doctor.objects.create_user(
    username='dr.smith',
    password='password123',
    first_name='John',
    last_name='Smith',
    specialization='Emergency Medicine',
    department='Emergency Department',
    is_emergency_doctor=True
)
```

## 📊 Data Models

### Doctor
- Unique doctor ID
- Personal data and credentials
- Specialization and department
- Emergency department flag

### Patient  
- Unique patient ID
- Complete personal data
- Tax code (Italian fiscal code)
- Emergency contacts

### Encounter
- Unique episode ID
- Patient-doctor association
- Admission and discharge date/time
- Triage priority and status
- Main reason for access

### AudioTranscript
- Audio file metadata
- Transcription text
- Processing status
- Timestamps

### ClinicalData
- Extracted medical entities
- Structured clinical information
- Processing method (LLM/NER)
- Confidence scores

## 🔧 REST API

### Main Endpoints
- `/api/doctors/` - Doctor management
- `/api/patients/` - Patient management  
- `/api/encounters/` - Episode management

### Medical Workflow Endpoints
- `/api/process-audio-visit/` - Audio processing and transcription
- `/api/transcripts/{id}/extract-clinical/` - Clinical data extraction
- `/api/transcripts/{id}/generate-pdf/` - PDF report generation
- `/api/transcripts/{id}/download-pdf/` - Report download
- `/api/dashboard/analytics/` - Analytics data
- `/api/interventions/` - Intervention management

### API Documentation
Access `/api/docs/` for interactive Swagger documentation

## 🏃‍♂️ Useful Commands

### Backend
```bash
# Test
python manage.py test

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Reset database (development)
rm db.sqlite3
python manage.py migrate

# Create demo data
python manage.py create_demo_data
```

### Frontend
```bash
# Production build
npm run build

# Preview build
npm run preview

# Lint
npm run lint
```

### Documentation
```bash
# Generate technical documentation
cd docs
.\generate_docs.bat

# View documentation
start build\html\index.html
```

## 🛠️ Development

### Adding New Features
1. **Backend**: Create models in `core/models.py`, serializers in `api/serializers.py`, views in `api/views.py`
2. **Frontend**: Create components in `src/components/`, services in `src/services/`
3. **Database**: Create migrations with `python manage.py makemigrations`
4. **AI Services**: Add new services in `services/` directory

### Testing
- Backend: Django Test Framework
- Frontend: Vitest + React Testing Library

### CORS Configuration
For development, CORS is configured to accept localhost. In production, update `CORS_ALLOWED_ORIGINS` in `settings.py`.

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

## 📝 Technical Notes

- **CSRF disabled** for REST API (development only)
- **Debug mode active** (remember to disable in production)  
- **SQLite database** (migrable to PostgreSQL for production)
- **Media files** saved in `/media/` (configure storage for production)
- **AI Services** have fallback modes when external services are unavailable
- **Real-time features** implemented with WebSocket connections

## 🚀 Production Deployment

1. Set `DEBUG = False` in settings.py
2. Configure PostgreSQL database
3. Set environment variables for secrets
4. Configure web server (nginx + gunicorn)
5. Enable HTTPS and CSP headers
6. Configure monitoring and logging
7. Set up proper CORS and security headers
8. Configure static file serving
9. Set up backup strategies for database and media files

### Environment Variables for Production
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/dbname
NVIDIA_API_KEY=your-nvidia-key  # Optional
MONGODB_URL=mongodb://host:port/db  # Optional
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/feature-name`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push branch (`git push origin feature/feature-name`)
5. Create Pull Request

## 📄 License

This project is proprietary - all rights reserved.

## 📞 Support

For technical support or questions:
- Documentation: [https://praiselab-picuslab.github.io/ER-Voice2Text/](https://praiselab-picuslab.github.io/ER-Voice2Text/)
- Issues: Create an issue in the repository
- Repository: [https://github.com/PRAISELab-PicusLab/ER-Voice2Text](https://github.com/PRAISELab-PicusLab/ER-Voice2Text)

---

**ER-Voice2Text System** - Digital Innovation for Emergency Departments 🏥

*Transforming emergency medicine through intelligent voice transcription and AI-powered clinical data extraction.*