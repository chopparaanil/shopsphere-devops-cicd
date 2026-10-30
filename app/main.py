import os

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# Use PostgreSQL when DATABASE_URL is configured.
# SQLite is a convenient fallback for local development.
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///shopsphere.db",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Book(db.Model):
    """A book stored in the database."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
        }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    # Liveness: the Flask process is responding.
    return jsonify({"status": "healthy"}), 200


@app.route("/ready")
def ready():
    # Readiness: the application can access its database.
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ready"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"status": "not ready"}), 503


@app.route("/books", methods=["GET"])
def get_books():
    try:
        books = db.session.execute(
            db.select(Book).order_by(Book.id)
        ).scalars().all()

        return jsonify({"books": [book.to_dict() for book in books]}), 200
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Failed to retrieve books")
        return jsonify({"error": "Unable to retrieve books"}), 500


@app.route("/books", methods=["POST"])
def add_book():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON request body is required"}), 400

    name = data.get("name")
    price = data.get("price")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Book name is required"}), 400

    name = name.strip()

    if len(name) > 200:
        return jsonify({"error": "Book name must be 200 characters or fewer"}), 400

    # Reject booleans, non-numeric values, NaN, infinity and invalid prices.
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        return jsonify({"error": "Price must be a positive number"}), 400

    import math

    if not math.isfinite(price) or price <= 0:
        return jsonify({"error": "Price must be a positive number"}), 400

    book = Book(name=name, price=round(price, 2))

    try:
        db.session.add(book)
        db.session.commit()
        return jsonify({"book": book.to_dict()}), 201
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Failed to add book")
        return jsonify({"error": "Unable to add book"}), 500


@app.route("/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    try:
        book = db.session.get(Book, book_id)

        if book is None:
            return jsonify({"error": "Book not found"}), 404

        db.session.delete(book)
        db.session.commit()

        return jsonify({"message": "Book deleted successfully"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Failed to delete book")
        return jsonify({"error": "Unable to delete book"}), 500




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)