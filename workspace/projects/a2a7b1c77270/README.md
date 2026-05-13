# Team Todo App

A collaborative todo application for teams to manage tasks within projects. Users can create projects, define custom task statuses, and add tasks with details like assignees and due dates. The application also provides basic metrics on task completion times. The backend is built with FastAPI and SQLAlchemy, and the frontend is a single-page application using React and Vite.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [API Endpoints](#api-endpoints)

## Prerequisites

Before you begin, ensure you have the following installed:

-   **Python 3.9+**: For the FastAPI backend.
-   **pip**: Python package installer (usually comes with Python).
-   **Node.js (LTS)**: For the React frontend.
-   **npm** or **Yarn**: Node.js package manager (npm comes with Node.js).

## Getting Started

Follow these steps to get the application up and running on your local machine.

### Backend Setup

The backend is a FastAPI application that uses SQLAlchemy with an SQLite database.

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a Python virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    -   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    -   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the FastAPI application:**
    ```bash
    uvicorn main:app --reload --port 8000
    ```
    The backend server will start at `http://localhost:8000`. The SQLite database file (`app.db`) will be created automatically in the `backend/` directory upon the first run.

### Frontend Setup

The frontend is a React application built with Vite.

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install the Node.js dependencies:**
    ```bash
    npm install
    # OR
    yarn install
    ```

3.  **Run the React development server:**
    ```bash
    npm run dev
    # OR
    yarn dev
    ```
    The frontend application will typically open in your browser at `http://localhost:5173`.

    **Note on API URL:**
    The frontend expects the backend API to be available at the URL specified by the `VITE_API_URL` environment variable. If not set, it defaults to `http://localhost:8000`. If your backend is running on a different host or port, create a `.env` file in the `frontend/` directory:
    ```
    VITE_API_URL=http://your-backend-host:your-backend-port
    ```

## API Endpoints

The following API endpoints are available:

| Method | Path                                  | Purpose                                                              |
| :----- | :------------------------------------ | :------------------------------------------------------------------- |
| `GET`  | `/api/users`                          | List all users, primarily for populating assignee dropdowns.         |
| `GET`  | `/api/projects`                       | List all available projects.                                         |
| `POST` | `/api/projects`                       | Create a new project.                                                |
| `GET`  | `/api/projects/{project_id}`          | Get detailed information for a single project, including its associated tasks and statuses. |
| `POST` | `/api/projects/{project_id}/tasks`    | Create a new task within a specific project.                         |
| `PUT`  | `/api/tasks/{task_id}`                | Update an existing task's details, such as its status, assignee, or description. |
| `DELETE`| `/api/tasks/{task_id}`               | Delete a task.                                                       |
| `POST` | `/api/projects/{project_id}/statuses` | Create a new custom status for a specific project.                   |
| `GET`  | `/api/tasks/{task_id}/comments`       | List all comments for a specific task.                               |
| `POST` | `/api/tasks/{task_id}/comments`       | Add a new comment to a specific task.                                |
| `GET`  | `/api/projects/{project_id}/metrics`  | Calculate and retrieve completion metrics (e.g., average cycle time) for a project. |