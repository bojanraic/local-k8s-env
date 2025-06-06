# Local Kubernetes Development Environment

A robust and flexible local Kubernetes development environment setup using KinD, with support for local container registry, DNS resolution, HTTPS certificates, and various development services.

## Features

- 🚀 Quick and easy local Kubernetes cluster setup using KinD
- 📦 Built-in local container registry with TLS support
- 🔒 Automatic TLS certificate generation for local domains
- 🌐 Local wildcard DNS resolution for `<local-domain>` (configurable) domain
- 📊 **Comprehensive Cluster Status**: Detailed view of cluster resources with `task status`
  - Node status with role-based filtering
  - Service status grouped by namespace
  - Ingress and registry information
  - User namespaces overview
  - DNS and service health checks
- 🎯 **Advanced Node Scheduling**: Flexible node labeling and workload placement
  - Custom node labels for control-plane and worker nodes
  - Infrastructure components on control-plane scheduling
  - Application services on workers-only scheduling
- 🔧 Support for common development services:
  - PostgreSQL
  - MySQL
  - MongoDB
  - RabbitMQ
  - Valkey (Redis-compatible)
- 🛠️ Helm-based service deployment from public repositories (Bitnami, etc.)
- 📋 **OCI Helm Chart Validation**: Local registry testing with OCI artifact storage
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

## Checking Cluster Status

Use the `status` command to get a comprehensive overview of your local Kubernetes environment:

```bash
task status
```

This will display:

- **Cluster Status**: Overall health of the Kubernetes cluster
- **DNS Status**: Status of the local DNS service
- **Node Status**: List of all nodes with their roles and status
- **Namespace Status**: Overview of all namespaces
- **Service Status**: Status of system services (cert-manager, ingress-nginx, registry)
- **User Namespaces**: Detailed view of user-created namespaces with pods and services
- **Enabled Services**: Status of enabled services from your configuration

Example output:
```
📊 Node Status:
├── dev-me-control-plane      Ready      Roles: control-plane      Age: 71m
├── dev-me-worker             Ready      Roles: worker             Age: 71m

📊 Registry Status:
├── Pods:
│   ├── registry-0     Running/1/1     Restarts: 0     Age: 68m
├── Services:
│   ├── registry       Type: ClusterIP Cluster-IP: 10.11.175.143       Ports: 5000/TCP
└── Ingress:
    ├── Name: registry
    ├── Hosts: cr.dev.me
    └── Address: 192.168.1.100
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
task setup-completions
```
or for a specific shell:
```bash
task utils:setup-completions-bash
task utils:setup-completions-zsh
task utils:setup-completions-fish
```

After restarting your shell, you should be able to use tab to complete commands using the tools mentioned above.

If you wish to remove these shell completions, run 
```bash
task utils:remove-completions
```

## Help and Information

### Task Help

List all available tasks:
```bash
task --list
```

Get detailed help for a specific task:
```bash
task help <task-name>
```

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

The environment manages development services (databases, message queues, etc.) through Helm deployments from public repositories.

Services are defined in two places:

1. `k8s-env.yaml`: Service enablement and specific configurations
2. `templates/service_presets.yaml`: Default service configurations and ports

> **Note**: These services are deployed from public Helm repositories (like Bitnami) using Helmfile, not from the local OCI registry. The local OCI registry is used for validation and custom application development.

### Service Presets

The `service_presets.yaml` file defines default configurations for supported services:

```yaml
service_ports:
  mysql: 3306
  postgres: 5432
  valkey: 6379
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

## Node Scheduling and Workload Placement

The environment supports advanced node scheduling configurations to separate infrastructure and application workloads.

### Node Labels

Configure custom labels for nodes to enable targeted scheduling:

```yaml
nodes:
  servers: 3
  workers: 3
  labels:
    control-plane: # Applied to ALL control-plane nodes
      tier: "infrastructure"
      environment: "production"
    worker: # Applied to ALL worker nodes
      tier: "application"
      environment: "production"
    individual: # Override specific nodes
      control-plane-0:
        zone: "us-west-1a"
        primary: "true"
      worker-0:
        zone: "us-west-1a"
        workload-type: "cpu-intensive"
```

### Scheduling Flags

#### `internal-components-on-control-plane`
Forces infrastructure components (cert-manager, nginx-ingress, registry) to run only on control-plane nodes:

```yaml
nodes:
  allow-scheduling-on-control-plane: true
  internal-components-on-control-plane: true
```

**Use cases:**
- Reserve worker nodes for application workloads
- Ensure infrastructure stability on control-plane
- Single-node development environments

#### `run-services-on-workers-only`
Forces application services (databases, message queues) to run only on worker nodes:

```yaml
run-services-on-workers-only: true  # Only when workers > 0
```

**Use cases:**
- Clean separation of infrastructure and applications
- Dedicated worker nodes for data services
- Multi-node production-like environments

### Scheduling Patterns

#### Single-Node Development
```yaml
nodes:
  servers: 1
  workers: 0
  allow-scheduling-on-control-plane: true
  internal-components-on-control-plane: true
# Everything runs on control-plane
```

#### Multi-Node with Separation
```yaml
nodes:
  servers: 3
  workers: 3
  allow-scheduling-on-control-plane: true
  internal-components-on-control-plane: true
run-services-on-workers-only: true

# Result:
# - Control-plane: Kubernetes system + infrastructure components
# - Workers: Application services and user workloads
```

### Using Node Labels in Your Applications

When deploying your own applications, use the configured labels:

```yaml
# Example deployment targeting worker nodes
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      nodeSelector:
        tier: "application"
      # or
      nodeSelector:
        node-role.kubernetes.io/worker: ""
```

## OCI Registry and Helm Chart Validation

The environment includes comprehensive validation workflows for testing OCI registry functionality with Helm charts stored as OCI artifacts.

> **Note**: This is separate from the regular service deployment (MySQL, PostgreSQL, etc.), which uses standard Helm repositories like Bitnami. The OCI validation specifically tests the local registry's ability to store and deploy Helm charts as OCI artifacts.

### Validation Workflow

The validation system tests the complete OCI container and Helm chart lifecycle:

1. **Image Build & Push**: Builds a test application and pushes to local registry
2. **Chart Packaging**: Packages a demo Helm chart as OCI artifact and pushes to local registry
3. **OCI Deployment**: Deploys the chart from the local OCI registry (not from public repos)
4. **Validation**: Tests connectivity and functionality of the OCI-deployed application

### Running Validation

```bash
# Complete validation workflow
task validate:local-registry

# Individual validation steps
task validate:build-push-image      # Build and push test image
task validate:package-helm-chart    # Package chart as OCI artifact
task validate:deploy-test-app       # Deploy from OCI registry
task validate:app                   # Test deployed application
```

### Demo Application

The validation includes a demo application that:
- Displays environment information (pod name, image tag, chart version)
- Demonstrates OCI registry integration
- Tests Helm chart templating and deployment
- Validates TLS certificate generation
- Respects node scheduling constraints

### OCI Registry Features

- **Helm Chart Storage**: Store and version Helm charts as OCI artifacts
- **Multi-Architecture Support**: Compatible with different architectures
- **TLS Security**: Secure registry with automatic certificate management
- **Local Development**: No external dependencies for chart development

### Two Types of Helm Deployments

The environment supports two distinct Helm deployment patterns:

#### 1. **Service Deployment** (MySQL, PostgreSQL, etc.)
Standard Helm deployment from public repositories:
```bash
# These are deployed automatically via Helmfile from public repos
# Example: PostgreSQL from Bitnami repository
helm install postgres bitnami/postgresql --version 16.7.9
```

#### 2. **OCI Chart Deployment** (Validation & Custom Apps)
Helm charts stored and deployed as OCI artifacts from local registry:
```bash
# 1. Develop your Helm chart
helm create my-app

# 2. Test locally
helm template my-app ./my-app

# 3. Package and push to local OCI registry
helm package ./my-app
helm push my-app-0.1.0.tgz oci://cr.dev.me/helm-charts

# 4. Deploy from local OCI registry
helm install my-app oci://cr.dev.me/helm-charts/my-app --version 0.1.0
```

**Key Differences:**
- **Services**: Use public Helm repositories (Bitnami, etc.) via Helmfile
- **OCI Validation**: Uses local registry to store/deploy charts as OCI artifacts
- **Use Cases**: Services for infrastructure, OCI for custom application development

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

4. **Node Scheduling Issues**
   - Check node labels: `kubectl get nodes --show-labels`
   - Verify pod placement: `kubectl get pods -o wide`
   - Review scheduling constraints: `kubectl describe pod <pod-name>`

5. **OCI Registry Issues**
   - Test registry connectivity: `docker pull cr.dev.me/test:latest`
   - Verify Helm OCI support: `helm registry login cr.dev.me`
   - Check chart availability: `helm search repo oci://cr.dev.me/helm-charts`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request


## Complete K8s-Env Configuration Schema Documentation

### Overview

The k8s-env configuration format is a YAML-based schema used to define a local Kubernetes development environment. This section provides a detailed description of all available configuration options, their types, and usage examples.

### Schema Structure

```yaml
environment:
  # General settings
  name: string                    # Name of the environment
  base-dir: string                # Base directory for storage
  expand-base-dir-vars: boolean   # Whether to expand variables in base-dir
  
  # Provider configuration
  provider:
    name: string                 # Provider name (currently only "kind" supported)
    runtime: string              # Container runtime (docker or podman)
  
  # Kubernetes configuration
  kubernetes:
    api-port: integer            # API server port
    image: string                # Node image
    tag: string                  # Node image tag
  
  # Node configuration
  nodes:
    servers: integer             # Number of control-plane nodes
    workers: integer             # Number of worker nodes
    allow-scheduling-on-control-plane: boolean # Allow scheduling on control-plane
  
  # Network configuration
  local-ip: string              # Local IP for DNS resolution
  local-domain: string          # Local domain for DNS resolution
  local-lb-ports: array         # Load balancer ports
  
  # Registry configuration
  registry:
    name: string                # Registry name
    storage:
      size: string              # Storage size for registry
  
  # Internal components
  internal-components: array    # List of internal components with versions
  
  # Service configuration
  use-service-presets: boolean  # Whether to use service presets
  services: array               # List of services to deploy
```

### Detailed Field Descriptions

#### General Settings

##### `name`
- **Type**: string
- **Description**: Name of the environment. This drives the naming of Kubernetes clusters, nodes, and host containers.
- **Example**: `dev-me`

##### `base-dir`
- **Type**: string
- **Description**: Directory where Kubernetes logs, storage, and various config files are stored.
- **Example**: `${PWD}/.local`
- **Notes**: Can use environment variables like `${PWD}` which will be expanded if `expand-base-dir-vars` is true.

##### `expand-base-dir-vars`
- **Type**: boolean
- **Description**: Whether to expand variables in the `base-dir` path.
- **Default**: true
- **Example**: true
- **Notes**: Set to false if using absolute paths.

#### Provider Configuration

##### `provider.name`
- **Type**: string
- **Description**: Provider for Kubernetes clusters.
- **Allowed Values**: Currently only "kind" is supported.
- **Example**: `kind`

##### `provider.runtime`
- **Type**: string
- **Description**: Container runtime to use.
- **Allowed Values**: "docker" or "podman"
- **Example**: `docker`
- **Notes**: Podman is not fully supported with KinD yet.

#### Kubernetes Configuration

##### `kubernetes.api-port`
- **Type**: integer
- **Description**: Port for the Kubernetes API server, exposed to the host machine as local-ip:api-port.
- **Default**: 6443
- **Example**: 6443

##### `kubernetes.image`
- **Type**: string
- **Description**: Docker image for the KinD nodes.
- **Default**: kindest/node
- **Example**: `kindest/node`

##### `kubernetes.tag`
- **Type**: string
- **Description**: Tag for the KinD node image.
- **Example**: `v1.32.3`

#### Node Configuration

##### `nodes.servers`
- **Type**: integer
- **Description**: Number of control-plane servers/masters.
- **Default**: 1
- **Example**: 1

##### `nodes.workers`
- **Type**: integer
- **Description**: Number of worker nodes.
- **Default**: 1
- **Example**: 1

##### `nodes.allow-scheduling-on-control-plane`
- **Type**: boolean
- **Description**: Whether to allow scheduling on control plane nodes even when workers exist.
- **Default**: true
- **Example**: true

##### `nodes.internal-components-on-control-plane`
- **Type**: boolean
- **Description**: Whether to force internal components (cert-manager, nginx-ingress, registry) to run only on control-plane nodes.
- **Default**: false
- **Example**: true
- **Notes**: Requires `allow-scheduling-on-control-plane: true` to be effective. Useful for reserving worker nodes for application workloads.

##### `nodes.labels`
- **Type**: object
- **Description**: Custom labels to apply to nodes for scheduling purposes.
- **Example**:
  ```yaml
  labels:
    control-plane: # Labels for ALL control-plane nodes
      tier: "infrastructure"
      environment: "production"
    worker: # Labels for ALL worker nodes
      tier: "application"
      environment: "production"
    individual: # Override specific nodes
      control-plane-0:
        zone: "us-west-1a"
        primary: "true"
      worker-0:
        zone: "us-west-1a"
        workload-type: "cpu-intensive"
  ```
- **Notes**: 
  - `control-plane` and `worker` labels are applied to all nodes of that type
  - `individual` labels override global labels for specific nodes
  - Node names follow the pattern: `control-plane-0`, `control-plane-1`, `worker-0`, `worker-1`, etc.

#### Network Configuration

##### `local-ip`
- **Type**: string
- **Description**: Local IP, mapping to the host IP to use for DNS resolution and wildcard certificates.
- **Example**: `192.168.0.10`

##### `local-domain`
- **Type**: string
- **Description**: Domain name to use for custom DNS resolution and wildcard certificates.
- **Example**: `dev.me`

##### `local-lb-ports`
- **Type**: array of integers
- **Description**: List of ports to expose on the load balancer side, mapping to the host machine.
- **Example**: 
  ```yaml
  local-lb-ports:
    - 80  # HTTP port for nginx ingress controller
    - 443 # HTTPS port for nginx ingress controller
  ```

#### Registry Configuration

##### `registry.name`
- **Type**: string
- **Description**: Name of the registry, used in the final URL for the registry (i.e., `<registry.name>.<local-domain>`).
- **Example**: `cr`

##### `registry.storage.size`
- **Type**: string
- **Description**: Size of the PersistentVolumeClaim for registry storage.
- **Example**: `15Gi`

#### Internal Components

##### `internal-components`
- **Type**: array of objects
- **Description**: List of internal components (Helm charts or Docker containers used for internal purposes) with their versions.
- **Example**:
  ```yaml
  internal-components:
    - cert-manager: "v1.17.1"
    - app-template: "3.7.3"
    - nginx-ingress: "4.12.1"
    - registry: "3"
    - dnsmasq: "2.91"
  ```
- **Notes**: Each component is specified as a key-value pair where the key is the component name and the value is its version.

#### Service Configuration

##### `use-service-presets`
- **Type**: boolean
- **Description**: Whether to use preset values for enabled services.
- **Default**: true
- **Example**: true
- **Notes**: Leave true unless you have a good reason to override the defaults.

##### `run-services-on-workers-only`
- **Type**: boolean
- **Description**: Whether to force application services to run only on worker nodes (when workers > 0).
- **Default**: false
- **Example**: true
- **Notes**: 
  - Only takes effect when `workers > 0`, otherwise services can run anywhere
  - Useful for separating infrastructure (control-plane) from application workloads (workers)
  - Applies to all enabled services in the `services` array

##### `services`
- **Type**: array of objects
- **Description**: List of additional services to deploy within the cluster.
- **Example**:
  ```yaml
  services:
    - name: mysql
      enabled: false
      namespace: common-services
      ports:
        - 3306
      storage:
        size: 10Gi
      config:
        chart: bitnami/mysql
        version: 12.3.2
        values:
          auth:
            createDatabase: false
  ```

###### Service Object Properties

###### `name`
- **Type**: string
- **Description**: Name of the service.
- **Example**: `mysql`

###### `enabled`
- **Type**: boolean
- **Description**: Whether to install this component and expose the port(s).
- **Default**: false
- **Example**: false

###### `namespace`
- **Type**: string
- **Description**: Kubernetes namespace for the service.
- **Default**: Same as service name
- **Example**: `common-services`

###### `ports`
- **Type**: array of integers
- **Description**: Ports to expose on the host machine.
- **Example**: 
  ```yaml
  ports:
    - 3306
  ```

###### `storage.size`
- **Type**: string
- **Description**: Size of the PersistentVolumeClaim for service storage.
- **Example**: `10Gi`

###### `config.chart`
- **Type**: string
- **Description**: Helm chart to use for the service.
- **Example**: `bitnami/mysql`

###### `config.version`
- **Type**: string
- **Description**: Version of the Helm chart.
- **Example**: `12.3.2`

###### `config.values`
- **Type**: object
- **Description**: Additional values to use for the Helm chart.
- **Example**:
  ```yaml
  values:
    auth:
      createDatabase: false
  ```

### Example Configuration

#### Basic Single-Node Development
```yaml
environment:
  name: dev-me
  base-dir: ${PWD}/.local
  expand-base-dir-vars: true

  provider:
    name: kind
    runtime: docker

  kubernetes:
    api-port: 6443
    image: kindest/node
    tag: v1.33.1

  nodes:
    servers: 1
    workers: 0
    allow-scheduling-on-control-plane: true
    internal-components-on-control-plane: true

  local-ip: 192.168.0.10
  local-domain: dev.me
  local-lb-ports:
    - 80
    - 443

  registry:
    name: cr
    storage:
      size: 15Gi

  internal-components:
    - cert-manager: "v1.17.2"
    - app-template: "4.0.1"
    - nginx-ingress: "4.12.3"
    - registry: "3"
    - dnsmasq: "2.91"

  use-service-presets: true
  services:
    - name: postgres
      enabled: true
      namespace: common-services
      ports:
        - 5432
      storage:
        size: 5Gi
      config:
        chart: bitnami/postgresql
        version: 16.7.9
```

#### Multi-Node with Workload Separation
```yaml
environment:
  name: prod-cluster
  base-dir: ${PWD}/.local
  expand-base-dir-vars: true

  provider:
    name: kind
    runtime: docker

  kubernetes:
    api-port: 6443
    image: kindest/node
    tag: v1.33.1

  nodes:
    servers: 3
    workers: 3
    allow-scheduling-on-control-plane: true
    internal-components-on-control-plane: true  # Infrastructure on control-plane
    labels:
      control-plane:
        tier: "infrastructure"
        environment: "production"
      worker:
        tier: "application"
        environment: "production"
      individual:
        control-plane-0:
          zone: "us-west-1a"
          primary: "true"
        worker-0:
          zone: "us-west-1a"
          workload-type: "database"

  local-ip: 192.168.1.100
  local-domain: prod.local
  local-lb-ports:
    - 80
    - 443

  registry:
    name: registry
    storage:
      size: 50Gi

  internal-components:
    - cert-manager: "v1.17.2"
    - app-template: "4.0.1"
    - nginx-ingress: "4.12.3"
    - registry: "3"
    - dnsmasq: "2.91"

  use-service-presets: true
  run-services-on-workers-only: true  # Services on workers only

  services:
    - name: postgres
      enabled: true
      namespace: common-services
      ports:
        - 5432
      storage:
        size: 20Gi
      config:
        chart: bitnami/postgresql
        version: 16.7.9
    - name: valkey
      enabled: true
      namespace: common-services
      ports:
        - 6379
      storage:
        size: 10Gi
      config:
        chart: bitnami/valkey
        version: 3.0.9
```

### Notes on Usage

1. The configuration is processed by the `generate_configs.py` script, which creates various Kubernetes configuration files based on the provided settings.

2. The script supports both macOS and Linux environments, with different DNS resolver configurations for each.

3. Service presets are loaded from a separate YAML file (`service_presets.yaml`) and can be overridden by setting `use-service-presets` to false.

4. The configuration generates several output files:
   - `cluster.yaml`: KinD cluster configuration
   - `containerd.yaml`: Containerd configuration
   - `dnsmasq.conf`: DNS configuration
   - `helmfile.yaml`: Helmfile configuration
   - `cluster-issuer.yaml`: Cert-manager cluster issuer configuration

5. The script requires sudo privileges to configure DNS resolvers on the host system.

6. Environment variables in paths (like `${PWD}`) are expanded if `expand-base-dir-vars` is set to true.


## License

[MIT](LICENSE)