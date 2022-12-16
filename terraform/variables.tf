variable "project-id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west3"
}

variable "zone" {
  type    = string
  default = "europe-west3-c"
}

variable "subnetwork-main-cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "master-cidr" {
  type    = string
  default = "10.1.0.0/28"
}

variable "subnetwork-pods-cidr" {
  type    = string
  default = "10.2.0.0/16"
}

variable "subnetwork-services-cidr" {
  type    = string
  default = "10.3.0.0/16"
}

variable "linux-agents-machine-type" {
  type    = string
  default = "e2-standard-32"
}

variable "linux-agents-count" {
  type    = number
  default = 6
}

variable "linux-agents-build-queue" {
  type    = string
  default = "linux"
}

variable "linux-agents-cpu-request" {
  type    = string
  default = "30"
}

variable "linux-agents-mem-request" {
  type    = string
  default = "80Gi"
}

variable "windows-agents-machine-type" {
  type    = string
  default = "c2-standard-16"
}

variable "windows-agents-count" {
  type    = number
  default = 8
}

variable "windows-agents-build-queue" {
  type    = string
  default = "windows"
}

variable "windows-agents-cpu-request" {
  type    = string
  default = "15"
}

variable "windows-agents-mem-request" {
  type    = string
  default = "60Gi"
}

variable "buildkite-api-token-readonly" {
  type = string
}

variable "buildkite-agent-token" {
  type = string
}

variable "conduit-api-token" {
  type = string
}

variable "git-id-rsa" {
  type = string
}

variable "id-rsa-pub" {
  type = string
}

variable "git-known-hosts" {
  type = string
}
