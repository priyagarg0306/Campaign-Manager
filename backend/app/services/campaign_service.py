"""
Campaign service for business logic operations.
"""
import logging
import math
from datetime import date
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.campaign import Campaign, CampaignStatus
from app.schemas.campaign_schema import validate_campaign_for_publish

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('audit')

# Default limit for unbounded queries to prevent memory exhaustion
DEFAULT_QUERY_LIMIT = 1000


class CampaignService:
    """Service class for campaign operations."""

    @staticmethod
    def create_campaign(data: Dict[str, Any]) -> Campaign:
        """
        Create a new campaign with DRAFT status.

        Args:
            data: Validated campaign data

        Returns:
            Created Campaign instance

        Raises:
            ValueError: If required fields are missing
            SQLAlchemyError: If database operation fails
        """
        # Validate required fields
        required_fields = ['name', 'objective', 'daily_budget', 'start_date']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Missing required field: {field}")

        # Parse dates if they're strings
        if isinstance(data.get('start_date'), str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if isinstance(data.get('end_date'), str):
            data['end_date'] = date.fromisoformat(data['end_date'])

        # Create campaign with DRAFT status
        campaign = Campaign(
            name=data['name'],
            owner_id=data.get('owner_id'),
            objective=data['objective'],
            campaign_type=data.get('campaign_type', 'DEMAND_GEN'),
            daily_budget=data['daily_budget'],
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            # Bidding strategy
            bidding_strategy=data.get('bidding_strategy'),
            target_cpa=data.get('target_cpa'),
            target_roas=data.get('target_roas'),
            # Legacy fields
            ad_group_name=data.get('ad_group_name'),
            ad_headline=data.get('ad_headline'),
            ad_description=data.get('ad_description'),
            asset_url=data.get('asset_url'),
            final_url=data.get('final_url'),
            # New dynamic fields
            headlines=data.get('headlines'),
            long_headline=data.get('long_headline'),
            descriptions=data.get('descriptions'),
            business_name=data.get('business_name'),
            images=data.get('images'),
            keywords=data.get('keywords'),
            video_url=data.get('video_url'),
            merchant_center_id=data.get('merchant_center_id'),
            status=CampaignStatus.DRAFT.value
        )

        try:
            db.session.add(campaign)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error creating campaign: {e}")
            raise

        # Audit log
        audit_logger.info(
            f"CAMPAIGN_CREATED: id={campaign.id}, name={campaign.name}, "
            f"type={campaign.campaign_type}, owner={campaign.owner_id}"
        )
        logger.info(f"Campaign created: {campaign.id} - {campaign.name}")
        return campaign

    @staticmethod
    def get_all_campaigns(limit: int = DEFAULT_QUERY_LIMIT) -> List[Campaign]:
        """
        Get all campaigns ordered by creation date (newest first).

        Args:
            limit: Maximum number of campaigns to return (default 1000)

        Returns:
            List of Campaign instances
        """
        stmt = (
            select(Campaign)
            .order_by(Campaign.created_at.desc())
            .limit(limit)
        )
        return list(db.session.scalars(stmt).all())

    @staticmethod
    def get_campaigns_paginated(
        owner_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated campaigns filtered by owner and optionally by status.

        Args:
            owner_id: Filter by campaign owner
            status: Optional status filter (DRAFT, PUBLISHED, PAUSED, ERROR)
            page: Page number (1-indexed)
            per_page: Items per page (max 100)

        Returns:
            Dictionary with campaigns list and pagination info
        """
        # Validate pagination parameters
        page = max(1, page)
        per_page = min(max(1, per_page), 100)

        # Build base query
        stmt = select(Campaign)
        count_stmt = select(func.count(Campaign.id))

        if owner_id:
            stmt = stmt.where(Campaign.owner_id == owner_id)
            count_stmt = count_stmt.where(Campaign.owner_id == owner_id)

        if status:
            stmt = stmt.where(Campaign.status == status)
            count_stmt = count_stmt.where(Campaign.status == status)

        # Order by creation date (newest first)
        stmt = stmt.order_by(Campaign.created_at.desc())

        # Get total count efficiently
        total = db.session.scalar(count_stmt) or 0

        # Calculate pagination
        pages = math.ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page

        # Get page of results
        stmt = stmt.offset(offset).limit(per_page)
        campaigns = list(db.session.scalars(stmt).all())

        return {
            'campaigns': campaigns,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages
        }

    @staticmethod
    def get_campaign_by_id(campaign_id: str) -> Optional[Campaign]:
        """
        Get a campaign by its ID.

        Args:
            campaign_id: UUID of the campaign

        Returns:
            Campaign instance or None if not found
        """
        return db.session.get(Campaign, campaign_id)

    @staticmethod
    def get_campaigns_by_status(status: str) -> List[Campaign]:
        """
        Get campaigns filtered by status.

        Args:
            status: Campaign status (DRAFT, PUBLISHED, PAUSED, ERROR)

        Returns:
            List of Campaign instances with matching status
        """
        stmt = (
            select(Campaign)
            .where(Campaign.status == status)
            .order_by(Campaign.created_at.desc())
        )
        return list(db.session.scalars(stmt).all())

    @staticmethod
    def update_campaign(
        campaign_id: str,
        data: Dict[str, Any],
        campaign: Optional[Campaign] = None
    ) -> Optional[Campaign]:
        """
        Update an existing campaign.

        Args:
            campaign_id: UUID of the campaign
            data: Dictionary with fields to update
            campaign: Optional pre-loaded campaign to avoid redundant query

        Returns:
            Updated Campaign instance or None if not found

        Raises:
            ValueError: If trying to update a published campaign's restricted fields
            SQLAlchemyError: If database operation fails
        """
        if campaign is None:
            campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            return None

        # Don't allow updating certain fields if already published
        if campaign.status == CampaignStatus.PUBLISHED.value:
            restricted_fields = ['objective', 'campaign_type', 'start_date']
            for field in restricted_fields:
                if field in data:
                    raise ValueError(f"Cannot update {field} for a published campaign")

        # Parse dates if they're strings
        if 'start_date' in data and isinstance(data['start_date'], str):
            data['start_date'] = date.fromisoformat(data['start_date'])
        if 'end_date' in data and isinstance(data['end_date'], str):
            data['end_date'] = date.fromisoformat(data['end_date'])

        # Update allowed fields (including new dynamic fields)
        allowed_fields = [
            'name', 'objective', 'campaign_type', 'daily_budget',
            'start_date', 'end_date', 'ad_group_name', 'ad_headline',
            'ad_description', 'asset_url', 'final_url',
            # Bidding strategy fields
            'bidding_strategy', 'target_cpa', 'target_roas',
            # New dynamic fields
            'headlines', 'long_headline', 'descriptions', 'business_name',
            'images', 'keywords', 'video_url', 'merchant_center_id'
        ]

        changed_fields = []
        for field in allowed_fields:
            if field in data:
                old_value = getattr(campaign, field)
                if old_value != data[field]:
                    changed_fields.append(field)
                setattr(campaign, field, data[field])

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error updating campaign {campaign_id}: {e}")
            raise

        # Audit log
        audit_logger.info(
            f"CAMPAIGN_UPDATED: id={campaign.id}, fields={changed_fields}, "
            f"owner={campaign.owner_id}"
        )
        logger.info(f"Campaign updated: {campaign.id}")
        return campaign

    @staticmethod
    def update_campaign_status(
        campaign_id: str,
        status: str,
        google_campaign_id: Optional[str] = None,
        google_ad_group_id: Optional[str] = None,
        google_ad_id: Optional[str] = None
    ) -> Optional[Campaign]:
        """
        Update campaign status and Google Ads IDs.

        Args:
            campaign_id: UUID of the campaign
            status: New status (DRAFT, PUBLISHED, PAUSED, ERROR)
            google_campaign_id: Google Ads campaign ID
            google_ad_group_id: Google Ads ad group ID
            google_ad_id: Google Ads ad ID

        Returns:
            Updated Campaign instance or None if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            return None

        old_status = campaign.status
        campaign.status = status

        if google_campaign_id:
            campaign.google_campaign_id = google_campaign_id
        if google_ad_group_id:
            campaign.google_ad_group_id = google_ad_group_id
        if google_ad_id:
            campaign.google_ad_id = google_ad_id

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error updating campaign status {campaign_id}: {e}")
            raise

        # Audit log
        audit_logger.info(
            f"CAMPAIGN_STATUS_CHANGED: id={campaign.id}, "
            f"old_status={old_status}, new_status={status}, "
            f"owner={campaign.owner_id}"
        )
        logger.info(f"Campaign status updated: {campaign.id} -> {status}")
        return campaign

    @staticmethod
    def delete_campaign(
        campaign_id: str,
        campaign: Optional[Campaign] = None
    ) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: UUID of the campaign
            campaign: Optional pre-loaded campaign to avoid redundant query

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If campaign is published
            SQLAlchemyError: If database operation fails
        """
        if campaign is None:
            campaign = db.session.get(Campaign, campaign_id)
        if not campaign:
            return False

        # Don't allow deleting published campaigns
        if campaign.google_campaign_id:
            raise ValueError("Cannot delete a campaign that has been published to Google Ads")

        owner_id = campaign.owner_id
        campaign_name = campaign.name

        try:
            db.session.delete(campaign)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error deleting campaign {campaign_id}: {e}")
            raise

        # Audit log
        audit_logger.info(
            f"CAMPAIGN_DELETED: id={campaign_id}, name={campaign_name}, "
            f"owner={owner_id}"
        )
        logger.info(f"Campaign deleted: {campaign_id}")
        return True

    @staticmethod
    def validate_for_publish(campaign: Campaign) -> List[str]:
        """
        Validate that a campaign is ready to be published.

        This method performs comprehensive validation based on the campaign type,
        including checking all required fields specific to each campaign type
        as defined by Google Ads API v22.

        Args:
            campaign: Campaign instance to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: List[str] = []

        # Basic validation
        if not campaign.name:
            errors.append("Campaign name is required")

        if not campaign.objective:
            errors.append("Campaign objective is required")

        if not campaign.daily_budget or campaign.daily_budget <= 0:
            errors.append("Valid daily budget is required")

        if not campaign.start_date:
            errors.append("Start date is required")

        if campaign.start_date and campaign.start_date < date.today():
            errors.append("Start date cannot be in the past")

        if campaign.end_date and campaign.start_date and campaign.end_date < campaign.start_date:
            errors.append("End date must be after start date")

        if campaign.status == 'PUBLISHED':
            errors.append("Campaign is already published")

        # Campaign type-specific validation
        type_errors = validate_campaign_for_publish(campaign)
        errors.extend(type_errors)

        return errors
