"""
Marshmallow schemas for Campaign validation.
"""
from datetime import date
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load

# Valid bidding strategies per campaign type (Google Ads API v22)
BIDDING_STRATEGIES_BY_TYPE = {
    'DEMAND_GEN': ['maximize_conversions', 'target_cpa', 'maximize_clicks', 'target_cpc'],
    'PERFORMANCE_MAX': ['maximize_conversions', 'maximize_conversion_value'],
    'SEARCH': ['manual_cpc', 'maximize_clicks', 'target_cpa', 'maximize_conversions'],
    'DISPLAY': ['manual_cpc', 'manual_cpm', 'maximize_conversions', 'target_cpa'],
    'VIDEO': ['maximize_conversions', 'target_cpa', 'target_cpm'],
    'SHOPPING': ['maximize_clicks', 'target_roas', 'manual_cpc'],
}

ALL_BIDDING_STRATEGIES = [
    'maximize_conversions', 'maximize_conversion_value', 'maximize_clicks',
    'target_cpa', 'target_roas', 'target_cpc', 'manual_cpc', 'manual_cpm', 'target_cpm'
]

# Campaign type requirements (aligned with Google Ads API v22)
CAMPAIGN_TYPE_REQUIREMENTS = {
    'DEMAND_GEN': {
        'headlines': {'min': 1, 'max': 5, 'max_length': 40},
        'descriptions': {'min': 1, 'max': 5, 'max_length': 90},
        'business_name': {'required': True, 'max_length': 25},
        'images': {'required': True},
        'final_url': {'required': True},
    },
    'PERFORMANCE_MAX': {
        'headlines': {'min': 3, 'max': 15, 'max_length': 30},
        'long_headline': {'required': True, 'max_length': 90},
        'descriptions': {'min': 2, 'max': 5, 'max_length': 90},
        'short_description_required': True,  # At least one description must be <= 60 chars
        'short_description_max_length': 60,
        'business_name': {'required': True, 'max_length': 25},
        'images': {'required': True},
        'final_url': {'required': True},
    },
    'SEARCH': {
        # RSA requires minimum 3 headlines and 2 descriptions
        'headlines': {'min': 3, 'max': 15, 'max_length': 30},
        'descriptions': {'min': 2, 'max': 4, 'max_length': 90},
        'keywords': {'required': True, 'unique': True},  # Keywords must be unique
        'final_url': {'required': True},
    },
    'DISPLAY': {
        'headlines': {'min': 1, 'max': 5, 'max_length': 30},
        'long_headline': {'required': True, 'max_length': 90},
        'descriptions': {'min': 1, 'max': 5, 'max_length': 90},
        'business_name': {'required': True, 'max_length': 25},
        'images': {'required': True},
        'final_url': {'required': True},
    },
    'VIDEO': {
        'video_url': {'required': True},
        'headlines': {'min': 0, 'max': 5, 'max_length': 30},
        'descriptions': {'min': 0, 'max': 5, 'max_length': 90},
        'api_creation_supported': False,  # VIDEO campaigns cannot be created via API
    },
    'SHOPPING': {
        'merchant_center_id': {'required': True},
    },
}


class ImageAssetsSchema(Schema):
    """Schema for image assets."""
    landscape_url = fields.Url(allow_none=True, load_default=None)
    square_url = fields.Url(allow_none=True, load_default=None)
    logo_url = fields.Url(allow_none=True, load_default=None)


class CampaignCreateSchema(Schema):
    """Schema for creating a new campaign."""

    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={'required': 'Campaign name is required'}
    )
    objective = fields.String(
        required=True,
        validate=validate.OneOf(
            ['SALES', 'LEADS', 'WEBSITE_TRAFFIC'],
            error='Objective must be one of: SALES, LEADS, WEBSITE_TRAFFIC'
        )
    )
    campaign_type = fields.String(
        load_default='DEMAND_GEN',
        validate=validate.OneOf(
            ['DEMAND_GEN', 'SEARCH', 'DISPLAY', 'VIDEO', 'SHOPPING', 'PERFORMANCE_MAX'],
            error='Invalid campaign type'
        )
    )
    daily_budget = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error='Daily budget must be greater than 0')
    )
    start_date = fields.Date(
        required=True,
        error_messages={'required': 'Start date is required'}
    )
    end_date = fields.Date(
        load_default=None,
        allow_none=True
    )

    # Bidding strategy fields
    bidding_strategy = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(ALL_BIDDING_STRATEGIES, error='Invalid bidding strategy')
    )
    target_cpa = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error='Target CPA must be greater than 0')
    )
    target_roas = fields.Float(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=0.01, error='Target ROAS must be greater than 0')
    )

    # Legacy ad creative fields
    ad_group_name = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255)
    )
    ad_headline = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=255)
    )
    ad_description = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=1000)
    )
    asset_url = fields.Url(
        load_default=None,
        allow_none=True
    )
    final_url = fields.Url(
        load_default=None,
        allow_none=True
    )

    # New dynamic campaign fields
    headlines = fields.List(
        fields.String(validate=validate.Length(max=40)),
        load_default=None,
        allow_none=True
    )
    long_headline = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=90)
    )
    descriptions = fields.List(
        fields.String(validate=validate.Length(max=90)),
        load_default=None,
        allow_none=True
    )
    business_name = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=25)
    )
    images = fields.Nested(ImageAssetsSchema, load_default=None, allow_none=True)
    keywords = fields.List(
        fields.String(validate=validate.Length(max=80)),
        load_default=None,
        allow_none=True
    )
    video_url = fields.Url(
        load_default=None,
        allow_none=True
    )
    merchant_center_id = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Length(max=100)
    )

    @validates('start_date')
    def validate_start_date(self, value):
        """Validate that start date is not in the past."""
        if value < date.today():
            raise ValidationError('Start date cannot be in the past')

    @validates('end_date')
    def validate_end_date(self, value):
        """Validate end date if provided."""
        if value is not None and value < date.today():
            raise ValidationError('End date cannot be in the past')

    @post_load
    def validate_campaign_data(self, data, **kwargs):
        """Validate campaign data including dates and type-specific fields."""
        # Validate date order
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise ValidationError('End date must be after start date', field_name='end_date')

        # Validate bidding strategy matches campaign type
        campaign_type = data.get('campaign_type', 'DEMAND_GEN')
        bidding_strategy = data.get('bidding_strategy')
        if bidding_strategy:
            valid_strategies = BIDDING_STRATEGIES_BY_TYPE.get(campaign_type, [])
            if bidding_strategy not in valid_strategies:
                raise ValidationError(
                    f'Bidding strategy {bidding_strategy} is not valid for {campaign_type} campaigns. '
                    f'Valid options: {", ".join(valid_strategies)}',
                    field_name='bidding_strategy'
                )

        # Validate target CPA/ROAS requirements
        if bidding_strategy == 'target_cpa' and not data.get('target_cpa'):
            raise ValidationError(
                'Target CPA value is required when using target_cpa bidding strategy',
                field_name='target_cpa'
            )
        if bidding_strategy == 'target_roas' and not data.get('target_roas'):
            raise ValidationError(
                'Target ROAS value is required when using target_roas bidding strategy',
                field_name='target_roas'
            )

        return data


class CampaignUpdateSchema(Schema):
    """Schema for updating an existing campaign."""

    name = fields.String(
        validate=validate.Length(min=1, max=255)
    )
    objective = fields.String(
        validate=validate.OneOf(
            ['SALES', 'LEADS', 'WEBSITE_TRAFFIC'],
            error='Objective must be one of: SALES, LEADS, WEBSITE_TRAFFIC'
        )
    )
    campaign_type = fields.String(
        validate=validate.OneOf(
            ['DEMAND_GEN', 'SEARCH', 'DISPLAY', 'VIDEO', 'SHOPPING', 'PERFORMANCE_MAX'],
            error='Invalid campaign type'
        )
    )
    daily_budget = fields.Integer(
        validate=validate.Range(min=1, error='Daily budget must be greater than 0')
    )
    start_date = fields.Date()
    end_date = fields.Date(allow_none=True)

    # Bidding strategy fields
    bidding_strategy = fields.String(
        allow_none=True,
        validate=validate.OneOf(ALL_BIDDING_STRATEGIES, error='Invalid bidding strategy')
    )
    target_cpa = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=1, error='Target CPA must be greater than 0')
    )
    target_roas = fields.Float(
        allow_none=True,
        validate=validate.Range(min=0.01, error='Target ROAS must be greater than 0')
    )

    # Legacy ad creative fields
    ad_group_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=255)
    )
    ad_headline = fields.String(
        allow_none=True,
        validate=validate.Length(max=255)
    )
    ad_description = fields.String(
        allow_none=True,
        validate=validate.Length(max=1000)
    )
    asset_url = fields.Url(allow_none=True)
    final_url = fields.Url(allow_none=True)

    # New dynamic campaign fields
    headlines = fields.List(
        fields.String(validate=validate.Length(max=40)),
        allow_none=True
    )
    long_headline = fields.String(
        allow_none=True,
        validate=validate.Length(max=90)
    )
    descriptions = fields.List(
        fields.String(validate=validate.Length(max=90)),
        allow_none=True
    )
    business_name = fields.String(
        allow_none=True,
        validate=validate.Length(max=25)
    )
    images = fields.Nested(ImageAssetsSchema, allow_none=True)
    keywords = fields.List(
        fields.String(validate=validate.Length(max=80)),
        allow_none=True
    )
    video_url = fields.Url(allow_none=True)
    merchant_center_id = fields.String(
        allow_none=True,
        validate=validate.Length(max=100)
    )

    @validates('start_date')
    def validate_start_date(self, value):
        """Validate that start date is not in the past when updating."""
        if value is not None and value < date.today():
            raise ValidationError('Start date cannot be in the past')

    @validates('end_date')
    def validate_end_date(self, value):
        """Validate end date if provided."""
        if value is not None and value < date.today():
            raise ValidationError('End date cannot be in the past')

    @post_load
    def validate_dates(self, data, **kwargs):
        """Validate that end_date is after start_date if both provided."""
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise ValidationError('End date must be after start date', field_name='end_date')
        return data


def validate_campaign_for_publish(campaign) -> list:
    """
    Validate that a campaign has all required fields for publishing based on its type.

    Args:
        campaign: Campaign model instance

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    campaign_type = campaign.campaign_type
    requirements = CAMPAIGN_TYPE_REQUIREMENTS.get(campaign_type, {})

    # Check VIDEO campaign API restriction
    if requirements.get('api_creation_supported') is False:
        errors.append(
            f'{campaign_type} campaigns cannot be created via the Google Ads API. '
            'Please use Google Ads UI or Google Ads Scripts.'
        )

    # Validate headlines
    if 'headlines' in requirements:
        req = requirements['headlines']
        headlines = campaign.headlines or []
        if len(headlines) < req['min']:
            if campaign_type == 'SEARCH':
                errors.append(
                    f'{campaign_type} campaigns require at least {req["min"]} headlines '
                    '(Responsive Search Ads minimum requirement)'
                )
            else:
                errors.append(f'{campaign_type} campaigns require at least {req["min"]} headline(s)')
        if len(headlines) > req['max']:
            errors.append(f'{campaign_type} campaigns allow at most {req["max"]} headlines')
        for i, headline in enumerate(headlines):
            if len(headline) > req['max_length']:
                errors.append(f'Headline {i+1} exceeds {req["max_length"]} characters')

    # Validate long headline
    if 'long_headline' in requirements:
        req = requirements['long_headline']
        if req.get('required') and not campaign.long_headline:
            errors.append(f'{campaign_type} campaigns require a long headline')
        elif campaign.long_headline and len(campaign.long_headline) > req['max_length']:
            errors.append(f'Long headline exceeds {req["max_length"]} characters')

    # Validate descriptions
    if 'descriptions' in requirements:
        req = requirements['descriptions']
        descriptions = campaign.descriptions or []
        if len(descriptions) < req['min']:
            if campaign_type == 'SEARCH':
                errors.append(
                    f'{campaign_type} campaigns require at least {req["min"]} descriptions '
                    '(Responsive Search Ads minimum requirement)'
                )
            else:
                errors.append(f'{campaign_type} campaigns require at least {req["min"]} description(s)')
        if len(descriptions) > req['max']:
            errors.append(f'{campaign_type} campaigns allow at most {req["max"]} descriptions')
        for i, desc in enumerate(descriptions):
            if len(desc) > req['max_length']:
                errors.append(f'Description {i+1} exceeds {req["max_length"]} characters')

    # Validate PMax short description requirement
    if requirements.get('short_description_required'):
        descriptions = campaign.descriptions or []
        short_max = requirements.get('short_description_max_length', 60)
        if descriptions and not any(len(desc) <= short_max for desc in descriptions):
            errors.append(
                f'{campaign_type} requires at least one description of {short_max} characters '
                'or fewer (short description requirement)'
            )

    # Validate business name
    if 'business_name' in requirements:
        req = requirements['business_name']
        if req.get('required') and not campaign.business_name:
            errors.append(f'{campaign_type} campaigns require a business name')
        elif campaign.business_name and len(campaign.business_name) > req['max_length']:
            errors.append(f'Business name exceeds {req["max_length"]} characters')

    # Validate images
    if 'images' in requirements:
        req = requirements['images']
        if req.get('required'):
            images = campaign.images or {}
            if not any([images.get('landscape_url'), images.get('square_url'), images.get('logo_url')]):
                errors.append(f'{campaign_type} campaigns require at least one image')

    # Validate final URL
    if 'final_url' in requirements:
        req = requirements['final_url']
        if req.get('required') and not campaign.final_url:
            errors.append(f'{campaign_type} campaigns require a final URL')

    # Validate keywords (SEARCH)
    if 'keywords' in requirements:
        req = requirements['keywords']
        keywords = campaign.keywords or []
        if req.get('required') and not keywords:
            errors.append(f'{campaign_type} campaigns require keywords')

        # Validate keyword uniqueness
        if req.get('unique') and keywords:
            seen = set()
            for keyword in keywords:
                normalized = keyword.strip().lower()
                if normalized in seen:
                    errors.append(f"Duplicate keyword detected: '{keyword}'")
                seen.add(normalized)

    # Validate video URL (VIDEO)
    if 'video_url' in requirements:
        req = requirements['video_url']
        if req.get('required') and not campaign.video_url:
            errors.append(f'{campaign_type} campaigns require a video URL')

    # Validate merchant center ID (SHOPPING)
    if 'merchant_center_id' in requirements:
        req = requirements['merchant_center_id']
        if req.get('required') and not campaign.merchant_center_id:
            errors.append(f'{campaign_type} campaigns require a Merchant Center ID')

    # Validate bidding strategy
    if campaign.bidding_strategy:
        valid_strategies = BIDDING_STRATEGIES_BY_TYPE.get(campaign_type, [])
        if campaign.bidding_strategy not in valid_strategies:
            errors.append(
                f'Bidding strategy {campaign.bidding_strategy} is not valid for {campaign_type} campaigns'
            )
        if campaign.bidding_strategy == 'target_cpa' and not campaign.target_cpa:
            errors.append('Target CPA value is required for target_cpa bidding strategy')
        if campaign.bidding_strategy == 'target_roas' and not campaign.target_roas:
            errors.append('Target ROAS value is required for target_roas bidding strategy')

    return errors
