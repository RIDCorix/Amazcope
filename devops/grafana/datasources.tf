# ============================================================================
# InfluxDB Datasource - For k6 Load Testing Metrics
# ============================================================================

resource "grafana_data_source" "influxdb" {
  count = var.enable_influxdb ? 1 : 0

  type = "influxdb"
  name = "InfluxDB-k6"
  url  = var.influxdb_url

  is_default = var.influxdb_is_default

  database_name = var.influxdb_database

  # InfluxDB 1.x specific settings
  json_data_encoded = jsonencode({
    # HTTP method for queries
    httpMode = "GET"

    # Query timeout in seconds
    timeInterval = "15s"

    # InfluxDB version
    version = "InfluxQL"

    # Database name
    dbName = var.influxdb_database
  })

  # Optional: Basic authentication for InfluxDB
  # Only set if InfluxDB requires authentication
  basic_auth_enabled = var.influxdb_username != "" ? true : false
  basic_auth_username = var.influxdb_username

  secure_json_data_encoded = var.influxdb_password != "" ? jsonencode({
    basicAuthPassword = var.influxdb_password
  }) : null
}

# ============================================================================
# Prometheus Datasource - For Application Metrics
# ============================================================================

resource "grafana_data_source" "prometheus" {
  count = var.enable_prometheus ? 1 : 0

  type = "prometheus"
  name = "Prometheus"
  url  = var.prometheus_url

  is_default = var.prometheus_is_default

  # Prometheus specific settings
  json_data_encoded = jsonencode({
    # HTTP method for queries (GET or POST)
    httpMethod = "POST"

    # Query timeout in seconds
    timeInterval = "15s"

    # Disable metrics lookup (faster for large datasets)
    disableMetricsLookup = false

    # Custom query parameters
    customQueryParameters = ""

    # Prometheus version
    prometheusType = "Prometheus"

    # Prometheus flavor
    prometheusVersion = "2.40.0"

    # Cache level (0-5, higher = more caching)
    cacheLevel = "High"

    # Incremental queries for faster dashboard loading
    incrementalQuerying = true

    # Query splitting for large time ranges
    incrementalQueryOverlapWindow = "10m"
  })

  # Optional: Basic authentication for Prometheus
  basic_auth_enabled = var.prometheus_basic_auth_user != "" ? true : false
  basic_auth_username = var.prometheus_basic_auth_user

  secure_json_data_encoded = var.prometheus_basic_auth_password != "" ? jsonencode({
    basicAuthPassword = var.prometheus_basic_auth_password
  }) : null
}

# ============================================================================
# Additional Datasources (Optional - Uncomment to enable)
# ============================================================================

# PostgreSQL Datasource - For direct database queries
# resource "grafana_data_source" "postgres" {
#   type = "postgres"
#   name = "PostgreSQL"
#   url  = "postgres:5432"
#
#   database_name = "amazcope"
#   username      = "postgres"
#
#   json_data_encoded = jsonencode({
#     sslmode       = "disable"
#     maxOpenConns  = 100
#     maxIdleConns  = 100
#     connMaxLifetime = 14400
#   })
#
#   secure_json_data_encoded = jsonencode({
#     password = "your-postgres-password"
#   })
# }

# Redis Datasource - For Redis metrics
# resource "grafana_data_source" "redis" {
#   type = "redis-datasource"
#   name = "Redis"
#   url  = "redis:6379"
#
#   json_data_encoded = jsonencode({
#     client       = "standalone"
#     poolSize     = 5
#     timeout      = 10
#     pingInterval = 0
#     pipelineWindow = 0
#   })
#
#   secure_json_data_encoded = jsonencode({
#     password = ""  # Redis password if auth enabled
#   })
# }

# Loki Datasource - For log aggregation
# resource "grafana_data_source" "loki" {
#   type = "loki"
#   name = "Loki"
#   url  = "http://loki:3100"
#
#   json_data_encoded = jsonencode({
#     maxLines = 1000
#     timeout  = 60
#   })
# }

# Elasticsearch Datasource - For logs and metrics
# resource "grafana_data_source" "elasticsearch" {
#   type = "elasticsearch"
#   name = "Elasticsearch"
#   url  = "http://elasticsearch:9200"
#
#   database_name = "[logs-]YYYY.MM.DD"
#
#   json_data_encoded = jsonencode({
#     esVersion                 = "7.10.0"
#     timeField                 = "@timestamp"
#     interval                  = "Daily"
#     logMessageField          = "message"
#     logLevelField            = "level"
#     maxConcurrentShardRequests = 5
#   })
# }

# ============================================================================
# Sentry Datasource - For Error Tracking and APM
# ============================================================================

resource "grafana_data_source" "sentry" {
  count = var.enable_sentry ? 1 : 0

  type = "grafana-sentry-datasource"
  name = "Sentry"
  url  = var.sentry_url

  is_default = false

  # Sentry specific settings
  json_data_encoded = jsonencode({
    # Organization slug
    orgSlug = var.sentry_org_slug
  })

  # Sentry auth token (required)
  secure_json_data_encoded = jsonencode({
    authToken = var.sentry_auth_token
  })
}
