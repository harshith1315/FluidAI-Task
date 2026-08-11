import os

import psycopg2
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, session, url_for


# Load environment variables
load_dotenv()


app = Flask(__name__)

# Application configuration
app.secret_key = os.getenv("SECRET_KEY")


# PostgreSQL configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_db_connection():
    """Create and return a PostgreSQL database connection."""

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


@app.route("/")
def home():
    """Redirect users to the login page."""

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, username
                FROM users
                WHERE username = %s AND password = %s
                """,
                (username, password)
            )

            user = cursor.fetchone()

            cursor.close()
            connection.close()

            if user:
                session["username"] = user[1]

                return redirect(url_for("dashboard"))

            error = "Invalid username or password"

        except Exception as e:

            print(f"Database error: {e}")

            error = "Unable to connect to database"

    return render_template(
        "login.html",
        error=error
    )


@app.route("/dashboard")
def dashboard():
    """Display the dashboard for authenticated users."""

    if "username" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        username=session["username"]
    )


@app.route("/logout")
def logout():
    """Log the user out."""

    session.clear()

    return redirect(url_for("login"))


@app.route("/health")
def health():
    """
    Kubernetes liveness endpoint.

    This only verifies that the Flask application
    process is running.
    """

    return {
        "status": "healthy"
    }, 200


@app.route("/ready")
def ready():
    """
    Kubernetes readiness endpoint.

    This verifies that the application can
    successfully communicate with PostgreSQL.
    """

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("SELECT 1")

        cursor.fetchone()

        return {
            "status": "ready",
            "database": "connected"
        }, 200

    except Exception as e:

        print(f"Readiness check failed: {e}")

        return {
            "status": "not ready",
            "database": "disconnected"
        }, 503

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )