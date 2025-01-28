# Local Kubernetes Development Environment

A robust and flexible local Kubernetes development environment setup using k3d, with support for local container registry, DNS resolution, and various development services.

## Features

- 🚀 Quick and easy local Kubernetes cluster setup using k3d
- 📦 Built-in local container registry with TLS support
- 🔒 Automatic TLS certificate generation for local domains
- 🌐 Local wildcard DNS resolution for `<local-domain>` (configurable) domain
- 🔧 Support for common development services:
  - PostgreSQL
  - MySQL
  - MongoDB
  - RabbitMQ
  - Dragonfly (Redis-compatible)
- 🛠️ Helm-based service deployment
- ⚙️ Configurable via single YAML file
- 🔄 Automated dependency management with Renovate

## Prerequisites

The following are required:

- macOS
- Docker (or docker-compatible runtime, e.g. OrbStack)
- k3d (https://k3d.io/)
- task (https://taskfile.dev/)

NOTES: 

- Podman is not supported yet, but is planned to be added in the future (There are bugs in the container runtime that are making Podman incompatible with this setup)
- kind is not supported yet, but is planned to be added in the future
- Linux support is planned to be added in the future (there are some intricacies around DNS resolution and systemd configuration that need to be ironed out)

These tools are also required and will be automatically installed if missing:
- kubectl
- k3d
- Helm
- Helmfile
- mkcert
- Python 3.12+
- go-task
- yq

## Quick Start

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Configure your environment by editing `.k8s-env.yaml`:
```yaml
environment:
name: my-local-env
local-ip: 127.0.0.1 # Change to your IP
local-domain: me.local # Change if desired
```
3. Create the environment:
```bash
task create-env
```
4. Verify the setup:
```bash
task validate-env
```

## Configuration

The environment is configured through `.k8s-env.yaml`. Key configuration options:

- `name`: Environment name (used for cluster and resource naming)
- `base-dir`: Directory for storing cluster data and configs
- `local-ip`: Your local machine's IP address
- `local-domain`: Domain for local services
- `nodes`: Control plane and worker node count
- `services`: Enable/disable and configure development services

To view the full list of configuration options, review the comments in the `.k8s-env.yaml` file.

## Available Tasks

Use `task --list` to see all available tasks. Main tasks include:

- `task create-env`: Create the complete environment
- `task destroy-env`: Tear down the environment
- `task recreate-env`: Rebuild the environment from scratch
- `task start-env`: Start a stopped environment
- `task stop-env`: Stop the environment
- `task validate-env`: Validate the environment setup
  

## Directory Structure

```
.
├── .k8s-env.yaml           # Main configuration file
├── .local/                 # Default directory for cluster data and configs
│   └── <env-name>/         # Environment-specific directory (e.g. my-local-env)
│       ├── certs/          # TLS certificates and keys
│       │   ├── rootCA.pem             # Root CA certificate
│       │   ├── <domain>.pem           # Domain certificate
│       │   ├── <domain>-key.pem       # Domain private key
│       │   └── <domain>-combined.pem  # Combined cert and key
│       ├── config/        # Generated configuration files
│       │   ├── cluster.yaml           # k3d cluster configuration
│       │   ├── containerd.yaml        # Container runtime config
│       │   ├── coredns-custom.yaml    # CoreDNS customization
│       │   ├── dnsmasq.conf           # Local DNS configuration
│       │   └── helmfile.yaml          # Helm releases definition
│       ├── logs/         # Kubernetes node logs
│       │   ├── server-0/              # Control plane logs
│       │   └── agent-*/               # Worker node logs
│       ├── storage/      # Persistent volume data
│       │   ├── server-0/              # Control plane storage
│       │   └── agent-*/               # Worker node storage
│       ├── kubeconfig    # Cluster access configuration
│       └── service-secrets.txt  # Generated service credentials
├── .scripts/               # Setup and configuration scripts
├── .taskfiles/             # Task definitions and variables
│   ├── help/               # Help tasks
│   ├── kubernetes/         # Kubernetes-related tasks
│   ├── validate/           # Validation tasks
│   └── vars/               # Common variables
├── tests/                  # Test files for validation
└── Taskfile.yaml           # Main task definitions
```

The `.local` directory (configurable via `base-dir` in `.k8s-env.yaml`) is created when you first run `task create-env` and contains all runtime data and configurations. Key points about the `.local` directory:

- **Location**: By default, it's created in the project root but can be configured via `base-dir` in `.k8s-env.yaml`
- **Persistence**: Contains all persistent data, including certificates, logs, and storage
- **Environment Isolation**: Each environment gets its own subdirectory (e.g., `.local/my-local-env/`)
- **Backup**: You may want to back up the `certs` and `config` directories
- **Cleanup**: The entire `.local` directory can be safely deleted to start fresh

> Note: The `.local` directory is git-ignored by default. If you need to preserve any configurations, consider committing them to a separate repository, being mindful of any sensitive data, such as passwords/keys/secrets/etc.

## Service Management

Services are defined in `.k8s-env.yaml` under the `services` section. Each service can be:

- Enabled/disabled via `enabled: true/false`
- Configured with storage size
- Exposed on specific ports

Example service configuration:
```yaml
services:
  - name: postgres
    enabled: true
    password-protected: true # whether or not the associated helm chart involves password protection for the service
    ports: 
      - 5432
    storage:
      size: 5Gi
```

## Using Local Services

### Accessing Services

Once the environment is running, services are accessible through:

1. **Direct Port Access**:
   ```bash
   # Example for PostgreSQL
   psql -h localhost -p 5432 -U postgres
   ```

2. **Domain Names**:
   ```bash
   # Example for PostgreSQL
   psql -h postgres.me.local -U postgres
   ```
> NOTE: DNS resolution is handled by the local DNSMasq container, which is automatically started when you create or start the environment. It will resolve any hostname with the `<local-domain>` to the local IP address. This means that you can use any hostname to access the services via corresponding ports. The advice is to use the service name as the hostname, for example `postgres.me.local` or `rabbitmq.me.local` instead of `localhost`. One additional advantage is that TLS certificates are automatically generated and trustedfor the `<local-domain>` and can be used for the services.

1. **Service Credentials**:
   - Passwords for password-protected services are automatically generated and stored in `<local-dir>/<env-name>/service-secrets.txt`
   - View them with:
     ```bash
     cat <local-dir>/<env-name>/service-secrets.txt
     ```

### Using the Local Container Registry

The environment includes a local container registry accessible at `<registry-name>.<local-domain>`. The value is configurable via `registry.name` in `.k8s-env.yaml`. 
To use it:

1. **Push Images**:
   ```bash
   # Tag your image, for example:
   docker tag myapp:latest cr.me.local/myapp:latest
   
   # Push the image to your local registry, for example:
   docker push cr.me.local/myapp:latest
   ```

2. **Use in Kubernetes**:
   
   Example deployment YAML:
   ```yaml
   # Example deployment
   apiVersion: apps/v1
   kind: Deployment
   spec:
     template:
       spec:
         containers:
         - name: myapp
           image: cr.me.local/myapp:latest
   ```

> Note: Replace `me.local` with your configured `local-domain` value from `.k8s-env.yaml`

## Troubleshooting

1. **DNS Resolution Issues**
   - Verify local DNS container is running: `docker ps | grep dnsmasq`
   - Check DNS configuration: `cat /etc/resolver/<your-domain>`

2. **Certificate Issues**
   - Regenerate certificates: `task setup-certificates`
   - Verify cert location: `ls <local-dir>/<your-domain>/certs/`

3. **Service Access Issues**
   - Validate TCP connectivity: `task validate:tcp-services`
   - Verify ingress: `kubectl get ingress -A`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

[MIT](LICENSE)