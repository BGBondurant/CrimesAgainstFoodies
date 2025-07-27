import sqlite3
from werkzeug.security import generate_password_hash

# Connect to the database (this will create the file if it doesn't exist)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create the users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    )
''')

# Create the submissions table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT NOT NULL,
        preparation_idea TEXT NOT NULL,
        submitted_by TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    )
''')

# Create a default admin user
admin_username = 'admin'
admin_password = 'password'  # In a real application, use a more secure password
hashed_password = generate_password_hash(admin_password)

# Check if the admin user already exists
cursor.execute("SELECT * FROM users WHERE username = ?", (admin_username,))
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                   (admin_username, hashed_password, 1))

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")
print("Admin user created with username 'admin' and password 'password'.")
