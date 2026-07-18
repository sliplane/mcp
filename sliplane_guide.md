# Sliplane Platform Mental Model

Sliplane is a cloud platform for running containerized applications, managed PostgreSQL databases, and S3-compatible object storage. Understanding these concepts will help you work effectively with the API and MCP server.

## Core Architecture

### Hierarchy
- **Team / Organization**: Top-level account and billing boundary. API requests may use the Organization ID / `X-Organization-ID` header when the user belongs to multiple teams.
- **Projects**: Logical grouping for services, such as "Production", "Staging", or one project per customer/app.
- **Services**: Individual running containers with Sliplane-managed configuration, networking, deploys, logs, and metrics.
- **Servers**: VMs that run services. A server can host many services as long as its CPU, memory, disk, and bandwidth can handle them.
- **Databases**: Managed PostgreSQL instances with separate compute, storage, TLS, backups, metrics, query stats, and access control.
- **Object Storage**: Team-level S3-compatible buckets for uploads, backups, generated files, and app assets.

### 1 Service = 1 Container
Each service runs exactly one container instance. There is no built-in horizontal scaling or replica count per service. To handle more load, scale the server vertically, move services across servers, or run multiple services behind your own load-balancing/application logic.

## Servers

Servers are VMs in specific locations:
- Germany: Falkenstein / Nuremberg (`fsn` / `nbg`)
- USA: Ashburn / Hillsboro (`ash` / `hil`)
- Singapore (`sin`)
- Finland / Helsinki (`hel`)

Server pricing depends on billing period, CPU type, location, server size, and selected disk size.

**Important behaviors:**
- Sliplane charges per server, not per service. You can run as many services on a server as its resources allow.
- Server resource scaling is zero-downtime for supported scale-up operations; services keep running while resources grow.
- Disk can be scaled independently from CPU/RAM, also without downtime.
- Disk growth is effectively one-way: you cannot downgrade to a configuration with less disk than the server currently has.
- Scaling the server type may also increase disk; use independent disk scaling when you only need storage.
- All services on a server share CPU, memory, disk, and included bandwidth. There is no hard per-service resource isolation.
- Rebooting a server causes downtime for all services on it; deleting a server deletes its services and volumes.

## Services

### Deployment Sources
1. **Git repository**: Sliplane builds from your repository on dedicated build servers with caching.
2. **Container image**: Sliplane can deploy OCI-compatible images from public or private registries, including Docker Hub, GHCR, AWS ECR, Google Artifact Registry, GitLab Container Registry, and similar registries.
3. **Presets**: The dashboard includes common preconfigured services/templates that can be deployed and then adjusted.

Git builds can use:
- Framework/language auto-detection
- `railpack.json` for Railpack build configuration
- A Dockerfile

You cannot change core service identity after creation: deploy source type, public/private exposure, protocol, and server are fixed. Use Deploy Copy or create a new service when those need to change.

For Dockerfile-based builds:
- Dockerfile path points to the Dockerfile inside the repo.
- Docker context controls which directory is sent as the build context.
- Set `SLIPLANE_SKIP_CACHE=true` only when you need to bypass build cache while debugging suspicious cache behavior.

### Port Detection
- Sliplane auto-detects which port your container exposes for HTTP services.
- The container must bind to all interfaces (`0.0.0.0` or `::`), not only localhost.
- Set the `PORT` environment variable to explicitly specify the port; Sliplane respects it.

### Deployments
- **Auto-deploy**: For git-based services, pushing to the configured branch can automatically trigger a deployment.
- **Deploy rules**: Include/ignore path rules can restrict auto-deploys, which is especially useful in monorepos.
- **Deploy hook**: A service can expose a secret hook URL that triggers a deploy. Treat it like a credential.
- **Zero-downtime deploys**: Sliplane starts the new version and redirects traffic only after it verifies the service is running.
- Services with attached volumes may have brief downtime during deploys because the persistent volume must move between container versions.
- Failed deployments do not replace a healthy previous version; Sliplane rolls back/keeps traffic on the last working version.
- If a running container crashes repeatedly, Sliplane restarts it a limited number of times before marking it down.

## Networking

### Public Services (HTTP)
- Automatic HTTPS with managed certificates.
- Assigned a managed subdomain: `*.sliplane.app`.
- Routed through Sliplane's load balancer / proxy layer.
- Custom domains can be added and verified via DNS records.
- Wildcard domains are supported, so an app can handle `*.example.com` style subdomains.

### Public Services (TCP/UDP)
- Get dedicated ports on the server's public IP.
- No automatic TLS at the TCP/UDP layer; handle encryption in the application/protocol if needed.
- Access control can be configured for TCP/UDP services when you need IP restrictions.

### Private Services
- Only accessible within the same server via internal hostnames such as `my-service.internal`.
- Services on different servers cannot reach private services directly.
- Public services can communicate across servers by using their public URLs.

### Cross-Server Communication
- Private service networking is same-server only.
- Cross-server traffic should use public service URLs, external databases/storage, or explicit application-level routing.

## Volumes

- Volumes are server-bound and tied to a specific server.
- Multiple services can share the same volume, but data consistency is your responsibility.
- Services with volumes may not get zero-downtime deployments.
- Volumes persist across deployments and service restarts.
- Deleting a volume is destructive and requires detaching services first.
- Volume backups are enabled by default, run daily, and are retained for 7 days.
- Manual backups are available, but limited to one backup per volume every 30 minutes.
- Restoring a backup creates a new volume; you must attach the restored volume to the service yourself.
- For busy databases, volume backups may not be enough for consistency. Prefer database-aware backup/restore procedures and test restores regularly.

## Object Storage

Object Storage is team-level, S3-compatible storage managed through the dashboard and Sliplane API.

Use it for:
- User uploads
- Generated files
- App assets
- Backups and exports
- Data that should not live on a single server-bound volume

Key behaviors:
- Buckets are top-level containers for objects.
- Bucket names are globally unique.
- A bucket has a region, endpoint, and status.
- Access keys are scoped to exactly one bucket.
- Access keys can read/write/list their own bucket and can list buckets/see whether other buckets exist in the same team.
- Access keys cannot read, write, or delete objects in other buckets.
- Secret access keys are returned only once at creation time. If lost, delete the key and create a new one.
- Versioning can preserve prior object versions when objects are overwritten or deleted.
- Object locking prevents overwrite/delete for a retention period and also enables versioning.
- Deleting a bucket schedules deletion with a 24-hour grace period, then removes the bucket and keys.

Pricing model:
- Object Storage is billed from average stored data across all buckets in the team, not per bucket.
- Current price is 5 EUR/month per started 250 GB block, excluding VAT.
- Examples: 1 GB, 10 GB, or 250 GB all cost 5 EUR/month; 251 GB costs 10 EUR/month.
- There are no Sliplane ingress, egress, API request, or per-bucket fees for Object Storage.

## Managed PostgreSQL Databases

Sliplane Databases are first-class managed PostgreSQL instances, not ordinary container services with volumes. Use them for production databases when you want database-aware operations instead of self-hosting PostgreSQL as a service.

Key capabilities:
- Provisioning is managed through the dashboard, this MCP server, and the API. Creation requires a name, region, compute size, storage size, and billing period.
- Databases are usually ready in about 30 seconds, then expose connection details in the dashboard.
- All connections support TLS. Prefer the dashboard's Connection URI with `sslmode=verify-full` so clients validate the certificate and hostname.
- JavaScript clients such as `pg`, `postgres.js`, and Drizzle/Postgres.js may reject `sslrootcert=system`; remove that query parameter for those clients because system roots are their default behavior.
- Access control is IP allowlist based. If the allowlist is empty, all database access is blocked. Add single IPs or CIDR ranges for IPv4 and IPv6.
- Credentials can be rotated, and databases can be paused/resumed through the dashboard, MCP server, and API.

Operational model:
- Backups use Point-in-Time Recovery (PITR) with a 7-day retention window on all tiers.
- Restoring a backup creates a new database at the current configuration; it does not overwrite the existing database.
- The restored database is billed separately from the moment it exists, at the same rate as its configuration.
- Compute and storage upgrades are zero-downtime. Storage can grow up to 1 TB and cannot be reduced.
- Shared CPU instances are suited for development and smaller apps; dedicated CPU instances are intended for production and performance-sensitive workloads.
- Shared instances allow up to 100 connections; dedicated instances allow up to 300 connections.
- Dedicated instances are available up to 48 vCPU and 196 GB RAM, with larger requirements handled by support.

Observability:
- Database logs are PostgreSQL logs. They can be filtered by time range or keyword and streamed live.
- Metrics include CPU, memory, disk, and active connections.
- Query Stats are based on PostgreSQL `pg_stat_statements` and show slow queries and top queries by total execution time.
- Use sustained CPU pressure, low memory headroom, disk growth, or connection pressure as signals to upgrade compute or storage.

Pricing model:
- Databases are billed separately from servers and Object Storage.
- Price is compute plus storage, excluding VAT unless stated otherwise.
- Compute and storage are billed hourly from database creation until deletion.
- Hourly, monthly, and yearly billing periods are available; monthly and yearly commitments are discounted.
- Each database includes 10 GB of storage at no extra cost. Additional storage is billed per GB per month.
- Prices vary by region; Germany and Finland pricing is documented, while the dashboard shows exact prices for each selected region and size.

MCP/API model:
- Database management is available through this MCP server and over the REST API, including create/delete, pause/resume, credential rotation, PITR restore, logs, and metrics.
- The API documentation groups these endpoints under the `postgres` tag.

Deploying databases:
- Sliplane offers two paths: **managed PostgreSQL** via `createPostgres`, or a **container preset** via `sliplane_preset_guide` and `createService`.
- For PostgreSQL or a generic "database" request, prefer managed PostgreSQL. Ask whether the user wants a self-hosted container instead. Use the `postgres` preset only when they choose that path.
- For other engines (MySQL, MongoDB, Redis, etc.), use the matching preset.
- Recommended `createPostgres` defaults: Germany (`ger`), Base shared CPU (`base`), monthly billing (`monthly`). Let the user choose region, compute (CPU), storage, db name, db user, and billing.

## Health Checks

- HTTP path-based health checks can verify a service before traffic moves to it.
- Failed health checks prevent a bad deployment from replacing the previous working version.
- Crash loops cause the service to be marked down after repeated restart attempts.

## Environment Variables

- Environment variables can be marked as `secret`, which masks them in API responses.
- Updating env vars is a full replacement, not a merge.
- To add one variable, include all existing variables plus the new one.
- For secrets, an empty value can preserve the existing secret value.

## Logs & Metrics

- Service logs are retained for 7 days, up to the documented log-line limit.
- Runtime and build logs can be searched/filtered in the dashboard.
- CPU, memory, and disk metrics are available at server level.
- Service-level resource views are available, but the sum of services will not exactly equal total server usage because system processes also consume resources.
- Managed PostgreSQL has its own database-level logs, CPU/memory/disk/connection metrics, and query statistics separate from service/server metrics.

## Billing

- Billing is managed per team. Each team has its own subscription, billing information, and optional prepaid credit balance.
- Servers are billed per server, not per service/container/resource. A server can run many services for the same server price as long as it has enough resources.
- Server billing can be hourly, monthly, or yearly. Monthly pricing is discounted compared with hourly, and yearly pricing is discounted further.
- Server price depends on billing period, CPU type, location, server size, and disk size.
- An idle server costs the same as a busy server for its selected plan. Paused/stopped services still incur server costs because the server still exists.
- To stop future server billing for hourly servers, delete the server. Monthly and yearly servers follow their selected billing period.
- Prices are listed excluding VAT unless stated otherwise; VAT may be added depending on billing address.
- Prepaid credits are account-wide, are not tied to a specific server, expire after one year, and are non-refundable.
- Egress is included with servers and subject to Sliplane's Fair Use Policy.
- Object Storage has its own pricing model based on average stored data across team buckets. It does not add ingress, egress, API request, or per-bucket fees.
- Managed PostgreSQL has its own compute-plus-storage pricing and does not share the per-server pricing model.
