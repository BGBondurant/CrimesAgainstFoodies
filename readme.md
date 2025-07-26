# Crimes Against Foodies

A fun project that generates interesting food combinations.

---

## Features

* **Random Food Combination Generator:** Generates random combinations of food items and preparation methods.
* **Themed Generators:** Users can select a theme (e.g., "Desserts," "Seafood") to get more specific food combinations.
* **Suggestion Box:** Users can suggest new food items and preparation methods.
* **Admin Panel:** An admin panel to approve or reject user suggestions.

---

## Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python, Flask, SQLAlchemy
* **Database:** SQLite

---

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/BGBondurant/CrimesAgainstFoodies.git
    cd CrimesAgainstFoodies
    ```

2.  **Install the backend dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Create and populate the database:**
    ```bash
    python backend/populate_database.py
    ```

4.  **Run the Flask application:**
    ```bash
    python backend/app.py
    ```

    Keep this terminal running. You should see output indicating the server is active at `http://127.0.0.1:5000/`.

5.  **Open the website:**
    In your web browser, navigate to `http://127.0.0.1:5000/`.

## Admin Panel

To access the admin panel, Alt+Click on the logo on the main page. The admin panel allows you to:

* View dashboard statistics.
* View and approve or reject user suggestions.
