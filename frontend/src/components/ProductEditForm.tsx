import { CopilotTextarea } from '@copilotkit/react-textarea';
import { Loader2, Save, Settings, Sparkles, User } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import {
  productService,
  type Product,
  type ProductContentUpdateRequest,
  type ProductUpdateRequest,
  type UserProductSettingsRequest,
} from '@/services/productService';

interface ProductEditFormProps {
  product: Product;
  onUpdate: (updatedProduct: Product) => void;
  onCancel: () => void;
}

interface FormData extends ProductUpdateRequest {
  // User settings
  user_is_active?: boolean | null;
  user_price_threshold?: number | null;
  user_bsr_threshold?: number | null;
  user_notes?: string | null;
  // Content
  product_description?: string | null;
  content_features?: string | null;
  content_marketing_copy?: string | null;
  content_seo_keywords?: string | null;
  content_competitor_analysis?: string | null;
}

export default function ProductEditForm({
  product,
  onUpdate,
  onCancel,
}: ProductEditFormProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');

  const { register, handleSubmit, watch, setValue } = useForm<FormData>({
    defaultValues: {
      title: product.title || '',
      brand: product.brand || '',
      category: product.category || '',
      small_category: product.small_category || '',
      is_active: product.is_active,
      track_frequency: 'daily', // Default value since this field doesn't exist in Product
      price_change_threshold: product.price_change_threshold,
      bsr_change_threshold: product.bsr_change_threshold,
      url: product.url || '',
      image_url: product.image_url || '',
      product_description: product.product_description, // This field doesn't exist in current Product interface
      // Initialize with empty values for new fields
      user_is_active: true,
      user_price_threshold: null,
      user_bsr_threshold: null,
      user_notes: '',
      content_features: '',
      content_marketing_copy: '',
      content_seo_keywords: '',
      content_competitor_analysis: '',
    },
  });

  const handleSave = async (data: FormData) => {
    try {
      setLoading(true);

      // Update basic product details
      if (activeTab === 'basic') {
        const basicUpdate: ProductUpdateRequest = {
          title: data.title,
          brand: data.brand,
          category: data.category,
          small_category: data.small_category,
          is_active: data.is_active,
          track_frequency: data.track_frequency,
          price_change_threshold: data.price_change_threshold,
          bsr_change_threshold: data.bsr_change_threshold,
          url: data.url,
          image_url: data.image_url,
          product_description: data.product_description,
        };

        const updatedProduct = await productService.updateProduct(
          product.id,
          basicUpdate
        );
        onUpdate(updatedProduct);

        toast({
          title: 'Product Updated',
          description:
            'Basic product information has been updated successfully.',
        });
      }

      // Update user settings
      else if (activeTab === 'settings') {
        const settingsUpdate: UserProductSettingsRequest = {
          is_active: data.user_is_active,
          price_change_threshold: data.user_price_threshold,
          bsr_change_threshold: data.user_bsr_threshold,
          notes: data.user_notes,
        };

        await productService.updateUserProductSettings(
          product.id,
          settingsUpdate
        );

        toast({
          title: 'Settings Updated',
          description: 'Your personal product settings have been updated.',
        });
      }

      // Update content with AI enhancements
      else if (activeTab === 'content') {
        const contentUpdate: ProductContentUpdateRequest = {
          product_description: data.product_description,
          features: data.content_features
            ? data.content_features.split('\n').filter(f => f.trim())
            : undefined,
          marketing_copy: data.content_marketing_copy,
          seo_keywords: data.content_seo_keywords
            ? data.content_seo_keywords.split(',').map(k => k.trim())
            : undefined,
          competitor_analysis: data.content_competitor_analysis,
        };

        const updatedProduct = await productService.updateProductContent(
          product.id,
          contentUpdate
        );
        onUpdate(updatedProduct);

        toast({
          title: 'Content Updated',
          description: 'Product content has been enhanced and updated.',
        });
      }
    } catch (error: any) {
      console.error('Failed to update product:', error);
      toast({
        title: 'Update Failed',
        description:
          error.response?.data?.detail ||
          error.message ||
          'Failed to update product',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleSave)} className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Edit Product</h2>
          <p className="text-gray-600">
            Update product information, tracking settings, and content
          </p>
        </div>
        <Badge variant="secondary">{product.asin}</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="basic" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Basic Info
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <User className="w-4 h-4" />
            My Settings
          </TabsTrigger>
          <TabsTrigger value="content" className="flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            AI Content
          </TabsTrigger>
        </TabsList>

        {/* Basic Information Tab */}
        <TabsContent value="basic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Product Information</CardTitle>
              <CardDescription>
                Update basic product details and metadata
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="title">Product Title</Label>
                  <Input
                    id="title"
                    {...register('title')}
                    placeholder="Product title"
                  />
                </div>
                <div>
                  <Label htmlFor="brand">Brand</Label>
                  <Input
                    id="brand"
                    {...register('brand')}
                    placeholder="Product brand"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    {...register('category')}
                    placeholder="Main category"
                  />
                </div>
                <div>
                  <Label htmlFor="small_category">Subcategory</Label>
                  <Input
                    id="small_category"
                    {...register('small_category')}
                    placeholder="Subcategory"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="product_description">Description</Label>
                <CopilotTextarea
                  className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('product_description') || ''}
                  onValueChange={value =>
                    setValue('product_description', value)
                  }
                  placeholder="Product description..."
                  autosuggestionsConfig={{
                    textareaPurpose: `Help write a clear and informative product description for this Amazon product: ${product.title}.

Product details:
- ASIN: ${product.asin}
- Brand: ${product.brand || 'Unknown'}
- Category: ${product.category || 'Unknown'}

Provide a concise, factual description that covers key product information, specifications, and basic features.`,
                    chatApiConfigs: {},
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  AI can help you write a clear product description
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="url">Amazon URL</Label>
                  <Input
                    id="url"
                    {...register('url')}
                    placeholder="https://amazon.com/dp/..."
                  />
                </div>
                <div>
                  <Label htmlFor="image_url">Image URL</Label>
                  <Input
                    id="image_url"
                    {...register('image_url')}
                    placeholder="https://..."
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tracking Settings</CardTitle>
              <CardDescription>
                Configure how this product is monitored
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="is_active">Active Tracking</Label>
                  <p className="text-sm text-gray-600">
                    Enable automatic data collection for this product
                  </p>
                </div>
                <Switch
                  id="is_active"
                  checked={watch('is_active') ?? false}
                  onCheckedChange={checked => setValue('is_active', checked)}
                />
              </div>

              <div>
                <Label htmlFor="track_frequency">Tracking Frequency</Label>
                <Select
                  value={watch('track_frequency') || 'daily'}
                  onChange={e => setValue('track_frequency', e.target.value)}
                >
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="price_change_threshold">
                    Price Change Alert (%)
                  </Label>
                  <Input
                    id="price_change_threshold"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    {...register('price_change_threshold', {
                      valueAsNumber: true,
                    })}
                    placeholder="10.0"
                  />
                </div>
                <div>
                  <Label htmlFor="bsr_change_threshold">
                    BSR Change Alert (%)
                  </Label>
                  <Input
                    id="bsr_change_threshold"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    {...register('bsr_change_threshold', {
                      valueAsNumber: true,
                    })}
                    placeholder="30.0"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* User Settings Tab */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal Settings</CardTitle>
              <CardDescription>
                Configure your personal preferences for this product
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="user_is_active">Track for Me</Label>
                  <p className="text-sm text-gray-600">
                    Include this product in your personal dashboard and alerts
                  </p>
                </div>
                <Switch
                  id="user_is_active"
                  checked={watch('user_is_active') ?? true}
                  onCheckedChange={checked =>
                    setValue('user_is_active', checked)
                  }
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="user_price_threshold">
                    My Price Alert (%)
                  </Label>
                  <Input
                    id="user_price_threshold"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    {...register('user_price_threshold', {
                      valueAsNumber: true,
                    })}
                    placeholder="Custom threshold (optional)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Leave empty to use product default
                  </p>
                </div>
                <div>
                  <Label htmlFor="user_bsr_threshold">My BSR Alert (%)</Label>
                  <Input
                    id="user_bsr_threshold"
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    {...register('user_bsr_threshold', {
                      valueAsNumber: true,
                    })}
                    placeholder="Custom threshold (optional)"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Leave empty to use product default
                  </p>
                </div>
              </div>

              <div>
                <Label htmlFor="user_notes">My Notes</Label>
                <CopilotTextarea
                  className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('user_notes') || ''}
                  onValueChange={value => setValue('user_notes', value)}
                  placeholder="Personal notes about this product..."
                  autosuggestionsConfig={{
                    textareaPurpose: `Help write personal notes about this Amazon product for tracking purposes: ${product.title}.

Product context:
- ASIN: ${product.asin}
- Brand: ${product.brand || 'Unknown'}
- Category: ${product.category || 'Unknown'}

Suggest helpful notes like tracking reasons, goals, important observations, monitoring strategies, or reminders about this product.`,
                    chatApiConfigs: {},
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  AI can suggest helpful notes for tracking this product
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Content Tab */}
        <TabsContent value="content" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                Amazcope Lens - AI Content Generation
              </CardTitle>
              <CardDescription>
                Use AI to enhance product descriptions, create marketing copy,
                and analyze competitors
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <Label htmlFor="product_description">
                  Enhanced Description
                </Label>
                <CopilotTextarea
                  className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('product_description') || ''}
                  onValueChange={value =>
                    setValue('product_description', value)
                  }
                  placeholder="Enhance the product description using AI..."
                  autosuggestionsConfig={{
                    textareaPurpose: `You are helping to write an enhanced Amazon product description for: ${
                      product.title
                    }.

Product details:
- ASIN: ${product.asin}
- Brand: ${product.brand || 'Unknown'}
- Category: ${product.category || 'Unknown'}
- Current description: ${product.title || 'None'}

Please help create compelling, SEO-optimized product descriptions that highlight key features, benefits, and selling points. Focus on clarity, persuasiveness, and keyword optimization for Amazon's search algorithm.`,
                    chatApiConfigs: {},
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  AI will help you create compelling, SEO-optimized product
                  descriptions
                </p>
              </div>

              <div>
                <Label htmlFor="content_features">Key Features</Label>
                <CopilotTextarea
                  className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('content_features') || ''}
                  onValueChange={value => setValue('content_features', value)}
                  placeholder="List key product features (one per line)..."
                  autosuggestionsConfig={{
                    textareaPurpose: `Help create bullet points listing the key features for this Amazon product: ${product.title}.

Format as one feature per line. Focus on:
- Unique selling propositions
- Technical specifications
- Benefits and advantages
- Use cases and applications
- Quality indicators

Make features concise, scannable, and benefit-focused rather than just listing specifications.`,
                    chatApiConfigs: {},
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  One feature per line - AI will suggest compelling bullet
                  points
                </p>
              </div>

              <div>
                <Label htmlFor="content_marketing_copy">Marketing Copy</Label>
                <CopilotTextarea
                  className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('content_marketing_copy') || ''}
                  onValueChange={value =>
                    setValue('content_marketing_copy', value)
                  }
                  placeholder="Create compelling marketing copy..."
                  autosuggestionsConfig={{
                    textareaPurpose: `Create persuasive marketing copy for this Amazon product: ${product.title}.

Write compelling promotional text that:
- Creates urgency and desire
- Highlights unique benefits
- Addresses customer pain points
- Uses emotional triggers
- Includes social proof elements
- Optimizes for conversion

Keep it engaging, customer-focused, and action-oriented.`,
                    chatApiConfigs: {},
                  }}
                />
              </div>

              <div>
                <Label htmlFor="content_seo_keywords">SEO Keywords</Label>
                <CopilotTextarea
                  className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('content_seo_keywords') || ''}
                  onValueChange={value =>
                    setValue('content_seo_keywords', value)
                  }
                  placeholder="Generate SEO keywords (comma-separated)..."
                  autosuggestionsConfig={{
                    textareaPurpose: `Generate SEO keywords for this Amazon product: ${product.title} in category: ${
                      product.category || 'General'
                    }.

Provide a comma-separated list of relevant keywords including:
- Primary product keywords
- Long-tail search terms
- Category-specific terms
- Brand-related keywords
- Feature-based keywords
- Use case keywords

Focus on terms customers would actually search for on Amazon.`,
                    chatApiConfigs: {},
                  }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Comma-separated keywords for Amazon search optimization
                </p>
              </div>

              <div>
                <Label htmlFor="content_competitor_analysis">
                  Competitor Analysis
                </Label>
                <CopilotTextarea
                  className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={watch('content_competitor_analysis') || ''}
                  onValueChange={value =>
                    setValue('content_competitor_analysis', value)
                  }
                  placeholder="Amazcope will help analyze competitors..."
                  autosuggestionsConfig={{
                    textareaPurpose: `Provide competitor analysis guidance for this Amazon product: ${product.title}.

Help identify:
- Key competitive advantages and disadvantages
- Pricing positioning strategies
- Feature differentiation opportunities
- Market gaps and opportunities
- Positioning recommendations
- Potential threats and risks

Focus on actionable insights for improving competitive position in the marketplace.`,
                    chatApiConfigs: {},
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
