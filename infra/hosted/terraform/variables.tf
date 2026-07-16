variable "mumbai_region" {
  type        = string
  description = "Primary content-bearing GCP region (India)."
  default     = "asia-south1"

  validation {
    condition     = var.mumbai_region == "asia-south1"
    error_message = "Hosted application/content region must remain asia-south1 (Mumbai)."
  }
}

variable "delhi_region" {
  type        = string
  description = "Disaster-recovery backup region only."
  default     = "asia-south2"

  validation {
    condition     = var.delhi_region == "asia-south2"
    error_message = "DR region must remain asia-south2 (Delhi)."
  }
}

variable "project_id" {
  type        = string
  description = "GCP project id (scaffold — not provisioned by this repo yet)."
  default     = ""

  validation {
    condition     = var.project_id == "" || can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be empty (scaffold) or a valid GCP project id."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment label."
  default     = "scaffold"

  validation {
    condition     = contains(["scaffold", "staging", "production"], var.environment)
    error_message = "environment must be scaffold|staging|production."
  }
}

variable "enable_live_provision" {
  type        = bool
  description = "Hard switch — must stay false until owner-authorized live provision."
  default     = false

  validation {
    condition     = var.enable_live_provision == false
    error_message = "Live GCP provision is owner-controlled; keep enable_live_provision=false."
  }
}

variable "content_locations" {
  type        = list(string)
  description = "Approved India locations for content-bearing resources."
  default     = ["asia-south1"]

  validation {
    condition = alltrue([
      for loc in var.content_locations : contains(["asia-south1"], loc)
    ])
    error_message = "Content-bearing locations must be restricted to asia-south1."
  }
}
