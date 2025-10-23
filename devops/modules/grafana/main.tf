# ============================================================================
# Grafana Module - Datasources and Dashboards
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
  }
}

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

    # Prometheus type
    prometheusType = "Prometheus"

    # Prometheus version
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
