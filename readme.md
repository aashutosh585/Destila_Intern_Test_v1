# Architecture — Mini Exception Inbox

This repository contains the implementation of the **Mini Exception Inbox**, a system designed to ingest daily manufacturing plans and actual production outputs, calculate production deficit exceptions, and present them in a responsive dashboard and monitoring UI.

### 🔗 Live Deployments
* **Unified Application (Frontend & API)**: [https://destila-intern-test-v1-pqh1.vercel.app/](https://destila-intern-test-v1-pqh1.vercel.app/)
  * *Note: Vercel routes `/api/*` requests to the serverless Python backend service, and all other routes to the static React frontend.*

---

## System Overview

The system consists of three main stages:
1. **Data Ingestion & Materialization**: An ETL script parses raw production CSVs, normalizes date formats and product IDs, detects production deficits (where actual units < 90% of planned units), and saves them to a relational SQLite database.
2. **REST API (FastAPI)**: Serves endpoints for retrieving statistics, listing and filtering exceptions (sorted by severity and worst deficit), fetching historical 7-day trends, and persisting user status changes (Acknowledge / Resolve).
3. **Frontend Dashboard (React + Vite)**: A single-page dashboard designed for operators to review anomalies, visualize 7-day moving trends, and resolve issues in real time.

---

## Architecture Diagram

```
                 ┌────────────────────────────────────────────────────────┐
                 │                       DATA LAYER                       │
                 │  ┌──────────────┐                  ┌────────────────┐  │
                 │  │  Production  │                  │  Production    │  │
                 │  │  Plan CSV    │                  │  Actuals CSV   │  │
                 │  └──────┬───────┘                  └───────┬────────┘  │
                 └─────────┼──────────────────────────────────┼───────────┘
                           │                                  │
                           └─────────────────┬────────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │  Ingestion & ETL Pipeline │
                               │   (scripts/ingest_data)   │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │                    RELATIONAL DATABASE                 │
                 │       ┌──────────┐             ┌────────────────┐      │
                 │       │ Raw Data │             │  Cleaned Data  │      │
                 │       │  Tables  │             │     Tables     │      │
                 │       └──────────┘             └───────┬────────┘      │
                 │                                        │               │
                 │                                        ▼               │
                 │                              ┌──────────────────┐      │
                 │                              │ Exceptions Table │      │
                 │                              └─────────┬────────┘      │
                 └────────────────────────────────────────┼───────────────┘
                                                          │
                                                          ▼
                 ┌────────────────────────────────────────────────────────┐
                 │                      FastAPI API                       │
                 │  GET /exceptions  │  GET /exceptions/{id}  │  PATCH   │
                 └──────────────────────────────┬─────────────────────────┘
                                                │
                                                ▼
                 ┌────────────────────────────────────────────────────────┐
                 │              REACT + VITE CLIENT FRONTEND              │
                 │     • Summary Dashboard      • Timeline Exceptions     │
                 └────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Selection Rationale |
|-------|-----------|--------|
| **Database** | SQLite | Serverless, zero setup, and self-contained. Fully portable for grading. |
| **Backend** | FastAPI + SQLAlchemy | High-performance Python ASGI framework. Auto-generates interactive Swagger documentation. |
| **Frontend** | React (Vite) + TailwindCSS | Fast development loop, efficient state management, and modern, utilities-first styling. |
| **Icons** | Lucide React | Modern, clean vector graphics for UI elements. |
| **Hosting** | Vercel | Seamless multi-project services deployment (monorepo), running React static files and FastAPI serverless functions in tandem. |

---

## Database Schema

```
 raw_plan             raw_production
    │                        │
    └───► clean_plan ◄───────┘
               │
               ▼
        clean_production
               │
               ▼
          exceptions ◄───► exception_status_history
```

* **Raw Data Tables (`raw_plan`, `raw_production`)**: Preserves the exact, untampered historical datasets for audits.
* **Cleaned Tables (`clean_plan`, `clean_production`)**: Standardizes formats, maps column fields, converts product codes to uppercase, and handles mixed dates.
* **Exceptions Table (`exceptions`)**: Caches materialized exceptions, storing planned units, actual units, production ratio, deficit units, status, and severity.
* **Status History Table (`exception_status_history`)**: Records audit history for status changes (e.g. changing status from `open` to `acknowledged` or `resolved`).

---

## Key Design Decisions & Features

1. **SQLite Replication for Serverless `/tmp`**:
   * *The Problem*: Vercel serverless runtimes are read-only. Standard SQLite files in the root folder will crash with write-permissions errors when mutating status.
   * *The Solution*: In [database.py](backend/app/database.py), the backend replicates the pre-populated `internship.db` to `/tmp/internship.db` when running on Vercel. Since `/tmp` is writable, operations run cleanly.
2. **Double-Mount Routing**:
   * To simplify development and production routing, the FastAPI app mounts its exception and dashboard routers twice: both at the root level (e.g., `/exceptions`) and with an `/api` prefix (e.g., `/api/exceptions`). This makes local development cross-origin compatible and avoids path translation errors when passing through Vercel's rewrite proxies.
3. **State Preservation**:
   * Re-running the data pipeline script does not wipe out your operator status configurations. It preserves existing statuses (e.g., keeping previously resolved items as `resolved`) using upsert logic.

---

## Project Structure

```
├── backend/                             # Python Backend Application
│   ├── app/
│   │   ├── routers/                     # Route endpoints (Exceptions, Dashboard)
│   │   ├── crud.py                      # SQLAlchemy DB query controllers
│   │   ├── database.py                  # DB setup & Vercel /tmp replication helper
│   │   ├── models.py                    # Relational SQLAlchemy model definitions
│   │   └── schemas.py                   # Pydantic schemas (serialization/validation)
│   ├── data/                            # Raw Ingestion Source CSVs
│   ├── scripts/
│   │   └── ingest_data.py               # Ingestion ETL & Exception Engine
│   ├── tests/                           # Pytest units
│   ├── internship.db                    # Bundled database template
│   ├── run_pipeline.py                  # Pipeline execution script
│   ├── vercel.json                      # Vercel Serverless Function build settings
│   └── requirements.txt                 # Backend dependency list
│
├── frontend/                            # Vite React App
│   ├── src/
│   │   ├── assets/                      # Image & svg vectors
│   │   ├── App.css                      # Global and component stylesheets
│   │   ├── App.jsx                      # Main UI Controller & Views
│   │   ├── api.js                       # Axios setup & API hooks (handles prod/dev URL)
│   │   └── main.jsx                     # Application entry point
│   ├── package.json                     # NodeJS scripts and package list
│   └── vite.config.js                   # Vite presets
│
├── vercel.json                          # Monorepo multi-project service routing
└── README.md                            # System documentation
```

---

## Running the Project Locally

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the ETL script to parse data and generate the local SQLite database:
   ```bash
   python run_pipeline.py
   ```
5. Start the FastAPI local server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The API will be available at `http://localhost:8000`. Interactive docs can be accessed at `http://localhost:8000/docs`.*

### 2. Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run the development build:
   ```bash
   npm run dev
   ```
   *The frontend client will spin up at `http://localhost:5173`.*
