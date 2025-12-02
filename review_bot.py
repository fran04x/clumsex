name: 'Actualizador Clumsex (Blindado)'

on:
  schedule:
    - cron: '*/5 * * * *'
  workflow_dispatch:

jobs:
  auto_update:
    runs-on: ubuntu-latest
    
    permissions:
      contents: write # ¡CRÍTICO!
      
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Libs
        run: pip install google-genai

      - name: Debug Previo
        run: |
          echo "=== ARCHIVOS ANTES DEL SCRIPT ==="
          ls -la
          echo "=== ESTADO GIT ==="
          git status

      - name: Run Bot
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python review_bot.py

      - name: Debug Post-Script
        run: |
          echo "=== ARCHIVOS DESPUES DEL SCRIPT ==="
          # Verificamos si la fecha cambió en el archivo (Linux timestamp)
          ls -l "clumsex v12.2 stable.py"
          echo "=== DIFERENCIAS GIT ==="
          git diff

      - name: Force Commit & Push
        run: |
          git config --global user.name 'Gemini Bot'
          git config --global user.email 'bot@noreply.github.com'
          
          # Agregamos usando comillas simples para proteger los espacios
          git add 'clumsex v12.2 stable.py'
          
          # Commit forzado
          git commit -m "chore: [AUTO-UPDATE] Nueva versión detectada"
          
          # PUSH EXPLÍCITO A MAIN (Esto soluciona el "no hace nada")
          git push origin HEAD:main
