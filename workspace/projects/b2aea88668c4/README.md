# Personal Notes App

A simple personal notes application for a single user, enabling creation, listing, viewing, editing, and deletion of notes. All data is stored locally using SQLite, prioritizing offline functionality without user accounts or multi-device synchronization.

## Features

- Create new notes with a title and body.
- View a list of all notes, sorted by creation date (newest first).
- View the full details of a specific note.
- Edit existing notes.
- Delete notes permanently.
- All data stored locally in SQLite (`app.db`).
- Designed for single-user, offline functionality.

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Node.js** (LTS version recommended) and **npm** (or Yarn) for the frontend.
-   **Python 3.8+** and **pip** for the backend.

## Getting Started

Follow these steps to set up and run the application.

### 1. Backend Setup

The backend is built with FastAPI and SQLAlchemy (SQLite).

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```

2.  (Optional but Recommended) Create and activate a Python virtual environment:
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  Run the FastAPI server:
    ```bash
    uvicorn main:app --reload
    ```
    The backend API will be available at `http://localhost:8000/api`. A `app.db` file will be created in the `backend/` directory to store your notes.

### 2. Frontend Setup

The frontend is built with React and Vite.

1.  Open a new terminal window and navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```

2.  Install the Node.js dependencies:
    ```bash
    npm install
    # or
    yarn install
    ```

3.  Start the Vite development server:
    ```bash
    npm run dev
    # or
    yarn dev
    ```
    The frontend application will typically open in your browser at `http://localhost:5173`.

### Environment Variables

**Frontend:**

-   `VITE_API_URL`: Specifies the base URL for the backend API.
    -   **Default:** `http://localhost:8000`
    -   If your backend is running on a different port or host, create a `.env` file in the `frontend/` directory and set this variable:
        ```
        VITE_API_URL=http://localhost:8000
        ```
        (No need to change if backend runs on default `8000`)

**Backend:**

-   No specific environment variables are required. The SQLite database `app.db` is created in the `backend/` directory by default.

## Usage

Once both the backend and frontend servers are running:

1.  Open your web browser and go to `http://localhost:5173` (or the address shown by Vite).
2.  You can then start creating, viewing, editing, and deleting your personal notes.