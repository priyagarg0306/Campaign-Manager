"""
Flask route blueprints.
"""
from app.routes.campaigns import campaigns_bp
from app.routes.health import health_bp

__all__ = ['campaigns_bp', 'health_bp']
