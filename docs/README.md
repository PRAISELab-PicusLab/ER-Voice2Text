# Documentazione ER-Voice2Text

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