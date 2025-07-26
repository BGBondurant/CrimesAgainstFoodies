from app import app, db, Suggestion
from datetime import datetime

with app.app_context():
    db.create_all()

    # Create some sample suggestions
    suggestion1 = Suggestion(
        item='Pineapple on Pizza',
        type='Food',
        status='pending',
        submission_date=datetime.utcnow(),
        ip_address='127.0.0.1',
        username='testuser1',
        user_request_count=1
    )

    suggestion2 = Suggestion(
        item='Ketchup on Hot Dog',
        type='Food',
        status='approved',
        submission_date=datetime.utcnow(),
        ip_address='192.168.1.1',
        username='testuser2',
        user_request_count=5
    )

    suggestion3 = Suggestion(
        item='Well-done Steak',
        type='Preperation',
        status='rejected',
        submission_date=datetime.utcnow(),
        ip_address='10.0.0.1',
        username='testuser3',
        user_request_count=10
    )

    db.session.add_all([suggestion1, suggestion2, suggestion3])
    db.session.commit()

    print('Database populated with sample data.')
