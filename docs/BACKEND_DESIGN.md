# Backend Design Notes

## Overview

The backend is a Flask REST API that manages Google Ads campaigns. It provides CRUD operations for campaigns, integrates with the Google Ads API for publishing, and follows a layered architecture for maintainability and testability.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Routes Layer                          │
│              (campaigns.py, health.py)                       │
│         HTTP endpoints, request/response handling            │
├─────────────────────────────────────────────────────────────┤
│                       Schemas Layer                          │
│                  (campaign_schema.py)                        │
│         Validation, serialization, type-specific rules       │
├─────────────────────────────────────────────────────────────┤
│                      Services Layer                          │
│         (campaign_service.py, google_ads_service.py)         │
│              Business logic, external API calls              │
├─────────────────────────────────────────────────────────────┤
│                       Models Layer                           │
│                     (campaign.py)                            │
│              SQLAlchemy ORM, database schema                 │
├─────────────────────────────────────────────────────────────┤
│                        Utils Layer                           │
│    (validators.py, image_validator.py, error_mapping.py)     │
│              Shared utilities, validation helpers            │
└─────────────────────────────────────────────────────────────┘
```

## Design Decisions

### 1. Application Factory Pattern (`app/__init__.py`)

**Why:** The application factory pattern (`create_app()`) enables:
- Different configurations for dev/test/production
- Clean test isolation (each test gets a fresh app instance)
- Avoiding circular imports with Flask extensions

**Implementation:**
```python
def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    # ... register blueprints, error handlers
    return app
```

### 2. Service Layer Pattern (`app/services/`)

**Why:** Separates business logic from HTTP handling:
- Routes stay thin (just handle HTTP concerns)
- Business logic is reusable and testable in isolation
- Google Ads API complexity is encapsulated

**Structure:**
- `CampaignService` - CRUD operations, validation, status management
- `GoogleAdsService` - All Google Ads API interactions

**Example flow:**
```
Route (campaigns.py)
  → validates request with Schema
  → calls CampaignService.create_campaign()
  → CampaignService calls GoogleAdsService.publish_campaign() if needed
  → returns response
```

### 3. Schema-Based Validation (`app/schemas/campaign_schema.py`)

**Why:** Marshmallow schemas provide:
- Declarative validation rules
- Automatic serialization/deserialization
- Campaign-type-specific validation (DEMAND_GEN vs SEARCH vs VIDEO, etc.)

**Key features:**
- Dynamic validation based on `campaign_type`
- Character limits per Google Ads API requirements (e.g., headlines: 30 chars for Search, 40 chars for Demand Gen)
- Bidding strategy validation per campaign type

### 4. Campaign Type Configuration

**Why:** Google Ads has different requirements per campaign type. Centralizing this:
- Makes adding new campaign types easier
- Ensures consistency between frontend and backend
- Simplifies validation logic

**Supported types:**
| Type | Key Requirements |
|------|------------------|
| DEMAND_GEN | Headlines (40 chars), descriptions, images, business name |
| SEARCH | Headlines (30 chars), descriptions, keywords |
| DISPLAY | Headlines, long headline, images |
| VIDEO | Video URL required, limited API support |
| SHOPPING | Merchant Center ID required |
| PERFORMANCE_MAX | Multiple headlines (3-15), asset groups |

### 5. Google Ads Service Design (`app/services/google_ads_service.py`)

**Why:** The Google Ads API is complex. This service:
- Abstracts API version details (currently v18)
- Handles authentication and client initialization
- Maps internal models to Google Ads API objects
- Provides meaningful error messages

**Key methods:**
- `publish_campaign()` - Creates campaign in Google Ads
- `pause_campaign()` / `enable_campaign()` - Status management
- `_create_campaign_by_type()` - Type-specific campaign creation
- `_create_asset_group()` - For Performance Max campaigns

**Error handling:**
- `google_ads_error_mapping.py` translates Google API errors to user-friendly messages
- Validation happens before API calls to fail fast

### 6. Database Model (`app/models/campaign.py`)

**Why:** SQLAlchemy ORM provides:
- Database-agnostic queries
- Migration support via Flask-Migrate
- Type safety with Python

**Key fields:**
```python
class Campaign(db.Model):
    id = db.Column(UUID, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='DRAFT')
    campaign_type = db.Column(db.String(50), default='DEMAND_GEN')

    # JSON fields for flexible storage
    headlines = db.Column(db.JSON)      # Array of strings
    descriptions = db.Column(db.JSON)   # Array of strings
    images = db.Column(db.JSON)         # {landscape: url, square: url, logo: url}
    keywords = db.Column(db.JSON)       # Array of keyword objects
```

**Design choice:** JSON columns for arrays/objects instead of separate tables because:
- Simpler queries for campaign retrieval
- Headlines/descriptions are always loaded with campaigns
- No need for complex joins

### 7. Security Features

**Implemented in `app/__init__.py` and throughout:**

| Feature | Implementation |
|---------|----------------|
| Rate Limiting | Flask-Limiter (100/hour default, Redis in production) |
| CORS | Restricted origins via config |
| Security Headers | CSP, X-Frame-Options, X-Content-Type-Options, etc. |
| Input Validation | Marshmallow schemas, size limits |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| Request Size | 16MB max to prevent DoS |

### 8. Configuration Management (`config.py`)

**Why:** Environment-based configuration:
- Development: Permissive, auto-generated secrets, local DB
- Testing: In-memory SQLite, rate limiting disabled
- Production: Strict validation, requires all secrets

**Production validation ensures:**
- SECRET_KEY is set and >= 32 characters
- DATABASE_URL is configured
- CORS_ORIGINS is specified

### 9. Health Check Endpoints (`app/routes/health.py`)

**Why:** Production readiness:
- `/api/health` - Full health check (DB + Google Ads config)
- `/api/health/live` - Kubernetes liveness probe
- `/api/health/ready` - Kubernetes readiness probe

### 10. Image Validation (`app/utils/image_validator.py`)

**Why:** Google Ads has strict image requirements:
- Aspect ratios: 1.91:1 (landscape), 1:1 (square), 4:1 (logo)
- Minimum dimensions per type
- File size limits

**Implementation:**
- Validates image URLs by fetching headers
- Checks dimensions via PIL
- Returns detailed error messages

## Testing Strategy

**Layered testing approach:**
- Unit tests for services and validators
- Integration tests for routes (with test DB)
- Separate Google Ads API integration tests (require credentials)

**Coverage:** 82% backend coverage with 406 tests

## File Structure

```
backend/
├── app/
│   ├── __init__.py          # App factory, extensions, error handlers
│   ├── models/
│   │   └── campaign.py      # SQLAlchemy models
│   ├── routes/
│   │   ├── campaigns.py     # Campaign CRUD endpoints
│   │   └── health.py        # Health check endpoints
│   ├── schemas/
│   │   └── campaign_schema.py  # Validation schemas
│   ├── services/
│   │   ├── campaign_service.py    # Business logic
│   │   └── google_ads_service.py  # Google Ads API
│   └── utils/
│       ├── validators.py           # Input validators
│       ├── image_validator.py      # Image validation
│       └── google_ads_error_mapping.py  # Error translation
├── config.py                # Environment configs
├── migrations/              # Alembic migrations
└── tests/                   # Test suite
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns` | List campaigns (with pagination, status filter) |
| POST | `/api/campaigns` | Create campaign (DRAFT status) |
| GET | `/api/campaigns/<id>` | Get campaign details |
| PUT | `/api/campaigns/<id>` | Update campaign |
| DELETE | `/api/campaigns/<id>` | Delete campaign |
| POST | `/api/campaigns/<id>/publish` | Publish to Google Ads |
| POST | `/api/campaigns/<id>/pause` | Pause campaign |
| POST | `/api/campaigns/<id>/enable` | Enable paused campaign |
| POST | `/api/campaigns/<id>/validate` | Validate before publish |
| GET | `/api/health` | Health check |

## Future Considerations

1. **Authentication** - Currently placeholder; implement JWT or OAuth
2. **Multi-tenancy** - `owner_id` field exists but not enforced
3. **Async publishing** - Long Google Ads API calls could use Celery
4. **Caching** - Redis caching for campaign lists
5. **Audit logging** - Structured audit trail for compliance
