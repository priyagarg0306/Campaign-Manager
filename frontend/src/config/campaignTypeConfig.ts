import { CampaignType } from '../types/campaign';

// Bidding strategy types available in Google Ads API v22
export type BiddingStrategyType =
  | 'maximize_conversions'
  | 'maximize_conversion_value'
  | 'maximize_clicks'
  | 'target_cpa'
  | 'target_roas'
  | 'target_cpc'
  | 'manual_cpc'
  | 'manual_cpm'
  | 'target_cpm';

export interface BiddingOption {
  value: BiddingStrategyType;
  label: string;
  description: string;
  requiresTarget?: 'cpa' | 'roas';
}

export interface FieldConfig {
  min: number;
  max: number;
  maxLength: number;
  required: boolean;
}

export interface DescriptionFieldConfig extends FieldConfig {
  shortRequired?: boolean;  // Whether at least one short description is required
  shortMaxLength?: number;  // Max length for short description (e.g., 60 for PMax)
}

export interface ImageDimensions {
  minWidth: number;
  minHeight: number;
  ratio: number;
  ratioTolerance?: number;
}

export interface ImageRequirements {
  landscape: boolean;
  square: boolean;
  logo: boolean;
  dimensions?: {
    landscape?: ImageDimensions;
    square?: ImageDimensions;
    logo?: ImageDimensions;
  };
}

export interface CampaignTypeConfig {
  label: string;
  description: string;
  headlines: FieldConfig;
  longHeadline?: FieldConfig;
  descriptions: DescriptionFieldConfig;
  businessName: { maxLength: number; required: boolean };
  images: ImageRequirements;
  finalUrl: { required: boolean };
  keywords: { required: boolean; maxLength: number; unique?: boolean };
  videoUrl: { required: boolean };
  merchantCenterId: { required: boolean };
  biddingOptions: BiddingOption[];
  apiCreationSupported?: boolean;  // Whether campaign can be created via API (false for VIDEO)
  creationWarning?: string;  // Warning message to display if API creation not supported
}

// Bidding strategy definitions with descriptions
export const BIDDING_STRATEGIES: Record<BiddingStrategyType, BiddingOption> = {
  maximize_conversions: {
    value: 'maximize_conversions',
    label: 'Maximize Conversions',
    description: 'Automatically set bids to get the most conversions within your budget',
  },
  maximize_conversion_value: {
    value: 'maximize_conversion_value',
    label: 'Maximize Conversion Value',
    description: 'Automatically set bids to maximize total conversion value within your budget',
  },
  maximize_clicks: {
    value: 'maximize_clicks',
    label: 'Maximize Clicks',
    description: 'Automatically set bids to get the most clicks within your budget',
  },
  target_cpa: {
    value: 'target_cpa',
    label: 'Target CPA',
    description: 'Set bids to achieve a target cost per acquisition',
    requiresTarget: 'cpa',
  },
  target_roas: {
    value: 'target_roas',
    label: 'Target ROAS',
    description: 'Set bids to achieve a target return on ad spend',
    requiresTarget: 'roas',
  },
  target_cpc: {
    value: 'target_cpc',
    label: 'Target CPC',
    description: 'Set a target cost per click for your ads',
  },
  manual_cpc: {
    value: 'manual_cpc',
    label: 'Manual CPC',
    description: 'Manually set maximum cost-per-click bids',
  },
  manual_cpm: {
    value: 'manual_cpm',
    label: 'Manual CPM',
    description: 'Manually set maximum cost-per-thousand-impressions bids',
  },
  target_cpm: {
    value: 'target_cpm',
    label: 'Target CPM',
    description: 'Set a target cost per thousand impressions',
  },
};

// Campaign type configurations following Google Ads API v22 requirements
export const CAMPAIGN_TYPE_CONFIGS: Record<CampaignType, CampaignTypeConfig> = {
  DEMAND_GEN: {
    label: 'Demand Gen',
    description: 'Drive demand across YouTube, Gmail, and Discover feeds',
    headlines: { min: 1, max: 5, maxLength: 40, required: true },
    descriptions: { min: 1, max: 5, maxLength: 90, required: true },
    businessName: { maxLength: 25, required: true },
    images: {
      landscape: true,
      square: true,
      logo: true,
      dimensions: {
        landscape: { minWidth: 600, minHeight: 314, ratio: 1.91 },
        square: { minWidth: 300, minHeight: 300, ratio: 1.0 },
        logo: { minWidth: 128, minHeight: 128, ratio: 1.0 },
      },
    },
    finalUrl: { required: true },
    keywords: { required: false, maxLength: 0 },
    videoUrl: { required: false },
    merchantCenterId: { required: false },
    biddingOptions: [
      BIDDING_STRATEGIES.maximize_conversions,
      BIDDING_STRATEGIES.target_cpa,
      BIDDING_STRATEGIES.maximize_clicks,
      BIDDING_STRATEGIES.target_cpc,
    ],
  },
  PERFORMANCE_MAX: {
    label: 'Performance Max',
    description: 'Access all Google Ads inventory from a single campaign',
    headlines: { min: 3, max: 15, maxLength: 30, required: true },
    longHeadline: { min: 1, max: 1, maxLength: 90, required: true },
    descriptions: {
      min: 2,
      max: 5,
      maxLength: 90,
      required: true,
      shortRequired: true,  // At least one description must be <= 60 chars
      shortMaxLength: 60,
    },
    businessName: { maxLength: 25, required: true },
    images: {
      landscape: true,
      square: true,
      logo: true,
      dimensions: {
        landscape: { minWidth: 600, minHeight: 314, ratio: 1.91 },
        square: { minWidth: 300, minHeight: 300, ratio: 1.0 },
        logo: { minWidth: 128, minHeight: 128, ratio: 1.0 },
      },
    },
    finalUrl: { required: true },
    keywords: { required: false, maxLength: 0 },
    videoUrl: { required: false },
    merchantCenterId: { required: false },
    biddingOptions: [
      BIDDING_STRATEGIES.maximize_conversions,
      BIDDING_STRATEGIES.maximize_conversion_value,
    ],
  },
  SEARCH: {
    label: 'Search',
    description: 'Show text ads on Google Search results',
    // RSA requires minimum 3 headlines and 2 descriptions
    headlines: { min: 3, max: 15, maxLength: 30, required: true },
    descriptions: { min: 2, max: 4, maxLength: 90, required: true },
    businessName: { maxLength: 25, required: false },
    images: { landscape: false, square: false, logo: false },
    finalUrl: { required: true },
    keywords: { required: true, maxLength: 80, unique: true },  // Keywords must be unique
    videoUrl: { required: false },
    merchantCenterId: { required: false },
    biddingOptions: [
      BIDDING_STRATEGIES.manual_cpc,
      BIDDING_STRATEGIES.maximize_clicks,
      BIDDING_STRATEGIES.target_cpa,
      BIDDING_STRATEGIES.maximize_conversions,
    ],
  },
  DISPLAY: {
    label: 'Display',
    description: 'Show visual ads across the Google Display Network',
    headlines: { min: 1, max: 5, maxLength: 30, required: true },
    longHeadline: { min: 1, max: 1, maxLength: 90, required: true },
    descriptions: { min: 1, max: 5, maxLength: 90, required: true },
    businessName: { maxLength: 25, required: true },
    images: {
      landscape: true,
      square: true,
      logo: false,
      dimensions: {
        landscape: { minWidth: 600, minHeight: 314, ratio: 1.91 },
        square: { minWidth: 300, minHeight: 300, ratio: 1.0 },
      },
    },
    finalUrl: { required: true },
    keywords: { required: false, maxLength: 0 },
    videoUrl: { required: false },
    merchantCenterId: { required: false },
    biddingOptions: [
      BIDDING_STRATEGIES.manual_cpc,
      BIDDING_STRATEGIES.manual_cpm,
      BIDDING_STRATEGIES.maximize_conversions,
      BIDDING_STRATEGIES.target_cpa,
    ],
  },
  VIDEO: {
    label: 'Video',
    description: 'Show video ads on YouTube and across the web',
    headlines: { min: 0, max: 5, maxLength: 30, required: false },
    descriptions: { min: 0, max: 5, maxLength: 90, required: false },
    businessName: { maxLength: 25, required: false },
    images: { landscape: false, square: false, logo: false },
    finalUrl: { required: false },
    keywords: { required: false, maxLength: 0 },
    videoUrl: { required: true },
    merchantCenterId: { required: false },
    biddingOptions: [
      BIDDING_STRATEGIES.maximize_conversions,
      BIDDING_STRATEGIES.target_cpa,
      BIDDING_STRATEGIES.target_cpm,
    ],
    apiCreationSupported: false,  // VIDEO campaigns cannot be created via API
    creationWarning: 'VIDEO campaigns cannot be created via the Google Ads API. This form will save a draft, but publishing requires the Google Ads UI.',
  },
  SHOPPING: {
    label: 'Shopping',
    description: 'Show product listings from your Merchant Center',
    headlines: { min: 0, max: 0, maxLength: 0, required: false },
    descriptions: { min: 0, max: 0, maxLength: 0, required: false },
    businessName: { maxLength: 25, required: false },
    images: { landscape: false, square: false, logo: false },
    finalUrl: { required: false },
    keywords: { required: false, maxLength: 0 },
    videoUrl: { required: false },
    merchantCenterId: { required: true },
    biddingOptions: [
      BIDDING_STRATEGIES.maximize_clicks,
      BIDDING_STRATEGIES.target_roas,
      BIDDING_STRATEGIES.manual_cpc,
    ],
  },
};

// Helper function to get config for a campaign type
export function getCampaignTypeConfig(type: CampaignType): CampaignTypeConfig {
  return CAMPAIGN_TYPE_CONFIGS[type];
}

// Helper to check if a field should be shown for a campaign type
export function shouldShowField(
  type: CampaignType,
  field: 'headlines' | 'longHeadline' | 'descriptions' | 'businessName' | 'images' | 'keywords' | 'videoUrl' | 'merchantCenterId' | 'finalUrl'
): boolean {
  const config = CAMPAIGN_TYPE_CONFIGS[type];

  switch (field) {
    case 'headlines':
      return config.headlines.max > 0;
    case 'longHeadline':
      return !!config.longHeadline && config.longHeadline.max > 0;
    case 'descriptions':
      return config.descriptions.max > 0;
    case 'businessName':
      return config.businessName.required;
    case 'images':
      return config.images.landscape || config.images.square || config.images.logo;
    case 'keywords':
      return config.keywords.required;
    case 'videoUrl':
      return config.videoUrl.required;
    case 'merchantCenterId':
      return config.merchantCenterId.required;
    case 'finalUrl':
      return config.finalUrl.required;
    default:
      return false;
  }
}

// Helper to get default bidding strategy for a campaign type
export function getDefaultBiddingStrategy(type: CampaignType): BiddingStrategyType {
  const config = CAMPAIGN_TYPE_CONFIGS[type];
  return config.biddingOptions[0]?.value ?? 'maximize_conversions';
}
