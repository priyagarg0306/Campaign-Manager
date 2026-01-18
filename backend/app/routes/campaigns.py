"""
Campaign API routes.
"""
import logging
import re
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.services.campaign_service import CampaignService
from app.services.google_ads_service import google_ads_service
from app.schemas.campaign_schema import (
    CampaignCreateSchema,
    CampaignUpdateSchema,
    validate_campaign_for_publish,
    CAMPAIGN_TYPE_REQUIREMENTS,
)
from app.utils.validators import is_valid_uuid
from app.utils.google_ads_validators import validate_campaign_for_google_ads
from app import limiter

campaigns_bp = Blueprint('campaigns', __name__)
logger = logging.getLogger(__name__)

# Schema instances
create_schema = CampaignCreateSchema()
update_schema = CampaignUpdateSchema()


def sanitize_error_message(error: Exception, include_details: bool = False) -> str:
    """
    Sanitize error messages to avoid leaking sensitive information.

    Args:
        error: The exception that occurred
        include_details: Whether to include error details for safe messages

    Returns:
        Safe error message string
    """
    # Never expose these patterns to clients (match actual secrets, not mentions)
    sensitive_patterns = [
        r'password\s*[=:]',
        r'secret\s*[=:]',
        r'token\s*[=:]',
        r'api_key\s*[=:]',
        r'credential\s*[=:]',
        r'connection.*string\s*[=:]',
        r'postgresql://[^\s]+',
        r'mysql://[^\s]+',
        r'redis://[^\s]+',
    ]

    error_str = str(error)
    for pattern in sensitive_patterns:
        if re.search(pattern, error_str, re.IGNORECASE):
            return 'An internal error occurred'

    # Return the actual error message if it doesn't contain sensitive data
    return error_str


@campaigns_bp.route('/api/campaigns', methods=['POST'])
@limiter.limit("10 per minute")
def create_campaign():
    """
    Create a new campaign (LOCAL DB only).

    Request body should contain:
    - name: string (required)
    - objective: string (required) - SALES, LEADS, or WEBSITE_TRAFFIC
    - daily_budget: integer (required) - Amount in micros
    - start_date: string (required) - ISO date format
    - end_date: string (optional)
    - campaign_type: string (optional) - defaults to DEMAND_GEN
    - ad_group_name: string (optional)
    - ad_headline: string (optional)
    - ad_description: string (optional)
    - asset_url: string (optional) - URL
    - final_url: string (optional) - Landing page URL

    Returns:
        201: Campaign created successfully
        400: Validation error
        500: Server error
    """
    try:
        # Get and validate request data
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Validate with schema
        try:
            validated_data = create_schema.load(data)
        except ValidationError as err:
            return jsonify({'error': 'Validation error', 'details': err.messages}), 400

        # Create campaign
        campaign = CampaignService.create_campaign(validated_data)

        logger.info(f"Campaign created: {campaign.id}")
        return jsonify(campaign.to_dict()), 201

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'error': sanitize_error_message(e, include_details=True)}), 400

    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@campaigns_bp.route('/api/campaigns', methods=['GET'])
@limiter.limit("60 per minute")
def get_campaigns():
    """
    Get all campaigns.

    Query parameters:
    - status: Filter by status (DRAFT, PUBLISHED, PAUSED, ERROR)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)

    Returns:
        200: Paginated list of campaigns
        500: Server error
    """
    try:
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)

        # Get paginated campaigns
        result = CampaignService.get_campaigns_paginated(
            status=status.upper() if status else None,
            page=page,
            per_page=per_page
        )

        return jsonify({
            'campaigns': [c.to_dict() for c in result['campaigns']],
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total': result['total'],
                'pages': result['pages']
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>', methods=['GET'])
@limiter.limit("60 per minute")
def get_campaign(campaign_id: str):
    """
    Get a single campaign by ID.

    Args:
        campaign_id: UUID of the campaign

    Returns:
        200: Campaign data
        400: Invalid ID format
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        campaign = CampaignService.get_campaign_by_id(campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        return jsonify(campaign.to_dict()), 200

    except Exception as e:
        logger.error(f"Error fetching campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>', methods=['PUT'])
@limiter.limit("30 per minute")
def update_campaign(campaign_id: str):
    """
    Update an existing campaign.

    Args:
        campaign_id: UUID of the campaign

    Returns:
        200: Updated campaign data
        400: Validation error
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        # Get and validate request data
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Validate with schema
        try:
            validated_data = update_schema.load(data)
        except ValidationError as err:
            return jsonify({'error': 'Validation error', 'details': err.messages}), 400

        # Update campaign
        campaign = CampaignService.update_campaign(campaign_id, validated_data)

        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        logger.info(f"Campaign updated: {campaign.id}")
        return jsonify(campaign.to_dict()), 200

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'error': sanitize_error_message(e, include_details=True)}), 400

    except Exception as e:
        logger.error(f"Error updating campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_campaign(campaign_id: str):
    """
    Delete a campaign.

    Args:
        campaign_id: UUID of the campaign

    Returns:
        204: Campaign deleted
        400: Invalid ID or cannot delete published campaign
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        deleted = CampaignService.delete_campaign(campaign_id)

        if not deleted:
            return jsonify({'error': 'Campaign not found'}), 404

        logger.info(f"Campaign deleted: {campaign_id}")
        return '', 204

    except ValueError as e:
        logger.warning(f"Cannot delete campaign: {str(e)}")
        return jsonify({'error': sanitize_error_message(e, include_details=True)}), 400

    except Exception as e:
        logger.error(f"Error deleting campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>/publish', methods=['POST'])
@limiter.limit("5 per minute")
def publish_campaign(campaign_id: str):
    """
    Publish a campaign to Google Ads.

    This endpoint:
    1. Validates the campaign is ready for publishing
    2. Creates the campaign in Google Ads (with PAUSED status)
    3. Creates an ad group
    4. Creates an ad
    5. Updates the local campaign with Google Ads IDs

    Args:
        campaign_id: UUID of the campaign

    Returns:
        200: Campaign published successfully
        400: Validation error or already published
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        campaign = CampaignService.get_campaign_by_id(campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        # Check if already published
        if campaign.status == 'PUBLISHED':
            return jsonify({'error': 'Campaign is already published'}), 400

        # Validate campaign is ready for publishing
        validation_errors = CampaignService.validate_for_publish(campaign)
        if validation_errors:
            return jsonify({
                'error': 'Campaign is not ready for publishing',
                'details': validation_errors
            }), 400

        # Check if Google Ads API is configured
        if not google_ads_service.is_configured():
            return jsonify({
                'error': 'Google Ads API is not configured',
                'message': 'Please configure Google Ads credentials to publish campaigns'
            }), 400

        # Publish to Google Ads
        result = google_ads_service.publish_campaign(campaign)

        # Update campaign status
        updated_campaign = CampaignService.update_campaign_status(
            campaign_id,
            'PUBLISHED',
            result['google_campaign_id'],
            result['google_ad_group_id'],
            result.get('google_ad_id')
        )

        logger.info(
            f"Campaign {campaign_id} published to Google Ads: "
            f"campaign_id={result['google_campaign_id']}"
        )

        return jsonify({
            'message': 'Campaign published successfully',
            'campaign': updated_campaign.to_dict(),
            'google_ads': {
                'campaign_id': result['google_campaign_id'],
                'ad_group_id': result['google_ad_group_id'],
                'ad_id': result.get('google_ad_id')
            }
        }), 200

    except Exception as e:
        logger.error(f"Error publishing campaign: {str(e)}")

        # Update campaign status to ERROR
        try:
            CampaignService.update_campaign_status(campaign_id, 'ERROR')
        except Exception:
            pass

        # Sanitize error message before returning
        safe_message = sanitize_error_message(e)
        return jsonify({'error': f'Failed to publish campaign: {safe_message}'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>/pause', methods=['POST'])
@limiter.limit("10 per minute")
def pause_campaign(campaign_id: str):
    """
    Pause a campaign in Google Ads.

    Args:
        campaign_id: UUID of the campaign

    Returns:
        200: Campaign paused successfully
        400: Invalid ID or campaign not published
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        campaign = CampaignService.get_campaign_by_id(campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        if not campaign.google_campaign_id:
            return jsonify({'error': 'Campaign is not published to Google Ads'}), 400

        # Pause in Google Ads
        google_ads_service.pause_campaign(campaign.google_campaign_id)

        # Update local status
        updated_campaign = CampaignService.update_campaign_status(
            campaign_id, 'PAUSED'
        )

        logger.info(f"Campaign {campaign_id} paused")

        return jsonify({
            'message': 'Campaign paused successfully',
            'campaign': updated_campaign.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        safe_message = sanitize_error_message(e)
        return jsonify({'error': f'Failed to pause campaign: {safe_message}'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>/enable', methods=['POST'])
@limiter.limit("10 per minute")
def enable_campaign(campaign_id: str):
    """
    Enable a paused campaign in Google Ads.

    Args:
        campaign_id: UUID of the campaign

    Returns:
        200: Campaign enabled successfully
        400: Invalid ID or campaign not published
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        campaign = CampaignService.get_campaign_by_id(campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        if not campaign.google_campaign_id:
            return jsonify({'error': 'Campaign is not published to Google Ads'}), 400

        # Enable in Google Ads
        google_ads_service.enable_campaign(campaign.google_campaign_id)

        # Update local status
        updated_campaign = CampaignService.update_campaign_status(
            campaign_id, 'PUBLISHED'
        )

        logger.info(f"Campaign {campaign_id} enabled")

        return jsonify({
            'message': 'Campaign enabled successfully',
            'campaign': updated_campaign.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error enabling campaign: {str(e)}")
        safe_message = sanitize_error_message(e)
        return jsonify({'error': f'Failed to enable campaign: {safe_message}'}), 500


@campaigns_bp.route('/api/campaigns/<campaign_id>/validate', methods=['POST'])
@limiter.limit("30 per minute")
def validate_campaign(campaign_id: str):
    """
    Pre-flight validation for campaign before publishing.

    Validates the campaign against Google Ads API requirements without
    actually publishing. Use this endpoint to check if a campaign is
    ready for publishing and get detailed validation feedback.

    Args:
        campaign_id: UUID of the campaign

    Returns:
        200: Validation results with valid flag and any errors
        400: Invalid campaign ID format
        404: Campaign not found
        500: Server error
    """
    try:
        # Validate UUID format
        if not is_valid_uuid(campaign_id):
            return jsonify({'error': 'Invalid campaign ID format'}), 400

        campaign = CampaignService.get_campaign_by_id(campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404

        # Run both standard and Google Ads specific validations
        standard_errors = validate_campaign_for_publish(campaign)
        google_ads_validation = validate_campaign_for_google_ads(campaign)

        # Combine all errors
        all_errors = standard_errors + google_ads_validation.get('errors', [])

        # Remove duplicates while preserving order
        seen = set()
        unique_errors = []
        for error in all_errors:
            if error not in seen:
                seen.add(error)
                unique_errors.append(error)

        # Get campaign type requirements for additional context
        campaign_type = campaign.campaign_type
        requirements = CAMPAIGN_TYPE_REQUIREMENTS.get(campaign_type, {})

        # Check if VIDEO campaign (cannot be created via API)
        is_video = campaign_type == 'VIDEO'
        api_creation_supported = requirements.get('api_creation_supported', True)

        is_valid = len(unique_errors) == 0 and api_creation_supported

        response = {
            'valid': is_valid,
            'errors': unique_errors,
            'campaign_type': campaign_type,
            'code': 'VALIDATION_ERROR' if unique_errors else None,
        }

        # Add warnings for VIDEO campaigns
        if is_video or not api_creation_supported:
            response['warnings'] = [
                f'{campaign_type} campaigns cannot be created via the Google Ads API. '
                'This campaign can be saved as a draft, but publishing requires Google Ads UI.'
            ]

        # Add requirements info for context
        response['requirements'] = {
            'headlines': requirements.get('headlines', {}),
            'descriptions': requirements.get('descriptions', {}),
            'short_description_required': requirements.get('short_description_required', False),
            'short_description_max_length': requirements.get('short_description_max_length'),
        }

        logger.info(f"Validation for campaign {campaign_id}: valid={is_valid}, errors={len(unique_errors)}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error validating campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
