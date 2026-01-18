"""
Campaign database model.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum

from app import db


class CampaignStatus(str, Enum):
    """Campaign status enum."""
    DRAFT = 'DRAFT'
    PUBLISHED = 'PUBLISHED'
    PAUSED = 'PAUSED'
    ERROR = 'ERROR'


class CampaignObjective(str, Enum):
    """Campaign objective enum."""
    SALES = 'SALES'
    LEADS = 'LEADS'
    WEBSITE_TRAFFIC = 'WEBSITE_TRAFFIC'


class CampaignType(str, Enum):
    """Campaign type enum."""
    DEMAND_GEN = 'DEMAND_GEN'
    SEARCH = 'SEARCH'
    DISPLAY = 'DISPLAY'
    VIDEO = 'VIDEO'
    SHOPPING = 'SHOPPING'
    PERFORMANCE_MAX = 'PERFORMANCE_MAX'


class BiddingStrategy(str, Enum):
    """Bidding strategy enum following Google Ads API v22."""
    MAXIMIZE_CONVERSIONS = 'maximize_conversions'
    MAXIMIZE_CONVERSION_VALUE = 'maximize_conversion_value'
    MAXIMIZE_CLICKS = 'maximize_clicks'
    TARGET_CPA = 'target_cpa'
    TARGET_ROAS = 'target_roas'
    TARGET_CPC = 'target_cpc'
    MANUAL_CPC = 'manual_cpc'
    MANUAL_CPM = 'manual_cpm'
    TARGET_CPM = 'target_cpm'


def utc_now():
    """Get current UTC datetime (Python 3.12+ compatible)."""
    return datetime.now(timezone.utc)


class Campaign(db.Model):
    """
    Campaign model for storing marketing campaign data.

    Campaigns start in DRAFT status and can be published to Google Ads.
    Once published, they receive a google_campaign_id and status becomes PUBLISHED.
    """
    __tablename__ = 'campaigns'

    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Owner (for authorization)
    owner_id = db.Column(db.String(255), nullable=True, index=True)

    # Campaign basic info
    name = db.Column(db.String(255), nullable=False, index=True)
    objective = db.Column(db.String(100), nullable=False)  # SALES, LEADS, WEBSITE_TRAFFIC
    campaign_type = db.Column(db.String(100), default='DEMAND_GEN', nullable=False)

    # Budget and dates
    daily_budget = db.Column(db.Integer, nullable=False)  # Amount in micros (1 USD = 1,000,000)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

    # Bidding strategy
    bidding_strategy = db.Column(db.String(50), nullable=True)
    target_cpa = db.Column(db.Integer, nullable=True)  # Amount in micros
    target_roas = db.Column(db.Float, nullable=True)  # Target ROAS multiplier (e.g., 2.0 = 200%)

    # Status tracking
    status = db.Column(db.String(50), default=CampaignStatus.DRAFT.value, nullable=False, index=True)
    # DRAFT - Local only, not published
    # PUBLISHED - Published to Google Ads (but starts PAUSED)
    # PAUSED - Explicitly paused in Google Ads
    # ERROR - Failed to publish

    # Google Ads mapping
    google_campaign_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    google_ad_group_id = db.Column(db.String(100), nullable=True)
    google_ad_id = db.Column(db.String(100), nullable=True)

    # Ad creative info (legacy fields)
    ad_group_name = db.Column(db.String(255), nullable=True)
    ad_headline = db.Column(db.String(255), nullable=True)
    ad_description = db.Column(db.Text, nullable=True)
    asset_url = db.Column(db.String(500), nullable=True)
    final_url = db.Column(db.String(500), nullable=True)  # Landing page URL

    # New dynamic campaign fields
    headlines = db.Column(db.JSON, nullable=True)  # Array of headline strings
    long_headline = db.Column(db.String(100), nullable=True)  # For DISPLAY/PERFORMANCE_MAX
    descriptions = db.Column(db.JSON, nullable=True)  # Array of description strings
    business_name = db.Column(db.String(25), nullable=True)
    images = db.Column(db.JSON, nullable=True)  # {landscape_url, square_url, logo_url}
    keywords = db.Column(db.JSON, nullable=True)  # Array of keyword strings (for SEARCH)
    video_url = db.Column(db.String(500), nullable=True)  # For VIDEO campaigns
    merchant_center_id = db.Column(db.String(100), nullable=True)  # For SHOPPING campaigns

    # Timestamps (using timezone-aware UTC datetime)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Constraints and indexes
    __table_args__ = (
        db.CheckConstraint('daily_budget > 0', name='check_positive_budget'),
        db.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name='check_date_order'
        ),
        db.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'PAUSED', 'ERROR')",
            name='check_valid_status'
        ),
        # Composite indexes for common query patterns
        db.Index('ix_campaigns_owner_created', 'owner_id', 'created_at'),
        db.Index('ix_campaigns_owner_status_created', 'owner_id', 'status', 'created_at'),
        db.Index('ix_campaigns_status_created', 'status', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Campaign(id='{self.id}', name='{self.name}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize campaign to dictionary for JSON response.

        Returns:
            Dictionary representation of the campaign
        """
        return {
            'id': self.id,
            'name': self.name,
            'objective': self.objective,
            'campaign_type': self.campaign_type,
            'daily_budget': self.daily_budget,
            'daily_budget_usd': self.daily_budget / 1_000_000,  # Convert micros to USD
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'bidding_strategy': self.bidding_strategy,
            'target_cpa': self.target_cpa,
            'target_cpa_usd': self.target_cpa / 1_000_000 if self.target_cpa else None,
            'target_roas': self.target_roas,
            'google_campaign_id': self.google_campaign_id,
            'google_ad_group_id': self.google_ad_group_id,
            'google_ad_id': self.google_ad_id,
            'ad_group_name': self.ad_group_name,
            'ad_headline': self.ad_headline,
            'ad_description': self.ad_description,
            'asset_url': self.asset_url,
            'final_url': self.final_url,
            'headlines': self.headlines,
            'long_headline': self.long_headline,
            'descriptions': self.descriptions,
            'business_name': self.business_name,
            'images': self.images,
            'keywords': self.keywords,
            'video_url': self.video_url,
            'merchant_center_id': self.merchant_center_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Campaign':
        """
        Create a Campaign instance from a dictionary.

        Args:
            data: Dictionary with campaign data

        Returns:
            Campaign instance
        """
        return cls(
            name=data.get('name'),
            objective=data.get('objective'),
            campaign_type=data.get('campaign_type', 'DEMAND_GEN'),
            daily_budget=data.get('daily_budget'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            bidding_strategy=data.get('bidding_strategy'),
            target_cpa=data.get('target_cpa'),
            target_roas=data.get('target_roas'),
            ad_group_name=data.get('ad_group_name'),
            ad_headline=data.get('ad_headline'),
            ad_description=data.get('ad_description'),
            asset_url=data.get('asset_url'),
            final_url=data.get('final_url'),
            headlines=data.get('headlines'),
            long_headline=data.get('long_headline'),
            descriptions=data.get('descriptions'),
            business_name=data.get('business_name'),
            images=data.get('images'),
            keywords=data.get('keywords'),
            video_url=data.get('video_url'),
            merchant_center_id=data.get('merchant_center_id'),
        )
