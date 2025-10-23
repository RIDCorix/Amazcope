# Grafana Terraform Configuration

This directory contains Terraform configurations for provisioning Grafana datasources automatically.

## Resources Created

- **InfluxDB Datasource** - For k6 load testing metrics
- **Prometheus Datasource** - For application metrics
- **k6 Dashboard** - Pre-configured load testing dashboard (8 panels)
- **Node Exporter Dashboard** - System metrics dashboard (7 panels)

## Prerequisites

1. **Terraform** - Install from https://www.terraform.io/downloads
2. **Grafana Instance** - Running and accessible
3. **Grafana API Key** - With admin permissions

## Quick Start

### 1. Set Grafana Credentials

```bash
# Export environment variables
export TF_VAR_grafana_url="http://localhost:3000"
export TF_VAR_grafana_auth="admin:admin"

# OR create terraform.tfvars
cat > terraform.tfvars <<EOF
grafana_url  = "http://localhost:3000"
grafana_auth = "admin:admin"
EOF
```

### 2. Initialize Terraform

```bash
cd devops/grafana
terraform init
```

### 3. Plan and Apply

```bash
# Preview changes
terraform plan

# Apply configuration
terraform apply

# Auto-approve (skip confirmation)
terraform apply -auto-approve
```

### 4. Verify

```bash
# Check created resources
terraform show

# List datasources
curl -u admin:admin http://localhost:3000/api/datasources
```

## Configuration

### Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `grafana_url` | Grafana instance URL | `http://localhost:3000` | No |
| `grafana_auth` | Basic auth (user:pass) | `admin:admin` | No |
| `grafana_api_key` | API key (alternative) | `""` | No |
| `influxdb_url` | InfluxDB URL | `http://influxdb:8086` | No |
| `influxdb_database` | InfluxDB database name | `k6` | No |
| `prometheus_url` | Prometheus URL | `http://prometheus:9090` | No |

### Using API Key (Recommended for Production)

```bash
# Create API key in Grafana UI:
# Configuration → API Keys → Add API key (Admin role)

export TF_VAR_grafana_api_key="eyJrIjoixxxx..."

# Apply with API key
terraform apply
```

## Datasource Details

### InfluxDB Datasource

- **Name:** `InfluxDB-k6`
- **Type:** `influxdb`
- **Purpose:** Store k6 load testing metrics
- **Database:** `k6`
- **Access:** `proxy` (via Grafana)
- **Default:** `true`

**Usage:**
```bash
# Run k6 test with InfluxDB output
k6 run --out influxdb=http://localhost:8086/k6 load-tests/k6/throughput-test.js
```

### Prometheus Datasource

- **Name:** `Prometheus`
- **Type:** `prometheus`
- **Purpose:** Store application metrics (FastAPI, Dragatiq)
- **URL:** `http://prometheus:9090`
- **Access:** `proxy`
- **Scrape Interval:** `15s`

**Metrics Available:**
- FastAPI request duration, request count
- Dragatiq task duration, task count
- System metrics (CPU, memory)

## Customization

### Add Custom Datasource

Edit `datasources.tf`:

```hcl
resource "grafana_data_source" "custom" {
  type = "postgres"
  name = "PostgreSQL"
  url  = "postgres:5432"

  database_name = "amazcope"
  username      = var.postgres_user

  secure_json_data_encoded = jsonencode({
    password = var.postgres_password
  })
}
```

### Change Default Datasource

```hcl
resource "grafana_data_source" "prometheus" {
  # ... other config ...
  is_default = true  # Set Prometheus as default
}

resource "grafana_data_source" "influxdb" {
  # ... other config ...
  is_default = false  # Disable InfluxDB as default
}
```

## Outputs

After applying, Terraform outputs:

- `influxdb_datasource_uid` - InfluxDB datasource UID
- `prometheus_datasource_uid` - Prometheus datasource UID
- `grafana_url` - Grafana instance URL
- `k6_dashboard_url` - Direct link to k6 dashboard
- `node_exporter_dashboard_url` - Direct link to Node Exporter dashboard

**Example:**
```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

grafana_url = "http://localhost:3000"
influxdb_datasource_uid = "P4169B1D6D1D5C7E5"
k6_dashboard_url = "http://localhost:3000/d/k6-load-testing/k6-load-testing-results"
node_exporter_dashboard_url = "http://localhost:3000/d/node-exporter-full/node-exporter-full"
prometheus_datasource_uid = "PBFA97CFB590B2093"
```

## Dashboards

### Pre-configured Dashboards (Automatic)

Terraform automatically creates two dashboards:

#### k6 Load Testing Dashboard
- **URL**: `http://localhost:3000/d/k6-load-testing`
- **Features**:
  - Virtual Users (VUs) over time
  - Request rate (req/s)
  - Response time (P95) with 2s threshold alert
  - Error rate percentage with 5% threshold
  - Summary stats (total requests, success rate, avg response time, peak VUs)
  - Test run filtering by `test_run_id`
- **Datasource**: InfluxDB-k6
- **Metrics**: All k6 metrics from load tests

#### Node Exporter Dashboard
- **URL**: `http://localhost:3000/d/node-exporter-full`
- **Features**:
  - CPU usage with 80% threshold alert
  - Memory usage (used vs total) with 85% threshold alert
  - Disk I/O (read/write rates)
  - Network traffic (receive/transmit)
  - Disk space usage gauge (0-100%)
  - System load (1m, 5m, 15m averages)
  - System uptime
- **Datasource**: Prometheus
- **Metrics**: Node Exporter metrics (node_*)

### Importing Official Dashboards (Manual Alternative)

If you prefer the official community dashboards:

#### k6 Load Testing Dashboard (Official)
1. Go to: `http://localhost:3000/dashboard/import`
2. Enter dashboard ID: **2587**
3. Select datasource: **InfluxDB-k6**
4. Click **Import**
5. Link: https://grafana.com/grafana/dashboards/2587

#### Node Exporter Dashboard (Official)
1. Go to: `http://localhost:3000/dashboard/import`
2. Enter dashboard ID: **1860**
3. Select datasource: **Prometheus**
4. Click **Import**
5. Link: https://grafana.com/grafana/dashboards/1860

### Dashboard Configuration Variables

Control dashboard creation in `terraform.tfvars`:

```hcl
# Enable/disable custom dashboards
enable_k6_dashboard           = true   # k6 load testing dashboard
enable_node_exporter_dashboard = true   # Node exporter system metrics

# Import official dashboards (requires downloading JSON files first)
import_k6_official_dashboard           = false
import_node_exporter_official_dashboard = false
```

## Troubleshooting

### Error: Failed to connect to Grafana

```
Error: status: 401, body: {"message":"Unauthorized"}
```

**Solution:**
```bash
# Check Grafana is running
curl http://localhost:3000/api/health

# Verify credentials
export TF_VAR_grafana_auth="admin:admin"

# Or use API key
export TF_VAR_grafana_api_key="your-api-key"
```

### Error: Datasource already exists

```
Error: status: 409, body: {"message":"Data source with the same name already exists"}
```

**Solution:**
```bash
# Import existing datasource
terraform import grafana_data_source.influxdb <datasource-id>

# Or delete and recreate
terraform destroy -target=grafana_data_source.influxdb
terraform apply
```

### InfluxDB Connection Failed

```bash
# Test InfluxDB connectivity
curl http://localhost:8086/ping

# Check InfluxDB logs
docker logs influxdb

# Verify database exists
curl http://localhost:8086/query?q=SHOW+DATABASES
```

### Prometheus Connection Failed

```bash
# Test Prometheus connectivity
curl http://localhost:9090/-/healthy

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify metrics available
curl http://localhost:9090/api/v1/query?query=up
```

## Cleanup

```bash
# Destroy all Grafana resources
terraform destroy

# Destroy specific resource
terraform destroy -target=grafana_data_source.influxdb
```

## Integration with Docker Compose

This configuration works with the Docker Compose setup in `devops/docker-compose.yml`:

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana

  influxdb:
    image: influxdb:1.8
    ports:
      - "8086:8086"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
```

**Workflow:**

1. Start services: `docker-compose up -d`
2. Apply Terraform: `terraform apply`
3. Run k6 tests: `k6 run --out influxdb=... test.js`
4. View in Grafana: http://localhost:3000

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Provision Grafana Datasources

on:
  push:
    branches: [main]
    paths:
      - 'devops/grafana/**'

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Terraform Init
        working-directory: devops/grafana
        run: terraform init

      - name: Terraform Plan
        working-directory: devops/grafana
        env:
          TF_VAR_grafana_url: ${{ secrets.GRAFANA_URL }}
          TF_VAR_grafana_api_key: ${{ secrets.GRAFANA_API_KEY }}
        run: terraform plan

      - name: Terraform Apply
        working-directory: devops/grafana
        env:
          TF_VAR_grafana_url: ${{ secrets.GRAFANA_URL }}
          TF_VAR_grafana_api_key: ${{ secrets.GRAFANA_API_KEY }}
        run: terraform apply -auto-approve
```

## Files

- `main.tf` - Provider configuration
- `datasources.tf` - Datasource definitions (InfluxDB, Prometheus)
- `dashboards.tf` - Pre-configured dashboards (k6, Node Exporter)
- `variables.tf` - Input variables (17 variables)
- `outputs.tf` - Output values (datasource UIDs, dashboard URLs)
- `versions.tf` - Terraform version constraints
- `terraform.tfvars.example` - Example variables file

## Dashboard Features

### k6 Dashboard Highlights
- **8 Panels**: VUs, RPS, P95 latency, error rate, 4 stat panels
- **Alerts**: Automatic alert if P95 > 2 seconds
- **Variables**: Filter by test run ID
- **Refresh**: Auto-refresh every 10 seconds
- **Time Range**: Last 15 minutes by default

### Node Exporter Dashboard Highlights
- **7 Panels**: CPU, memory, disk I/O, network, disk space, load, uptime
- **Alerts**: CPU > 80%, Memory > 85%
- **Variables**: Filter by instance and job
- **Refresh**: Auto-refresh every 30 seconds
- **Time Range**: Last 1 hour by default
- **Gauges**: Visual disk space usage gauge with color thresholds

## Resources

- **Terraform Grafana Provider:** https://registry.terraform.io/providers/grafana/grafana/latest/docs
- **InfluxDB Documentation:** https://docs.influxdata.com/
- **Prometheus Documentation:** https://prometheus.io/docs/
- **Grafana Datasources:** https://grafana.com/docs/grafana/latest/datasources/

## Support

For issues or questions:
- Check Grafana logs: `docker logs grafana`
- Review Terraform state: `terraform state list`
- Validate configuration: `terraform validate`
