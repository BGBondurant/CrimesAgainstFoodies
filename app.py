from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in a real application

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    submissions = conn.execute("SELECT * FROM submissions WHERE status = 'approved'").fetchall()
    conn.close()
    return render_template('index.html', submissions=submissions)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        food_name = request.form['food_name']
        preparation_idea = request.form['preparation_idea']
        submitted_by = request.form['submitted_by']

        conn = get_db_connection()
        conn.execute("INSERT INTO submissions (food_name, preparation_idea, submitted_by) VALUES (?, ?, ?)",
                     (food_name, preparation_idea, submitted_by))
        conn.commit()
        conn.close()
        flash('Your submission has been received and is pending approval.')
        return redirect(url_for('index'))
    return render_template('submit.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin_redirect():
    if 'is_admin' in session and session['is_admin']:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    pending_submissions = conn.execute("SELECT * FROM submissions WHERE status = 'pending'").fetchall()
    conn.close()
    return render_template('admin_dashboard.html', submissions=pending_submissions)

@app.route('/admin/approve/<int:submission_id>')
def approve_submission(submission_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("UPDATE submissions SET status = 'approved' WHERE id = ?", (submission_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/decline/<int:submission_id>')
def decline_submission(submission_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("UPDATE submissions SET status = 'declined' WHERE id = ?", (submission_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage')
def manage_content():
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    approved_submissions = conn.execute("SELECT * FROM submissions WHERE status = 'approved'").fetchall()
    conn.close()
    return render_template('admin_manage.html', submissions=approved_submissions)

@app.route('/admin/edit/<int:submission_id>', methods=['GET', 'POST'])
def edit_submission(submission_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    submission = conn.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,)).fetchone()

    if request.method == 'POST':
        food_name = request.form['food_name']
        preparation_idea = request.form['preparation_idea']
        conn.execute('UPDATE submissions SET food_name = ?, preparation_idea = ? WHERE id = ?',
                     (food_name, preparation_idea, submission_id))
        conn.commit()
        conn.close()
        return redirect(url_for('manage_content'))

    conn.close()
    return render_template('edit_submission.html', submission=submission)

@app.route('/admin/delete/<int:submission_id>')
def delete_submission(submission_id):
    if 'is_admin' not in session or not session['is_admin']:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_content'))

if __name__ == '__main__':
    app.run(debug=True)
