# Deployment

The project has two deployment surfaces:

## Frontend

`app.py` and `ui.py` are the Streamlit frontend. They expose Account Analysis and Post Analysis tabs. `index.html` can be deployed to GitHub Pages as a static launch page.

## Backend

The Python modules and model artifacts are the backend. Run them with:

```bash
cp .env.example .env
bash run_app.sh
```

The launcher selects `.venv/bin/python` when it exists and otherwise uses `PYTHON_BIN` or `python`. Set `HOST` and `PORT` through `.env` or the environment. Online provider keys are optional and should be stored as deployment secrets, never committed.

GitHub Pages only serves the static frontend. Set the repository variable `STREAMLIT_APP_URL` to a separately hosted Streamlit URL so the launch button works.