"""
Flask application entry point.

Note: The Flask development server should only be used for development.
For production, use a WSGI server like gunicorn or uwsgi.
"""
import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    env = os.getenv('FLASK_ENV', 'development')
    debug = env == 'development'

    # Bind to localhost in development for security
    # Use HOST env var or 0.0.0.0 only when explicitly needed (e.g., Docker)
    host = os.getenv('HOST', '127.0.0.1')

    # Print startup banner with URLs
    print("\n" + "=" * 60)
    print("  Google Ads Campaign Manager - Backend Started")
    print("=" * 60)
    print(f"\n  Backend API:  http://localhost:{port}/api")
    print(f"  Frontend:     http://localhost:3001")
    print(f"\n  Health Check: http://localhost:{port}/api/health")
    print("=" * 60 + "\n")

    app.run(
        host=host,
        port=port,
        debug=debug
    )
