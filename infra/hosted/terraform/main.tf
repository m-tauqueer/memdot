terraform {
  required_version = ">= 1.6.0"
}

module "mumbai_app" {
  source = "./modules/mumbai-app"
  region = var.mumbai_region
}

module "delhi_dr" {
  source = "./modules/delhi-dr"
  region = var.delhi_region
}
