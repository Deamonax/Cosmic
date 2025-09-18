# JobFit MVP

JobFit is a mock full stack application that demonstrates how a job matching workflow could look. The stack uses a Next.js frontend, a FastAPI backend, and a Postgres database, all orchestrated with Docker Compose. Every AI feature is mocked so the project can run completely offline.

## Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable WSL 2 integration during setup.
2. Install Node.js 20 LTS from [nodejs.org](https://nodejs.org/) and confirm `node -v` returns a 20.x release.
3. Install Python 3.12 from the Microsoft Store or python.org. Confirm `python --version` returns 3.12.x.
4. Install Git for Windows and enable the option to use Git from the Windows Command Prompt.
5. Ensure WSL is installed and that you have a default Linux distribution configured.

## Getting Started

```powershell
# Clone the repository
 git clone https://example.com/jobfit.git
 cd jobfit

# Start all services
 docker compose up --build
```

Once the containers are healthy:

- Visit [http://localhost:3000](http://localhost:3000) to load the web app. The landing page reports whether the API is reachable.
- Visit [http://localhost:3000/demo](http://localhost:3000/demo) to try the mock AI actions. Each button triggers a fetch to the FastAPI backend and displays pretty printed mock JSON.
- Visit [http://localhost:8000/healthz](http://localhost:8000/healthz) to view the backend health check response.

Stop the stack with `Ctrl + C` in the terminal and run `docker compose down` when you are done.

## Environment Configuration

Docker Compose sets the following key environment variables:

- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` for the web container.
- `DATABASE_URL=postgresql+psycopg://jobfit:jobfit@db:5432/jobfit` for the API container.
- `POSTGRES_USER=jobfit`, `POSTGRES_PASSWORD=jobfit`, and `POSTGRES_DB=jobfit` for the database container.

The backend exposes a feature flag in `api/config.py` named `USE_LIVE_OPENAI`. It defaults to `False` and is not used yet. All services currently rely on local mock JSON data.

## Running Tests Locally

You can run frontend and backend tests outside Docker:

```powershell
# In the web directory
 npm install
 npm run lint
 npm run test

# In the api directory
 python -m venv .venv
 .venv\\Scripts\\activate
 pip install -r requirements.txt
 pytest
```

On Linux shells replace the activation command with `source .venv/bin/activate`.

## Troubleshooting on Windows

- **Port already in use**: Close applications that may be listening on ports 3000 or 8000, or edit `docker-compose.yml` to expose different ports before running `docker compose up`.
- **Long path errors**: Enable long paths in Windows by running `git config --global core.longpaths true` and ensure `LongPathsEnabled` is set to `1` under `HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\FileSystem`.
- **WSL integration issues**: Open Docker Desktop settings, verify that your default WSL distro is checked under Resources > WSL Integration, then restart Docker Desktop.
- **File sharing problems**: If file mounts fail, run Docker Desktop as Administrator and ensure your project directory is inside your user profile.

## Repository Layout

```
jobfit/
├── README.md
├── docker-compose.yml
├── web/
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── globals.css
│       │   ├── page.tsx
│       │   └── demo/
│       │       └── page.tsx
│       └── lib/
│           └── api.ts
└── api/
    ├── Dockerfile
    ├── requirements.txt
    ├── pytest.ini
    ├── main.py
    ├── config.py
    ├── routers/
    │   ├── __init__.py
    │   └── core.py
    ├── services/
    │   ├── __init__.py
    │   └── gpt_service.py
    ├── mocks/
    │   ├── jd_analysis.json
    │   ├── fit_assessment.json
    │   ├── cv_rewrite.json
    │   └── qa.json
    └── tests/
        ├── __init__.py
        ├── test_health.py
        └── test_endpoints.py
```

## Continuous Integration

GitHub Actions runs the following workflow on each push:

- Frontend: `npm ci` followed by `npm test` in the `web` directory.
- Backend: `pip install -r requirements.txt` followed by `pytest` in the `api` directory.

## Mock Data Source

The backend ships with four JSON files under `api/mocks`. The `DummyGptService` class loads these files and serves them to the API routes. There are no external AI calls in this project.

Enjoy exploring the JobFit MVP!
