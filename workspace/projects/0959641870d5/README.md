# Simple Web Calculator

A basic web-based calculator application that performs standard arithmetic operations (addition, subtraction, multiplication, division) and includes a clear function. This application is designed to operate entirely on the client-side, with all calculations performed in the browser.

## Summary

The Simple Web Calculator provides a straightforward user interface for basic arithmetic. It supports integers and floating-point numbers, handles division by zero errors, and allows users to clear the current input. As per the requirements, the application is purely client-side; the included backend structure serves as a placeholder to meet project architectural specifications but is not utilized by the calculator's functionality.

## Features

*   **Basic Arithmetic**: Perform addition, subtraction, multiplication, and division.
*   **Clear Function**: Reset the calculator display and state.
*   **Error Handling**: Displays "Error" for division by zero.
*   **Client-Side Only**: All calculations are performed in the browser; no backend interaction or history storage.
*   **Responsive UI**: Designed for desktop screen sizes.

## Technologies Used

### Frontend

*   **React 18**: JavaScript library for building user interfaces.
*   **Vite 5**: Next-generation frontend tooling for fast development.
*   **Tailwind CSS**: A utility-first CSS framework for styling.

### Backend (Placeholder)

*   **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
*   **SQLAlchemy 2**: Python SQL toolkit and Object Relational Mapper.
*   **Pydantic v2**: Data validation and settings management using Python type hints.
*   **SQLite**: A C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine.

**Note**: The backend components (FastAPI, SQLAlchemy, Pydantic, SQLite) are included to fulfill the full-stack project structure requirement but are not actively used by the calculator application, which operates entirely on the client-side.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Node.js** (LTS version recommended) & **npm** (or yarn)
*   **Python 3.8+** & **pip**

## Getting Started

Follow these steps to set up and run the application locally.

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/simple-web-calculator.git
cd simple-web-calculator
```

### 2. Frontend Setup

Navigate to the `frontend` directory, install dependencies, and start the development server.

```bash
cd frontend
npm install
npm run dev
```

The frontend application will typically be available at `http://localhost:5173`.

### 3. Backend Setup (Optional - Placeholder)

Navigate to the `backend` directory, install dependencies, and start the FastAPI server.

```bash
cd ../backend
pip install -r requirements.txt
python main.py
```

The backend API will typically be available at `http://localhost:8000`.
**Important**: As mentioned, the backend is a placeholder and does not provide any functionality for the calculator. The frontend does not make any API calls to it.

## Usage

1.  Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2.  Click the number buttons to input your first number.
3.  Click an operator button (+, -, \*, /).
4.  Click the number buttons to input your second number.
5.  Click the `=` button to see the result.
6.  Click the `C` button to clear the display and start a new calculation.

## Project Structure

```
simple-web-calculator/
├── backend/
│   ├── database.py         # SQLAlchemy database configuration (placeholder)
│   ├── main.py             # FastAPI application entry point (placeholder)
│   ├── models.py           # SQLAlchemy ORM models (placeholder)
│   ├── requirements.txt    # Python dependencies
│   └── schemas.py          # Pydantic schemas (placeholder)
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── package.json        # Frontend dependencies and scripts
│   ├── postcss.config.js   # PostCSS configuration for Tailwind
│   ├── public/             # Static assets
│   ├── src/
│   │   ├── api.js          # Placeholder for API calls (empty)
│   │   ├── App.jsx         # Root React component
│   │   ├── components/
│   │   │   ├── Button.jsx  # Reusable calculator button
│   │   │   ├── Calculator.jsx # Main calculator logic and UI
│   │   │   └── Display.jsx # Calculator display screen
│   │   ├── main.jsx        # React entry point
│   │   └── styles.css      # Main stylesheet (includes Tailwind directives)
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   └── vite.config.js      # Vite configuration
└── README.md               # Project overview and instructions
```