# Grafana Terraform Module

This module creates Grafana datasources and dashboards for monitoring.

## Features

- **InfluxDB Datasource**: For k6 load testing metrics
- **Prometheus Datasource**: For application and infrastructure metrics
- **k6 Dashboard**: Pre-configured load testing dashboard (8 panels)
- **Node Exporter Dashboard**: System metrics dashboard (7 panels)

## Usage

```hcl
module "grafana" {
  source = "./modules/grafana"

  # InfluxDB configuration
  influxdb_url      = "http://influxdb:8086"
  influxdb_database = "k6"

  # Prometheus configuration
  prometheus_url = "http://prometheus:9090"

  # Feature flags
  enable_influxdb   = true
  enable_prometheus = true

  # Dashboard configuration
  enable_k6_dashboard           = true
  enable_node_exporter_dashboard = true
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| influxdb_url | InfluxDB instance URL | `string` | `"http://influxdb:8086"` | no |
| influxdb_database | InfluxDB database name | `string` | `"k6"` | no |
| influxdb_username | InfluxDB username | `string` | `""` | no |
| influxdb_password | InfluxDB password | `string` | `""` | no |
| prometheus_url | Prometheus instance URL | `string` | `"http://prometheus:9090"` | no |
| prometheus_basic_auth_user | Prometheus username | `string` | `""` | no |
| prometheus_basic_auth_password | Prometheus password | `string` | `""` | no |
| enable_influxdb | Enable InfluxDB datasource | `bool` | `true` | no |
| enable_prometheus | Enable Prometheus datasource | `bool` | `true` | no |
| influxdb_is_default | Set InfluxDB as default | `bool` | `true` | no |
| prometheus_is_default | Set Prometheus as default | `bool` | `false` | no |
| enable_k6_dashboard | Enable k6 dashboard | `bool` | `true` | no |
| enable_node_exporter_dashboard | Enable Node Exporter dashboard | `bool` | `true` | no |

## Outputs

| Name | Description |
|------|-------------|
| influxdb_datasource_uid | UID of the InfluxDB datasource |
| prometheus_datasource_uid | UID of the Prometheus datasource |
| k6_dashboard_uid | UID of the k6 dashboard |
| node_exporter_dashboard_uid | UID of the Node Exporter dashboard |
| datasource_summary | Summary of configured datasources |
| dashboard_summary | Summary of created dashboards |

## Requirements

- Terraform >= 1.0
- Grafana provider ~> 2.0
- Grafana instance running and accessible

## Resources Created

- `grafana_data_source.influxdb` - InfluxDB datasource
- `grafana_data_source.prometheus` - Prometheus datasource
- `grafana_dashboard.k6_load_testing` - k6 load testing dashboard
- `grafana_dashboard.node_exporter` - Node Exporter dashboard

## Example with All Options

```hcl
module "grafana" {
  source = "./modules/grafana"

  # InfluxDB configuration
  influxdb_url      = "http://influxdb:8086"
  influxdb_database = "k6"
  influxdb_username = "k6_user"
  influxdb_password = var.influxdb_password

  # Prometheus configuration
  prometheus_url                  = "http://prometheus:9090"
  prometheus_basic_auth_user      = "prometheus"
  prometheus_basic_auth_password  = var.prometheus_password

  # Feature flags
  enable_influxdb   = true
  enable_prometheus = true

  # Default datasource
  influxdb_is_default   = true
  prometheus_is_default = false

  # Dashboards
  enable_k6_dashboard           = true
  enable_node_exporter_dashboard = true
}
```
