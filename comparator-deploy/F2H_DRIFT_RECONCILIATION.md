# F2h deployed drift reconciliation

Deployed pre-change snapshots are authoritative for existing runtime behavior. The reviewed, merged release will become the authority for the changed profile and diagnostics. Snapshots preserve the actual deployment rather than silently replacing it with older local scripts.

| Deployed file | Repo before import | Generation-tree copy | Authority |
| --- | --- | --- | --- |
| `/opt/viridis/comparator-live/server/scripts/comparator.sh` | ABSENT | DIFF | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/scripts/compile.sh` | ABSENT | MATCH | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/scripts/collectThms.sh` | ABSENT | MATCH | Deployed pre-change bytes |
| `/usr/local/bin/viridis-comparator-verify` | MATCH | DIFF | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/src/exec.ts` | ABSENT | MATCH | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/src/worker.ts` | ABSENT | MATCH | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/src/app.ts` | ABSENT | ABSENT | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/src/env.ts` | ABSENT | ABSENT | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/server/src/workqueue.ts` | ABSENT | ABSENT | Deployed pre-change bytes |
| `/opt/viridis/comparator-live/shared/shared.ts` | ABSENT | MATCH | Deployed pre-change bytes |
| `/etc/systemd/system/viridis-comparator.service` | ABSENT | MATCH | Deployed pre-change bytes |
| `/etc/systemd/system.control/viridis-comparator.service.d/50-CPUQuota.conf` | ABSENT | ABSENT | Deployed pre-change bytes |
| `/etc/systemd/system.control/viridis-comparator.service.d/50-MemoryMax.conf` | ABSENT | ABSENT | Deployed pre-change bytes |

The repository lacked all five service/launcher artifacts except the current delivery wrapper; this commit imports exact deployed public source into `remote_service/` and preserves snapshots. The generation-tree comparator launcher uses CPU `ulimit -t 60`; the deployed script uses `600` and includes setup permission changes, as shown by the full diff. Compile and collection launchers match. The generation-tree wrapper is older than the deployed F2f wrapper.

The service fragment matches its generation-tree copy (MemoryMax=3G, CPUQuota=180%), but deployed systemd control drop-ins override those values to MemoryMax=7864320000 and CPUQuota=400%. Both drop-ins are independently snapshotted and hashed. No service limits or launcher bytes are changed by F2h; only the proposed comparator wall profile changes for reserved foundational runs.

No keys or environment dumps are included. Inline service settings are public runtime paths/values; no credential files were read. Per-file hashes, permissions and the full differences are in the snapshot manifest and `.diff` files.
