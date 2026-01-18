# Google Ads Campaign Manager

A full-stack application for creating and publishing marketing campaigns to Google Ads.

Built with **React** (TypeScript) + **Python Flask** + **PostgreSQL** + **Google Ads API**.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [API Documentation](#api-documentation)
- [Google Ads Setup](#google-ads-setup)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)

## Features

- **Create Campaigns**: Create marketing campaigns locally with all required details
- **Campaign Listing**: View all campaigns with status indicators
- **Publish to Google Ads**: Publish campaigns to Google Ads API (creates PAUSED campaigns)
- **Campaign Management**: Pause, enable, and delete campaigns
- **Form Validation**: Client-side and server-side validation
- **Responsive UI**: Works on desktop and mobile devices

## Architecture

```
+------------------+      +------------------+      +------------------+
|                  |      |                  |      |                  |
|  React Frontend  +----->+   Flask API      +----->+   PostgreSQL     |
|  (TypeScript)    |      |   (Python)       |      |   Database       |
|                  |      |                  |      |                  |
+------------------+      +--------+---------+      +------------------+
                                   |
                                   v
                          +------------------+
                          |                  |
                          |  Google Ads API  |
                          |                  |
                          +------------------+
```

### Components

1. **Frontend (React + TypeScript)**
   - Campaign creation form with validation
   - Campaign listing with actions
   - API integration with Axios
   - React Hook Form for form handling

2. **Backend (Flask + SQLAlchemy)**
   - RESTful API endpoints
   - PostgreSQL database integration
   - Google Ads API integration
   - Request validation with Marshmallow

3. **Database (PostgreSQL)**
   - Campaign storage with UUID primary keys
   - Status tracking (DRAFT, PUBLISHED, PAUSED, ERROR)
   - Google Ads ID mapping

4. **Google Ads Integration**
   - Campaign creation with PAUSED status
   - Ad Group creation
   - Responsive Display Ad creation
   - Campaign status management

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Docker & Docker Compose** (optional, for containerized setup)
- **Google Ads API credentials** (for publishing campaigns)

## Quick Start

### Using Docker Compose

1. **Clone and navigate to the project:**
   ```bash
   cd google-ads-campaign-manager
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:5001/api

4. **Configure Google Ads (optional):**
   Create a `.env` file in the root directory with your Google Ads credentials:
   ```bash
   GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
   GOOGLE_ADS_CLIENT_ID=your-client-id
   GOOGLE_ADS_CLIENT_SECRET=your-client-secret
   GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
   GOOGLE_ADS_CUSTOMER_ID=0987654321
   ```

## Manual Setup

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb google_ads_manager

   # Or using psql
   psql -U postgres -c "CREATE DATABASE google_ads_manager;"
   ```

5. **Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

6. **Run the backend:**
   ```bash
   python run.py
   ```

   The API will be available at http://localhost:5001

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm start
   ```

   The app will be available at http://localhost:3001

## API Documentation

### Base URL
```
http://localhost:5001/api
```

### Endpoints

#### Create Campaign
```http
POST /api/campaigns
Content-Type: application/json

{
  "name": "My Campaign",
  "objective": "SALES",
  "campaign_type": "DEMAND_GEN",
  "daily_budget": 10000000,
  "start_date": "2024-01-20",
  "end_date": "2024-02-20",
  "ad_group_name": "My Ad Group",
  "ad_headline": "Amazing Product",
  "ad_description": "Check out our product",
  "asset_url": "https://example.com/image.jpg",
  "final_url": "https://example.com"
}

Response: 201 Created
{
  "id": "uuid",
  "name": "My Campaign",
  "status": "DRAFT",
  ...
}
```

#### Get All Campaigns
```http
GET /api/campaigns
GET /api/campaigns?status=DRAFT

Response: 200 OK
[
  {
    "id": "uuid",
    "name": "My Campaign",
    "status": "DRAFT",
    ...
  }
]
```

#### Get Single Campaign
```http
GET /api/campaigns/{id}

Response: 200 OK
{
  "id": "uuid",
  "name": "My Campaign",
  ...
}
```

#### Update Campaign
```http
PUT /api/campaigns/{id}
Content-Type: application/json

{
  "name": "Updated Name"
}

Response: 200 OK
```

#### Delete Campaign
```http
DELETE /api/campaigns/{id}

Response: 204 No Content
```

#### Publish Campaign to Google Ads
```http
POST /api/campaigns/{id}/publish

Response: 200 OK
{
  "message": "Campaign published successfully",
  "campaign": {...},
  "google_ads": {
    "campaign_id": "123456",
    "ad_group_id": "789012",
    "ad_id": "345678"
  }
}
```

#### Pause Campaign
```http
POST /api/campaigns/{id}/pause

Response: 200 OK
```

#### Enable Campaign
```http
POST /api/campaigns/{id}/enable

Response: 200 OK
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Campaign name (1-255 chars) |
| objective | string | Yes | SALES, LEADS, or WEBSITE_TRAFFIC |
| campaign_type | string | No | DEMAND_GEN (default), SEARCH, DISPLAY, etc. |
| daily_budget | integer | Yes | Budget in micros (1 USD = 1,000,000) |
| start_date | date | Yes | Campaign start date (ISO format) |
| end_date | date | No | Campaign end date (ISO format) |
| ad_group_name | string | No | Name for the ad group |
| ad_headline | string | No | Ad headline (max 30 chars for display) |
| ad_description | string | No | Ad description (max 90 chars for display) |
| asset_url | URL | No | Image asset URL |
| final_url | URL | No | Landing page URL |

## Google Ads Setup

Complete these three phases to set up Google Ads API access.

### Phase 1: Account & Developer Token Setup

This phase establishes the account structure required for API access and testing.

#### 1.1 Create a Production Account
- Visit the [Google Ads Start Page](https://ads.google.com/home/) to set up your primary production account

#### 1.2 Create a Test Manager Account
- Navigate to the [Google Ads Test Accounts](https://ads.google.com/nav/selectaccount?authuser=0&dst=/aw/overview?supportResource%3Dtopic_702369&subid=ALL-en-et-g-aw-a-tools_t1-awhp_xin1!o2) page to create a manager account specifically for testing

#### 1.3 Provision a Test Client Account
1. Access the **Account** tab on the left side of your Test Manager dashboard
2. Click the **+ blue icon**
3. Select **Create a new account** and click **Save**

#### 1.4 Generate Developer Token
1. Sign in to your **Google Ads Production Account**
2. Click the **Admin** tab in the left navigation panel
3. Select **API Center**
4. Enter all required details and click **Create token**

---

### Phase 2: Google Cloud Console Configuration

These steps link your Ads account to a developer project to manage security and credentials.

#### 2.1 Enable the API
1. Log in to the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services > Library** via the navigation panel
3. Search for **Google Ads API** and click **Enable**

#### 2.2 Configure OAuth Consent Screen
1. Return to **APIs & Services** and select **OAuth consent screen**
2. Click **Get Started**
3. Enter your **App Name** and **Support Email**
4. Select **External** as the user type
5. Complete the **Contact Info** and click **Create**

#### 2.3 Add Test Users
1. Go to the **Audience/Test Users** tab
2. Click **Add Users** and enter the Gmail address of your Test Manager Account

---

### Phase 3: Credentials & Refresh Token

The final steps to obtain the Client ID, Secret, and the long-lived Refresh Token.

#### 3.1 Generate OAuth Credentials
1. Navigate to **APIs & Services > Credentials**
2. Click **+ Create Credentials** and select **OAuth client ID**
3. Choose **Web Application** as the application type
4. Add `https://developers.google.com/oauthplayground` to **Authorized redirect URIs**
5. Click **Create** and download the JSON file which contains your **Client ID** and **Client Secret**

#### 3.2 Generate Refresh Token
1. Go to the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
2. Sign in using your **Test Manager Gmail account**
3. Click the **Gear icon** (top right) and check **"Use your own OAuth credentials"**
4. Enter your **Client ID** and **Client Secret**
5. In the left panel, find **Google Ads API**, select the `auth/adwords` scope, and click **Authorize APIs**
6. Click **Exchange authorization code for tokens**
7. Copy the **Refresh Token** from the right-hand panel

#### 3.3 Get Customer IDs
- **Login Customer ID**: Your Test Manager account ID (the 10-digit number shown in Google Ads)
- **Customer ID**: The Test Client account ID where campaigns will be created

---

### Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
GOOGLE_ADS_CUSTOMER_ID=0987654321
```

**Important Notes**:
- Remove dashes from customer IDs (e.g., `123-456-7890` becomes `1234567890`)
- The developer token from a test account has limited functionality
- For production use, you'll need to apply for Basic or Standard API access

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| FLASK_ENV | Environment (development/production) | Yes |
| SECRET_KEY | Flask secret key | Yes |
| DATABASE_URL | PostgreSQL connection string | Yes |
| GOOGLE_ADS_DEVELOPER_TOKEN | Google Ads developer token | For publishing |
| GOOGLE_ADS_CLIENT_ID | OAuth2 client ID | For publishing |
| GOOGLE_ADS_CLIENT_SECRET | OAuth2 client secret | For publishing |
| GOOGLE_ADS_REFRESH_TOKEN | OAuth2 refresh token | For publishing |
| GOOGLE_ADS_LOGIN_CUSTOMER_ID | Manager account ID | For publishing |
| GOOGLE_ADS_CUSTOMER_ID | Target account ID | For publishing |

## Testing

### Backend Tests

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest

# Run with coverage (terminal output)
pytest --cov=app --cov-report=term-missing

# Run with coverage (HTML report)
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_campaigns.py -v
```

**Current coverage: 83% (131 tests)**

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## Project Structure

```
google-ads-campaign-manager/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Application factory
│   │   ├── models/
│   │   │   └── campaign.py      # Campaign model
│   │   ├── routes/
│   │   │   ├── campaigns.py     # Campaign API routes
│   │   │   └── health.py        # Health check routes
│   │   ├── services/
│   │   │   ├── campaign_service.py
│   │   │   └── google_ads_service.py
│   │   ├── schemas/
│   │   │   └── campaign_schema.py
│   │   └── utils/
│   ├── tests/
│   │   ├── test_campaigns.py
│   │   ├── test_campaign_service.py
│   │   └── test_google_ads_service.py
│   ├── config.py
│   ├── run.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CampaignForm.tsx
│   │   │   └── CampaignList.tsx
│   │   ├── hooks/
│   │   │   └── useCampaigns.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── campaign.ts
│   │   ├── utils/
│   │   │   └── validation.ts
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
└── README.md
```

## Design Decisions

### 1. Database Schema

- **UUID Primary Keys**: Distributed-friendly, non-sequential IDs
- **Status Tracking**: DRAFT -> PUBLISHED -> PAUSED lifecycle
- **Budget in Micros**: Google Ads API uses micros (1 USD = 1,000,000)
- **Timestamps**: created_at and updated_at for auditing

### 2. API Design

- **RESTful Endpoints**: Standard HTTP methods and status codes
- **Validation**: Server-side with Marshmallow, client-side with Yup
- **Error Handling**: Consistent error response format
- **CORS**: Enabled for cross-origin requests

### 3. Google Ads Integration

- **PAUSED Campaigns**: All campaigns start PAUSED to prevent charges
- **Campaign Structure**: Budget -> Campaign -> Ad Group -> Ad
- **Responsive Display Ads**: Flexible ad format for Demand Gen
- **Error Handling**: Comprehensive error parsing and logging

### 4. Frontend Architecture

- **React Hooks**: useState, useEffect, useCallback for state management
- **TypeScript**: Type safety throughout the application
- **React Hook Form**: Performance-optimized form handling
- **Yup Validation**: Schema-based client-side validation

### 5. Security Considerations

- **Environment Variables**: Credentials stored in .env (never committed)
- **Input Validation**: All inputs validated on both client and server
- **SQL Injection Prevention**: Using SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Restricted to expected origins in production

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running
   - Check DATABASE_URL is correct
   - Verify database exists

2. **Google Ads API Errors**
   - Verify all credentials are set correctly
   - Check customer IDs don't have dashes
   - Ensure developer token is approved

3. **CORS Issues**
   - Backend CORS is configured for all origins in development
   - For production, restrict to your frontend domain

4. **Frontend Build Errors (TypeScript/Jest)**
   - If you see `TS2708: Cannot use namespace 'jest' as a value`, ensure test files are excluded from the build
   - The `tsconfig.json` should include an `exclude` array for test files:
     ```json
     "exclude": ["src/**/*.test.ts", "src/**/*.test.tsx", "src/setupTests.ts"]
     ```

5. **Port Already in Use**
   - If port 3001 or 5001 is already in use, stop the conflicting process:
     ```bash
     lsof -i :3001  # Find process using port 3001
     kill <PID>     # Kill the process
     ```

## License

MIT License
