"""Rally Planner API: creates the Flask app and connects the pieces."""

from flask import Flask, jsonify

from config import Config
from extensions import bcrypt, db, migrate
from routes.auth import auth_bp
from routes.drills import drills_bp
from routes.plans import plans_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(drills_bp)
    app.register_blueprint(plans_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "Backend is running."}), 200

    # Always answer the frontend with JSON, even for errors.
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return jsonify({"error": "Something went wrong on the server."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5555)
