# ============================================================================
# Grafana Alert Rules - Unified Alerting
# ============================================================================

# Note: This uses Grafana Unified Alerting (available in Grafana 8.0+)
# Dashboard alerts are deprecated in favor of alert rules

# ============================================================================
# Contact Points (Notification Channels)
# ============================================================================

# Default contact point for alerts (can be customized)
resource "grafana_contact_point" "default_email" {
  count = var.enable_alerting ? 1 : 0

  name = "Default Email"

  email {
    addresses               = var.alert_email_addresses
    single_email            = false
    disable_resolve_message = false
  }
}

# Slack contact point (optional)
resource "grafana_contact_point" "slack" {
  count = var.enable_alerting && var.alert_slack_webhook_url != "" ? 1 : 0

  name = "Slack Alerts"

  slack {
    url                     = var.alert_slack_webhook_url
    text                    = "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
    title                   = "{{ .GroupLabels.alertname }}"
    disable_resolve_message = false
  }
}

# Webhook contact point (optional)
resource "grafana_contact_point" "webhook" {
  count = var.enable_alerting && var.alert_webhook_url != "" ? 1 : 0

  name = "Webhook Alerts"

  webhook {
    url                     = var.alert_webhook_url
    http_method             = "POST"
    disable_resolve_message = false
  }
}

# ============================================================================
# Notification Policies
# ============================================================================

resource "grafana_notification_policy" "default" {
  count = var.enable_alerting ? 1 : 0

  group_by      = ["alertname", "grafana_folder"]
  group_wait    = "30s"
  group_interval = "5m"
  repeat_interval = "4h"

  contact_point = grafana_contact_point.default_email[0].name

  policy {
    matcher {
      label = "severity"
      match = "="
      value = "critical"
    }
    group_by      = ["alertname"]
    group_wait    = "10s"
    repeat_interval = "1h"
    contact_point = grafana_contact_point.default_email[0].name
  }

  policy {
    matcher {
      label = "severity"
      match = "="
      value = "warning"
    }
    group_by      = ["alertname"]
    repeat_interval = "12h"
    contact_point = grafana_contact_point.default_email[0].name
  }
}

# ============================================================================
# Alert Rule Groups
# ============================================================================

# Container Alerts - cAdvisor Metrics
# ============================================================================

resource "grafana_rule_group" "container_alerts" {
  count = var.enable_prometheus && var.enable_cadvisor_dashboard && var.enable_alerting ? 1 : 0

  name             = "Container Alerts"
  folder_uid       = "container-monitoring"
  interval_seconds = 60

  rule {
    name      = "High Container CPU Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "sum(rate(container_cpu_usage_seconds_total{name=~\".+\"}[5m])) by (name) * 100"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [80]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "Container {{ $labels.name }} CPU usage is {{ $value }}% (threshold: 80%)"
      summary     = "High CPU usage detected on container {{ $labels.name }}"
    }

    labels = {
      severity = "warning"
      service  = "containers"
      type     = "performance"
    }
  }

  rule {
    name      = "Critical Container CPU Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "sum(rate(container_cpu_usage_seconds_total{name=~\".+\"}[5m])) by (name) * 100"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [95]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "2m"

    annotations = {
      description = "Container {{ $labels.name }} CPU usage is critically high at {{ $value }}% (threshold: 95%)"
      summary     = "CRITICAL: Container {{ $labels.name }} CPU usage is above 95%"
    }

    labels = {
      severity = "critical"
      service  = "containers"
      type     = "performance"
    }
  }

  rule {
    name      = "High Container Memory Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "(sum(container_memory_usage_bytes{name=~\".+\"}) by (name) / sum(container_spec_memory_limit_bytes{name=~\".+\"}) by (name)) * 100"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [85]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "Container {{ $labels.name }} memory usage is {{ $value }}% of limit (threshold: 85%)"
      summary     = "High memory usage detected on container {{ $labels.name }}"
    }

    labels = {
      severity = "warning"
      service  = "containers"
      type     = "memory"
    }
  }

  rule {
    name      = "Container Restart Detected"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "changes(container_last_seen{name=~\".+\"}[5m])"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [0]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "last"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "OK"
    for            = "0s"

    annotations = {
      description = "Container {{ $labels.name }} has restarted {{ $value }} times in the last 5 minutes"
      summary     = "Container restart detected: {{ $labels.name }}"
    }

    labels = {
      severity = "warning"
      service  = "containers"
      type     = "availability"
    }
  }

  rule {
    name      = "Container Not Running"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "absent(container_last_seen{name=~\".+\"})"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [0]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "last"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "Alerting"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "No containers are currently running"
      summary     = "All containers are down"
    }

    labels = {
      severity = "critical"
      service  = "containers"
      type     = "availability"
    }
  }
}

# System Alerts - Node Exporter Metrics
# ============================================================================

resource "grafana_rule_group" "system_alerts" {
  count = var.enable_prometheus && var.enable_node_exporter_dashboard && var.enable_alerting ? 1 : 0

  name             = "System Alerts"
  folder_uid       = "system-monitoring"
  interval_seconds = 60

  rule {
    name      = "High System CPU Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [80]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "System {{ $labels.instance }} CPU usage is {{ $value }}% (threshold: 80%)"
      summary     = "High CPU usage on {{ $labels.instance }}"
    }

    labels = {
      severity = "warning"
      service  = "system"
      type     = "performance"
    }
  }

  rule {
    name      = "High System Memory Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "((node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes) * 100"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [85]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "System {{ $labels.instance }} memory usage is {{ $value }}% (threshold: 85%)"
      summary     = "High memory usage on {{ $labels.instance }}"
    }

    labels = {
      severity = "warning"
      service  = "system"
      type     = "memory"
    }
  }

  rule {
    name      = "High Disk Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "100 - ((node_filesystem_avail_bytes{mountpoint=\"/\", fstype!~\"tmpfs|fuse.lxcfs|squashfs|vfat\"} / node_filesystem_size_bytes{mountpoint=\"/\", fstype!~\"tmpfs|fuse.lxcfs|squashfs|vfat\"}) * 100)"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [85]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "last"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "10m"

    annotations = {
      description = "Disk usage on {{ $labels.instance }} is {{ $value }}% (threshold: 85%)"
      summary     = "High disk usage on {{ $labels.instance }}"
    }

    labels = {
      severity = "warning"
      service  = "system"
      type     = "storage"
    }
  }

  rule {
    name      = "Critical Disk Usage"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = try(grafana_data_source.prometheus[0].uid, "")
      model = jsonencode({
        expr         = "100 - ((node_filesystem_avail_bytes{mountpoint=\"/\", fstype!~\"tmpfs|fuse.lxcfs|squashfs|vfat\"} / node_filesystem_size_bytes{mountpoint=\"/\", fstype!~\"tmpfs|fuse.lxcfs|squashfs|vfat\"}) * 100)"
        refId        = "A"
        intervalMs   = 1000
        maxDataPoints = 43200
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [95]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "last"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 600
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "5m"

    annotations = {
      description = "CRITICAL: Disk usage on {{ $labels.instance }} is {{ $value }}% (threshold: 95%)"
      summary     = "Critical disk usage on {{ $labels.instance }}"
    }

    labels = {
      severity = "critical"
      service  = "system"
      type     = "storage"
    }
  }
}

# Performance Alerts - k6 Load Testing
# ============================================================================

resource "grafana_rule_group" "performance_alerts" {
  count = var.enable_influxdb && var.enable_k6_dashboard && var.enable_alerting ? 1 : 0

  name             = "Performance Alerts"
  folder_uid       = "load-testing"
  interval_seconds = 60

  rule {
    name      = "High Response Time"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = try(grafana_data_source.influxdb[0].uid, "")
      model = jsonencode({
        query = "SELECT percentile(\"value\", 95) FROM \"http_req_duration\" WHERE $timeFilter GROUP BY time(10s) fill(null)"
        rawQuery = true
        refId    = "A"
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [2000]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "2m"

    annotations = {
      description = "P95 response time is {{ $value }}ms (threshold: 2000ms)"
      summary     = "High response time detected during load test"
    }

    labels = {
      severity = "warning"
      service  = "load-testing"
      type     = "performance"
    }
  }

  rule {
    name      = "High Error Rate"
    condition = "C"

    data {
      ref_id = "A"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = try(grafana_data_source.influxdb[0].uid, "")
      model = jsonencode({
        query = "SELECT mean(\"value\") FROM \"http_req_failed\" WHERE $timeFilter GROUP BY time(10s) fill(null)"
        rawQuery = true
        refId    = "A"
      })
    }

    data {
      ref_id = "B"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        conditions = [
          {
            evaluator = {
              params = [0.05]
              type   = "gt"
            }
            operator = {
              type = "and"
            }
            query = {
              params = ["A"]
            }
            reducer = {
              params = []
              type   = "avg"
            }
            type = "query"
          }
        ]
        refId = "B"
        type  = "classic_conditions"
      })
    }

    data {
      ref_id = "C"

      relative_time_range {
        from = 300
        to   = 0
      }

      datasource_uid = "-100"
      model = jsonencode({
        expression = "B"
        reducer    = "last"
        refId      = "C"
        type       = "reduce"
      })
    }

    no_data_state  = "NoData"
    exec_err_state = "Alerting"
    for            = "1m"

    annotations = {
      description = "Error rate is {{ $value }}% (threshold: 5%)"
      summary     = "High error rate detected during load test"
    }

    labels = {
      severity = "critical"
      service  = "load-testing"
      type     = "errors"
    }
  }
}
