import sqlite3
import json

def init_db():
    conn = sqlite3.connect('crimes.db')
    c = conn.cursor()

    # Create tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS preparations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY,
            item TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            date TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def populate_db():
    conn = sqlite3.connect('crimes.db')
    c = conn.cursor()

    # Populate preparations and foods from PF.json
    with open('PF.json', 'r') as f:
        data = json.load(f)
        for preparation in data['Preperation']:
            c.execute("INSERT OR IGNORE INTO preparations (name) VALUES (?)", (preparation,))
        for food in data['Food']:
            c.execute("INSERT OR IGNORE INTO foods (name) VALUES (?)", (food,))

    # Populate suggestions from temp.json
    with open('temp.json', 'r') as f:
        suggestions = json.load(f)
        for suggestion in suggestions:
            c.execute("INSERT OR IGNORE INTO suggestions (item, status, date) VALUES (?, ?, ?)",
                      (suggestion['item'], suggestion['status'], suggestion['date']))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    populate_db()
    print("Database initialized and populated.")
