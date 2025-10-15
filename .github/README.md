# GitHub Pages Configuration

This repository uses GitHub Actions to build and deploy documentation.

## Setup Instructions

1. Go to repository Settings > Pages
2. Set Source to "GitHub Actions" 
3. The documentation will be automatically built and deployed on push to main branch

## Documentation URL

https://praiselab-picuslab.github.io/ER-Voice2Text/

## Workflow

The documentation is built using:
- Sphinx for documentation generation
- GitHub Actions for CI/CD
- GitHub Pages for hosting

See `.github/workflows/documentation.yml` for the complete workflow.