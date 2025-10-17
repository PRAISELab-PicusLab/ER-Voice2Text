# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath('../../backend'))

# Mock Django setup for documentation
import django
from django.conf import settings
from unittest.mock import MagicMock
import sys

# Mock delle unità di reportlab
class MockMM:
    def __mul__(self, other):
        return other * 2.834645669  # conversione mm to points
    def __rmul__(self, other):
        return other * 2.834645669

# Mock module per reportlab.lib.units
mock_units = MagicMock()
mock_units.mm = MockMM()
sys.modules['reportlab.lib.units'] = mock_units

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='dummy-secret-key-for-docs',
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'core',
            'api',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
        # Aggiungiamo le impostazioni mancanti per evitare errori
        NVIDIA_API_KEY='dummy-key-for-docs',
        NVIDIA_BASE_URL='https://dummy-url-for-docs',
        NVIDIA_MODEL='dummy-model-for-docs',
        MONGODB_URL='mongodb://dummy-for-docs',
        MEDIA_ROOT='/tmp/dummy-media',
        STATIC_ROOT='/tmp/dummy-static',
        STATIC_URL='/static/',
        MEDIA_URL='/media/',
        AUTH_USER_MODEL='core.Doctor',
    )

try:
    django.setup()
except Exception as e:
    print(f"Warning: Django setup failed: {e}")

# -- Project information -----------------------------------------------------
project = 'ER-Voice2Text'
copyright = '2025, PRAISELab-PicusLab'
author = 'PRAISELab-PicusLab'
release = '1.0.0'
version = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Language settings
language = 'en'
locale_dirs = ['locale/']   # path is example but recommended.
gettext_compact = False     # optional.

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

# Configurazioni per gestire meglio i moduli problematici
autoclass_content = 'both'
autodoc_inherit_docstrings = True
autodoc_member_order = 'bysource'

# Permetti di continuare anche con errori di importazione
autodoc_warningiserror = False

# Forza la documentazione di tutti i membri, inclusi quelli decorati
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

autodoc_mock_imports = [
    'mongoengine',
    'openai',
    'transformers',
    'torch',
    'librosa',
    'whisper',
    'numpy',
    'PIL',
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.styles',
    'reportlab.lib.colors',
    'reportlab.pdfgen',
    'reportlab.platypus',
    'pyaudio',
    'webrtcvad',
    'environ',
    'django_environ',
    'corsheaders',
    'rest_framework',
    'rest_framework.decorators',
    'rest_framework.response',
    'rest_framework.permissions',
    'rest_framework.parsers',
    'rest_framework.status',
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_theme_options = {
    'analytics_id': '',
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

html_context = {
    "display_github": True,
    "github_user": "PRAISELab-PicusLab", 
    "github_repo": "ER-Voice2Text",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}

html_title = f"{project} v{release}"

# Suppress warnings for mock imports
suppress_warnings = [
    'autodoc.import_error', 
    'ref.python',
    'autodoc.mock_object',
    'autodoc.autodoc_mock',
]

# Configurazione per evitare i warning sui cross-reference duplicati
nitpicky = False
nitpick_ignore = [
    ('py:class', 'AudioTranscript'),
    ('py:class', 'ClinicalData'),
    ('py:class', 'ClinicalReport'),
]

# Gestione dei mock objects e decoratori
autodoc_mock_imports.extend([
    'rest_framework.decorators.api_view',
    'rest_framework.decorators.permission_classes',
    'rest_framework.decorators.parser_classes',
])

# Ignora errori di signature per decoratori complessi
autodoc_preserve_defaults = True
