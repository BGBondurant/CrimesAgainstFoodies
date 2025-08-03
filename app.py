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
    return render_template('main.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

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
    item_type = data.get('type', 'food')  # Default to 'food'

    if not all([item, status, date, item_type]):
        return jsonify({'error': 'Missing data'}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO suggestions (item, status, date, type) VALUES (?, ?, ?, ?)',
                     (item, status, date, item_type))
        new_id = cursor.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

    new_suggestion = {
        'id': new_id,
        'item': item,
        'status': status,
        'date': date,
        'type': item_type
    }
    return jsonify(new_suggestion), 201

@app.route('/api/suggestions/check_duplicates', methods=['POST'])
def check_duplicates():
    data = request.get_json()
    suggestion_text = data.get('text', '')
    words = suggestion_text.lower().split()

    if not words:
        return jsonify({'duplicates': []})

    conn = get_db_connection()
    duplicates = []

    # Using a set to avoid redundant checks for the same word
    for word in set(words):
        # Check in foods
        food_match = conn.execute('SELECT name FROM foods WHERE LOWER(name) = ?', (word,)).fetchone()
        if food_match:
            duplicates.append({'word': word, 'list': 'foods'})

        # Check in preparations
        prep_match = conn.execute('SELECT name FROM preparations WHERE LOWER(name) = ?', (word,)).fetchone()
        if prep_match:
            duplicates.append({'word': word, 'list': 'preparations'})

    conn.close()
    return jsonify({'duplicates': duplicates})

@app.route('/api/suggestions/approve', methods=['POST'])
def approve_suggestion():
    data = request.get_json()
    item_name = data.get('item')
    suggestion_id = data.get('id')
    item_type = data.get('type')  # 'foods' or 'preparations'

    if not all([item_name, suggestion_id, item_type]):
        return jsonify({'error': 'Missing data: item, id, and type are required.'}), 400

    if item_type not in ['foods', 'preparations']:
        return jsonify({'error': 'Invalid item type specified.'}), 400

    conn = get_db_connection()
    try:
        conn.execute(f'INSERT OR IGNORE INTO {item_type} (name) VALUES (?)', (item_name,))
        conn.execute('DELETE FROM suggestions WHERE id = ?', (suggestion_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

    return jsonify({'message': f'Suggestion "{item_name}" approved and added to {item_type}.'})

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