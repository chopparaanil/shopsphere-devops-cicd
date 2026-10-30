from app.main import app, db

with app.app_context():
    db.create_all()

print("ShopSphere database tables initialized successfully.")