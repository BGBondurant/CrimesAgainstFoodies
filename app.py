import os
from datetime import date, timedelta, datetime
from functools import wraps
from flask import Flask, jsonify, request, render_template, g, Response
from sqlalchemy import desc, asc, func

from database import SessionLocal, DailyImage, Preparation, Food, Suggestion
from tasks import tasks_bp

app = Flask(__name__)
app.register_blueprint(tasks_bp)

# --- Database Session Management ---
@app.before_request
def before_request():
    g.db = SessionLocal()

@app.teardown_appcontext
def teardown_appcontext(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Authentication ---
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        admin_user = os.environ.get('ADMIN_USERNAME')
        admin_pass = os.environ.get('ADMIN_PASSWORD')
        if auth and auth.username == admin_user and auth.password == admin_pass:
            return f(*args, **kwargs)
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated

# --- Frontend Routes ---
@app.route('/')
def home():
    # Query for the most recent daily image
    latest_image = g.db.query(DailyImage).order_by(desc(DailyImage.generation_date)).first()
    image_url = latest_image.public_url if latest_image else None
    return render_template('main.html', image_url=image_url)

@app.route('/archive/')
@app.route('/archive/<date_str>')
def archive(date_str=None):
    current_image = None
    prev_date_str = None
    next_date_str = None

    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD.", 400
    else:
        # If no date is specified, default to the latest image's date
        latest_image = g.db.query(DailyImage).order_by(desc(DailyImage.generation_date)).first()
        target_date = latest_image.generation_date if latest_image else date.today()

    # Get the image for the target date
    current_image = g.db.query(DailyImage).filter_by(generation_date=target_date).first()

    # Find previous and next image dates for navigation
    if current_image:
        prev_image = g.db.query(DailyImage.generation_date).filter(DailyImage.generation_date < target_date).order_by(desc(DailyImage.generation_date)).first()
        if prev_image:
            prev_date_str = prev_image[0].isoformat()

        next_image = g.db.query(DailyImage.generation_date).filter(DailyImage.generation_date > target_date).order_by(asc(DailyImage.generation_date)).first()
        if next_image:
            next_date_str = next_image[0].isoformat()

    # Get all unique dates for the dropdown
    all_dates_query = g.db.query(DailyImage.generation_date).order_by(desc(DailyImage.generation_date)).all()
    all_dates = [d[0].isoformat() for d in all_dates_query]

    return render_template('archive.html',
                           image=current_image,
                           prev_date=prev_date_str,
                           next_date=next_date_str,
                           all_dates=all_dates,
                           current_date=target_date.isoformat())

@app.route('/admin')
@auth_required
def admin():
    return render_template('admin.html')


# --- API Routes (Refactored to use SQLAlchemy) ---
def serialize(model_instance):
    """A simple serializer for our models."""
    return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}

@app.route('/api/preparations', methods=['GET'])
def get_preparations():
    preparations = g.db.query(Preparation).all()
    return jsonify([serialize(p) for p in preparations])

@app.route('/api/foods', methods=['GET'])
def get_foods():
    foods = g.db.query(Food).all()
    return jsonify([serialize(f) for f in foods])

@app.route('/api/suggestions', methods=['GET'])
@auth_required
def get_suggestions():
    suggestions = g.db.query(Suggestion).order_by(desc(Suggestion.id)).all()
    return jsonify([serialize(s) for s in suggestions])

@app.route('/api/suggestions', methods=['POST'])
@auth_required
def add_suggestion():
    data = request.get_json()
    if not data or not all(k in data for k in ['item', 'status', 'date', 'type']):
        return jsonify({'error': 'Missing data'}), 400

    new_suggestion = Suggestion(**data)
    g.db.add(new_suggestion)
    g.db.commit()
    return jsonify(serialize(new_suggestion)), 201

@app.route('/api/suggestions/check_duplicates', methods=['POST'])
@auth_required
def check_duplicates():
    data = request.get_json()
    suggestion_text = data.get('text', '').lower()
    words = set(suggestion_text.split())
    duplicates = []

    if not words:
        return jsonify({'duplicates': []})

    for word in words:
        if g.db.query(Food).filter(func.lower(Food.name) == word).first():
            duplicates.append({'word': word, 'list': 'foods'})
        if g.db.query(Preparation).filter(func.lower(Preparation.name) == word).first():
            duplicates.append({'word': word, 'list': 'preparations'})

    return jsonify({'duplicates': duplicates})

@app.route('/api/suggestions/approve', methods=['POST'])
@auth_required
def approve_suggestion():
    data = request.get_json()
    suggestion_id = data.get('id')
    item_type = data.get('type') # 'food' or 'preparation'
    item_name = data.get('item')

    if not all([suggestion_id, item_type, item_name]):
        return jsonify({'error': 'Missing data'}), 400

    suggestion = g.db.query(Suggestion).get(suggestion_id)
    if not suggestion:
        return jsonify({'error': 'Suggestion not found'}), 404

    if item_type == 'food':
        if not g.db.query(Food).filter_by(name=item_name).first():
            g.db.add(Food(name=item_name))
    elif item_type == 'preparation':
        if not g.db.query(Preparation).filter_by(name=item_name).first():
            g.db.add(Preparation(name=item_name))
    else:
        return jsonify({'error': 'Invalid item type'}), 400

    g.db.delete(suggestion)
    g.db.commit()
    return jsonify({'message': 'Suggestion approved.'})

@app.route('/api/suggestions/reject', methods=['POST'])
@auth_required
def reject_suggestion():
    data = request.get_json()
    suggestion_id = data.get('id')
    if not suggestion_id:
        return jsonify({'error': 'Missing suggestion ID'}), 400

    suggestion = g.db.query(Suggestion).get(suggestion_id)
    if suggestion:
        g.db.delete(suggestion)
        g.db.commit()
        return jsonify({'message': 'Suggestion rejected.'})
    return jsonify({'error': 'Suggestion not found'}), 404

@app.route('/api/suggestions/update', methods=['POST'])
@auth_required
def update_suggestion():
    data = request.get_json()
    suggestion_id = data.get('id')
    if not suggestion_id:
        return jsonify({'error': 'Missing suggestion ID'}), 400

    suggestion = g.db.query(Suggestion).get(suggestion_id)
    if suggestion:
        suggestion.item = data.get('item', suggestion.item)
        suggestion.status = data.get('status', suggestion.status)
        g.db.commit()
        return jsonify(serialize(suggestion))
    return jsonify({'error': 'Suggestion not found'}), 404

if __name__ == '__main__':
    # The 'debug=True' parameter enables the reloader, which is great for development.
    # No need for the manual scheduler setup anymore.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))