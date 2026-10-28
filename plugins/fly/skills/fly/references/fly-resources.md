# Fly resources

Resolve the app and organization within the current Fly grant. Read summaries
first; full configurations, process arguments, metadata, and historical versions
can contain sensitive values and require additional scopes.

## Apps and discovery

Use `list_apps` and `get_app` for identity, status, organization, and counts.
`delete_app` permanently deletes an app and can disrupt or delete its resources;
inspect the target and require explicit deletion intent. There is no app-create
tool. Launch blockers can be explained with `get_launch_requirements`.

## Machines

| Task | Tools | Behavior that affects the choice |
| --- | --- | --- |
| Inspect identity and lifecycle | `list_machines`, `get_machine` | Summaries exclude configuration and secrets. |
| Diagnose events or wait for state | `list_machine_events`, `wait_for_machine_state` | Check the observed state before reporting success. |
| Read configuration or history | `get_machine_configuration`, `list_machine_versions` | Requires sensitive-read consent; avoid exposing environment or file values. |
| Read processes | `list_machine_processes` | Arguments can contain secrets; requires sensitive-read consent. |
| Create | `create_machine` | Billable; uses explicit configuration and starts unless `skip_launch` is set. Inspect existing Machines before retrying a lost response. |
| Change lifecycle | `start_machine`, `stop_machine`, `restart_machine`, `suspend_machine`, `signal_machine` | Can interrupt running work. Stopping still honors existing `auto_destroy` configuration. |
| Change routing | `cordon_machine`, `uncordon_machine` | Cordoning removes proxy routing but does not stop application work. |
| Run a command | `exec_machine_command` | Takes an explicit argv array, without an implicit shell. Execution and output can access sensitive application data. |
| Manage leases | `get_machine_lease`, `create_machine_lease`, `release_machine_lease` | Requires management scope. Treat lease nonces as private concurrency credentials; release the exact acquired lease. |
| Inspect or change memory | `get_machine_memory`, `set_machine_memory_limit`, `reclaim_machine_memory` | Even the memory query requires the Machine write scope. |
| Read metadata | `get_machine_metadata`, `get_machine_metadata_key` | Arbitrary values require sensitive-read consent. |
| Change metadata | `update_machine_metadata`, `set_machine_metadata_key`, `delete_machine_metadata_key` | Bulk update requires `machine_version`; stale versions fail. Null or empty values remove keys. Re-read on a version conflict and reconsider the intended change. |
| Delete | `delete_machine` | Permanently removes the Machine and ephemeral root filesystem. Attached volumes are separate. Never enable `force` implicitly. |

Creation, interruption, and deletion must serve the user's requested operation.
An instruction to investigate an outage is not permission to restart or delete
resources. Do not include lease nonces or sensitive configuration in progress
messages, public files, or final summaries.

## Volumes

- Inspect with `list_volumes`, `get_volume`, and `list_volume_snapshots`.
  Deleted-state volumes are hidden unless `include_destroyed` is requested;
  summary listings omit byte and block statistics, rather than reporting zero.
- `create_volume` creates billable storage. It cannot restore or fork a source
  volume; those operations require separate source-resource authorization.
- Use `update_volume` for supported settings and `extend_volume` to increase
  capacity. Extension increases charges and cannot be undone by shrinking.
- `create_volume_snapshot` schedules a snapshot of an attached, ready volume.
  A successful scheduling response may have no snapshot ID; inspect
  `list_volume_snapshots` for the ID and completion status before claiming a
  completed backup.
- `delete_volume` permanently destroys persistent data and requires detaching
  the volume from Machines first. Do not expand Machine cleanup into volume
  deletion without explicit authorization for those volumes.

## Secrets

`list_app_secrets` and `get_app_secret` return names, digests, and timestamps,
never secret values. Do not attempt to recover values through Machine exec or
configuration reads when asked to inspect secret metadata.

Use `set_app_secret` for one value, `update_app_secrets` for a batch, and
`delete_app_secret` for deletion. Null batch values delete secrets and need
delete consent as well as write consent. The upstream bulk API also requires
create, write, and delete action bits for sets; report missing access instead
of silently expanding it. Use an authorized secure source for values; do not
ask the user to paste credentials into chat or echo values in summaries.

Deleting an absent secret can still succeed and advance the secrets version.
Verify resulting metadata, without treating a changed version as proof that a
previously existing secret was removed.

## Network and certificates

`list_app_ips`, `list_app_certificates`, and `get_app_certificate` inspect
existing assignments and certificates. They cannot allocate addresses or
create, renew, or delete certificates. Explain that limitation when relevant.

## Managed Postgres

Resolve the organization, cluster, and (where applicable) database within the
current grant. Managed Postgres uses `fly:mpg:read` and `fly:mpg:write`; access
to an app or Sprites does not by itself authorize its organization's databases.
Discover the live schemas before supplying arguments.

| Task | Tools | Behavior that affects the choice |
| --- | --- | --- |
| Inspect clusters and plans | `list_postgres_clusters`, `get_postgres_cluster`, `get_postgres_plans` | Plans are listed cheapest first. Cluster endpoints become available once ready. |
| Provision a cluster | `create_postgres_cluster` | Billable and asynchronous. Poll `get_postgres_cluster` until ready before creating databases or enabling extensions. |
| Fork a cluster | `fork_postgres_cluster` | Requires a ready source; creates a new cluster without changing the source. Inherits source settings and its plan unless another plan is supplied. Wait for the fork to become ready. |
| Inspect or create backups | `list_postgres_backups`, `create_postgres_backup` | Creation is asynchronous and rejected while a backup is already in progress. Check the backup listing before reporting completion or retrying. |
| Inspect or create databases | `list_postgres_databases`, `create_postgres_database` | Select a ready cluster and verify the resulting database list after creation. |
| Inspect or enable extensions | `list_postgres_extensions`, `enable_postgres_extension` | The listing distinguishes available and installed extensions. PostGIS extensions need a PostGIS-enabled cluster. |
| Inspect users | `list_postgres_users` | Lists users; does not change users or passwords or return passwords. |
| Diagnose query activity | `list_postgres_active_queries`, `list_postgres_slow_queries` | Returns full SQL text, which may contain private data. Summarize findings without exposing query literals. Times are in seconds. |

Slow-query results are the top 20 queries by cumulative total execution time,
excluding the `postgres` database. They use the latest available metrics within
the lookback range; the counters are cumulative, not changes during that range.

Creation and forks must serve the user's requested operation; an inspection
request does not authorize provisioning. If a mutation's response is lost,
inspect the cluster, backup, database, or extension state before retrying.
These tools do not delete Postgres resources, change users or passwords, return
passwords, or provide an arbitrary SQL execution tool.
