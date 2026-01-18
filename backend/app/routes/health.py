"""
Health check routes.
"""
import logging
from flask import Blueprint, jsonify

from app import db, limiter
from app.services.google_ads_service import google_ads_service

health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)

# Rate limits for health endpoints (more permissive than API endpoints)
HEALTH_RATE_LIMIT = "60 per minute"


@health_bp.route('/api/health', methods=['GET'])
@limiter.limit(HEALTH_RATE_LIMIT)
def health_check():
    """
    Health check endpoint.

    Returns:
        200: Service is healthy
        500: Service is unhealthy
    """
    health_status = {
        'status': 'healthy',
        'checks': {
            'database': check_database(),
            'google_ads': check_google_ads()
        }
    }

    # If any check failed, overall status is unhealthy
    if any(not check['healthy'] for check in health_status['checks'].values()):
        health_status['status'] = 'unhealthy'
        return jsonify(health_status), 500

    return jsonify(health_status), 200


@health_bp.route('/api/health/live', methods=['GET'])
@limiter.limit(HEALTH_RATE_LIMIT)
def liveness():
    """
    Liveness probe - is the service running?

    Returns:
        200: Service is alive
    """
    return jsonify({'status': 'alive'}), 200


@health_bp.route('/api/health/ready', methods=['GET'])
@limiter.limit(HEALTH_RATE_LIMIT)
def readiness():
    """
    Readiness probe - is the service ready to accept traffic?

    Returns:
        200: Service is ready
        503: Service is not ready
    """
    try:
        # Check if database is accessible
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'ready'}), 200
    except Exception as e:
        # Log the actual error for debugging but don't expose to clients
        logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not ready',
            'error': 'Service temporarily unavailable'
        }), 503


def check_database():
    """Check database connectivity."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return {'healthy': True, 'message': 'Database connection OK'}
    except Exception as e:
        # Log the actual error for debugging but don't expose details
        logger.error(f"Database health check failed: {str(e)}")
        return {'healthy': False, 'message': 'Database connection failed'}


def check_google_ads():
    """Check Google Ads API configuration."""
    is_configured = google_ads_service.is_configured()
    return {
        'healthy': True,  # Not having Google Ads configured is not unhealthy
        'configured': is_configured,
        'message': 'Google Ads API configured' if is_configured else 'Google Ads API not configured'
    }


