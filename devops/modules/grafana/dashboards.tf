# ============================================================================
# Grafana Dashboards - Pre-configured Monitoring Dashboards
# ============================================================================

# ============================================================================
# k6 Load Testing Dashboard - From InfluxDB Datasource
# ============================================================================

resource "grafana_dashboard" "k6_load_testing" {
  count = var.enable_influxdb && var.enable_k6_dashboard ? 1 : 0

  config_json = jsonencode({
    title   = "k6 Load Testing Results"
    uid     = "k6-load-testing"
    version = 1

    # Link to InfluxDB datasource
    # Use the datasource UID from the created datasource
    __inputs = [{
      name        = "DS_INFLUXDB"
      label       = "InfluxDB"
      description = ""
      type        = "datasource"
      pluginId    = "influxdb"
      pluginName  = "InfluxDB"
    }]

    __requires = [{
      type    = "grafana"
      id      = "grafana"
      name    = "Grafana"
      version = "8.0.0"
    }, {
      type    = "datasource"
      id      = "influxdb"
      name    = "InfluxDB"
      version = "1.0.0"
    }]

    tags        = ["k6", "load-testing", "performance"]
    timezone    = "browser"
    refresh     = "10s"
    time = {
      from = "now-15m"
      to   = "now"
    }

    # Dashboard variables for filtering
    templating = {
      list = [
        {
          name       = "TestRun"
          type       = "query"
          datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
          query      = "SHOW TAG VALUES WITH KEY = \"test_run_id\""
          refresh    = 1
          multi      = false
          includeAll = false
        }
      ]
    }

    panels = [
      # Virtual Users (VUs)
      {
        id        = 1
        title     = "Virtual Users (VUs)"
        type      = "graph"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 0, y = 0, w = 12, h = 8 }
        targets = [{
          measurement = "vus"
          select = [[
            { type = "field", params = ["value"] },
            { type = "mean", params = [] }
          ]]
          groupBy = [
            { type = "time", params = ["10s"] },
            { type = "fill", params = ["linear"] }
          ]
        }]
        yaxes = [{
          format = "short"
          label  = "VUs"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        pointradius = 5
      },

      # Request Rate (RPS)
      {
        id        = 2
        title     = "Request Rate (req/s)"
        type      = "graph"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 12, y = 0, w = 12, h = 8 }
        targets = [{
          measurement = "http_reqs"
          select = [[
            { type = "field", params = ["value"] },
            { type = "mean", params = [] }
          ]]
          groupBy = [
            { type = "time", params = ["10s"] },
            { type = "fill", params = ["null"] }
          ]
        }]
        yaxes = [{
          format = "reqps"
          label  = "Requests/sec"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
      },

      # Response Time (P95)
      {
        id        = 3
        title     = "Response Time (P95)"
        type      = "graph"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 0, y = 8, w = 12, h = 8 }
        targets = [{
          measurement = "http_req_duration"
          select = [[
            { type = "field", params = ["value"] },
            { type = "percentile", params = [95] }
          ]]
          groupBy = [
            { type = "time", params = ["10s"] },
            { type = "fill", params = ["null"] }
          ]
        }]
        yaxes = [{
          format = "ms"
          label  = "Duration"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        alert = {
          conditions = [{
            type = "query"
            query = {
              params = ["A", "5m", "now"]
            }
            reducer = {
              type   = "avg"
              params = []
            }
            evaluator = {
              type   = "gt"
              params = [2000] # Alert if P95 > 2 seconds
            }
          }]
          executionErrorState = "alerting"
          frequency           = "60s"
          handler             = 1
          name                = "High Response Time Alert"
          noDataState         = "no_data"
          notifications       = []
        }
      },

      # Error Rate
      {
        id        = 4
        title     = "Error Rate (%)"
        type      = "graph"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 12, y = 8, w = 12, h = 8 }
        targets = [{
          measurement = "http_req_failed"
          select = [[
            { type = "field", params = ["value"] },
            { type = "mean", params = [] }
          ]]
          groupBy = [
            { type = "time", params = ["10s"] },
            { type = "fill", params = ["null"] }
          ]
        }]
        yaxes = [{
          format = "percentunit"
          label  = "Error Rate"
          max    = 1
          min    = 0
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        thresholds = [{
          value     = 0.05
          colorMode = "critical"
          op        = "gt"
          fill      = true
          line      = true
        }]
      },

      # Summary Stats
      {
        id        = 5
        title     = "Test Summary"
        type      = "stat"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 0, y = 16, w = 6, h = 4 }
        targets = [{
          measurement = "http_reqs"
          select = [[
            { type = "field", params = ["value"] },
            { type = "sum", params = [] }
          ]]
        }]
        options = {
          graphMode  = "none"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Total Requests"
            unit        = "short"
          }
        }
      },

      # Success Rate
      {
        id        = 6
        title     = "Success Rate"
        type      = "stat"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 6, y = 16, w = 6, h = 4 }
        targets = [{
          measurement = "http_req_failed"
          select = [[
            { type = "field", params = ["value"] },
            { type = "mean", params = [] }
          ]]
        }]
        options = {
          graphMode  = "area"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Success Rate"
            unit        = "percentunit"
            max         = 1
            min         = 0
            thresholds = {
              mode = "absolute"
              steps = [
                { value = 0, color = "red" },
                { value = 0.95, color = "yellow" },
                { value = 0.99, color = "green" }
              ]
            }
          }
        }
      },

      # Average Response Time
      {
        id        = 7
        title     = "Avg Response Time"
        type      = "stat"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 12, y = 16, w = 6, h = 4 }
        targets = [{
          measurement = "http_req_duration"
          select = [[
            { type = "field", params = ["value"] },
            { type = "mean", params = [] }
          ]]
        }]
        options = {
          graphMode  = "area"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Avg Duration"
            unit        = "ms"
            thresholds = {
              mode = "absolute"
              steps = [
                { value = 0, color = "green" },
                { value = 1000, color = "yellow" },
                { value = 2000, color = "red" }
              ]
            }
          }
        }
      },

      # Peak VUs
      {
        id        = 8
        title     = "Peak VUs"
        type      = "stat"
        datasource = try(grafana_data_source.influxdb[0].uid, "InfluxDB-k6")
        gridPos   = { x = 18, y = 16, w = 6, h = 4 }
        targets = [{
          measurement = "vus"
          select = [[
            { type = "field", params = ["value"] },
            { type = "max", params = [] }
          ]]
        }]
        options = {
          graphMode  = "none"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Peak VUs"
            unit        = "short"
          }
        }
      }
    ]
  })

  overwrite = true

  depends_on = [
    grafana_data_source.influxdb
  ]
}

# ============================================================================
# Node Exporter Dashboard - System Metrics from Prometheus
# ============================================================================

resource "grafana_dashboard" "node_exporter" {
  count = var.enable_prometheus && var.enable_node_exporter_dashboard ? 1 : 0

  config_json = jsonencode({
    title   = "Node Exporter Full"
    uid     = "node-exporter-full"
    version = 1

    __inputs = [{
      name        = "DS_PROMETHEUS"
      label       = "Prometheus"
      description = ""
      type        = "datasource"
      pluginId    = "prometheus"
      pluginName  = "Prometheus"
    }]

    tags        = ["prometheus", "node-exporter", "system"]
    timezone    = "browser"
    refresh     = "30s"
    time = {
      from = "now-1h"
      to   = "now"
    }

    # Dashboard variables
    templating = {
      list = [
        {
          name       = "instance"
          type       = "query"
          datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
          query      = "label_values(node_uname_info, instance)"
          refresh    = 1
          multi      = false
          includeAll = false
          allValue   = ".*"
        },
        {
          name       = "job"
          type       = "query"
          datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
          query      = "label_values(node_exporter_build_info, job)"
          refresh    = 1
          multi      = false
          includeAll = false
          current = {
            text  = "node"
            value = "node"
          }
        }
      ]
    }

    panels = [
      # CPU Usage
      {
        id        = 1
        title     = "CPU Usage"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 0, w = 12, h = 8 }
        targets = [{
          expr = "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\", instance=~\"$instance\"}[5m])) * 100)"
          legendFormat = "CPU Usage"
          refId = "A"
        }]
        yaxes = [{
          format = "percent"
          label  = "CPU %"
          max    = 100
          min    = 0
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        alert = {
          conditions = [{
            type = "query"
            query = {
              params = ["A", "5m", "now"]
            }
            reducer = {
              type   = "avg"
              params = []
            }
            evaluator = {
              type   = "gt"
              params = [80] # Alert if CPU > 80%
            }
          }]
          executionErrorState = "alerting"
          frequency           = "60s"
          handler             = 1
          name                = "High CPU Usage Alert"
          noDataState         = "no_data"
          notifications       = []
        }
      },

      # Memory Usage
      {
        id        = 2
        title     = "Memory Usage"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 12, y = 0, w = 12, h = 8 }
        targets = [
          {
            expr = "node_memory_MemTotal_bytes{instance=~\"$instance\"} - node_memory_MemAvailable_bytes{instance=~\"$instance\"}"
            legendFormat = "Used Memory"
            refId = "A"
          },
          {
            expr = "node_memory_MemTotal_bytes{instance=~\"$instance\"}"
            legendFormat = "Total Memory"
            refId = "B"
          }
        ]
        yaxes = [{
          format = "bytes"
          label  = "Memory"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        alert = {
          conditions = [{
            type = "query"
            query = {
              params = ["A", "5m", "now"]
            }
            reducer = {
              type   = "avg"
              params = []
            }
            evaluator = {
              type   = "gt"
              params = [85] # Alert if memory > 85%
            }
          }]
          executionErrorState = "alerting"
          frequency           = "60s"
          handler             = 1
          name                = "High Memory Usage Alert"
          noDataState         = "no_data"
          notifications       = []
        }
      },

      # Disk I/O
      {
        id        = 3
        title     = "Disk I/O"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 8, w = 12, h = 8 }
        targets = [
          {
            expr = "irate(node_disk_read_bytes_total{instance=~\"$instance\"}[5m])"
            legendFormat = "Read - {{device}}"
            refId = "A"
          },
          {
            expr = "irate(node_disk_written_bytes_total{instance=~\"$instance\"}[5m])"
            legendFormat = "Write - {{device}}"
            refId = "B"
          }
        ]
        yaxes = [{
          format = "Bps"
          label  = "I/O Rate"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
      },

      # Network Traffic
      {
        id        = 4
        title     = "Network Traffic"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 12, y = 8, w = 12, h = 8 }
        targets = [
          {
            expr = "irate(node_network_receive_bytes_total{instance=~\"$instance\", device!~\"lo\"}[5m])"
            legendFormat = "Receive - {{device}}"
            refId = "A"
          },
          {
            expr = "irate(node_network_transmit_bytes_total{instance=~\"$instance\", device!~\"lo\"}[5m])"
            legendFormat = "Transmit - {{device}}"
            refId = "B"
          }
        ]
        yaxes = [{
          format = "Bps"
          label  = "Network Rate"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
      },

      # Disk Space Usage
      {
        id        = 5
        title     = "Disk Space Usage"
        type      = "gauge"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 16, w = 8, h = 6 }
        targets = [{
          expr = "100 - ((node_filesystem_avail_bytes{instance=~\"$instance\", mountpoint=\"/\", fstype!~\"tmpfs|fuse.lxcfs|squashfs|vfat\"} / node_filesystem_size_bytes{instance=~\"$instance\", mountpoint=\"/\", fstype!~\"tmpfs|fuse.lxcfs|squashfs|vfat\"}) * 100)"
          legendFormat = "Disk Usage %"
          refId = "A"
        }]
        options = {
          showThresholdLabels = false
          showThresholdMarkers = true
        }
        fieldConfig = {
          defaults = {
            unit = "percent"
            max  = 100
            min  = 0
            thresholds = {
              mode = "absolute"
              steps = [
                { value = 0, color = "green" },
                { value = 70, color = "yellow" },
                { value = 85, color = "red" }
              ]
            }
          }
        }
      },

      # System Load
      {
        id        = 6
        title     = "System Load (1m, 5m, 15m)"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 8, y = 16, w = 8, h = 6 }
        targets = [
          {
            expr = "node_load1{instance=~\"$instance\"}"
            legendFormat = "Load 1m"
            refId = "A"
          },
          {
            expr = "node_load5{instance=~\"$instance\"}"
            legendFormat = "Load 5m"
            refId = "B"
          },
          {
            expr = "node_load15{instance=~\"$instance\"}"
            legendFormat = "Load 15m"
            refId = "C"
          }
        ]
        yaxes = [{
          format = "short"
          label  = "Load"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 0
        linewidth  = 2
      },

      # System Uptime
      {
        id        = 7
        title     = "System Uptime"
        type      = "stat"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 16, y = 16, w = 8, h = 6 }
        targets = [{
          expr = "node_time_seconds{instance=~\"$instance\"} - node_boot_time_seconds{instance=~\"$instance\"}"
          legendFormat = "Uptime"
          refId = "A"
        }]
        options = {
          graphMode  = "none"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "System Uptime"
            unit        = "s"
          }
        }
      }
    ]
  })

  overwrite = true

  depends_on = [
    grafana_data_source.prometheus
  ]
}

# ============================================================================
# Import Official k6 Dashboard from Grafana.com (Alternative)
# ============================================================================

# Note: This is an alternative to the custom dashboard above
# Uncomment to use the official k6 dashboard from grafana.com

# resource "grafana_dashboard" "k6_official" {
#   count = var.enable_influxdb && var.import_k6_official_dashboard ? 1 : 0
#
#   # Import dashboard from grafana.com
#   # Dashboard ID: 2587 (k6 Load Testing Results)
#   config_json = file("${path.module}/dashboards/k6-official.json")
#
#   overwrite = true
#
#   depends_on = [
#     grafana_data_source.influxdb
#   ]
# }

# ============================================================================
# Import Official Node Exporter Dashboard from Grafana.com (Alternative)
# ============================================================================

# resource "grafana_dashboard" "node_exporter_official" {
#   count = var.enable_prometheus && var.import_node_exporter_official_dashboard ? 1 : 0
#
#   # Import dashboard from grafana.com
#   # Dashboard ID: 1860 (Node Exporter Full)
#   config_json = file("${path.module}/dashboards/node-exporter-official.json")
#
#   overwrite = true
#
#   depends_on = [
#     grafana_data_source.prometheus
#   ]
# }

# ============================================================================
# cAdvisor Dashboard - Docker Container Metrics from Prometheus
# ============================================================================

resource "grafana_dashboard" "cadvisor" {
  count = var.enable_prometheus && var.enable_cadvisor_dashboard ? 1 : 0

  config_json = jsonencode({
    title   = "Docker Container Metrics (cAdvisor)"
    uid     = "cadvisor-containers"
    version = 1

    __inputs = [{
      name        = "DS_PROMETHEUS"
      label       = "Prometheus"
      description = ""
      type        = "datasource"
      pluginId    = "prometheus"
      pluginName  = "Prometheus"
    }]

    tags        = ["prometheus", "cadvisor", "docker", "containers"]
    timezone    = "browser"
    refresh     = "30s"
    time = {
      from = "now-1h"
      to   = "now"
    }

    # Dashboard variables
    templating = {
      list = [
        {
          name       = "container"
          type       = "query"
          datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
          query      = "label_values(container_last_seen, name)"
          refresh    = 1
          multi      = true
          includeAll = true
          allValue   = ".*"
        }
      ]
    }

    panels = [
      # Container CPU Usage
      {
        id        = 1
        title     = "Container CPU Usage (%)"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 0, w = 12, h = 8 }
        targets = [{
          expr = "sum(rate(container_cpu_usage_seconds_total{name=~\"$container\"}[5m])) by (name) * 100"
          legendFormat = "{{name}}"
          refId = "A"
        }]
        yaxes = [{
          format = "percent"
          label  = "CPU %"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        legend = {
          show         = true
          alignAsTable = true
          rightSide    = false
          values       = true
          current      = true
          avg          = true
          max          = true
        }
        alert = {
          conditions = [{
            type = "query"
            query = {
              params = ["A", "5m", "now"]
            }
            reducer = {
              type   = "avg"
              params = []
            }
            evaluator = {
              type   = "gt"
              params = [80]
            }
          }]
          executionErrorState = "alerting"
          frequency           = "60s"
          handler             = 1
          name                = "High Container CPU Usage"
          noDataState         = "no_data"
          notifications       = []
        }
      },

      # Container Memory Usage
      {
        id        = 2
        title     = "Container Memory Usage"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 12, y = 0, w = 12, h = 8 }
        targets = [{
          expr = "sum(container_memory_usage_bytes{name=~\"$container\"}) by (name)"
          legendFormat = "{{name}}"
          refId = "A"
        }]
        yaxes = [{
          format = "bytes"
          label  = "Memory"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        legend = {
          show         = true
          alignAsTable = true
          rightSide    = false
          values       = true
          current      = true
          avg          = true
          max          = true
        }
      },

      # Container Network I/O
      {
        id        = 3
        title     = "Container Network I/O"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 8, w = 12, h = 8 }
        targets = [
          {
            expr = "sum(rate(container_network_receive_bytes_total{name=~\"$container\"}[5m])) by (name)"
            legendFormat = "RX - {{name}}"
            refId = "A"
          },
          {
            expr = "sum(rate(container_network_transmit_bytes_total{name=~\"$container\"}[5m])) by (name)"
            legendFormat = "TX - {{name}}"
            refId = "B"
          }
        ]
        yaxes = [{
          format = "Bps"
          label  = "Network Rate"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        legend = {
          show         = true
          alignAsTable = true
          rightSide    = false
          values       = true
          current      = true
          avg          = true
        }
      },

      # Container Disk I/O
      {
        id        = 4
        title     = "Container Disk I/O"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 12, y = 8, w = 12, h = 8 }
        targets = [
          {
            expr = "sum(rate(container_fs_reads_bytes_total{name=~\"$container\"}[5m])) by (name)"
            legendFormat = "Read - {{name}}"
            refId = "A"
          },
          {
            expr = "sum(rate(container_fs_writes_bytes_total{name=~\"$container\"}[5m])) by (name)"
            legendFormat = "Write - {{name}}"
            refId = "B"
          }
        ]
        yaxes = [{
          format = "Bps"
          label  = "Disk I/O Rate"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        legend = {
          show         = true
          alignAsTable = true
          rightSide    = false
          values       = true
          current      = true
          avg          = true
        }
      },

      # Container Memory Limit
      {
        id        = 5
        title     = "Container Memory Usage vs Limit"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 16, w = 12, h = 8 }
        targets = [
          {
            expr = "sum(container_memory_usage_bytes{name=~\"$container\"}) by (name)"
            legendFormat = "Used - {{name}}"
            refId = "A"
          },
          {
            expr = "sum(container_spec_memory_limit_bytes{name=~\"$container\"}) by (name)"
            legendFormat = "Limit - {{name}}"
            refId = "B"
          }
        ]
        yaxes = [{
          format = "bytes"
          label  = "Memory"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 0
        linewidth  = 2
        legend = {
          show         = true
          alignAsTable = true
          rightSide    = false
          values       = true
          current      = true
          max          = true
        }
      },

      # Container Restart Count
      {
        id        = 6
        title     = "Container Restarts"
        type      = "graph"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 12, y = 16, w = 12, h = 8 }
        targets = [{
          expr = "sum(container_last_seen{name=~\"$container\"}) by (name)"
          legendFormat = "{{name}}"
          refId = "A"
        }]
        yaxes = [{
          format = "short"
          label  = "Count"
        }, {
          format = "short"
          show   = false
        }]
        lines      = true
        fill       = 1
        linewidth  = 2
        bars       = true
      },

      # Running Containers Count
      {
        id        = 7
        title     = "Running Containers"
        type      = "stat"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 0, y = 24, w = 6, h = 4 }
        targets = [{
          expr = "count(container_last_seen{name=~\"$container\"})"
          legendFormat = "Running Containers"
          refId = "A"
        }]
        options = {
          graphMode  = "none"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Running"
            unit        = "short"
            thresholds = {
              mode = "absolute"
              steps = [
                { value = 0, color = "red" },
                { value = 1, color = "green" }
              ]
            }
          }
        }
      },

      # Total Memory Usage
      {
        id        = 8
        title     = "Total Memory Usage"
        type      = "stat"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 6, y = 24, w = 6, h = 4 }
        targets = [{
          expr = "sum(container_memory_usage_bytes{name=~\"$container\"})"
          legendFormat = "Total Memory"
          refId = "A"
        }]
        options = {
          graphMode  = "area"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Memory"
            unit        = "bytes"
            thresholds = {
              mode = "absolute"
              steps = [
                { value = 0, color = "green" },
                { value = 1073741824, color = "yellow" },  # 1GB
                { value = 2147483648, color = "red" }      # 2GB
              ]
            }
          }
        }
      },

      # Total CPU Usage
      {
        id        = 9
        title     = "Total CPU Usage"
        type      = "stat"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 12, y = 24, w = 6, h = 4 }
        targets = [{
          expr = "sum(rate(container_cpu_usage_seconds_total{name=~\"$container\"}[5m])) * 100"
          legendFormat = "Total CPU"
          refId = "A"
        }]
        options = {
          graphMode  = "area"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "CPU %"
            unit        = "percent"
            thresholds = {
              mode = "absolute"
              steps = [
                { value = 0, color = "green" },
                { value = 50, color = "yellow" },
                { value = 80, color = "red" }
              ]
            }
          }
        }
      },

      # Total Network I/O
      {
        id        = 10
        title     = "Total Network I/O"
        type      = "stat"
        datasource = try(grafana_data_source.prometheus[0].uid, "Prometheus")
        gridPos   = { x = 18, y = 24, w = 6, h = 4 }
        targets = [
          {
            expr = "sum(rate(container_network_receive_bytes_total{name=~\"$container\"}[5m]))"
            legendFormat = "RX"
            refId = "A"
          },
          {
            expr = "sum(rate(container_network_transmit_bytes_total{name=~\"$container\"}[5m]))"
            legendFormat = "TX"
            refId = "B"
          }
        ]
        options = {
          graphMode  = "area"
          colorMode  = "value"
          reduceOptions = {
            values = false
            calcs  = ["lastNotNull"]
          }
        }
        fieldConfig = {
          defaults = {
            displayName = "Network"
            unit        = "Bps"
          }
        }
      }
    ]
  })

  overwrite = true

  depends_on = [
    grafana_data_source.prometheus
  ]
}
