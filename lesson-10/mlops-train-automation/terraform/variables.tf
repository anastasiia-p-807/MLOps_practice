variable "aws_region" {
  description = "AWS region for Lambda and Step Functions."
  type        = string
  default     = "eu-central-1"
}

variable "aws_profile" {
  description = "Local AWS CLI profile used by Terraform."
  type        = string
  default     = "default"
}

variable "project_name" {
  description = "Prefix for created AWS resources."
  type        = string
  default     = "mlops-train-automation"
}

variable "environment" {
  description = "Environment tag."
  type        = string
  default     = "dev"
}
