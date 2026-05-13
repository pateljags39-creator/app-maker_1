# Stock Analyst Analyzer MVP

A financial research application that allows users to filter by sector and market to discover top-rated analysts, view their stock recommendations, and evaluate company solvency metrics through a four-tab report interface.

## Tech Stack

- **Frontend:** React 18, Vite 5, JavaScript, CSS (Modern Minimalist Theme)
- **Backend:** FastAPI, Python 3.9+
- **Database/ORM:** SQLite, SQLAlchemy 2, Pydantic v2

## Prerequisites

- Node.js (v18 or newer recommended)
- Python 3.9 or newer
- pip (Python package manager)

## Setup & Running Locally

### Backend Setup

The backend runs on **port 8000** by default.

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the backend server:
   ```bash
   python main.py
   ```
   *The SQLite database (`app.db`) will be automatically created on the first run.*

### Frontend Setup

The frontend runs on **port 5173** by default.

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the required dependencies:
   ```bash
   npm install
   ```
3. Environment Configuration:
   The frontend expects the backend API at `http://localhost:8000`. You can override this by creating a `.env` file in the `frontend` directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```

## Application Structure

- `backend/main.py`: Entry point for the FastAPI application and API router definition.
- `backend/database.py`: SQLAlchemy setup, engine, and Base definition.
- `backend/models.py`: Database schema definitions.
- `backend/schemas.py`: Pydantic models for request/response validation.
- `frontend/src/App.jsx`: Main React application component.
- `frontend/src/styles.css`: Global CSS containing the theme variables and styling rules.
- `frontend/src/api.js`: Axios/Fetch wrapper for communicating with the backend.