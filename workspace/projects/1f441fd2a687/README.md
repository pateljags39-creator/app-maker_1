# Web Calculator Pro

Web Calculator Pro is a full-stack web application that provides a simple yet powerful calculator. It supports basic arithmetic, advanced functions like square root and percentage, and memory controls. The application features a persistent history of calculations, storing data from the user's last three sessions in a backend database, which is accessible through a clean, modern interface.

## Features

*   **Basic Arithmetic**: Perform addition, subtraction, multiplication, and division.
*   **Advanced Functions**: Includes percentage (%), square root (√), and sign change (+/-).
*   **Memory Controls**: M+ (Memory Add), M- (Memory Subtract), MR (Memory Recall), MC (Memory Clear).
*   **Clear Options**: Separate functions for Clear Entry (CE) and Clear All (C).
*   **Persistent History**: Stores and retrieves calculation history for the last three user sessions.
*   **Error Handling**: Displays clear text messages for invalid operations (e.g., division by zero).
*   **Responsive Design**: Modern and clean user interface.

## Tech Stack

### Frontend
*   **React 18**: A JavaScript library for building user interfaces.
*   **Vite 5**: A fast build tool for modern web projects.
*   **JavaScript**: The primary programming language.
*   **Tailwind CSS**: A utility-first CSS framework for rapid UI development.
*   **Axios**: Promise-based HTTP client for the browser and Node.js.
*   **UUID**: For generating unique session IDs.

### Backend
*   **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.9+.
*   **Python 3.9+**: The primary programming language.
*   **SQLAlchemy 2**: The Python SQL toolkit and Object Relational Mapper.
*   **SQLite**: A lightweight, file-based SQL database.
*   **Pydantic v2**: Data validation and settings management using Python type hints.
*   **Uvicorn**: An ASGI web server for Python.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Node.js**: LTS version recommended (includes npm).
    *   [Download Node.js](https://nodejs.org/)
*   **Python 3.9+**:
    *   [Download Python](https://www.python.org/downloads/)

## Setup and Run

Follow these steps to get the Web Calculator Pro application up and running on your local machine.

### 1. Clone the Repository

```bash
git clone <repository_url>
cd web-calculator-pro
```

### 2. Backend Setup

The backend API runs on `http://localhost:8000`.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```

2.  **Create and activate a Python virtual environment**:
    ```bash
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install backend dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the FastAPI application**:
    ```bash
    uvicorn main:app --reload
    ```
    The backend server will start, and the SQLite database file (`app.db`) will be created in the `backend/` directory. You should see output indicating that the server is running, typically on `http://127.0.0.1:8000`.

### 3. Frontend Setup

The frontend application runs on `http://localhost:5173` (Vite's default development port).

1.  **Open a new terminal window** and navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```

2.  **Install frontend dependencies**:
    ```bash
    npm install
    # or yarn install
    # or pnpm install
    ```

3.  **Configure API Base URL (Optional but Recommended)**:
    The frontend expects the backend API URL to be available via `import.meta.env.VITE_API_URL`. By default, it falls back to `http://localhost:8000`. If your backend runs on a different host or port, create a `.env` file in the `frontend/` directory:
    ```
    VITE_API_URL=http://localhost:8000
    ```
    Adjust the URL if your backend is not running on `http://localhost:8000`.

4.  **Run the frontend development server**:
    ```bash
    npm run dev
    # or yarn dev
    # or pnpm dev
    ```
    The frontend development server will start. Open your web browser and navigate to the URL displayed in the terminal (e.g., `http://localhost:5173`).

## API Endpoints

The backend provides the following API endpoints:

*   **`POST /api/calculations`**:
    *   **Purpose**: Save a new calculation to the history.
    *   **Request Body**: JSON object containing `sessionId`, `expression`, and `result`.
*   **`GET /api/calculations?session_ids=id1,id2,...`**:
    *   **Purpose**: Retrieve calculation history for a list of specified session IDs.
    *   **Query Parameter**: `session_ids` (comma-separated string of session IDs).

## Environment Variables

### Frontend
*   `VITE_API_URL`: Specifies the base URL for the backend API. Defaults to `http://localhost:8000` if not set. This should be defined in a `.env` file in the `frontend/` directory.

## Ports

*   **Backend**: `http://localhost:8000`
*   **Frontend**: `http://localhost:5173` (default for Vite development server)