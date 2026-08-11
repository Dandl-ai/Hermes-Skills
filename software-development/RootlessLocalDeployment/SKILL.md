---
name: RootlessLocalDeployment
description: "Host local repositories without root: Docker rootless, nvm."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Hosting, Docker, Rootless, Node, Monorepo, Dev-Environment]
    related_skills: [OffensiveAuditOrchestration, PhpMySqlWebAppPenetrationTesting]
---

# Rootless Local Deployment of Applications / Monorepos

A verified method for running heavy applications locally (Node/Ember/NestJS monorepos, apps with PostgreSQL/Redis/S3) **without a root account or sudo**. Derived from the full hosting of AcmePlatform (acme-platform, v5.476.0, 6 apps + API + 4 containers) on a non-root Fedora machine.

## When to Use
- The user asks to "host", "run", or "install" a repo/applicative that requires Docker plus services (DB, cache)
- `docker` is installed, but the daemon is inactive and there is no sudo
- A monorepo requires a specific Node version that differs from the installed one

## Validated Workflow (in order)

### 1. Enable Docker in rootless mode (without sudo)
```bash
# Verify: inactive daemon + dockerd-rootless-setuptool.sh present
systemctl is-active docker        # → inactive
which dockerd-rootless-setuptool.sh

# Install rootless mode (user-space, no sudo required)
export XDG_RUNTIME_DIR=/run/user/$(id -u)
mkdir -p "$XDG_RUNTIME_DIR" && chmod 700 "$XDG_RUNTIME_DIR"
dockerd-rootless-setuptool.sh install

# Start + persist the environment
systemctl --user start docker.service
export DOCKER_HOST=unix:///run/user/1000/docker.sock   # (1000 = your uid)
export PATH=/usr/sbin:$PATH
docker info   # → Server Version: 29.x, Storage Driver: overlayfs
```
**Persistence**: add `XDG_RUNTIME_DIR`, `DOCKER_HOST`, `PATH` to `~/.bashrc` — each new terminal command must re-export them (the persistent shell PATH does not retain them).

### 2. Install the `docker compose` plugin manually
`docker compose` is not a default subcommand. The binary is downloaded and installed as a CLI plugin:
```bash
mkdir -p ~/.docker/cli-plugins
curl -sL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose
docker compose version   # → Docker Compose version vX
```
Note: `docker-compose` (hyphenated) does not exist standalone — use `docker compose`.

### 3. Install the required Node version (via nvm)
Monorepos pin their Node version in `.nvmrc` (e.g. AcmePlatform: `24.18.0`). `npm install` fails with `EBADENGINE` if the version differs:
```bash
# Install nvm (user-space) then the required version
curl -sL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"
nvm install $(cat .nvmrc) && nvm use $(cat .nvmrc)
node --version   # → verify the correct version
```
**Pitfall**: each terminal command must re-source nvm (`export NVM_DIR=...; . "$NVM_DIR/nvm.sh"; nvm use ...`) — the persistent shell does not retain the nvm PATH.

### 4. Install dependencies and configure
```bash
npm install --no-audit --no-fund        # at the monorepo root
npm run configure                       # official script: creates the DB/cache containers + seeds
```
The `dev:*` scripts (e.g. `dev:api`) are **declared at the root** of the monorepo (`"dev:api": "cd api && npm run dev"`) — run them from the root, not from `api/` (otherwise "Missing script").

### 5. Launch the services in the background
```bash
# API: Docker containers + Node server
npm run dev:api   # (background=true in Hermes)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/   # → 204 = UP

# Front apps (Ember): long build, RAM-hungry
NODE_OPTIONS="--max-old-space-size=3072" npm run dev:mon-acme-platform
curl -s -o /dev/null -w "%{http_code}" http://localhost:4200/   # → 200
```

## Pitfalls (all experienced)

- **OOM-kill of the Ember build**: the default build gets killed (exit -9) with little free RAM. Fix: `NODE_OPTIONS="--max-old-space-size=3072"` (and check `free -h` first). The first build takes 2-5 min; the port only appears at the end.
- **`dev:api` not found in `api/package.json`**: the scripts are at the monorepo root — always run `npm run dev:api` from the root.
- **Partial seeds**: a seed can fail cleanly with a managed warning (`UnseedableError` → "seeding is only minimal/partial") without breaking the environment. Do not re-run everything for that — just verify the API starts.
- **RAM**: the full monorepo (API + front build + 4 containers) ≈ 6-8 GB. Close the apps (`npm run dev:*` killed) AND `docker stop` the containers to free memory.
- **`docker info` OK but `docker compose` missing** → see step 2 (CLI plugin), not an installation error.
- **Rootless containers**: ports exposed on localhost (e.g. 5432 postgres, 6379 redis) — check with `ss -tlnp` if a service "does not respond".
- **Verify each step with a curl** (`204` API / `200` app), never by the absence of an error in the log.

## Verification
- `docker ps` lists the containers UP
- The API responds (204 on `/`), the front app responds (200, `<title>` present)
- The Node version = the one in `.nvmrc` (`node --version`)
- RAM: `free -h` retains margin before a front build

## Out of Scope
- Non-Linux platforms (macOS/Windows): the rootless workflow and OSTree-agnostic commands here are validated on Linux only; macOS rootless mode differs and Docker Desktop is the usual path on Windows/macOS.
- Root/sudo-based installs: if you can run `sudo` or install daemons system-wide, the standard `dockerd` + `systemctl enable docker` path is simpler than this rootless procedure.
- GPU/CUDA acceleration: rootless Docker GPU passthrough (`--gpus all`, nvidia-container-toolkit) is not covered here.
- Production server deployment: this covers local dev hosting on a workstation, not hardened, multi-user, or internet-facing deployments.
- Docker Desktop: use the official Docker Desktop installers where supported, instead of this rootless Linux method.