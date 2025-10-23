# Amazcope API Design

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Conventions](#api-conventions)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Endpoints](#endpoints)
   - [Authentication](#authentication-endpoints)
   - [Users](#users-endpoints)
   - [Product Tracking](#product-tracking-endpoints)
   - [User Products](#user-products-endpoints)
   - [Metrics & Analytics](#metrics--analytics-endpoints)
   - [AI Suggestions](#ai-suggestions-endpoints)
   - [Notifications](#notifications-endpoints)
   - [User Settings](#user-settings-endpoints)
   - [Chat](#chat-endpoints)
7. [Data Models](#data-models)
8. [Best Practices](#best-practices)

---

## Overview

The Amazcope API is a RESTful API built with FastAPI that enables programmatic access to Amazon product tracking, metrics analysis, and AI-powered optimization features. The API follows REST principles, uses JSON for request/response payloads, and requires JWT-based authentication for most endpoints.

### Key Features

- **Product Tracking:** Import and monitor Amazon products by URL or ASIN
- **Real-time Metrics:** Track price, BSR (Best Seller Rank), ratings, and reviews over time
- **AI Suggestions:** Generate optimization recommendations using OpenAI
- **Alerts & Notifications:** Configurable threshold-based alerts for product changes
- **Competitor Analysis:** Discover and track competitor products from bestseller lists
- **Multi-user Support:** Product ownership and user-specific settings

---

## Authentication

### JWT Token Authentication

All authenticated endpoints require a valid JWT access token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

### Token Lifecycle

- **Access Token:** Short-lived (30 minutes), used for API requests
- **Refresh Token:** Long-lived (7 days), used to obtain new access tokens
- **Token Refresh:** Use `/api/v1/auth/refresh` before access token expires

### Authentication Flow

```mermaid
sequenceDiagram
    Client->>API: POST /auth/login
    API->>Client: {access_token, refresh_token}
    Client->>API: GET /products (Bearer token)
    API->>Client: {products: [...]}
    Note over Client,API: Token expires after 30 min
    Client->>API: POST /auth/refresh (Bearer token)
    API->>Client: {new_access_token, new_refresh_token}
```

### Example: Login & API Call

```bash
# 1. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_username": "user@example.com",
    "password": "securepass123"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "username": "johnsmith"
  }
}

# 2. Use access token for subsequent requests
curl -X GET "http://localhost:8000/api/v1/tracking/products" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## API Conventions

### Request/Response Format

- **Content Type:** `application/json`
- **Date Format:** ISO 8601 (`2025-10-23T10:30:00Z`)
- **Currency:** USD (default), configurable per user
- **Pagination:** Query parameters `skip` and `limit`

### HTTP Methods

| Method   | Usage                              | Idempotent |
|----------|------------------------------------|------------|
| `GET`    | Retrieve resources                 | ✅ Yes     |
| `POST`   | Create resources, trigger actions  | ❌ No      |
| `PUT`    | Full resource update               | ✅ Yes     |
| `PATCH`  | Partial resource update            | ✅ Yes     |
| `DELETE` | Remove resources                   | ✅ Yes     |

### Naming Conventions

- **Endpoints:** Plural nouns (`/products`, `/suggestions`)
- **Fields:** Snake_case (`price_change_threshold`, `review_count`)
- **Query Params:** Snake_case (`active_only`, `min_rating`)

### Common Query Parameters

| Parameter | Type    | Description                      | Example              |
|-----------|---------|----------------------------------|----------------------|
| `skip`    | integer | Pagination offset (default: 0)   | `skip=20`            |
| `limit`   | integer | Results per page (max: 100)      | `limit=50`           |
| `sort_by` | string  | Sort field                       | `sort_by=created_at` |
| `order`   | string  | Sort order (`asc` or `desc`)     | `order=desc`         |

---

## Error Handling

### Error Response Format

All errors follow a consistent structure:

```json
{
  "detail": "Error message or structured error object"
}
```

### HTTP Status Codes

| Code | Meaning                  | Usage                                      |
|------|--------------------------|--------------------------------------------|
| 200  | OK                       | Successful GET/PATCH/PUT                   |
| 201  | Created                  | Successful POST (resource created)         |
| 204  | No Content               | Successful DELETE                          |
| 400  | Bad Request              | Invalid input, validation errors           |
| 401  | Unauthorized             | Missing/invalid authentication token       |
| 403  | Forbidden                | Valid token but insufficient permissions   |
| 404  | Not Found                | Resource doesn't exist                     |
| 409  | Conflict                 | Duplicate resource, conflicting state      |
| 422  | Unprocessable Entity     | Semantic validation errors                 |
| 429  | Too Many Requests        | Rate limit exceeded                        |
| 500  | Internal Server Error    | Unexpected server error                    |

### Error Examples

**400 Bad Request - Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "price_change_threshold"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**404 Not Found:**
```json
{
  "detail": "Product not found"
}
```

**429 Too Many Requests:**
```json
{
  "detail": {
    "error": "Too many requests",
    "message": "Rate limit exceeded. Maximum 5 requests per 300 seconds.",
    "retry_after": 300
  }
}
```

---

## Rate Limiting

### Default Limits
Processed by `RateLimitMiddleware`. Limits are per-IP address.

| Endpoint Pattern          | Limit              | Window    |
|---------------------------|--------------------|-----------|
| `/auth/login`             | 5 requests         | 5 minutes |
| `/auth/register`          | 3 requests         | 1 hour    |
| `/auth/refresh`           | 10 requests        | 1 minute  |
| **All other endpoints**   | 100 requests       | 1 minute  |

```

### Account Lockout (Login)

After **5 failed login attempts**, accounts are locked for **15 minutes**. Users receive an email notification about suspicious activity.

---

## Data Models

### Product

```typescript
interface Product {
  id: string;                          // UUID
  asin: string;                        // Amazon ASIN (10 chars)
  title: string;
  brand: string | null;
  manufacturer: string | null;
  category: string | null;
  small_category: string | null;
  marketplace: string;                 // 'com', 'co.uk', 'de', etc.
  url: string;
  image_url: string | null;
  product_description: string | null;
  features: string[] | null;
  is_active: boolean;
  track_frequency: 'daily' | 'hourly';
  price_change_threshold: number;      // Percentage (0-100)
  bsr_change_threshold: number;        // Percentage (0-100)
  is_competitor: boolean;
  is_unlisted: boolean;
  created_at: string;                  // ISO 8601
  updated_at: string;
  latest_snapshot?: ProductSnapshot;
}
```

### ProductSnapshot

```typescript
interface ProductSnapshot {
  id: string;
  product_id: string;
  scraped_at: string;
  price: number;
  original_price: number | null;
  buybox_price: number | null;
  currency: string;
  discount_percentage: number | null;
  bsr_main_category: number | null;
  bsr_small_category: number | null;
  rating: number;
  review_count: number;
  in_stock: boolean;
  seller_name: string | null;
}
```

### Suggestion

```typescript
interface Suggestion {
  id: string;
  product_id: string;
  user_id: string;
  category: 'title' | 'pricing' | 'description' | 'images' | 'keywords';
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'approved' | 'applied' | 'rejected';
  title: string;
  description: string;
  reasoning: string;
  current_value: string | null;
  suggested_value: string | null;
  expected_impact: string | null;
  impact_score: number;           // 0-10
  effort_score: number;           // 0-10
  confidence_score: number;       // 0-1
  created_at: string;
  reviewed_at: string | null;
  implemented_at: string | null;
}
```


## Best Practices

### Authentication
- Store refresh tokens securely (HttpOnly cookies recommended)
- Refresh access tokens proactively (before expiration)
- Never expose tokens in URLs or logs

### Performance
- Use pagination for large result sets (`skip` and `limit`)
- Cache responses when appropriate (respect `Cache-Control` headers)
- Use batch endpoints for multiple operations (`/batch-refresh`)
- Avoid excessive real-time refreshes; rely on scheduled scraping

### Error Handling
- Always check HTTP status codes
- Parse `detail` field for structured error information
- Implement exponential backoff for 429 (rate limit) errors
- Log 500 errors and report to support

### Future Improvements
- Websocket support for live product updates
- Bulk import/export of products via CSV
- Enhanced filtering and sorting options on list endpoints
- Generic pagination mechanism and response for all list endpoints
---

## API Versioning

Current version: **v1**
Base path: `/api/v1`

Breaking changes will be introduced in new API versions (`/api/v2`). Minor updates and additions are backward-compatible within the same version.

---

## Support & Resources

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc
- **Status Page:** https://status.amazcope.com
- **Support:** support@amazcope.com
- **GitHub:** https://github.com/RIDCorix/amazcope

---
