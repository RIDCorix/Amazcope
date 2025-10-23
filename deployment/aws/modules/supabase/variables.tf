# Supabase Module Variables

variable "create_project" {
  description = "Whether to create a new Supabase project"
  type        = bool
  default     = true
}

variable "organization_id" {
  description = "Supabase organization ID"
  type        = string
}

variable "project_name" {
  description = "Name of the Supabase project"
  type        = string
}

variable "region" {
  description = "Supabase region"
  type        = string
  default     = "ap-southeast-1"
}

variable "instance_size" {
  description = "Supabase instance size (micro, small, medium, large, xlarge, 2xlarge, 4xlarge, 8xlarge, 12xlarge, 16xlarge)"
  type        = string
  default     = "micro"
}

variable "existing_project_ref" {
  description = "Reference ID of existing Supabase project (when create_project = false)"
  type        = string
  default     = ""
}

# Manual Configuration (for existing projects)
variable "manual_config" {
  description = "Manual configuration for existing Supabase project"
  type = object({
    project_id       = string
    url              = string
    anon_key         = string
    service_role_key = string
    database_url     = string
    host             = string
    user             = string
    password         = string
  })
  default = {
    project_id       = ""
    url              = ""
    anon_key         = ""
    service_role_key = ""
    database_url     = ""
    host             = ""
    user             = ""
    password         = ""
  }
}

# Tags
variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
