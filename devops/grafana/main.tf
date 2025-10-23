terraform {
  required_version = ">= 1.0"

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
  }
}

provider "grafana" {
  url  = var.grafana_url
  auth = var.grafana_auth != "" ? var.grafana_auth : null

  # Use backend key if provided (takes precedence over basic auth)
  # To create backend key: Grafana UI → Configuration → backend Keys → Add backend key
  sm_access_token = var.grafana_backend_key != "" ? var.grafana_backend_key : null
}
