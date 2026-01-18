"""
Flask application factory.
"""
import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config, ConfigurationError

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Rate limiter with configurable storage (Redis in production, memory in dev)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri=os.getenv('REDIS_URL', 'memory://'),
)

# Request size limits
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size


def create_app(config_name: str = None) -> Flask:
    """
    Application factory function.

    Args:
        config_name: Configuration name ('development', 'testing', 'production')

    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Set request size limit to prevent DoS
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

    # Validate production configuration
    config_class = config[config_name]
    if hasattr(config_class, 'validate'):
        config_class.validate()

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure rate limiting with Redis in production
    if app.config.get('RATELIMIT_ENABLED', True):
        # Update storage URI from config if available
        storage_uri = app.config.get('RATELIMIT_STORAGE_URL', os.getenv('REDIS_URL', 'memory://'))
        limiter._storage_uri = storage_uri
        limiter.init_app(app)

    # Configure CORS with restricted origins
    cors_origins = app.config.get('CORS_ORIGINS', [])
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    else:
        # In development without CORS_ORIGINS, allow localhost
        if config_name == 'development':
            CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3001"]}})

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        # Content Security Policy
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Enable XSS filter
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions Policy - restrict access to sensitive browser features
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'
        # HSTS (only in production with HTTPS)
        if config_name == 'production' and request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Configure logging
    configure_logging(app)

    # Register blueprints
    from app.routes.campaigns import campaigns_bp
    from app.routes.health import health_bp

    app.register_blueprint(campaigns_bp)
    app.register_blueprint(health_bp)

    # Register error handlers
    register_error_handlers(app)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO if not app.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Reduce noise from third-party libraries
    logging.getLogger('google.ads').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error.description)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': 'The requested resource was not found'}), 404

    @app.errorhandler(413)
    def request_too_large(error):
        return jsonify({'error': 'Request too large', 'message': 'The request payload exceeds the maximum allowed size'}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({'error': 'Rate limit exceeded', 'message': 'Too many requests. Please try again later.'}), 429

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
