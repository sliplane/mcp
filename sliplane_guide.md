# Sliplane Platform Mental Model

Sliplane is a container hosting platform. Understanding these concepts will help you work effectively with the API.

## Core Architecture

### Hierarchy
- **Organization**: Top-level account, identified by Organization ID
- **Projects**: Logical grouping for services (e.g., "Production", "Staging")
- **Services**: Individual running containers
- **Servers**: VMs that run your services

### 1 Service = 1 Container
Each service runs exactly one container instance. There is no horizontal scaling or replicas. To handle more load, you scale the server vertically (upgrade instance type) or run multiple services behind your own load balancing logic.

## Servers

Servers are VMs in specific locations:
- `fsn` / `nbg` - Germany
- `ash` / `hil` - USA
- `sin` - Singapore
- `hel` - Finland

Instance types range from Base (2 vCPU, 2GB RAM, €9/mo) to Dedicated XXX-Large (48 vCPU, 192GB RAM).

**Important behaviors:**
- Servers can only scale UP, not down
- Rescaling causes brief downtime for all services on that server
- All services on a server share CPU and memory (no hard isolation)
- No imposed limit on services per server - depends on available resources, use at your own risk

## Services

### Deployment Sources
1. **Git repository**: Sliplane builds your Dockerfile on dedicated build servers with extensive caching. Set `SLIPLANE_SKIP_CACHE=true` env var to bypass cache (usually indicates a Dockerfile issue).
2. **Container image**: Pull from Docker Hub or GHCR (with optional registry credentials)

You cannot change deployment type after creation.

### Port Detection
- Sliplane auto-detects which port your container exposes for HTTP services
- Container MUST bind to all interfaces (`0.0.0.0` or `::`) - NOT localhost
- Set the `PORT` environment variable to explicitly specify the port (always respected)

### Deployments
- **Auto-deploy**: For git-based services, pushing to the configured branch automatically triggers a new deployment
- **Zero-downtime deployments** for services WITHOUT volumes
- Services WITH volumes have brief downtime during deploy
- If a new deploy fails health checks, Sliplane rolls back to the previous version
- If a container crashes, it restarts up to 5 times before giving up

## Networking

### Public Services (HTTP)
- Automatic HTTPS with managed certificates
- Assigned a managed subdomain: `*.sliplane.app`
- Sits behind a load balancer
- Can add custom domains (verified via CNAME or A record, up to 24h verification)

### Public Services (TCP/UDP)
- Get dedicated ports on the server's public IP
- No automatic TLS - handle encryption yourself if needed

### Private Services
- Only accessible within the same server via internal domain (e.g., `my-service.internal`)
- Services on DIFFERENT servers cannot reach private services
- Public services CAN communicate across servers (via their public URLs)

### Cross-Server Communication
- Private services: same-server only
- Public services: can reach each other across servers via public URLs

## Volumes

- Volumes are server-bound (tied to a specific server)
- Multiple services can share the same volume (consider data consistency)
- Services with volumes cannot do zero-downtime deployments
- Volumes persist across deployments and service restarts

## Health Checks

- HTTP path-based health checks (e.g., `/health`)
- Failed health checks trigger rollback to previous version
- Crash loops (5 restarts) cause the service to stop

## Environment Variables

- Can be marked as `secret` (masked in API responses)
- Updating env vars is a FULL REPLACEMENT, not a merge
- To add a variable, include all existing variables plus the new one
- For secrets, you can leave value empty to preserve the existing secret value

## Logs & Metrics

- Logs retained for 7 days
- CPU and memory metrics available per service and per server
