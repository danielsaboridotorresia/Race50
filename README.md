# Race50 — Karting Telemetry Uploader and Analyzer

Race50 is a Django web application that lets drivers upload karting session CSV files and instantly see session summaries and lap-by-lap breakdowns. The app stores every upload, highlights best laps and theoretical best lap (TBL), computes a basic consistency metric, and lets you compare two sessions at the same track side-by-side. It includes authentication, a helpful CSV guide, and a clean Bootstrap-based UI.

## Distinctiveness and Complexity

Race50 is distinct from the course’s prior projects in both problem domain and technical approach:

- File upload and parsing pipeline: Users upload CSV files; the server performs rigorous validation (header presence, positive integers, lap time ranges, sector sum ± tolerance, consistent SessionID within file, binary detection, size limit). The code uses csv.Sniffer to auto-detect delimiters and robustly handle UTF-8 with BOM.
- Data modeling for telemetry: Custom models represent Sessions and Laps with proper indexing and a uniqueness constraint on (session, lap). A custom User model is configured and used as a foreign key owner for all data.
- Statistical summaries: On upload, the app computes summary stats (best/worst/avg lap, theoretical best lap from best sectors, and a consistency percentage using standard deviation), demonstrating domain-specific logic beyond CRUD.
- Session comparison workflow: A dedicated session view renders two sessions at the same track and displays their laps side-by-side with best-lap highlighting, enabling meaningful analysis.
- Template filters and global context: A custom template filter formats millisecond times as M:SS.mmm, and a global context processor surfaces the user’s last five sessions in the sidebar across pages.

These features go beyond straightforward CRUD pages and present a small but realistic data-processing workflow with non-trivial validation, transformation, and presentation layers.

## What’s in each file

- manage.py: Django entry point for local development.
- telemetry/settings.py: Django configuration, including custom user model, static files (WhiteNoise), and context processors.
- telemetry/urls.py: Project URL routing to the app.
- race50/models.py: Data model: User (custom auth), Session (per-upload summary), Lap (per-lap details) with indexes and constraints.
- race50/views.py: All views including upload (CSV validation + parsing + summary computation), index, sessions list, single session with comparison, guide, and auth flows.
- race50/urls.py: App URL routes (/, upload/, sessions, session/<id>, guide, auth).
- race50/templatetags/race50_extras.py: format_ms filter to render milliseconds as human-readable.
- Templates (race50/templates/race50/*.html):
  - layout.html: Base layout, sidebar with last five sessions, auth nav.
  - index.html: Welcome/overview and last-session card for logged-in users.
  - upload.html: Drag-and-drop upload UI and constraints notice.
  - session.html: Session summary and side-by-side comparison.
  - sessions.html: List of all user sessions.
  - guide.html: CSV upload guide with schema and rules.
  - login.html, register.html: Authentication pages.
- Static assets (race50/static/race50/...): CSS, JS (upload drag/drop handling), and illustrative images.
- requirements.txt: Python dependencies for local dev and deployment.

## How to run (Windows/PowerShell)

Prerequisites: Python 3.11+ recommended. Git optional.

```powershell
# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3) Apply migrations
python manage.py migrate

# 4) (Optional) Create a superuser for admin
python manage.py createsuperuser

# 5) Run the development server
python manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser.

- Register or log in.
- Use “Upload Sessions” to submit a CSV with header:
  SessionID,Track,Date,Lap,LapTime_ms,S1_ms,S2_ms,S3_ms,Notes
- In the project root you will find example csv files that you can use for this web app.
- After upload, you’ll be redirected to the session page. From there, select another session at the same track to compare.
- If you need help preparing the CSV, check the in-app Guide at /guide.

## Additional notes for staff

- The app is hosted on the following link: https://race50.onrender.com/race50/ as it's a free server the first few requests will be slower and the first one will have a loading screen. Hope the host of the page gives extra credit.
- CSV validation: The app rejects binary-like files, enforces .csv extension, and limits uploads to 10MB. LapTime_ms must be between 10s and 5min (10000–300000 ms), sectors must sum to LapTime_ms within ±2 ms, and SessionID must be consistent within a file. Rows missing required fields or with invalid numbers are skipped; if no valid rows remain, the upload fails with an error list.
- Computations: Average lap is rounded to an integer for storage. TBL is computed from best sector times. Consistency is (1 - stddev/mean) * 100.
- Data integrity: (session, lap) is unique. Sessions are owned by the authenticated user. The sidebar shows the last five sessions via a context processor.
- Static files: WhiteNoise is enabled for production; STATICFILES_STORAGE is configured. ALLOWED_HOSTS includes localhost and Render domains used during deployment testing.
- Authentication: Custom user model (race50.User) is active (AUTH_USER_MODEL). All data views (upload, session, sessions) are login-protected.
- Requirements: The file includes Django and deployment helpers (gunicorn, whitenoise, dj-database-url, python-dotenv, psycopg2-binary). pandas and matplotlib are included for potential future analysis/visualizations; the core app does not depend on them at runtime but they were part of exploratory work.
- Mobile usage: The app can run perfectly in mobile devices though depends on the device the contents (images or tables) will distortion a bit.

If you have any trouble running locally, try removing db.sqlite3 to start fresh, re-running migrations, and ensuring the virtual environment is active.

## Academic honesty

This README and the codebase are submitted in accordance with the course’s academic honesty policy. Some of the texts and images in this project have been created with AI but not a single line of code.
