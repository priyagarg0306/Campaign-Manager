"""
Google Ads API service for campaign management.
"""
import os
import logging
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

# Google Ads API character limits
HEADLINE_MAX_LENGTH = 30
LONG_HEADLINE_MAX_LENGTH = 90
DESCRIPTION_MAX_LENGTH = 90
BUSINESS_NAME_MAX_LENGTH = 25
DEMAND_GEN_HEADLINE_MAX_LENGTH = 40

# Default values
DEFAULT_BUSINESS_NAME = "Campaign Manager"

# Check if google-ads is available
try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
    GOOGLE_ADS_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_AVAILABLE = False
    logger.warning("google-ads library not installed. Google Ads functionality will be limited.")


class GoogleAdsService:
    """Service for Google Ads API operations."""

    def __init__(self):
        """Initialize Google Ads client."""
        self._client = None
        self._customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID', '').replace('-', '')

    @property
    def client(self):
        """Lazy-load Google Ads client."""
        if self._client is None:
            self._client = self._get_client()
        return self._client

    def _get_client(self) -> Optional[Any]:
        """
        Initialize and return Google Ads client.

        Returns:
            GoogleAdsClient instance or None if not configured
        """
        if not GOOGLE_ADS_AVAILABLE:
            logger.warning("Google Ads library not available")
            return None

        # Try loading from YAML file first
        config_path = os.getenv('GOOGLE_ADS_CONFIG_PATH', 'google-ads.yaml')
        if os.path.exists(config_path):
            try:
                return GoogleAdsClient.load_from_storage(config_path)
            except Exception as e:
                logger.warning(f"Failed to load from YAML: {e}")

        # Try loading from environment variables
        try:
            credentials = {
                "developer_token": os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN', ''),
                "client_id": os.getenv('GOOGLE_ADS_CLIENT_ID', ''),
                "client_secret": os.getenv('GOOGLE_ADS_CLIENT_SECRET', ''),
                "refresh_token": os.getenv('GOOGLE_ADS_REFRESH_TOKEN', ''),
                "login_customer_id": os.getenv('GOOGLE_ADS_LOGIN_CUSTOMER_ID', '').replace('-', ''),
                "use_proto_plus": True
            }

            # Check if all required credentials are present
            if all(credentials.get(k) for k in ['developer_token', 'client_id', 'client_secret', 'refresh_token']):
                return GoogleAdsClient.load_from_dict(credentials)
            else:
                logger.warning("Google Ads credentials not fully configured")
                return None

        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {e}")
            return None

    def is_configured(self) -> bool:
        """Check if Google Ads API is properly configured."""
        return self.client is not None

    def publish_campaign(self, campaign) -> Dict[str, Any]:
        """
        Publish a campaign to Google Ads.

        This creates resources based on campaign type:
        1. Campaign Budget
        2. Campaign (PAUSED status) with appropriate bidding strategy
        3. Ad Group (type depends on campaign type)
        4. Ad (type depends on campaign type)
        5. Keywords (for SEARCH campaigns)

        Args:
            campaign: Campaign model instance

        Returns:
            Dictionary with google_campaign_id, google_ad_group_id, google_ad_id

        Raises:
            Exception: If publishing fails
        """
        if not self.is_configured():
            raise Exception("Google Ads API is not configured. Please set up credentials.")

        # VIDEO campaigns cannot be created via the Google Ads API
        if campaign.campaign_type == 'VIDEO':
            raise ValueError(
                "VIDEO campaigns cannot be created via the Google Ads API. "
                "Please use Google Ads UI or Google Ads Scripts to create VIDEO campaigns."
            )

        try:
            # 1. Create campaign budget
            budget_resource = self._create_campaign_budget(
                campaign.name,
                campaign.daily_budget
            )
            logger.info(f"Created budget: {budget_resource}")

            # 2. Create campaign with bidding strategy
            campaign_resource = self._create_campaign(
                campaign.name,
                budget_resource,
                campaign.campaign_type,
                campaign.start_date,
                campaign.end_date,
                campaign.bidding_strategy,
                campaign.target_cpa,
                campaign.target_roas,
                campaign.merchant_center_id
            )
            logger.info(f"Created campaign: {campaign_resource}")

            # 3. Handle different campaign types
            # Performance Max uses Asset Groups, not Ad Groups
            if campaign.campaign_type == 'PERFORMANCE_MAX':
                # Performance Max requires Asset Groups instead of Ad Groups
                asset_group_resource = self._create_performance_max_asset_group(
                    campaign_resource,
                    campaign
                )
                logger.info(f"Created asset group: {asset_group_resource}")

                # Extract IDs from resource names
                google_campaign_id = campaign_resource.split('/')[-1]
                google_ad_group_id = asset_group_resource.split('/')[-1]  # Asset group ID
                google_ad_id = None  # PMax doesn't have separate ads
            else:
                # Standard flow for other campaign types
                ad_group_resource = self._create_ad_group(
                    campaign_resource,
                    campaign.ad_group_name or f"{campaign.name} Ad Group",
                    campaign.campaign_type
                )
                logger.info(f"Created ad group: {ad_group_resource}")

                # 4. Create ad based on campaign type
                ad_resource = self._create_ad_by_type(campaign, ad_group_resource)
                if ad_resource:
                    logger.info(f"Created ad: {ad_resource}")

                # 5. Add keywords for SEARCH campaigns
                if campaign.campaign_type == 'SEARCH' and campaign.keywords:
                    self._add_keywords(ad_group_resource, campaign.keywords)
                    logger.info(f"Added {len(campaign.keywords)} keywords")

                # Extract IDs from resource names
                google_campaign_id = campaign_resource.split('/')[-1]
                google_ad_group_id = ad_group_resource.split('/')[-1]
                google_ad_id = ad_resource.split('/')[-1] if ad_resource else None

            return {
                'success': True,
                'google_campaign_id': google_campaign_id,
                'google_ad_group_id': google_ad_group_id,
                'google_ad_id': google_ad_id,
                'campaign_resource': campaign_resource
            }

        except GoogleAdsException as ex:
            error_details = self._handle_google_ads_error(ex)
            logger.error(f"Google Ads API error: {error_details}")
            raise Exception(f"Failed to publish campaign: {error_details['message']}")

        except Exception as ex:
            logger.error(f"Unexpected error publishing campaign: {str(ex)}")
            raise

    def _create_campaign_budget(self, name: str, amount_micros: int) -> str:
        """
        Create a campaign budget.

        Args:
            name: Budget name
            amount_micros: Daily budget in micros

        Returns:
            Budget resource name
        """
        budget_service = self.client.get_service("CampaignBudgetService")
        budget_operation = self.client.get_type("CampaignBudgetOperation")

        budget = budget_operation.create
        budget.name = f"Budget for {name} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        budget.amount_micros = amount_micros
        budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD
        budget.explicitly_shared = False

        response = budget_service.mutate_campaign_budgets(
            customer_id=self._customer_id,
            operations=[budget_operation]
        )

        return response.results[0].resource_name

    def _create_campaign(
        self,
        name: str,
        budget_resource: str,
        campaign_type: str,
        start_date,
        end_date=None,
        bidding_strategy: Optional[str] = None,
        target_cpa: Optional[int] = None,
        target_roas: Optional[float] = None,
        merchant_center_id: Optional[str] = None
    ) -> str:
        """
        Create a campaign with PAUSED status.

        Args:
            name: Campaign name
            budget_resource: Budget resource name
            campaign_type: Type of campaign (DEMAND_GEN, DISPLAY, etc.)
            start_date: Campaign start date
            end_date: Campaign end date (optional)
            bidding_strategy: Bidding strategy to use
            target_cpa: Target CPA in micros (for target_cpa strategy)
            target_roas: Target ROAS multiplier (for target_roas strategy)
            merchant_center_id: Merchant Center ID (for SHOPPING campaigns)

        Returns:
            Campaign resource name
        """
        campaign_service = self.client.get_service("CampaignService")
        campaign_operation = self.client.get_type("CampaignOperation")

        campaign = campaign_operation.create
        campaign.name = f"{name} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        campaign.status = self.client.enums.CampaignStatusEnum.PAUSED  # Start PAUSED
        campaign.campaign_budget = budget_resource

        # Set advertising channel type based on campaign type
        channel_type_map = {
            'DEMAND_GEN': 'DEMAND_GEN',
            'DISPLAY': 'DISPLAY',
            'SEARCH': 'SEARCH',
            'VIDEO': 'VIDEO',
            'SHOPPING': 'SHOPPING',
            'PERFORMANCE_MAX': 'PERFORMANCE_MAX'
        }

        channel_type = channel_type_map.get(campaign_type, 'DISPLAY')
        campaign.advertising_channel_type = getattr(
            self.client.enums.AdvertisingChannelTypeEnum,
            channel_type
        )

        # Set dates
        campaign.start_date = start_date.strftime('%Y%m%d')
        if end_date:
            campaign.end_date = end_date.strftime('%Y%m%d')

        # Required field in API v22 - EU Political Advertising disclosure
        campaign.contains_eu_political_advertising = (
            self.client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
        )

        # Set network settings for SEARCH campaigns
        # Based on official example: examples/basic_operations/add_campaigns.py
        if campaign_type == 'SEARCH':
            campaign.network_settings.target_google_search = True
            campaign.network_settings.target_search_network = True
            campaign.network_settings.target_content_network = False
            campaign.network_settings.target_partner_search_network = False

        # Set network settings for DISPLAY campaigns
        if campaign_type == 'DISPLAY':
            campaign.network_settings.target_content_network = True

        # Set Merchant Center ID for SHOPPING campaigns
        if campaign_type == 'SHOPPING' and merchant_center_id:
            shopping_settings = campaign.shopping_setting
            shopping_settings.merchant_id = int(merchant_center_id)
            # Note: sales_country is deprecated in API v22, feed_label is used instead
            shopping_settings.feed_label = 'US'
            shopping_settings.campaign_priority = 0  # Low priority (0-2)

        # Set bidding strategy
        self._set_bidding_strategy(campaign, campaign_type, bidding_strategy, target_cpa, target_roas)

        response = campaign_service.mutate_campaigns(
            customer_id=self._customer_id,
            operations=[campaign_operation]
        )

        return response.results[0].resource_name

    def _set_bidding_strategy(
        self,
        campaign,
        campaign_type: str,
        bidding_strategy: Optional[str],
        target_cpa: Optional[int],
        target_roas: Optional[float]
    ):
        """
        Set bidding strategy on a campaign.

        Google Ads API v22 bidding strategy field mapping:
        - maximize_conversions: campaign.maximize_conversions
        - maximize_conversion_value: campaign.maximize_conversion_value
        - maximize_clicks: campaign.target_spend (with no cpc_bid_ceiling)
        - target_cpa: campaign.target_cpa
        - target_roas: campaign.target_roas
        - manual_cpc: campaign.manual_cpc
        - manual_cpm: campaign.manual_cpm
        - target_cpm: campaign.target_cpm

        Args:
            campaign: Campaign proto object
            campaign_type: Type of campaign
            bidding_strategy: Selected bidding strategy
            target_cpa: Target CPA in micros
            target_roas: Target ROAS multiplier
        """
        # Get default bidding strategy if not specified
        if not bidding_strategy:
            defaults = {
                'DEMAND_GEN': 'maximize_conversions',
                'PERFORMANCE_MAX': 'maximize_conversions',
                'SEARCH': 'manual_cpc',
                'DISPLAY': 'manual_cpc',
                'VIDEO': 'target_cpm',  # VIDEO doesn't support maximize_conversions
                'SHOPPING': 'maximize_clicks'
            }
            bidding_strategy = defaults.get(campaign_type, 'manual_cpc')

        # Apply bidding strategy - using Google Ads API v22 field names
        # Proto-plus: access sub-message to mark oneof as set, then modify its fields
        if bidding_strategy == 'maximize_conversions':
            # MaximizeConversions - automatically maximize conversions within budget
            # Accessing the field marks it as set; leave target_cpa_micros unset for no target
            campaign.maximize_conversions.target_cpa_micros = 0
        elif bidding_strategy == 'maximize_conversion_value':
            # MaximizeConversionValue - maximize conversion value within budget
            # Leave target_roas unset for no target (0.0 = no target)
            campaign.maximize_conversion_value.target_roas = 0.0
        elif bidding_strategy == 'maximize_clicks':
            # MaximizeClicks uses target_spend in Google Ads API v22
            # Set target_spend_micros to 0 to use full budget
            campaign.target_spend.target_spend_micros = 0
        elif bidding_strategy == 'target_cpa':
            # TargetCpa - target cost per acquisition
            if target_cpa:
                campaign.target_cpa.target_cpa_micros = target_cpa
            else:
                campaign.target_cpa.target_cpa_micros = 1000000  # Default $1
        elif bidding_strategy == 'target_roas':
            # TargetRoas - target return on ad spend
            if target_roas:
                campaign.target_roas.target_roas = target_roas
            else:
                campaign.target_roas.target_roas = 1.0  # Default 100%
        elif bidding_strategy in ('target_cpc', 'manual_cpc'):
            # ManualCpc - manual cost per click bidding
            campaign.manual_cpc.enhanced_cpc_enabled = False
        elif bidding_strategy == 'manual_cpm':
            # ManualCpm - accessing the field should mark the oneof
            # ManualCpm has no required fields, just needs to be present
            _ = campaign.manual_cpm._pb.ByteSize()  # Force proto serialization
        elif bidding_strategy == 'target_cpm':
            # TargetCpm - need to access the sub-message to mark as set
            # For VIDEO campaigns, target_cpm with frequency goal
            campaign.target_cpm.target_frequency_goal.target_count = 1
            campaign.target_cpm.target_frequency_goal.time_unit = (
                self.client.enums.TargetFrequencyTimeUnitEnum.WEEKLY
            )
        else:
            # Default to manual_cpc
            campaign.manual_cpc.enhanced_cpc_enabled = False

    def _create_ad_group(
        self,
        campaign_resource: str,
        ad_group_name: str,
        campaign_type: str = 'DISPLAY',
        cpc_bid_micros: Optional[int] = None
    ) -> str:
        """
        Create an ad group.

        Based on official example: examples/basic_operations/add_ad_groups.py
        Ad groups for CPC-based campaigns require cpc_bid_micros.

        Args:
            campaign_resource: Campaign resource name
            ad_group_name: Ad group name
            campaign_type: Campaign type to determine ad group type
            cpc_bid_micros: CPC bid in micros (required for SEARCH with Manual CPC)

        Returns:
            Ad group resource name
        """
        ad_group_service = self.client.get_service("AdGroupService")
        ad_group_operation = self.client.get_type("AdGroupOperation")

        ad_group = ad_group_operation.create
        ad_group.name = f"{ad_group_name} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        ad_group.campaign = campaign_resource
        ad_group.status = self.client.enums.AdGroupStatusEnum.ENABLED

        # Set ad group type based on campaign type
        # Based on official examples for each campaign type
        ad_group_type_map = {
            'DEMAND_GEN': 'DISPLAY_STANDARD',  # Demand Gen uses display standard
            'DISPLAY': 'DISPLAY_STANDARD',
            'SEARCH': 'SEARCH_STANDARD',
            'VIDEO': 'VIDEO_TRUE_VIEW_IN_STREAM',
            'SHOPPING': 'SHOPPING_PRODUCT_ADS',
            'PERFORMANCE_MAX': 'DISPLAY_STANDARD'  # PMax uses Asset Groups, not Ad Groups
        }

        ad_group_type = ad_group_type_map.get(campaign_type, 'DISPLAY_STANDARD')
        ad_group.type_ = getattr(self.client.enums.AdGroupTypeEnum, ad_group_type)

        # Set CPC bid for SEARCH and DISPLAY campaigns (required for Manual CPC bidding)
        # Default to $1 (1,000,000 micros) if not specified
        if campaign_type in ('SEARCH', 'DISPLAY'):
            ad_group.cpc_bid_micros = cpc_bid_micros or 1000000  # $1 default

        # Set CPM bid for VIDEO campaigns
        if campaign_type == 'VIDEO':
            ad_group.cpm_bid_micros = 10000000  # $10 default CPM

        response = ad_group_service.mutate_ad_groups(
            customer_id=self._customer_id,
            operations=[ad_group_operation]
        )

        return response.results[0].resource_name

    def _create_performance_max_asset_group(
        self,
        campaign_resource: str,
        campaign
    ) -> str:
        """
        Create an Asset Group for Performance Max campaigns.

        Based on official example: examples/advanced_operations/add_performance_max_campaign.py
        Performance Max campaigns use Asset Groups instead of Ad Groups.
        Asset Groups contain all the creative assets linked via AssetGroupAsset.

        Args:
            campaign_resource: Campaign resource name
            campaign: Campaign model instance

        Returns:
            Asset group resource name
        """
        # First, create text assets (headlines, descriptions)
        text_asset_resources = self._create_text_assets_for_pmax(campaign)

        # Upload image assets if provided
        image_asset_resources = self._upload_campaign_images(campaign.images, "PMax")

        # Create Asset Group
        asset_group_service = self.client.get_service("AssetGroupService")
        asset_group_operation = self.client.get_type("AssetGroupOperation")

        asset_group = asset_group_operation.create
        asset_group.name = f"{campaign.name} Asset Group - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        asset_group.campaign = campaign_resource
        asset_group.status = self.client.enums.AssetGroupStatusEnum.ENABLED

        # Final URL is required for Asset Groups
        asset_group.final_urls.append(campaign.final_url or "https://example.com")

        response = asset_group_service.mutate_asset_groups(
            customer_id=self._customer_id,
            operations=[asset_group_operation]
        )
        asset_group_resource = response.results[0].resource_name
        logger.info(f"Created asset group: {asset_group_resource}")

        # Link assets to the asset group
        self._link_assets_to_asset_group(
            asset_group_resource,
            text_asset_resources,
            image_asset_resources
        )

        return asset_group_resource

    def _create_text_assets_for_pmax(self, campaign) -> Dict[str, List[str]]:
        """
        Create text assets (headlines, descriptions) for Performance Max.

        Args:
            campaign: Campaign model instance

        Returns:
            Dictionary with asset type keys and lists of asset resource names
        """
        asset_service = self.client.get_service("AssetService")
        operations = []
        asset_mapping = {'headlines': [], 'long_headlines': [], 'descriptions': [], 'business_name': []}

        # Create headline assets (need at least 3)
        headlines = campaign.headlines or [campaign.ad_headline or campaign.name]
        while len(headlines) < 3:
            headlines.append(f"Discover More {len(headlines) + 1}")

        for i, headline in enumerate(headlines[:5]):
            operation = self.client.get_type("AssetOperation")
            asset = operation.create
            asset.text_asset.text = headline[:HEADLINE_MAX_LENGTH]
            asset.name = f"Headline {i+1} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
            operations.append(('headlines', operation))

        # Create long headline asset
        long_headline = campaign.long_headline or (headlines[0] if headlines else campaign.name)
        operation = self.client.get_type("AssetOperation")
        asset = operation.create
        asset.text_asset.text = long_headline[:LONG_HEADLINE_MAX_LENGTH]
        asset.name = f"Long Headline - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        operations.append(('long_headlines', operation))

        # Create description assets (need at least 2)
        descriptions = campaign.descriptions or [campaign.ad_description or f"Check out {campaign.name}"]
        while len(descriptions) < 2:
            descriptions.append("Visit our website for more information.")

        for i, description in enumerate(descriptions[:5]):
            operation = self.client.get_type("AssetOperation")
            asset = operation.create
            asset.text_asset.text = description[:DESCRIPTION_MAX_LENGTH]
            asset.name = f"Description {i+1} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
            operations.append(('descriptions', operation))

        # Create business name asset
        business_name = campaign.business_name or DEFAULT_BUSINESS_NAME
        operation = self.client.get_type("AssetOperation")
        asset = operation.create
        asset.text_asset.text = business_name[:BUSINESS_NAME_MAX_LENGTH]
        asset.name = f"Business Name - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        operations.append(('business_name', operation))

        # Execute all operations
        if operations:
            ops_only = [op for _, op in operations]
            response = asset_service.mutate_assets(
                customer_id=self._customer_id,
                operations=ops_only
            )

            # Map results back to categories
            for i, result in enumerate(response.results):
                category = operations[i][0]
                asset_mapping[category].append(result.resource_name)

        return asset_mapping

    def _create_asset_link_operation(
        self,
        asset_group_resource: str,
        asset_resource: str,
        field_type
    ):
        """Create a single asset group asset link operation."""
        operation = self.client.get_type("AssetGroupAssetOperation")
        asset_group_asset = operation.create
        asset_group_asset.asset_group = asset_group_resource
        asset_group_asset.asset = asset_resource
        asset_group_asset.field_type = field_type
        return operation

    def _link_assets_to_asset_group(
        self,
        asset_group_resource: str,
        text_assets: Dict[str, List[str]],
        image_assets: Dict[str, str]
    ) -> None:
        """
        Link assets to an Asset Group using AssetGroupAsset.

        Args:
            asset_group_resource: Asset group resource name
            text_assets: Dictionary of text asset resources by type
            image_assets: Dictionary of image asset resources by type
        """
        asset_group_asset_service = self.client.get_service("AssetGroupAssetService")
        operations = []
        field_type_enum = self.client.enums.AssetFieldTypeEnum

        # Map text asset types to their field types
        text_asset_mappings = [
            ('headlines', field_type_enum.HEADLINE),
            ('long_headlines', field_type_enum.LONG_HEADLINE),
            ('descriptions', field_type_enum.DESCRIPTION),
            ('business_name', field_type_enum.BUSINESS_NAME),
        ]

        for asset_key, field_type in text_asset_mappings:
            for asset_resource in text_assets.get(asset_key, []):
                operations.append(self._create_asset_link_operation(
                    asset_group_resource, asset_resource, field_type
                ))

        # Map image asset types to their field types
        image_asset_mappings = [
            ('landscape', field_type_enum.MARKETING_IMAGE),
            ('square', field_type_enum.SQUARE_MARKETING_IMAGE),
            ('logo', field_type_enum.LOGO),
        ]

        for asset_key, field_type in image_asset_mappings:
            if image_assets.get(asset_key):
                operations.append(self._create_asset_link_operation(
                    asset_group_resource, image_assets[asset_key], field_type
                ))

        if operations:
            asset_group_asset_service.mutate_asset_group_assets(
                customer_id=self._customer_id,
                operations=operations
            )
            logger.info(f"Linked {len(operations)} assets to asset group")

    def _create_ad_by_type(self, campaign, ad_group_resource: str) -> Optional[str]:
        """
        Create an ad based on campaign type.

        Args:
            campaign: Campaign model instance
            ad_group_resource: Ad group resource name

        Returns:
            Ad resource name or None for SHOPPING campaigns
        """
        campaign_type = campaign.campaign_type

        if campaign_type == 'SEARCH':
            return self._create_responsive_search_ad(
                ad_group_resource,
                campaign.headlines or [campaign.ad_headline or campaign.name],
                campaign.descriptions or [campaign.ad_description or f"Check out {campaign.name}"],
                campaign.final_url or "https://example.com"
            )
        elif campaign_type == 'VIDEO':
            return self._create_video_ad(
                ad_group_resource,
                campaign.video_url,
                campaign.headlines[0] if campaign.headlines else campaign.name,
                campaign.descriptions[0] if campaign.descriptions else f"Check out {campaign.name}",
                campaign.final_url
            )
        elif campaign_type == 'SHOPPING':
            # Shopping campaigns use product data from Merchant Center, no ad needed
            return None
        else:
            # DEMAND_GEN, DISPLAY, PERFORMANCE_MAX use responsive display ad
            return self._create_responsive_display_ad(
                ad_group_resource,
                campaign.headlines or [campaign.ad_headline or campaign.name],
                campaign.long_headline or (campaign.headlines[0] if campaign.headlines else campaign.name),
                campaign.descriptions or [campaign.ad_description or f"Check out {campaign.name}"],
                campaign.business_name or DEFAULT_BUSINESS_NAME,
                campaign.final_url or "https://example.com",
                campaign.images
            )

    def _create_responsive_display_ad(
        self,
        ad_group_resource: str,
        headlines: List[str],
        long_headline: str,
        descriptions: List[str],
        business_name: str,
        final_url: str,
        images: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a responsive display ad.

        Based on official examples, Responsive Display Ads REQUIRE:
        - At least 1 marketing image (landscape 1.91:1 ratio)
        - At least 1 square marketing image (1:1 ratio)
        - At least 1 logo image
        - Long headline
        - At least 1 short headline
        - At least 1 description
        - Business name
        - Final URL

        Args:
            ad_group_resource: Ad group resource name
            headlines: List of ad headlines
            long_headline: Long headline
            descriptions: List of ad descriptions
            business_name: Business name
            final_url: Landing page URL
            images: Image URLs dict with landscape_url, square_url, logo_url

        Returns:
            Ad resource name

        Raises:
            Exception: If required images are missing
        """
        # Upload image assets first (REQUIRED for Responsive Display Ads)
        uploaded_images = self._upload_campaign_images(images, "Display")
        marketing_image_assets = [uploaded_images['landscape']] if uploaded_images.get('landscape') else []
        square_image_assets = [uploaded_images['square']] if uploaded_images.get('square') else []
        logo_image_assets = [uploaded_images['logo']] if uploaded_images.get('logo') else []

        # Check if we have required images
        if not marketing_image_assets and not square_image_assets:
            raise Exception(
                "Responsive Display Ads require at least one marketing image "
                "(landscape_url or square_url). Please provide image URLs."
            )

        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")

        ad_group_ad = ad_group_ad_operation.create
        ad_group_ad.ad_group = ad_group_resource
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED

        # Create responsive display ad
        ad = ad_group_ad.ad
        rda = ad.responsive_display_ad

        # Add headlines (truncate to max length)
        for headline in headlines[:5]:  # Max 5 headlines
            rda.headlines.append(self._create_ad_text_asset(headline[:HEADLINE_MAX_LENGTH]))

        # Set long headline (REQUIRED)
        rda.long_headline.text = long_headline[:LONG_HEADLINE_MAX_LENGTH]

        # Add descriptions
        for description in descriptions[:5]:  # Max 5 descriptions
            rda.descriptions.append(self._create_ad_text_asset(description[:DESCRIPTION_MAX_LENGTH]))

        # Set business name (REQUIRED)
        rda.business_name = business_name[:BUSINESS_NAME_MAX_LENGTH]

        # Add marketing images (landscape)
        for asset_resource in marketing_image_assets:
            ad_image_asset = self.client.get_type("AdImageAsset")
            ad_image_asset.asset = asset_resource
            rda.marketing_images.append(ad_image_asset)

        # Add square marketing images
        for asset_resource in square_image_assets:
            ad_image_asset = self.client.get_type("AdImageAsset")
            ad_image_asset.asset = asset_resource
            rda.square_marketing_images.append(ad_image_asset)

        # Add logo images
        for asset_resource in logo_image_assets:
            ad_image_asset = self.client.get_type("AdImageAsset")
            ad_image_asset.asset = asset_resource
            rda.logo_images.append(ad_image_asset)

        ad.final_urls.append(final_url)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self._customer_id,
            operations=[ad_group_ad_operation]
        )

        return response.results[0].resource_name

    def _create_responsive_search_ad(
        self,
        ad_group_resource: str,
        headlines: List[str],
        descriptions: List[str],
        final_url: str,
        path1: Optional[str] = None,
        path2: Optional[str] = None
    ) -> str:
        """
        Create a responsive search ad for SEARCH campaigns.

        Based on official example: examples/advanced_operations/add_responsive_search_ad_full.py
        RSA requires MINIMUM 3 headlines and MINIMUM 2 descriptions.

        Args:
            ad_group_resource: Ad group resource name
            headlines: List of ad headlines (min 3, max 15)
            descriptions: List of ad descriptions (min 2, max 4)
            final_url: Landing page URL
            path1: Optional display URL path 1 (max 15 chars)
            path2: Optional display URL path 2 (max 15 chars)

        Returns:
            Ad resource name

        Raises:
            ValueError: If minimum requirements not met
        """
        # Validate minimum requirements - RSA needs at least 3 headlines and 2 descriptions
        if len(headlines) < 3:
            raise ValueError(
                f"Responsive Search Ads require at least 3 headlines. "
                f"Only {len(headlines)} provided."
            )

        if len(descriptions) < 2:
            raise ValueError(
                f"Responsive Search Ads require at least 2 descriptions. "
                f"Only {len(descriptions)} provided."
            )

        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")

        ad_group_ad = ad_group_ad_operation.create
        ad_group_ad.ad_group = ad_group_resource
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED

        ad = ad_group_ad.ad
        rsa = ad.responsive_search_ad

        # Add headlines (min 3, max 15 for RSA)
        for headline in headlines[:15]:
            rsa.headlines.append(self._create_ad_text_asset(headline[:HEADLINE_MAX_LENGTH]))

        # Add descriptions (min 2, max 4 for RSA)
        for description in descriptions[:4]:
            rsa.descriptions.append(self._create_ad_text_asset(description[:DESCRIPTION_MAX_LENGTH]))

        # Set optional display URL paths (shows as example.com/path1/path2)
        if path1:
            rsa.path1 = path1[:15]
        if path2:
            rsa.path2 = path2[:15]

        ad.final_urls.append(final_url)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self._customer_id,
            operations=[ad_group_ad_operation]
        )

        return response.results[0].resource_name

    def _create_video_ad(
        self,
        ad_group_resource: str,
        video_url: str,
        headline: str,
        description: str,
        final_url: Optional[str] = None
    ) -> str:
        """
        Create a video ad for VIDEO campaigns.

        Args:
            ad_group_resource: Ad group resource name
            video_url: YouTube video URL
            headline: Ad headline
            description: Ad description
            final_url: Landing page URL (optional)

        Returns:
            Ad resource name
        """
        ad_group_ad_service = self.client.get_service("AdGroupAdService")
        ad_group_ad_operation = self.client.get_type("AdGroupAdOperation")

        ad_group_ad = ad_group_ad_operation.create
        ad_group_ad.ad_group = ad_group_resource
        ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED

        ad = ad_group_ad.ad

        # Create in-stream video ad
        video_ad = ad.video_ad
        video_ad.video.asset = self._get_or_create_youtube_video_asset(video_url)

        # Set companion banner info if needed
        in_stream = video_ad.in_stream
        in_stream.action_headline = headline[:HEADLINE_MAX_LENGTH]

        if final_url:
            ad.final_urls.append(final_url)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self._customer_id,
            operations=[ad_group_ad_operation]
        )

        return response.results[0].resource_name

    def _get_or_create_youtube_video_asset(self, video_url: str) -> str:
        """
        Get or create a YouTube video asset.

        Based on official examples, YouTube video assets require:
        - youtube_video_id extracted from the URL
        - type_ set to YOUTUBE_VIDEO
        - A unique name

        Args:
            video_url: YouTube video URL

        Returns:
            Asset resource name
        """
        if not video_url:
            raise Exception("Video URL is required for VIDEO campaigns")

        # Extract video ID from various YouTube URL formats
        # Handles: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/v/ID
        video_id = None
        if 'v=' in video_url:
            video_id = video_url.split('v=')[-1].split('&')[0]
        elif 'youtu.be/' in video_url:
            video_id = video_url.split('youtu.be/')[-1].split('?')[0]
        elif '/v/' in video_url:
            video_id = video_url.split('/v/')[-1].split('?')[0]
        else:
            # Assume it's already a video ID
            video_id = video_url.split('/')[-1]

        if not video_id:
            raise Exception(f"Could not extract video ID from URL: {video_url}")

        asset_service = self.client.get_service("AssetService")
        asset_operation = self.client.get_type("AssetOperation")

        asset = asset_operation.create
        asset.type_ = self.client.enums.AssetTypeEnum.YOUTUBE_VIDEO
        asset.youtube_video_asset.youtube_video_id = video_id
        asset.name = f"Video Asset - {video_id} - {datetime.now().strftime('%Y%m%d%H%M%S')}"

        response = asset_service.mutate_assets(
            customer_id=self._customer_id,
            operations=[asset_operation]
        )

        asset_resource = response.results[0].resource_name
        logger.info(f"Created YouTube video asset: {asset_resource}")
        return asset_resource

    def _add_keywords(self, ad_group_resource: str, keywords: List[str]) -> List[str]:
        """
        Add keywords to an ad group for SEARCH campaigns.

        Args:
            ad_group_resource: Ad group resource name
            keywords: List of keyword strings

        Returns:
            List of keyword resource names
        """
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        operations = []

        for keyword in keywords:
            operation = self.client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = ad_group_resource
            criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = keyword[:80]  # Max 80 chars
            criterion.keyword.match_type = self.client.enums.KeywordMatchTypeEnum.BROAD
            operations.append(operation)

        if operations:
            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=self._customer_id,
                operations=operations
            )
            return [result.resource_name for result in response.results]

        return []

    def _create_ad_text_asset(self, text: str):
        """Create an ad text asset."""
        ad_text_asset = self.client.get_type("AdTextAsset")
        ad_text_asset.text = text
        return ad_text_asset

    def _upload_campaign_images(
        self,
        images: Optional[Dict[str, str]],
        prefix: str = "Campaign"
    ) -> Dict[str, str]:
        """
        Upload all campaign images and return their asset resources.

        Args:
            images: Dictionary with landscape_url, square_url, logo_url
            prefix: Prefix for asset names (e.g., "PMax", "Display")

        Returns:
            Dictionary mapping image type to asset resource name
        """
        if not images:
            return {}

        image_asset_resources = {}
        image_configs = [
            ('landscape_url', 'landscape', f"{prefix} Marketing Image"),
            ('square_url', 'square', f"{prefix} Square Image"),
            ('logo_url', 'logo', f"{prefix} Logo"),
        ]

        for url_key, asset_key, asset_name in image_configs:
            if images.get(url_key):
                try:
                    image_asset_resources[asset_key] = self._upload_image_asset(
                        images[url_key], asset_name
                    )
                except Exception as e:
                    logger.warning(f"Failed to upload {asset_key} image: {e}")

        return image_asset_resources

    def _upload_image_asset(self, image_url: str, asset_name: str) -> str:
        """
        Upload an image asset from URL to Google Ads.

        Based on official example: examples/assets/upload_image_asset.py
        Images must be downloaded as bytes and uploaded with proper metadata.

        Args:
            image_url: URL of the image to upload
            asset_name: Name for the asset

        Returns:
            Asset resource name
        """
        # Download image bytes from URL
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_bytes = response.content
        except requests.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise Exception(f"Failed to download image: {e}")

        # Determine MIME type from content-type header or URL
        content_type = response.headers.get('content-type', '').lower()
        if 'png' in content_type or image_url.lower().endswith('.png'):
            mime_type = self.client.enums.MimeTypeEnum.IMAGE_PNG
        elif 'gif' in content_type or image_url.lower().endswith('.gif'):
            mime_type = self.client.enums.MimeTypeEnum.IMAGE_GIF
        else:
            # Default to JPEG
            mime_type = self.client.enums.MimeTypeEnum.IMAGE_JPEG

        # Create asset operation
        asset_service = self.client.get_service("AssetService")
        asset_operation = self.client.get_type("AssetOperation")

        asset = asset_operation.create
        asset.type_ = self.client.enums.AssetTypeEnum.IMAGE
        asset.name = f"{asset_name} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        asset.image_asset.data = image_bytes
        asset.image_asset.file_size = len(image_bytes)
        asset.image_asset.mime_type = mime_type

        # Upload the asset
        response = asset_service.mutate_assets(
            customer_id=self._customer_id,
            operations=[asset_operation]
        )

        asset_resource = response.results[0].resource_name
        logger.info(f"Uploaded image asset: {asset_resource}")
        return asset_resource

    def pause_campaign(self, google_campaign_id: str) -> bool:
        """
        Pause a campaign in Google Ads.

        Args:
            google_campaign_id: Google Ads campaign ID

        Returns:
            True if successful
        """
        logger.debug(f"Attempting to pause campaign: {google_campaign_id}")
        if not self.is_configured():
            logger.error("pause_campaign failed: Google Ads API is not configured")
            raise Exception("Google Ads API is not configured")

        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")

            campaign_resource_name = campaign_service.campaign_path(
                self._customer_id, google_campaign_id
            )

            campaign = campaign_operation.update
            campaign.resource_name = campaign_resource_name
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED

            campaign_operation.update_mask.paths.append("status")

            campaign_service.mutate_campaigns(
                customer_id=self._customer_id,
                operations=[campaign_operation]
            )

            logger.info(f"Campaign {google_campaign_id} paused")
            return True

        except GoogleAdsException as ex:
            error_details = self._handle_google_ads_error(ex)
            raise Exception(f"Failed to pause campaign: {error_details['message']}")

    def enable_campaign(self, google_campaign_id: str) -> bool:
        """
        Enable a campaign in Google Ads.

        Args:
            google_campaign_id: Google Ads campaign ID

        Returns:
            True if successful
        """
        logger.debug(f"Attempting to enable campaign: {google_campaign_id}")
        if not self.is_configured():
            logger.error("enable_campaign failed: Google Ads API is not configured")
            raise Exception("Google Ads API is not configured")

        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")

            campaign_resource_name = campaign_service.campaign_path(
                self._customer_id, google_campaign_id
            )

            campaign = campaign_operation.update
            campaign.resource_name = campaign_resource_name
            campaign.status = self.client.enums.CampaignStatusEnum.ENABLED

            campaign_operation.update_mask.paths.append("status")

            campaign_service.mutate_campaigns(
                customer_id=self._customer_id,
                operations=[campaign_operation]
            )

            logger.info(f"Campaign {google_campaign_id} enabled")
            return True

        except GoogleAdsException as ex:
            error_details = self._handle_google_ads_error(ex)
            raise Exception(f"Failed to enable campaign: {error_details['message']}")

    def _handle_google_ads_error(self, ex) -> Dict[str, Any]:
        """
        Handle Google Ads API errors with comprehensive error mapping.

        Args:
            ex: GoogleAdsException

        Returns:
            Dictionary with error details and user-friendly messages
        """
        from app.utils.google_ads_error_mapping import (
            parse_google_ads_exception,
            map_google_ads_error,
            is_retryable_error,
        )

        # Parse the exception into structured format
        parsed = parse_google_ads_exception(ex)

        error_messages = []
        error_codes = []

        for error in ex.failure.errors:
            # Log the original error
            logger.error(f"Google Ads Error: {error.message}")

            if error.location:
                for field_path_element in error.location.field_path_elements:
                    logger.error(f"  On field: {field_path_element.field_name}")

            # Try to map to user-friendly message
            error_code = None
            if hasattr(error, 'error_code'):
                # Extract specific error code
                for attr in dir(error.error_code):
                    if not attr.startswith('_'):
                        val = getattr(error.error_code, attr, None)
                        if val and val != 0 and isinstance(val, int):
                            error_code = attr.upper()
                            error_codes.append(error_code)
                            break

            if error_code:
                user_message = map_google_ads_error(error_code, {'detail': error.message})
            else:
                user_message = error.message

            error_messages.append(user_message)

        return {
            'request_id': ex.request_id,
            'status': str(ex.error.code().name) if hasattr(ex, 'error') else 'UNKNOWN',
            'errors': error_messages,
            'error_codes': error_codes,
            'message': '; '.join(error_messages) if error_messages else str(ex),
            'is_retryable': any(is_retryable_error(code) for code in error_codes),
        }


# Singleton instance
google_ads_service = GoogleAdsService()
