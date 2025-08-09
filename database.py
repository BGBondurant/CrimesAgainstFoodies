import sqlite3

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
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_images (
            id INTEGER PRIMARY KEY,
            image_url TEXT NOT NULL,
            prompt TEXT NOT NULL,
            date TEXT NOT NULL UNIQUE
        )
    ''')


    # --- Add initial starter data from PF.csv ---
    import csv
    with open('PF.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        preparations_data = []
        foods_data = []
        for row in reader:
            if row[0]:
                preparations_data.append((row[0],))
            if row[1]:
                foods_data.append((row[1],))

    c.executemany('INSERT OR IGNORE INTO preparations (name) VALUES (?)', preparations_data)
    c.executemany('INSERT OR IGNORE INTO foods (name) VALUES (?)', foods_data)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    # First, delete the old corrupted database if it exists
    # Then, run this script to create a fresh one with data
    init_db()
    print("Database initialized and populated with starter data.")