"""
Flask application configuration.
"""
import os
import logging
import secrets
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Minimum secret key length for security
MIN_SECRET_KEY_LENGTH = 32


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = False
    TESTING = False

    # JWT Authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # Database - no fallback credentials for security
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_timeout': 30,      # Timeout for getting connection from pool
        'pool_recycle': 1800,    # Recycle connections after 30 minutes
    }

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100/hour')
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        pass  # Base config allows missing values for flexibility

    # Google Ads API Configuration
    GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN', '')
    GOOGLE_ADS_CLIENT_ID = os.getenv('GOOGLE_ADS_CLIENT_ID', '')
    GOOGLE_ADS_CLIENT_SECRET = os.getenv('GOOGLE_ADS_CLIENT_SECRET', '')
    GOOGLE_ADS_REFRESH_TOKEN = os.getenv('GOOGLE_ADS_REFRESH_TOKEN', '')
    GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '')
    GOOGLE_ADS_CUSTOMER_ID = os.getenv('GOOGLE_ADS_CUSTOMER_ID', '')
    GOOGLE_ADS_USE_PROTO_PLUS = True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

    # Generate random secrets for development if not provided
    # This prevents using static fallback values
    _dev_secret = secrets.token_hex(32)
    _dev_jwt_secret = secrets.token_hex(32)

    SECRET_KEY = os.getenv('SECRET_KEY') or _dev_secret
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or _dev_jwt_secret

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/google_ads_manager'
    )
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3001').split(',')

    @classmethod
    def validate(cls) -> None:
        """Log warnings for development configuration."""
        if not os.getenv('SECRET_KEY'):
            logger.warning(
                "SECRET_KEY not set - using auto-generated key. "
                "Sessions will not persist across restarts."
            )
        if not os.getenv('JWT_SECRET_KEY'):
            logger.warning(
                "JWT_SECRET_KEY not set - using auto-generated key. "
                "Tokens will not persist across restarts."
            )


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SECRET_KEY = 'test-secret-key-for-testing-only'
    JWT_SECRET_KEY = 'test-jwt-secret-key-for-testing-only'
    # Use SQLite for testing by default (no external DB required)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///:memory:'
    )
    SQLALCHEMY_ENGINE_OPTIONS = {}  # SQLite doesn't support pool options
    RATELIMIT_ENABLED = False  # Disable rate limiting in tests


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration for production."""
        errors = []

        if not cls.SECRET_KEY:
            errors.append('SECRET_KEY environment variable is required')
        elif len(cls.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            errors.append(f'SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters')

        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append('DATABASE_URL environment variable is required')

        if not cls.JWT_SECRET_KEY:
            errors.append('JWT_SECRET_KEY environment variable is required')
        elif len(cls.JWT_SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            errors.append(f'JWT_SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters')

        if not cls.CORS_ORIGINS:
            errors.append('CORS_ORIGINS environment variable is required')

        # Warn about using memory storage for rate limiting in production
        if cls.RATELIMIT_STORAGE_URL == 'memory://':
            logger.warning(
                "Rate limiting using in-memory storage. "
                "Set REDIS_URL for distributed rate limiting."
            )

        if errors:
            raise ConfigurationError(
                'Production configuration errors:\n' + '\n'.join(f'  - {e}' for e in errors)
            )


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
