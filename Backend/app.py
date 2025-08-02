import flask
import sqlite3
from flask import jsonify, request, render_template

app = flask.Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('crimes.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('Admin/index.html')

@app.route('/api/preparations', methods=['GET'])
def get_preparations():
    conn = get_db_connection()
    preparations = conn.execute('SELECT * FROM preparations').fetchall()
    conn.close()
    return jsonify([dict(row) for row in preparations])

@app.route('/api/foods', methods=['GET'])
def get_foods():
    conn = get_db_connection()
    foods = conn.execute('SELECT * FROM foods').fetchall()
    conn.close()
    return jsonify([dict(row) for row in foods])

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    conn = get_db_connection()
    suggestions = conn.execute('SELECT * FROM suggestions').fetchall()
    conn.close()
    return jsonify([dict(row) for row in suggestions])

@app.route('/api/suggestions', methods=['POST'])
def add_suggestion():
    data = request.get_json()
    item = data.get('item')
    status = data.get('status')
    date = data.get('date')

    if not item or not status or not date:
        return jsonify({'error': 'Missing data'}), 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO suggestions (item, status, date) VALUES (?, ?, ?)',
                     (item, status, date))
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

    conn.close()
    return jsonify({'message': f'Suggestion "{item}" received.'}), 201

@app.route('/api/suggestions/approve', methods=['POST'])
def approve_suggestion():
    data = request.get_json()
    item_name = data.get('item')
    suggestion_id = data.get('id')

    if not item_name or not suggestion_id:
        return jsonify({'error': 'Missing item name or suggestion id'}), 400

    conn = get_db_connection()
    # Check if the item is a preparation or a food and add it to the correct table
    # This is a simplified logic. A more robust solution would be to have a way to distinguish them.
    # For now, we'll just add to foods as a default.
    conn.execute('INSERT OR IGNORE INTO foods (name) VALUES (?)', (item_name,))
    conn.execute('DELETE FROM suggestions WHERE id = ?', (suggestion_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Suggestion "{item_name}" approved and added to foods.'})

@app.route('/api/suggestions/reject', methods=['POST'])
def reject_suggestion():
    data = request.get_json()
    suggestion_id = data.get('id')

    if not suggestion_id:
        return jsonify({'error': 'Missing suggestion id'}), 400

    conn = get_db_connection()
    conn.execute('DELETE FROM suggestions WHERE id = ?', (suggestion_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Suggestion rejected.'})

@app.route('/api/suggestions/update', methods=['POST'])
def update_suggestion():
    data = request.get_json()
    suggestion_id = data.get('id')
    item = data.get('item')
    status = data.get('status')

    if not all([suggestion_id, item, status]):
        return jsonify({'error': 'Missing data for update'}), 400

    conn = get_db_connection()
    try:
        # Using a tuple for the parameters is crucial
        conn.execute('UPDATE suggestions SET item = ?, status = ? WHERE id = ?',
                     (item, status, suggestion_id))
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        # It's good practice to log the error as well
        print(f"Database error: {e}")
        return jsonify({'error': f'Database error: {e}'}), 500
    finally:
        # Ensure the connection is closed even if commit fails
        if conn:
            conn.close()

    return jsonify({'message': 'Suggestion updated successfully.'})

if __name__ == '__main__':
    app.run(debug=True)