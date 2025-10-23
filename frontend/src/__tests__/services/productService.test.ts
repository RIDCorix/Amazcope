import apiClient from '@/lib/api';
import {
  Product,
  ProductFromUrlRequest,
  productService,
} from '@/services/productService';

jest.mock('@/lib/api');
const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('productService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getProducts', () => {
    it('should fetch all products successfully', async () => {
      const mockProducts: Product[] = [
        {
          id: 'test-uuid-1',
          asin: 'B07XJ8C8F5',
          title: 'Test Product 1',
          brand: 'Test Brand',
          category: 'Electronics',
          url: 'https://amazon.com/dp/B07XJ8C8F5',
          image_url: 'https://example.com/image1.jpg',
          is_active: true,
          price_change_threshold: 10.0,
          bsr_change_threshold: 30.0,
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ];

      mockedApiClient.get.mockResolvedValueOnce({ data: mockProducts });

      const result = await productService.getProducts();

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/tracking/products'
      );
      expect(result).toEqual(mockProducts);
    });

    it('should handle fetch error', async () => {
      mockedApiClient.get.mockRejectedValueOnce(new Error('Network error'));

      await expect(productService.getProducts()).rejects.toThrow(
        'Network error'
      );
    });
  });

  describe('getProduct', () => {
    it('should fetch product by id', async () => {
      const mockProduct: Product = {
        id: 'test-uuid-1',
        asin: 'B07XJ8C8F5',
        title: 'Test Product',
        brand: 'Test Brand',
        category: 'Electronics',
        url: 'https://amazon.com/dp/B07XJ8C8F5',
        image_url: 'https://example.com/image.jpg',
        is_active: true,
        price_change_threshold: 10.0,
        bsr_change_threshold: 30.0,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      };

      mockedApiClient.get.mockResolvedValueOnce({ data: mockProduct });

      const result = await productService.getProduct('test-uuid-1');

      expect(mockedApiClient.get).toHaveBeenCalledWith(
        '/api/v1/tracking/products/1'
      );
      expect(result).toEqual(mockProduct);
    });

    it('should handle product not found', async () => {
      mockedApiClient.get.mockRejectedValueOnce(new Error('Product not found'));

      await expect(productService.getProduct('test-uuid-999')).rejects.toThrow(
        'Product not found'
      );
    });
  });

  describe('importFromUrl', () => {
    it('should import product from URL successfully', async () => {
      const mockRequest: ProductFromUrlRequest = {
        url: 'https://www.amazon.com/dp/B07XJ8C8F5',
        price_change_threshold: 10.0,
        bsr_change_threshold: 30.0,
        scrape_reviews: true,
        scrape_bestsellers: true,
      };

      const mockProduct: Product = {
        id: 'test-uuid-1',
        asin: 'B07XJ8C8F5',
        title: 'Imported Product',
        brand: 'Test Brand',
        category: 'Electronics',
        url: mockRequest.url,
        image_url: 'https://example.com/image.jpg',
        is_active: true,
        price_change_threshold: 10.0,
        bsr_change_threshold: 30.0,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      };

      mockedApiClient.post.mockResolvedValueOnce({ data: mockProduct });

      const result = await productService.importFromUrl(mockRequest);

      expect(mockedApiClient.post).toHaveBeenCalledWith(
        '/api/v1/tracking/products/from-url',
        mockRequest
      );
      expect(result).toEqual(mockProduct);
    });

    it('should handle invalid URL', async () => {
      const mockRequest: ProductFromUrlRequest = {
        url: 'invalid-url',
        price_change_threshold: 10.0,
        bsr_change_threshold: 30.0,
        scrape_reviews: false,
        scrape_bestsellers: false,
      };

      mockedApiClient.post.mockRejectedValueOnce(new Error('Invalid URL'));

      await expect(productService.importFromUrl(mockRequest)).rejects.toThrow(
        'Invalid URL'
      );
    });
  });

  describe('deleteProduct', () => {
    it('should delete product successfully', async () => {
      mockedApiClient.delete.mockResolvedValueOnce({ data: {} });

      await productService.deleteProduct('test-uuid-1');

      expect(mockedApiClient.delete).toHaveBeenCalledWith(
        '/api/v1/tracking/products/1'
      );
    });

    it('should handle delete error', async () => {
      mockedApiClient.delete.mockRejectedValueOnce(new Error('Delete failed'));

      await expect(productService.deleteProduct('test-uuid-1')).rejects.toThrow(
        'Delete failed'
      );
    });
  });

  describe('updateProduct', () => {
    it('should update product successfully', async () => {
      const updates = {
        price_change_threshold: 15.0,
        bsr_change_threshold: 25.0,
      };

      const mockProduct: Product = {
        id: 'test-uuid-1',
        asin: 'B07XJ8C8F5',
        title: 'Updated Product',
        brand: 'Test Brand',
        category: 'Electronics',
        url: 'https://amazon.com/dp/B07XJ8C8F5',
        image_url: 'https://example.com/image.jpg',
        is_active: true,
        price_change_threshold: 15.0,
        bsr_change_threshold: 25.0,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      };

      mockedApiClient.put.mockResolvedValueOnce({ data: mockProduct });

      const result = await productService.updateProduct('test-uuid-1', updates);

      expect(mockedApiClient.put).toHaveBeenCalledWith(
        '/api/v1/tracking/products/1',
        updates
      );
      expect(result.price_change_threshold).toBe(15.0);
    });
  });

  // Note: refreshProduct, getProductSnapshots, and getProductReviews
  // are not exported from productService - they may be internal or deprecated
});
