# Scientific Calculator

A full-stack scientific calculator application featuring a React frontend and a FastAPI backend with SQLite persistence. The frontend provides basic and advanced mathematical functions, memory operations, a calculation history, a responsive dark-mode UI, and comprehensive accessibility features including keyboard input and screen reader support. The backend is responsible for persisting the calculator's memory register and calculation history, ensuring data is retained across user sessions.

## Features

- **Basic Arithmetic:** Addition, subtraction, multiplication, division.
- **Scientific Functions:** Sine, cosine, tangent (DEG/RAD mode toggle), common logarithm (log), natural logarithm (ln), square (x²), square root (√x), arbitrary exponentiation (xʸ), factorial (x!), constants (π, e).
- **Memory Functions:** M+, M-, MR, MC with persistence across sessions.
- **Calculation History:** Keeps a log of past operations, persisted across sessions.
- **Order of Operations:** Supports PEMDAS/BODMAS.
- **Responsive Design:** Works well on various screen sizes.
- **Dark Mode:** Modern, accessible dark theme.
- **Accessibility:** Keyboard navigation and screen reader support.
- **Persistence:** Calculator memory and history are saved using a FastAPI backend and SQLite database.

## Technologies Used

### Frontend
- **React 18:** JavaScript library for building user interfaces.
- **Vite 5:** Fast build tool for modern web projects.
- **CSS:** For styling and responsive design.

### Backend
- **FastAPI:** Modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- **Pydantic v2:** Data validation and settings management using Python type hints.
- **SQLAlchemy 2:** SQL toolkit and Object-Relational Mapper (ORM).
- **SQLite:** Lightweight, file-based SQL database.
- **Uvicorn:** ASGI server for running FastAPI.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (LTS version, e.g., 18.x or 20.x) & **npm** (comes with Node.js) or **yarn**.
- **Python 3.9+**
- **pip** (Python package installer)

## Getting Started

Follow these steps to set up and run the application locally.

### 1. Clone the repository

```bash
git clone <repository_url>
cd scientific-calculator
```

### 2. Backend Setup and Run

Navigate to the `backend` directory:

```bash
cd backend
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Run the FastAPI backend server:

```bash
uvicorn main:app --reload --port 8000
```

The backend server will start at `http://localhost:8000`. It will create an `app.db` SQLite database file in the `backend` directory automatically.

### 3. Frontend Setup and Run

Open a new terminal and navigate to the `frontend` directory:

```bash
cd ../frontend
```

Install the Node.js dependencies:

```bash
npm install
# OR
# yarn install
```

Start the React development server:

```bash
npm run dev
# OR
# yarn dev
```

The frontend application will typically open in your browser at `http://localhost:5173`.

### Accessing the Application

- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000/api`

The frontend is configured to communicate with the backend at `http://localhost:8000` by default. This URL is set via the `VITE_API_URL` environment variable.

## Environment Variables

### Frontend (`.env` file in `frontend` directory)
- `VITE_API_URL`: The base URL of your backend API.
  - Default value: `http://localhost:8000`
  - Example: `VITE_API_URL=http://localhost:8000`

### Backend
No explicit environment variables are strictly required for the database as it uses a local SQLite file (`app.db`).

## API Endpoints

The backend provides the following API endpoints under the `/api` prefix:

- **GET `/api/calculator-state`**
  - **Purpose:** Retrieve the persisted memory register and calculation history.
  - **Response:** JSON object containing `memory_register` (float) and `history_log` (JSON string).

- **POST `/api/calculator-state`**
  - **Purpose:** Save the current memory register and calculation history.
  - **Request Body:** JSON object with `memory_register` (float) and `history_log` (JSON string).
  - **Response:** The saved `PersistentCalculatorData` object.