# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath('../../backend'))

# Mock Django setup for documentation
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='dummy-secret-key-for-docs',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
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

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

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
    'display_version': True,
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
suppress_warnings = ['autodoc.import_error']
