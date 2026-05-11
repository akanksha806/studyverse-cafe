from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

from routes.reservations import reservations_bp
from routes.menu          import menu_bp
from routes.membership    import membership_bp
from routes.contact       import contact_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from utils.email_helper import init_mail, mail
    mail.init_app(app)

    app.register_blueprint(reservations_bp, url_prefix="/api/reservations")
    app.register_blueprint(menu_bp,         url_prefix="/api/menu")
    app.register_blueprint(membership_bp,   url_prefix="/api/membership")
    app.register_blueprint(contact_bp,      url_prefix="/api/contact")

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "message": "Studyverse Café API is running ☕"
        }), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)