# Personal Notes App

A simple, local-first personal notes application for single-user use on a laptop. It enables users to create, view, edit, and delete notes, each comprising an ID, title, body, and creation timestamp. Notes are displayed in a list with the newest ones first, and the application aims to function primarily offline.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Setup and Run](#backend-setup-and-run)
- [Frontend Setup and Run](#frontend-setup-and-run)
- [Ports](#ports)
- [Environment Variables](#environment-variables)

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Node.js**: v18 or higher (includes npm)
-   **Python**: v3.9 or higher
-   **pip**: Python package installer
-   **git**: For cloning the repository (optional, if you download directly)

## Backend Setup and Run

The backend is built with FastAPI and uses SQLite for local data storage.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the FastAPI application**:
    ```bash
    uvicorn main:app --reload
    ```
    The backend API will be available at `http://localhost:8000`.

## Frontend Setup and Run

The frontend is a React application built with Vite.

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    # or yarn install
    ```

3.  **Run the development server**:
    ```bash
    npm run dev
    # or yarn dev
    ```
    The frontend application will be available at `http://localhost:5173`.

## Ports

-   **Backend API**: `http://localhost:8000`
-   **Frontend App**: `http://localhost:5173`

## Environment Variables

The frontend relies on an environment variable to connect to the backend API.

-   **`VITE_API_URL`**: Specifies the base URL for the backend API.
    -   **Default**: `http://localhost:8000`
    -   You can override this by creating a `.env` file in the `frontend/` directory (e.g., `frontend/.env`) with the following content:
        ```
        VITE_API_URL=http://localhost:8000
        ```
        (Replace `http://localhost:8000` if your backend runs on a different address/port).