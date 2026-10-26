from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "application": "ShopSphere",
        "message": "Welcome to ShopSphere!",
        "version": "1.0.0"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/ready")
def ready():
    return jsonify({"status": "ready"}), 200


@app.route("/books")
def books():
    return jsonify({
        "books": [
            {"id": 1, "name": "Linux for Beginners", "price": 499},
            {"id": 2, "name": "AWS DevOps Guide", "price": 799},
            {"id": 3, "name": "Kubernetes Essentials", "price": 699}
        ]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)