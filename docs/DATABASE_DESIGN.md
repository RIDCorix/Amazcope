# Database Design Documentation

> **Project**: Amazcope - Amazon Product Tracking & Optimization System
> **Database**: PostgreSQL 14+
> **ORM**: SQLAlchemy 2.0 (Async)
> **Migration Tool**: Alembic
> **Last Updated**: 2025-10-23

---

## Table of Contents

1. [Overview](#overview)
2. [Database Architecture](#database-architecture)
3. [Schema Diagrams](#schema-diagrams)
4. [Core Tables](#core-tables)
5. [Relationships](#relationships)
6. [Indexes & Performance](#indexes--performance)
7. [Data Integrity](#data-integrity)
8. [Migration Strategy](#migration-strategy)
9. [Naming Conventions](#naming-conventions)

---

## Overview

Amazcope uses **PostgreSQL** as its primary database, chosen for:
- **JSON support**: Store complex product data (features, dimensions, variations)
- **UUID support**: Primary keys use UUIDs for distributed systems compatibility
- **Time-series optimization**: Efficient storage of daily product snapshots
- **ACID compliance**: Critical for tracking price/ranking changes
- **Advanced indexing**: GIN indexes for JSON fields, composite indexes for queries

### Key Design Principles

1. **Multi-tenancy**: User-based product ownership via `user_products` junction table
2. **Time-series data**: Separate `product_snapshots` table for historical tracking
3. **Soft deletes**: Use `is_active` flags instead of hard deletes
4. **Denormalization**: Latest product data (price, BSR, rating) stored in `products` table for fast access
5. **Cascading deletes**: Proper foreign key constraints with `CASCADE` for data integrity

---

## Database Architecture

### Technology Stack

```
┌─────────────────────────────────────────────────┐
│  Application Layer (FastAPI)                    │
├─────────────────────────────────────────────────┤
│  ORM Layer (SQLAlchemy 2.0 Async)              │
├─────────────────────────────────────────────────┤
│  Migration Layer (Alembic)                      │
├─────────────────────────────────────────────────┤
│  Database Layer (PostgreSQL 14+)                │
│  - UUID Extension (uuid-ossp)                   │
│  - JSONB Support                                │
│  - Time-series Optimization                     │
└─────────────────────────────────────────────────┘
```

### Connection Configuration

- **Connection Pool**: 20 connections (configurable)
- **Async Driver**: `asyncpg`
- **Isolation Level**: READ COMMITTED
- **Timezone**: UTC (all timestamps)

---

## Schema Diagrams

### Entity Relationship Diagram (ERD)

**Generate Visual ERD**:
```bash
# From backend/src directory
uv run cli.py erd

# This generates erd.dot file using eralchemy
# Convert to PNG/SVG using Graphviz:
dot -Tpng erd.dot -o erd.png
dot -Tsvg erd.dot -o erd.svg
```

### High-Level ERD (Simplified)

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│    Users     │1      * │  UserProducts    │*      1 │   Products   │
│──────────────│◄────────│──────────────────│─────────►│──────────────│
│ id (UUID)    │         │ user_id (FK)     │         │ id (UUID)    │
│ username     │         │ product_id (FK)  │         │ asin         │
│ email        │         │ price_threshold  │         │ marketplace  │
│ full_name    │         │ bsr_threshold    │         │ title        │
│ ...          │         │ is_active        │         │ brand        │
└──────────────┘         │ notes            │         │ price        │
       │1                └──────────────────┘         │ bsr          │
       │                                              │ rating       │
       │                                              │ ...          │
       │                                              └──────────────┘
       │                                                     │1
       │                                                     │
       │                                                     │*
       │                                              ┌──────────────┐
       │                                              │  Snapshots   │
       │                                              │──────────────│
       │                                              │ id (UUID)    │
       │                                              │ product_id   │
       │                                              │ price        │
       │                                              │ bsr_main     │
       │                                              │ bsr_small    │
       │                                              │ rating       │
       │                                              │ in_stock     │
       │                                              │ is_prime     │
       │                                              │ scraped_at   │
       │                                              └──────────────┘
       │1                                                    │
       │                                                     │
       │*                                                    │*
┌──────────────┐                                     ┌──────────────┐
│UserSettings  │                                     │    Alerts    │
│──────────────│                                     │──────────────│
│ user_id (FK) │                                     │ id (UUID)    │
│ theme        │                                     │ product_id   │
│ language     │                                     │ user_id      │
│ ...          │                                     │ snapshot_id  │
└──────────────┘                                     │ alert_type   │
                                                     │ severity     │
       ┌──────────────┐                              └──────────────┘
       │Notifications │
       │──────────────│         ┌──────────────────┐
       │ id (UUID)    │         │    Categories    │
       │ user_id (FK) │         │──────────────────│
       │ product_id   │         │ id (UUID)        │
       │ type         │         │ name             │
       │ priority     │         │ parent_id (FK)   │◄┐ Self-referencing
       │ is_read      │         │ level            │  │ for hierarchy
       └──────────────┘         │ marketplace      │──┘
                                └──────────────────┘
       ┌──────────────┐                │1
       │ Suggestions  │1             * │
       │──────────────│◄────────┬──────┘
       │ id (UUID)    │         │
       │ product_id   │         │
       │ title        │         │* ┌──────────────────┐
       │ description  │            │BestsellerSnapshot│
       │ category     │            │──────────────────│
       │ priority     │            │ id (UUID)        │
       │ status       │            │ category_id (FK) │
       │ ai_model     │            │ product_id (FK)  │
       └──────────────┘            │ rank             │
              │1                   │ price            │
              │                    │ scraped_at       │
              │*                   └──────────────────┘
       ┌──────────────────┐
       │SuggestionActions │       ┌──────────────┐
       │──────────────────│       │   Reviews    │
       │ suggestion_id    │       │──────────────│
       │ action_type      │       │ id (UUID)    │
       │ target_field     │       │ product_id   │
       │ current_value    │       │ review_id    │
       │ proposed_value   │       │ rating       │
       │ status           │       │ title        │
       │ applied_at       │       │ text         │
       └──────────────────┘       │ verified     │
                                  └──────────────┘
```

---

## Indexes & Performance

### Primary Indexes

All tables have:
- **Primary key index** on `id` (UUID)
- **Created_at index** for time-based queries
- **Updated_at index** for change tracking

### Composite Indexes

Critical composite indexes for common queries:

```sql
-- Product lookups by ASIN and marketplace
CREATE INDEX idx_products_asin_marketplace ON products(asin, marketplace);

-- User's products with status
CREATE INDEX idx_user_products_user_active ON user_products(user_id)
    WHERE product_id IN (SELECT id FROM products WHERE is_active = TRUE);

-- Unread alerts by user
CREATE INDEX idx_alerts_user_unread ON alerts(user_id, is_read, created_at DESC);

-- Recent snapshots by product
CREATE INDEX idx_snapshots_product_recent ON product_snapshots(product_id, scraped_at DESC);

-- Active suggestions by priority
CREATE INDEX idx_suggestions_active ON suggestions(status, priority)
    WHERE status = 'pending';
```

### JSON Indexes (GIN)

For JSONB column searches:

```sql
-- Product features search
CREATE INDEX idx_products_features ON products USING GIN (features);

-- Amazon's Choice keywords
CREATE INDEX idx_products_amazons_choice ON products USING GIN (amazons_choice_keywords);

-- Notification metadata
CREATE INDEX idx_notifications_metadata ON notifications USING GIN (metadata);
```

### Partial Indexes

For frequently filtered queries:

```sql
-- Only active products
CREATE INDEX idx_products_active ON products(id) WHERE is_active = TRUE;

-- Only unread notifications
CREATE INDEX idx_notifications_unread ON notifications(user_id, created_at DESC)
    WHERE status = 'unread';

-- Only unlisted products
CREATE INDEX idx_products_unlisted ON products(unlisted_at)
    WHERE is_unlisted = TRUE;
```

---

## Data Integrity

### Foreign Key Constraints

All foreign keys use appropriate `ON DELETE` actions:

- **CASCADE**: Child records deleted when parent deleted
  - `UserProducts.user_id` → `Users.id`
  - `ProductSnapshots.product_id` → `Products.id`
  - `Alerts.product_id` → `Products.id`

- **SET NULL**: Reference cleared when parent deleted
  - `Products.created_by_id` → `Users.id`
  - `Alerts.snapshot_id` → `ProductSnapshots.id`

### Check Constraints

```sql
-- Rating must be between 0 and 5
ALTER TABLE products ADD CONSTRAINT chk_rating
    CHECK (rating IS NULL OR (rating >= 0 AND rating <= 5));

-- Thresholds must be positive
ALTER TABLE user_products ADD CONSTRAINT chk_price_threshold
    CHECK (price_change_threshold >= 0 AND price_change_threshold <= 100);

-- Scraped date must be reasonable
ALTER TABLE product_snapshots ADD CONSTRAINT chk_scraped_at
    CHECK (scraped_at >= '2024-01-01' AND scraped_at <= NOW());
```

### Unique Constraints

```sql
-- One product per ASIN/marketplace combination
ALTER TABLE products ADD CONSTRAINT uq_product_asin_marketplace
    UNIQUE (asin, marketplace);

-- User can track each product only once
ALTER TABLE user_products ADD CONSTRAINT uq_user_product
    UNIQUE (user_id, product_id);

-- One settings record per user
ALTER TABLE user_settings ADD CONSTRAINT uq_user_settings_user
    UNIQUE (user_id);
```

---

## Migration Strategy

### Alembic Configuration

Migrations located in: `backend/src/alembic/versions/`

**Migration workflow**:
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current
```

### Major Migrations

1. **fd2c4d97639a**: Convert integer IDs to UUIDs
   - Destructive migration
   - Creates UUID extension
   - Migrates all primary keys and foreign keys
   - Maintains referential integrity

2. **Partition Management**: Monthly snapshot partitions
   ```sql
   -- Create next month's partition
   CREATE TABLE product_snapshots_2025_03 PARTITION OF product_snapshots
       FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

   -- Drop old partitions (90 days retention)
   DROP TABLE product_snapshots_2024_10;
   ```

### Best Practices

1. **Always backup before migrations**
2. **Test migrations on staging first**
3. **Use transactions for data migrations**
4. **Add indexes CONCURRENTLY in production**
5. **Monitor migration duration**

---

## Naming Conventions

### Tables

- **Plural nouns**: `users`, `products`, `alerts`
- **Snake_case**: `user_products`, `bestseller_snapshots`
- **Junction tables**: `{table1}_{table2}` format

### Columns

- **Snake_case**: `created_at`, `price_change_threshold`
- **Boolean prefix**: `is_active`, `has_variations`
- **Timestamps suffix**: `_at` (e.g., `scraped_at`, `reviewed_at`)
- **Foreign keys suffix**: `_id` (e.g., `user_id`, `product_id`)

### Indexes

- **Prefix**: `idx_` for regular indexes
- **Format**: `idx_{table}_{columns}` (e.g., `idx_products_asin_marketplace`)
- **Partial indexes**: `idx_{table}_{columns}_{condition}`

### Constraints

- **Primary key**: `pk_{table}`
- **Foreign key**: `fk_{table}_{column}`
- **Unique**: `uq_{table}_{columns}`
- **Check**: `chk_{table}_{column}`

---

## Performance Considerations

### Query Optimization

1. **Use indexes effectively**: Most queries should use existing indexes
2. **Limit result sets**: Always use `LIMIT` for large tables
3. **Partition large tables**: `product_snapshots` partitioned by month
4. **Denormalize when needed**: Latest product data in `products` table
5. **Use connection pooling**: 20 connections max

### Monitoring

- **Slow query log**: Queries > 1 second
- **Index usage**: `pg_stat_user_indexes`
- **Table bloat**: Monitor with `pg_stat_user_tables`
- **Connection pool**: Track active/idle connections

---

## Future Enhancements

### Planned Improvements

1. **Read Replicas**: For analytics queries
2. **Materialized Views**: For dashboard aggregations
3. **Time-series DB**: Consider TimescaleDB extension for snapshots
4. **Full-text Search**: PostgreSQL FTS for product search
5. **Archival Strategy**: Move old data to cold storage (S3)

### Scalability Considerations

- **Horizontal Scaling**: UUID keys support distributed systems
- **Sharding Strategy**: By marketplace or user segments
- **Caching Layer**: Redis for frequently accessed data
- **CDN**: For product images and static assets

---

## Quick Reference Commands

### Generate ERD
```bash
cd backend/src
uv run cli.py erd  # Generates erd.dot file

# Convert to image formats
dot -Tpng erd.dot -o erd.png
dot -Tsvg erd.dot -o erd.svg
dot -Tpdf erd.dot -o erd.pdf
```

### Database Migrations
```bash
cd backend/src

# Check current version
alembic current

# View migration history
alembic history

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"
```

### Database Inspection
```bash
# Connect to PostgreSQL
psql -U postgres -d amazcope

# List all tables
\dt

# Describe table structure
\d products

# View indexes
\di

# Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```
