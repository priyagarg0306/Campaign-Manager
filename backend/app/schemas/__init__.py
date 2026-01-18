"""
Marshmallow schemas for request validation.
"""
from app.schemas.campaign_schema import (
    CampaignCreateSchema,
    CampaignUpdateSchema,
)

__all__ = [
    'CampaignCreateSchema',
    'CampaignUpdateSchema',
]
