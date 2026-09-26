# aws-devops — domain knowledge

Personal cheat sheet for the aws-devops agent. Terse, durable facts only.

<!-- entries below; newest on top -->

### Kopia on S3: Glacier tier choice, economics, and required IAM
Prefer **Glacier Instant Retrieval** for backups that must restore without a thaw step; Deep Archive/Flexible need an explicit un-archive (hours) before Kopia can read blobs — only with user sign-off. Glacier has a 128 KB minimum-billable-object-size and per-tier minimum storage duration (GIR 90 days), so configure Kopia for large pack blobs and never transition tiny metadata objects. Required IAM for Kopia: `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on bucket+`/*`; add `s3:GetBucketObjectLockConfiguration`, `s3:GetObjectRetention`, `s3:PutObjectRetention`, `s3:GetBucketVersioning`, `s3:ListBucketVersions` when object-lock retention is used. Object Lock requires versioning and must be enabled at (or very close to) bucket creation.

### Kopia S3 lifecycle: transition only the `p` prefix
Kopia stores large immutable data packs under the `p` blob prefix and small, frequently-rewritten metadata/index under `q`/`n`/`x` plus singletons `kopia.repository`/`kopia.blobcfg`/`kopia.maintenance`. S3 lifecycle rules for Glacier should filter on prefix `p` only; leaving metadata in Standard keeps maintenance/listing fast and dodges Glacier's 128 KB min-billable + min-storage-duration penalties on tiny objects.

### Object Lock + Kopia maintenance coexistence
With S3 Object Lock enabled, Kopia (0.23) does not hard-delete blobs during maintenance; it relies on retention + S3 lifecycle (expire noncurrent versions) for reclamation. The backup IAM principal must NOT have `s3:BypassGovernanceRetention`. Kopia sets retention natively via `kopia repository create s3 --retention-mode=GOVERNANCE --retention-period=<dur>`; the period should exceed the full-maintenance interval.
