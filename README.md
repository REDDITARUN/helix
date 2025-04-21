# Helix Agent

This document provides instructions for setting up and running the Helix agent, which consists of a Flask backend and a React/TypeScript frontend.

## Setup Instructions

Follow the steps below to get the Helix project up and running on your local machine.

### Backend Setup

1.  **Navigate to the Backend Directory:**
    ```bash
    cd helix-backend
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate   # On Windows
    ```

3.  **PostgreSQL Prerequisites:**
    Ensure you have PostgreSQL installed on your system.

4.  **Create the PostgreSQL Database:**
    Create a database named `helix_db` in your PostgreSQL instance.

5.  **Database User and Password:**
    For this project, the database user is `helix_user` and the password is `1123`. The database is assumed to be running on `localhost` at the default port `5432`.

    **Important:** You can choose a different password, but you **must** update the `.env` file in the `helix-backedn` directory with your chosen password and database URL.

6.  **Configure API Keys:**
    * Obtain an API key from Gemini and set it in your `.env` file.
    * Obtain a Pinecone API key and set it in your `.env` file.

7.  **Install Dependencies:**
    Navigate to the `helix-backedn` directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```

8.  **Initialize Flask Database Migrations:**
    ```bash
    flask db init
    ```

9.  **Run Initial Database Migration:**
    ```bash
    flask db migrate -m "Initial migration"
    ```

10. **Upgrade the Database:**
    ```bash
    flask db upgrade
    ```

11. **Run the Backend:**
    ```bash
    python run.py
    ```
    Your backend server will now be running. Check your terminal for the specific address (usually `http://127.0.0.1:5000/`).

### Frontend Setup

1.  **Navigate to the Frontend Directory:**
    Open a new terminal window and navigate to the `helix-frontend` directory:
    ```bash
    cd helix-frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Run the Frontend Development Server:**
    ```bash
    npm run dev
    ```
    Your React frontend will now be running. Check your terminal for the local development server URL (usually `http://localhost:5173/` or similar). You can access the application in your web browser using this URL.

You are now ready to use the Helix project!