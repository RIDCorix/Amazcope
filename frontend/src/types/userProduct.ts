/**
 * TypeScript types for UserProduct (Product Ownership) system
 */

export interface UserProductCreate {
  product_id: string;
  is_primary?: boolean;
  price_change_threshold?: number | null;
  bsr_change_threshold?: number | null;
  notes?: string | null;
  tags?: string[] | null;
}

export interface UserProductUpdate {
  is_primary?: boolean | null;
  price_change_threshold?: number | null;
  bsr_change_threshold?: number | null;
  notes?: string | null;
  tags?: string[] | null;
}

export interface UserProduct {
  id: string;
  user_id: string;
  product_id: string;
  claimed_at: string;
  is_primary: boolean;
  price_change_threshold: number | null;
  bsr_change_threshold: number | null;
  notes: string | null;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface ProductWithOwnership {
  // Product details
  id: string;
  asin: string;
  title: string;
  brand: string | null;
  category: string | null;
  url: string;
  image_url: string | null;
  is_competitor: boolean;
  is_active: boolean;

  // Ownership info
  is_owned: boolean;
  ownership: UserProduct | null;

  // Latest snapshot data
  latest_price: number | null;
  latest_bsr: number | null;
  latest_rating: number | null;
}

export interface CompetitorProductList {
  total: number;
  owned_count: number;
  competitor_count: number;
  products: ProductWithOwnership[];
}

export interface ClaimProductResponse {
  success: boolean;
  message: string;
  user_product: UserProduct;
  product_id: string;
  asin: string;
}
