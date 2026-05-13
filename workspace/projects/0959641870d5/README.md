# Simple Web Calculator

This is a client-side web application that provides a basic calculator for arithmetic operations. It supports addition, subtraction, multiplication, and division, and includes a clear function. All calculations are performed in the browser without any backend interaction or data persistence, as per the business requirements.

## Features

*   Perform addition, subtraction, multiplication, and division.
*   Clear button to reset the current calculation.
*   Handles both integers and floating-point numbers.
*   Displays 'Error' for division by zero.
*   Displays 'Error' for invalid input or results exceeding display limits.
*   Follows standard mathematical order of operations (PEMDAS).
*   Operates entirely on the client-side with no backend interaction for calculations.
*   No history of calculations is stored.
*   User interface with a display area and clickable buttons.
*   Designed for desktop screen sizes only (no responsive design).
*   Does not support keyboard input.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Node.js** (LTS version recommended) and **npm** (comes with Node.js) or **Yarn**.
*   **Python 3.9+** and **pip**.

## Getting Started

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd simple-web-calculator
    ```

2.  **Frontend Setup:**

    The frontend is a React application built with Vite and styled with Tailwind CSS.

    *   **Navigate to the frontend directory:**
        ```bash
        cd frontend
        ```

    *   **Install dependencies:**
        ```bash
        npm install
        # or yarn install
        ```

    *   **Run the development server:**
        This will start the Vite development server, typically on `http://localhost:5173`.
        ```bash
        npm run dev
        # or yarn dev
        ```

    *   **Build for production:**
        ```bash
        npm run build
        # or yarn build
        ```
        You can then preview the production build using `npm run preview`.

3.  **Backend Setup (Boilerplate):**

    The backend is a FastAPI application. **Note:** This application is primarily client-side. The backend is included as boilerplate for a full-stack project structure but is not actively used for the calculator's core functionality.

    *   **Navigate to the backend directory:**
        ```bash
        cd ../backend
        ```

    *   **Create and activate a virtual environment (recommended):**
        ```bash
        python -m venv venv
        # On Windows:
        # .\venv\Scripts\activate
        # On macOS/Linux:
        source venv/bin/activate
        ```

    *   **Install dependencies:**
        ```bash
        pip install -r requirements.txt
        ```

    *   **Run the development server:**
        This will start the FastAPI server, typically on `http://localhost:8000`.
        ```bash
        uvicorn main:app --reload
        ```
        Deactivate the virtual environment when done: `deactivate`

## Ports

*   **Frontend:** `http://localhost:5173` (default Vite development server port)
*   **Backend:** `http://localhost:8000` (default FastAPI/Uvicorn port)

## Environment Variables

*   **Frontend:**
    *   `VITE_API_URL`: Specifies the base URL for API requests. Defaults to `http://localhost:8000` if not set.
        Example in a `.env` file (in the `frontend/` directory):
        ```
        VITE_API_URL=http://localhost:8000
        ```
        *Note: For this client-side calculator, the frontend does not make API calls, so this variable is not strictly necessary for functionality but is included for standard project setup.*