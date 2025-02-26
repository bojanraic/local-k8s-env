# Local Kubernetes Development Environment

A robust and flexible local Kubernetes development environment setup using KinD, with support for local container registry, DNS resolution, HTTPS certificates, and various development services.

## Features

- 🚀 Quick and easy local Kubernetes cluster setup using KinD
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
- 💻 Shell completions for all applicable tools

## Demo

![Demo Screencast](demo.gif)
## Prerequisites

The following are required:

-  macOS or 🐧 Linux (recent Ubuntu or Ubuntu-based distribution)
- 🐳 Docker (or docker-compatible runtime, e.g. OrbStack)
- 🧰 [mise](https://mise.jdx.dev/) for tool version management
- (optional) nss (for macOS) or libnss3-tools (for Linux) 
> [!IMPORTANT] nss is needed to automatically trust mkcert-generated certificates in Firefox

NOTES: 
- Podman is not supported yet as it is not a first-class citizen with KinD 
- Ubuntu 22.04, 24.04 and Pop!_OS 24.04 are tested and known to work, although distros with a standard systemd/systemd-resolved setup might work as well

All other dependencies are automatically managed by mise:
- 🐍 Python
- 📦 kubectl
- 📦 kind
- 📦 Helm
- 📦 Helmfile
- 📦 mkcert
- 📦 go-task
- 📦 yq
- 📦 kustomize
- 📦 kubeconform

## Quick Start

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install mise and initialize the environment:
```bash
# Install mise (if not already installed)
curl https://mise.run | sh
```

3. Activate mise 

> Follow the instructions [here](https://mise.jdx.dev/getting-started/installation/) to activate mise for your shell.

4. Re-open your terminal, navigate to the project root directory and verify the mise environment:
```bash 
mise trust
mise doctor
```

5. Install tools, create Python virtual environment and install dependencies:
```bash
mise install
mise run deps
```

6. Copy the example configuration:
```bash
cp k8s-env.yaml.example k8s-env.yaml
```

7. Configure your environment by editing `k8s-env.yaml`:
```yaml
environment:
  name: my-local-env
  local-ip: 192.168.1.123 # Change to your IP; can't be 127.0.0.1
  local-domain: me.local # Change if desired
```

8. Create the environment:
```bash
task create-env
```

9. Verify the setup:
```bash
task validate-env
```

## Shell Completions

The environment automatically sets up shell completions for mise-managed tools. This includes:

- task
- kubectl (including the 'k' alias)
- helm
- helmfile
- kind
- kustomize
- yq

To re-run completions setup for your shell manually: 
```bash
task help:setup-completions
```
or for a specific shell: 
```bash
task help:setup-completions:bash
task help:setup-completions:zsh
task help:setup-completions:fish
```

After restarting your shell, you should be able to use tab to complete commands using the tools mentioned above.

## Help and Information

The environment includes comprehensive help tasks. To see available information:

```bash
# List all help tasks
task help

# Show environment information
task help:environment

# Sample output:
🌍 Environment Configuration:
├── Name: my-local-env
├── Base Directory: /home/user/.local/k8s-env
├── Local Domain: me.local
├── Local IP: 192.168.1.123
├── Container Runtime: docker
├── Nodes:
│   ├── Control Plane: 1
│   ├── Workers: 1
│   └── Control Plane Scheduling: true
└── Service Presets Enabled: true

# Show all information
task help:all
```

## Project Structure

```
.
├── k8s-env.yaml              # Main configuration file
├── .mise.toml                # Tool version management
├── templates/                # Jinja2 templates for configuration
│   ├── containerd/           # Containerd configuration templates
│   ├── dnsmasq/              # DNSmasq configuration templates
│   ├── helmfile/             # Helmfile configuration templates
│   ├── kind/                 # KinD cluster configuration templates
│   └── service_presets.yaml  # Service presets and default values
├── .local/                   # Runtime data (git-ignored)
├── .taskfiles/               # Task definitions
├── generate_configs.py       # Python script for generating configuration files
└── Taskfile.yaml             # Main task definitions
```

### Templates Directory

The `templates/` directory contains all Jinja2 templates used to generate configurations:

- `containerd/`: Container runtime configurations
- `coredns/`: Kubernetes DNS service configurations
- `dnsmasq/`: Local DNS resolver configurations
- `helmfile/`: Helm release definitions
- `kind/`: Kubernetes cluster configurations
- `tests/`: Validation test configurations
- `presets.yaml`: Default service configurations and ports

## Configuration

The environment is configured through `k8s-env.yaml`. Key configuration options:

- `name`: Environment name (used for cluster and resource naming)
- `base-dir`: Directory for storing cluster data and configs
- `local-ip`: Your local machine's IP address
- `local-domain`: Domain for local services
- `nodes`: Control plane and worker node count
- `services`: Enable/disable and configure development services

To view the full list of configuration options, review the comments in the `k8s-env.yaml` file.

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
├── k8s-env.yaml                       # Main configuration file
├── .local/                            # Default directory for cluster data and configs
│   └── <env-name>/                    # Environment-specific directory (e.g. my-local-env)
│       ├── certs/                     # TLS certificates and keys
│       │   ├── rootCA.pem             # Root CA certificate
│       │   ├── <domain>.pem           # Domain certificate
│       │   ├── <domain>-key.pem       # Domain private key
│       │   └── <domain>-combined.pem  # Combined cert and key
│       ├── config/                    # Generated configuration files
│       │   ├── cluster.yaml           # KinD cluster configuration
│       │   ├── containerd.yaml        # Container runtime config
│       │   ├── dnsmasq.conf           # Local DNS configuration
│       │   └── helmfile.yaml          # Helm releases definition
│       ├── logs/                      # Kubernetes node logs
│       │   ├── control-0/             # Control plane logs
│       │   └── worker-0/              # Worker node logs
│       ├── storage/                   # Persistent volume data
│       │   ├── control-0/             # Control plane storage
│       │   └── worker-0/              # Worker node storage
│       ├── kubeconfig                 # Cluster access configuration
│       └── service-secrets.txt        # Generated service credentials
├── .taskfiles/                        # Task definitions and variables
│   ├── help/                          # Help tasks
│   ├── kubernetes/                    # Kubernetes-related tasks
│   ├── validate/                      # Validation tasks
│   └── vars/                          # Common variables used in tasks
├── tests/                             # Test files for validation
└── Taskfile.yaml                      # Main task definitions
```

The `.local` directory (configurable via `base-dir` in `k8s-env.yaml`) is created when you first run `task create-env` and contains all runtime data and configurations. Key points about the `.local` directory:

- **Location**: By default, it's created in the project root but can be configured via `base-dir` in `k8s-env.yaml`
- **Persistence**: Contains all persistent data, including certificates, logs, and storage
- **Environment Isolation**: Each environment gets its own subdirectory (e.g., `.local/my-local-env/`)
- **Backup**: You may want to back up the `certs` and `config` directories
- **Cleanup**: The entire `.local` directory can be safely deleted to start fresh

> Note: The `.local` directory is git-ignored by default. If you need to preserve any configurations, consider committing them to a separate repository, being mindful of any sensitive data, such as passwords/keys/secrets/etc.

## Service Management

Services are defined in two places:

1. `k8s-env.yaml`: Service enablement and specific configurations
2. `templates/service_presets.yaml`: Default service configurations and ports

### Service Presets

The `service_presets.yaml` file defines default configurations for supported services:

```yaml
service_ports:
  mysql: 3306
  postgres: 5432
  # ... other service ports

service_values_presets:
  mysql:
    fullNameOverride: mysql
    nameOverride: mysql
    # ... other default values
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
> NOTE: DNS resolution is handled by the local DNSMasq container, which is automatically started when you create or start the environment. It will resolve any hostname with the `<local-domain>` to the local IP address. This means that you can use any hostname to access the services via corresponding ports. The advice is to use the service name as the hostname, for example `postgres.me.local` or `rabbitmq.me.local` instead of `localhost`. One additional advantage is that TLS certificates are automatically generated and trusted for the `<local-domain>` and can be used for the services.

1. **Service Credentials**:
   - Passwords for password-protected services are automatically generated and stored in `<local-dir>/<env-name>/service-secrets.txt`
   - View them with:
     ```bash
     cat <local-dir>/<env-name>/service-secrets.txt
     ```

### Using the Local Container Registry

The environment includes a local container registry accessible at `<registry-name>.<local-domain>`. The value is configurable via `registry.name` in `k8s-env.yaml`. 
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

> Note: Replace `me.local` with your configured `local-domain` value from `k8s-env.yaml`

## Troubleshooting

1. **DNS Resolution Issues**
   - Verify local DNS container is running: `docker ps | grep <env-name>-dns`
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