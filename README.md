# NeoIA Security Monorepo

Monorepo com tres frentes:

- `apps/web`: frontend React/Vite
- `apps/api`: API Python para Bedrock, tickets e governanca
- `apps/streamlit`: MVP original em Streamlit mantido como fallback

## Docker

Para subir o stack principal de desenvolvimento:

```powershell
docker compose up --build
```

Depois abra:

- `http://localhost:5173`
- `http://localhost:8000/health`

O compose sobe somente `apps/web` e `apps/api`. O `apps/streamlit` fica fora do stack principal.

## Frontend local

```powershell
npm install --prefix apps/web
npm run dev:web
```

## Backend API local

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r apps/api/requirements.txt
python apps/api/main.py
```

## Streamlit legado

```powershell
pip install -r apps/streamlit/requirements.txt
streamlit run apps/streamlit/app.py
```
