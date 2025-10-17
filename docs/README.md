# ER-Voice2Text Documentation

This folder contains the complete technical documentation for the ER-Voice2Text project, automatically generated using Sphinx with comprehensive API documentation.

## 📚 Documentation Overview

The ER-Voice2Text system provides an integrated solution for Emergency Department medical workflows, combining:

- **Voice Transcription**: Automatic speech-to-text using Whisper models
- **Clinical AI**: Intelligent extraction of medical entities using NVIDIA NIM
- **Workflow Management**: Complete patient episode tracking and management
- **Report Generation**: Automated PDF medical reports
- **REST API**: Full API suite for integration and development

## 📁 Documentation Structure

- `source/` - Sphinx documentation source files (`.rst` format)
- `build/html/` - Generated HTML documentation (English)
- `make.bat` - Windows build script
- `generate_docs.bat` - Automated generation script with fixes
- `api_fix.py` - Auto-fix script for medical workflow documentation

## 🚀 Quick Start

### View Documentation
Open the generated documentation:
```bash
start build\html\index.html
```

Or view online: [https://praiselab-picuslab.github.io/ER-Voice2Text/](https://praiselab-picuslab.github.io/ER-Voice2Text/)

### Regenerate Documentation
```bash
.\generate_docs.bat
```

This script will:
1. Activate virtual environment
2. Clean previous build
3. Regenerate RST files from code
4. Apply medical workflow fixes
5. Generate English documentation
6. Apply GitHub Pages compatibility

## 📖 Documentation Sections

### Core Modules
- **`core`** - Django models (Doctor, Patient, Encounter, etc.)
- **`api`** - REST API endpoints and serializers
- **`services`** - AI services (Whisper, NVIDIA NIM, MongoDB, PDF generation)
- **`medical_system`** - Main Django configuration

### API Documentation
The API documentation includes detailed information about:

#### Medical Workflow Endpoints
- **Patient Management**: List, create, update patient records
- **Audio Processing**: Voice recording and transcription
- **Clinical Extraction**: AI-powered medical entity extraction
- **Report Generation**: Automated PDF medical reports
- **Analytics**: Dashboard data and statistics

#### Authentication & Security
- Doctor authentication system
- Session management
- API permissions and access control

#### Data Models
- Complete model relationships
- Field descriptions and validation
- Migration history

## 🛠️ Technical Setup

### Prerequisites
- Python 3.9+ with virtual environment
- Sphinx documentation system
- All project dependencies installed

### Dependencies
The documentation generation requires:
```
sphinx
sphinx-rtd-theme
sphinx-autodoc-typehints
django
djangorestframework
mongoengine
```

### Environment Configuration
The documentation system includes mock configurations for:
- Django settings
- External AI services (NVIDIA NIM, Whisper)
- Database connections (SQLite, MongoDB)
- Report generation libraries

## 🔧 Advanced Usage

### Manual Generation
For manual control over the process:

1. **Activate environment**:
```bash
..\.venv\Scripts\activate
```

2. **Clean build**:
```bash
.\make.bat clean
```

3. **Generate RST files**:
```bash
sphinx-apidoc -o ./source ../backend -f --module-first
```

4. **Apply fixes**:
```bash
python api_fix.py
```

5. **Build HTML**:
```bash
.\make.bat html
```

### Customization
- **Themes**: Current theme is `sphinx_rtd_theme`
- **Language**: Documentation is generated in English
- **Modules**: All backend modules are included with proper exclusions
- **Cross-references**: Configured to handle Django/MongoDB model duplicates

## 🌐 GitHub Pages Integration

### Automatic Deployment
Documentation is automatically deployed to GitHub Pages via workflow:
- **Trigger**: Push to main branch or manual dispatch
- **Build**: Ubuntu with Python 3.9
- **Output**: Available at GitHub Pages URL

### Workflow Features
- Dependency management with proper mocking
- Consistent build process with local generation
- Verification checks for English language and content
- Error handling and build success validation

## 🔍 Troubleshooting

### Common Issues

#### Import Errors
If you see Django import errors:
- Ensure virtual environment is activated
- Check all dependencies are installed
- Verify Django settings configuration

#### Missing Functions
If API functions don't appear:
- Run `python api_fix.py` to apply medical workflow fixes
- Check exclude patterns in module configurations
- Verify decorator compatibility with Sphinx

#### Build Warnings
The system is configured to handle warnings gracefully:
- Mock objects for external dependencies
- Suppress warnings for known issues
- Continue build process despite minor warnings

### Debug Mode
For detailed build information, run:
```bash
sphinx-build -v -b html source build/html
```

## 📚 Content Organization

### Backend Modules Documentation
- **Models**: Complete Django model documentation with relationships
- **API Views**: All REST endpoints with request/response examples
- **Services**: AI service integration and processing pipelines
- **Authentication**: Security and access control systems

### Code Quality
- **Type Hints**: Full type annotation support
- **Docstrings**: Comprehensive function and class documentation
- **Examples**: Usage examples and code samples
- **Cross-references**: Linked references between modules

## 🚀 Deployment Notes

### Production Documentation
For production deployment:
1. Ensure all secrets are properly mocked
2. Verify external service dependencies are handled
3. Test build process in clean environment
4. Validate all links and references

### Performance Optimization
- Build caching enabled for faster regeneration
- Selective module loading to reduce build time
- Optimized asset management for web delivery

---

## 📞 Support

For documentation issues:
- Check troubleshooting section above
- Verify build process follows the automated script
- Ensure all dependencies match requirements
- Create issue in repository for persistent problems

**Complete technical documentation for the ER-Voice2Text Emergency Department management system.**

Questa cartella contiene la documentazione Sphinx del progetto ER-Voice2Text.

## Struttura

- `source/`: File sorgenti RST per Sphinx
- `build/`: Output generato (ignorato da Git)
- `requirements.txt`: Dipendenze Python per la generazione documentazione

## Generazione locale

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

2. Genera i file API:
```bash
sphinx-apidoc -o ./source ../backend -f --module-first
```

3. Builda la documentazione:
```bash
make html  # Linux/Mac
# oppure
make.bat html  # Windows
```

4. Apri `build/html/index.html` nel browser

## Deploy automatico

La documentazione viene automaticamente generata e pubblicata su GitHub Pages tramite GitHub Actions quando si fa push sul branch `main`.

## Configurazione GitHub Pages

Per abilitare la pubblicazione automatica:

1. Vai nelle Settings del repository GitHub
2. Sezione "Pages" 
3. Source: "GitHub Actions"
4. La documentazione sarà disponibile su: https://praiselab-picuslab.github.io/ER-Voice2Text/

## Troubleshooting

Se la documentazione non si aggiorna:

1. Controlla che GitHub Actions sia abilitato
2. Verifica che GitHub Pages sia configurato per usare "GitHub Actions"
3. Controlla i log del workflow nella tab "Actions"
4. Assicurati che il file `.nojekyll` sia presente nella root del repo