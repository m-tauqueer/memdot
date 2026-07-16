# Memdot hosted infrastructure (India-first)

Version: scaffold — not live GCP

## Topology

- **Mumbai (`asia-south1`)** — application, content, inference, and operator-facing services.
- **Delhi (`asia-south2`)** — encrypted disaster-recovery backups only; no content-bearing workloads.

## Layout

```text
infra/hosted/
  README.md
  terraform/
    main.tf
    variables.tf
    modules/
      mumbai-app/
        main.tf
      delhi-dr/
        main.tf
  k8s/
    mumbai/
      namespace.yaml
      core-deployment.yaml
    delhi/
      backup-cronjob.yaml
```

## Operator notes

- Terraform modules are stubs documenting intended regional separation.
- Delhi module provisions backup storage and replication jobs only.
- Mumbai module provisions GKE namespace, Core/MCP deployments, and ingress skeleton.
- Live GCP credentials, state buckets, and KMS keys remain owner-controlled.

## Self-host parity

Self-host Compose remains the authoritative local profile. Hosted skeletons must not
change self-host behavior or require Tex/paid model APIs.
