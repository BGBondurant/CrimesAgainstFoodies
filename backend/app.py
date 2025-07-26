import os
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=os.path.join(basedir, '..'), static_url_path='')
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this in your production environment!
jwt = JWTManager(app)
CORS(app)
bcrypt = Bcrypt(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=True)

class Preparation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=True)

class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    submission_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    username = db.Column(db.String(80))
    user_request_count = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Combination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item1 = db.Column(db.String(100), nullable=False)
    item2 = db.Column(db.String(100), nullable=False)
    item3 = db.Column(db.String(100), nullable=False)
    item4 = db.Column(db.String(100), nullable=False)
    upvotes = db.Column(db.Integer, default=0)

class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    combination_id = db.Column(db.Integer, db.ForeignKey('combination.id'), nullable=False)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(100), nullable=True)

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)

@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    db.create_all()
    print('Initialized the database.')

# API Endpoints
@app.route('/api/items', methods=['GET'])
def get_items():
    category = request.args.get('category')
    if category:
        foods = Food.query.filter_by(category=category).all()
        preparations = Preparation.query.filter_by(category=category).all()
    else:
        foods = Food.query.all()
        preparations = Preparation.query.all()

    return jsonify({
        'Food': [food.name for food in foods],
        'Preperation': [prep.name for prep in preparations]
    })

@app.route('/api/suggestions', methods=['POST'])
def create_suggestion():
    data = request.get_json()
    ip_address = request.remote_addr
    username = data.get('username') # This will be None for now

    user_request_count = Suggestion.query.filter_by(ip_address=ip_address).count() + 1

    new_suggestion = Suggestion(
        item=data['item'],
        type=data['type'],
        ip_address=ip_address,
        username=username,
        user_request_count=user_request_count
    )
    db.session.add(new_suggestion)
    db.session.commit()
    return jsonify({'message': 'Suggestion created successfully'}), 201

@app.route('/api/admin/suggestions', methods=['GET'])
def get_admin_suggestions():
    suggestions = Suggestion.query.all()
    return jsonify([{
        'id': s.id,
        'item': s.item,
        'type': s.type,
        'status': s.status,
        'submission_date': s.submission_date.isoformat(),
        'ip_address': s.ip_address,
        'username': s.username,
        'user_request_count': s.user_request_count
    } for s in suggestions])

@app.route('/api/admin/approve/<int:suggestion_id>', methods=['POST'])
def approve_suggestion(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    suggestion.status = 'approved'

    if suggestion.type == 'Food':
        if not Food.query.filter_by(name=suggestion.item).first():
            new_item = Food(name=suggestion.item)
            db.session.add(new_item)
    elif suggestion.type == 'Preperation':
        if not Preparation.query.filter_by(name=suggestion.item).first():
            new_item = Preparation(name=suggestion.item)
            db.session.add(new_item)
    elif suggestion.type == 'Both':
        if not Food.query.filter_by(name=suggestion.item).first():
            new_food = Food(name=suggestion.item)
            db.session.add(new_food)
        if not Preparation.query.filter_by(name=suggestion.item).first():
            new_prep = Preparation(name=suggestion.item)
            db.session.add(new_prep)

    db.session.commit()
    return jsonify({'message': 'Suggestion approved successfully'})

@app.route('/api/admin/reject/<int:suggestion_id>', methods=['DELETE'])
def reject_suggestion(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    suggestion.status = 'rejected'
    db.session.commit()
    return jsonify({'message': 'Suggestion rejected successfully'})

@app.route('/api/admin/items/<item_type>/<int:item_id>', methods=['PUT'])
def update_item(item_type, item_id):
    data = request.get_json()
    new_name = data.get('name')
    if not new_name:
        return jsonify({'error': 'New name is required'}), 400

    if item_type == 'food':
        item = Food.query.get_or_404(item_id)
    elif item_type == 'preparation':
        item = Preparation.query.get_or_404(item_id)
    else:
        return jsonify({'error': 'Invalid item type'}), 400

    item.name = new_name
    db.session.commit()
    return jsonify({'message': f'{item_type.capitalize()} item updated successfully'})

@app.route('/api/admin/items/<item_type>/<int:item_id>', methods=['DELETE'])
def delete_item(item_type, item_id):
    if item_type == 'food':
        item = Food.query.get_or_404(item_id)
    elif item_type == 'preparation':
        item = Preparation.query.get_or_404(item_id)
    else:
        return jsonify({'error': 'Invalid item type'}), 400

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': f'{item_type.capitalize()} item deleted successfully'})

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    pending_suggestions = Suggestion.query.filter_by(status='pending').count()
    total_foods = Food.query.count()
    total_preparations = Preparation.query.count()
    return jsonify({
        'pending_suggestions': pending_suggestions,
        'total_foods': total_foods,
        'total_preparations': total_preparations
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"msg": "Username, email, and password are required"}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"msg": "Username or email already exists"}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)

    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/api/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    item1 = data.get('item1')
    item2 = data.get('item2')
    item3 = data.get('item3')
    item4 = data.get('item4')

    combination = Combination(item1=item1, item2=item2, item3=item3, item4=item4)
    db.session.add(combination)
    db.session.commit()

    user_favorite = UserFavorite(user_id=current_user_id, combination_id=combination.id)
    db.session.add(user_favorite)
    db.session.commit()

    return jsonify({"msg": "Favorite added successfully"}), 201

@app.route('/api/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    current_user_id = get_jwt_identity()
    favorites = UserFavorite.query.filter_by(user_id=current_user_id).all()
    favorite_combinations = []
    for fav in favorites:
        combo = Combination.query.get(fav.combination_id)
        favorite_combinations.append({
            "item1": combo.item1,
            "item2": combo.item2,
            "item3": combo.item3,
            "item4": combo.item4,
        })
    return jsonify(favorite_combinations)

@app.route('/api/hall-of-fame', methods=['GET'])
def get_hall_of_fame():
    top_combinations = Combination.query.order_by(Combination.upvotes.desc()).limit(10).all()
    return jsonify([{
        "item1": combo.item1,
        "item2": combo.item2,
        "item3": combo.item3,
        "item4": combo.item4,
        "upvotes": combo.upvotes
    } for combo in top_combinations])

@app.route('/api/upvote/<int:combination_id>', methods=['POST'])
@jwt_required()
def upvote(combination_id):
    current_user_id = get_jwt_identity()
    combination = Combination.query.get_or_404(combination_id)
    combination.upvotes += 1
    db.session.commit()

    # Award "Hall of Famer" achievement
    if combination.upvotes >= 10: # Assuming 10 upvotes are needed for the Hall of Fame
        achievement = Achievement.query.filter_by(name='Hall of Famer').first()
        if achievement and not UserAchievement.query.filter_by(user_id=current_user_id, achievement_id=achievement.id).first():
            user_achievement = UserAchievement(user_id=current_user_id, achievement_id=achievement.id)
            db.session.add(user_achievement)
            db.session.commit()

    return jsonify({"msg": "Upvoted successfully"})

@app.route('/api/achievements', methods=['GET'])
@jwt_required()
def get_achievements():
    current_user_id = get_jwt_identity()
    user_achievements = UserAchievement.query.filter_by(user_id=current_user_id).all()
    achievements = []
    for ua in user_achievements:
        achievement = Achievement.query.get(ua.achievement_id)
        achievements.append({
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon
        })
    return jsonify(achievements)

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        # NOTE: You'll need to set up authentication for Vertex AI
        # This might involve setting GOOGLE_APPLICATION_CREDENTIALS environment variable
        # https://cloud.google.com/docs/authentication/provide-credentials-adc
        vertexai.init(project=os.environ.get("GCP_PROJECT_ID"), location=os.environ.get("GCP_PROJECT_LOCATION"))

        model = ImageGenerationModel.from_pretrained("imagegeneration@006") # Using the latest stable model

        response = model.generate_images(
            prompt=prompt,
            number_of_images=1, # Generate one image
        )

        image_bytes = response.images[0]._image_bytes
        image_filename = "generated_image.png"
        # Save the image to the parent directory (the frontend root)
        output_path = os.path.join(basedir, '..', image_filename)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        # Return a URL that the frontend can use. The leading slash makes it a root-relative URL.
        return jsonify({'image_url': f'/{image_filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_index():
    # Serve index.html from the static folder (which is the project root)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin')
def serve_admin():
    # Serve index.html from the Admin directory
    return send_from_directory(os.path.join(app.static_folder, 'Admin'), 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
