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
    c.execute('DROP TABLE IF EXISTS suggestions')
    c.execute('''
        CREATE TABLE suggestions (
            id INTEGER PRIMARY KEY,
            item TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            date TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'food'
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
