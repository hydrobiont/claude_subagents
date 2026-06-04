# aws-devops — domain knowledge

Personal cheat sheet for the aws-devops agent. Terse, durable facts only.

<!-- entries below; newest on top -->

### Kopia S3 lifecycle: transition only the `p` prefix
Kopia stores large immutable data packs under the `p` blob prefix and small, frequently-rewritten metadata/index under `q`/`n`/`x` plus singletons `kopia.repository`/`kopia.blobcfg`/`kopia.maintenance`. S3 lifecycle rules for Glacier should filter on prefix `p` only; leaving metadata in Standard keeps maintenance/listing fast and dodges Glacier's 128 KB min-billable + min-storage-duration penalties on tiny objects.

### Object Lock + Kopia maintenance coexistence
With S3 Object Lock enabled, Kopia (0.23) does not hard-delete blobs during maintenance; it relies on retention + S3 lifecycle (expire noncurrent versions) for reclamation. The backup IAM principal must NOT have `s3:BypassGovernanceRetention`. Kopia sets retention natively via `kopia repository create s3 --retention-mode=GOVERNANCE --retention-period=<dur>`; the period should exceed the full-maintenance interval.
