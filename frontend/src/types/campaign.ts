/**
 * Type definitions for Campaign
 */

export type CampaignObjective = 'SALES' | 'LEADS' | 'WEBSITE_TRAFFIC';

export type CampaignType =
  | 'DEMAND_GEN'
  | 'SEARCH'
  | 'DISPLAY'
  | 'VIDEO'
  | 'SHOPPING'
  | 'PERFORMANCE_MAX';

export type CampaignStatus = 'DRAFT' | 'PUBLISHED' | 'PAUSED' | 'ERROR';

export type BiddingStrategy =
  | 'maximize_conversions'
  | 'maximize_conversion_value'
  | 'maximize_clicks'
  | 'target_cpa'
  | 'target_roas'
  | 'target_cpc'
  | 'manual_cpc'
  | 'manual_cpm'
  | 'target_cpm';

export interface ImageAssets {
  landscape_url?: string;
  square_url?: string;
  logo_url?: string;
}

export interface Campaign {
  id: string;
  name: string;
  objective: CampaignObjective;
  campaign_type: CampaignType;
  daily_budget: number;
  daily_budget_usd: number;
  start_date: string;
  end_date: string | null;
  status: CampaignStatus;
  google_campaign_id: string | null;
  google_ad_group_id: string | null;
  google_ad_id: string | null;
  ad_group_name: string | null;
  // Legacy fields (kept for backwards compatibility)
  ad_headline: string | null;
  ad_description: string | null;
  asset_url: string | null;
  final_url: string | null;
  // New dynamic fields
  bidding_strategy: BiddingStrategy | null;
  target_cpa: number | null;
  target_roas: number | null;
  headlines: string[] | null;
  long_headline: string | null;
  descriptions: string[] | null;
  business_name: string | null;
  images: ImageAssets | null;
  keywords: string[] | null;
  video_url: string | null;
  merchant_center_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignFormData {
  name: string;
  objective: CampaignObjective;
  campaign_type: CampaignType;
  daily_budget: number;
  start_date: string;
  end_date?: string;
  ad_group_name?: string;
  // Legacy fields (for backwards compatibility)
  ad_headline?: string;
  ad_description?: string;
  asset_url?: string;
  final_url?: string;
  // New dynamic fields
  bidding_strategy?: BiddingStrategy;
  target_cpa?: number;
  target_roas?: number;
  headlines?: string[];
  long_headline?: string;
  descriptions?: string[];
  business_name?: string;
  images?: ImageAssets;
  keywords?: string[];
  video_url?: string;
  merchant_center_id?: string;
}

export interface CreateCampaignRequest extends CampaignFormData {}

export interface UpdateCampaignRequest extends Partial<CampaignFormData> {}

export interface PublishCampaignResponse {
  message: string;
  campaign: Campaign;
  google_ads: {
    campaign_id: string;
    ad_group_id: string;
    ad_id: string | null;
  };
}

export interface ApiError {
  error: string;
  message?: string;
  details?: Record<string, string[]>;
  code?: string;
  googleAdsCode?: string;
}

/**
 * Validation result from the backend validation endpoint.
 */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings?: string[];
  campaign_type: CampaignType;
  code?: string;
  requirements?: {
    headlines?: { min: number; max: number; max_length: number };
    descriptions?: { min: number; max: number; max_length: number };
    short_description_required?: boolean;
    short_description_max_length?: number;
  };
}

/**
 * Individual validation error with field location and code.
 */
export interface ValidationError {
  field: string;
  message: string;
  code?: string;
  googleAdsCode?: string;
}
