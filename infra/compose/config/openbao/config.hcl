# OpenBao local file-storage configuration for the production-like base topology.
# Initialization/unseal is performed by openbao_bootstrap.sh into ignored paths.
# Do not use -dev mode in the base Compose graph.

storage "file" {
  path = "/openbao/file"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://openbao:8200"
ui = false

default_lease_ttl = "168h"
max_lease_ttl     = "720h"
