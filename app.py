import flask
import sqlite3
from flask import jsonify, request, render_template
import os
import random
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

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

def generate_daily_image():
    """
    This function is run daily by the scheduler. It generates a new AI image
    based on a random food combination and saves it to the database.
    """
    # This function runs in a separate thread, so it needs its own app context
    # to access the database and other Flask features.
    with app.app_context():
        conn = get_db_connection()
        try:
            prep = conn.execute('SELECT name FROM preparations ORDER BY RANDOM() LIMIT 1').fetchone()
            food = conn.execute('SELECT name FROM foods ORDER BY RANDOM() LIMIT 1').fetchone()

            if not prep or not food:
                print("Could not generate image: not enough data in preparations or foods.")
                return

            prompt = f"A detailed, photorealistic image of {prep['name']} {food['name']}"

            # --- AI Image Generation Placeholder ---
            # In a real application, you would call an AI image generation API here
            # (e.g., DALL-E, Midjourney, Stability AI) with the 'prompt'.
            # For this example, we'll use a placeholder service (Unsplash)
            # that returns a random image based on keywords.
            image_url = f"https://source.unsplash.com/800x600/?{prep['name']},{food['name']}"

            today_str = date.today().isoformat()

            # The 'UNIQUE' constraint on the 'date' column prevents duplicates.
            conn.execute(
                'INSERT OR IGNORE INTO daily_images (image_url, prompt, date) VALUES (?, ?, ?)',
                (image_url, prompt, today_str)
            )
            conn.commit()
            print(f"Generated and saved daily image for prompt: {prompt}")
        except sqlite3.Error as e:
            print(f"Database error in generate_daily_image: {e}")
        finally:
            conn.close()

@app.route('/api/daily-image', methods=['GET'])
def get_daily_image():
    conn = get_db_connection()
    # Get the most recent image
    image_data = conn.execute('SELECT * FROM daily_images ORDER BY date DESC LIMIT 1').fetchone()
    conn.close()
    if image_data:
        return jsonify(dict(image_data))
    else:
        return jsonify({'error': 'No daily image found'}), 404

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
    # The scheduler should not run when the Flask reloader is active in debug mode.
    # This check ensures it only runs in the main process.
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # For initial testing, you might want to generate an image right away.
        generate_daily_image()
        scheduler = BackgroundScheduler()
        # Schedule the job to run every day at midnight.
        scheduler.add_job(func=generate_daily_image, trigger="cron", hour=0)
        scheduler.start()
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
    app.run(debug=True)