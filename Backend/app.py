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

if __name__ == '__main__':
    app.run(debug=True)