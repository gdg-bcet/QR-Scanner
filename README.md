# QR Scanner (FastAPI)

QR-based T-shirt pickup tracker backed by Google Sheets.

## Local Run

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` from `.env.example` and fill values.
4. For local auth, place Google service account file as `credentials.json` in project root.
5. Start server:

   ```bash
   uvicorn main:app --reload
   ```

## Push To GitHub

This repository already has `origin` configured. To push current files:

```bash
git add .
git commit -m "Initial app setup with Render deployment config"
git push origin main
```

## Deploy On Render

The repository includes `render.yaml` for Blueprint deploy.

1. Push code to GitHub.
2. In Render: `New +` -> `Blueprint`.
3. Select this repository.
4. Set required environment variables in Render:
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_CREDENTIALS` (paste full JSON content of your service account file)
   - `SHEET_NAME` (optional, default is `Sheet1`)

Render will build with `pip install -r requirements.txt` and start with:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Security Notes

- Do not commit secret files.
- `credentials.json`, `gmail_credentials.json`, and `token.json` are git-ignored.
