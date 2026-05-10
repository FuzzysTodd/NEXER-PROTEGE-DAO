# Nexus Redundancy Implementation Checklist

## Scope
This checklist implements:
1. GitHub settings and repository resilience controls
2. Azure identity, storage, and service redundancy controls
3. Validation and metadata controls for DAO source manifest governance

## 1. GitHub Controls
- Enable branch protection on `main`.
- Require pull request review and status checks.
- Require signed commits and prevent force pushes.
- Keep linear history and block direct pushes for protected branches.
- Add immutable release tags and signed release process.
- Add backup workflow that publishes repository bundles to Azure Blob.
- Add manifest-validation workflow for `dao-data-source-manifest.json`.

## 2. Azure Controls
- Create Microsoft Entra app registrations and managed identities for services.
- Store all credentials in Azure Key Vault.
- Use Azure Blob Storage with retention/immutability for repository and manifest backups.
- Deploy signal and REST services in active-active mode (minimum two instances).
- Add health probes and failover routing for service endpoints.
- Enable Application Insights + Log Analytics for runtime telemetry.

## 3. Validation + Metadata Controls
- All source entries must include:
  - `type`
  - `locator`
  - `trust`
  - `scope`
  - `notes`
  - `metadata.validationStatus`
  - `metadata.addedBy`
  - `metadata.addedAt`
  - optional `metadata.provenanceHash` (SHA-256)
- Secrets are never allowed in source locator or notes.
- Canonical repo remains: `FuzzysTodd/The-Nexus-Protocol-Token-DOA`.
- Owner authority remains: `@FuzzysTodd`.

## Rollout Order
1. Apply GitHub protection and workflows.
2. Configure Entra + Key Vault + Blob retention.
3. Deploy active-active signal and REST runtime.
4. Enforce manifest validation in CI and in dapp UI.
5. Expand source trust policy into execution gating.
