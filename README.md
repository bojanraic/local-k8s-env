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

## Demo

![Demo Screencast](demo.gif)

### Demo Output

The animated GIF above is sped up for brevity; the complete output of the screencast is below.

<details>

<summary>Full Demo screencast output</summary>

```
$> task create-env && task validate-env
[check-deps] 🔄 Checking dependencies...
[check-deps]   ⚙️ Installing mise tools...
[check-deps] mise all runtimes are installed
[check-deps]   ⚙️ Installing Python dependencies...
[check-deps] ✅ All dependencies installed
[generate-dirs] 🔄 Creating directories...
[generate-dirs]   📁 Creating control plane directories...
[generate-dirs]   📁 Creating worker node directories...
[generate-dirs] ✅ Directories created
[generate-configs] 🔄 Generating configuration files...
Password:
[generate-configs] 📝 Generating configurations from .k8s-env.yaml
[generate-configs] 📝 Generating helmfile.yaml
[generate-configs] ✅ Created /Users/devuser/demo/.local/my-cluster/config/helmfile.yaml
[generate-configs] 📝 Generating containerd.yaml
[generate-configs] ✅ Created /Users/devuser/demo/.local/my-cluster/config/containerd.yaml
[generate-configs] 📝 Generating dnsmasq.conf
[generate-configs] ✅ Created /Users/devuser/demo/.local/my-cluster/config/dnsmasq.conf
[generate-configs] 📝 Generating cluster.yaml
[generate-configs] ✅ Created /Users/devuser/demo/.local/my-cluster/config/cluster.yaml
[generate-configs] 🔧 Setting up DNS resolver for dev.me...
[generate-configs] ✅ Resolver file created at /etc/resolver/dev.me
[generate-configs] ✨ Configuration generation complete!
[generate-configs] ✅ Configuration files generated
[setup-certificates] 🔄 Setting up certificates...
[setup-certificates]   🔐 Generating certificates using mkcert...
[setup-certificates] The local CA is already installed in the system trust store! 👍
[setup-certificates] The local CA is already installed in the Firefox trust store! 👍
[setup-certificates] 
[setup-certificates] 
[setup-certificates] Created a new certificate valid for the following names 📜
[setup-certificates]  - "*.dev.me"
[setup-certificates]  - "dev.me"
[setup-certificates]  - "*.192.168.1.100"
[setup-certificates]  - "192.168.1.100"
[setup-certificates] 
[setup-certificates] Reminder: X.509 wildcards only go one level deep, so this won't match a.b.dev.me ℹ️
[setup-certificates] 
[setup-certificates] The certificate is at "/Users/devuser/demo/.local/my-cluster/certs/dev.me.pem" and the key at "/Users/devuser/demo/.local/my-cluster/certs/dev.me-key.pem" ✅
[setup-certificates] 
[setup-certificates] It will expire on 6 May 2027 🗓
[setup-certificates] 
[setup-certificates] Certificates set up successfully
[setup-certificates]   📁 Setting up containerd registry certificates...
[setup-certificates] ✅ Certificates setup complete
[start-dnsmasq] 🔄 Starting DNS service...
[start-dnsmasq]   🚀 Starting dnsmasq container...
[start-dnsmasq] 04c7b98bb5392e330c441423b146641f390740ab875941b56a63c09ce0f02b74
[start-dnsmasq] ✅ DNS service ready
[kubernetes:create-cluster] 🔄 Creating KinD cluster 'my-cluster'...
[kubernetes:create-cluster] Creating cluster "my-cluster" ...
[kubernetes:create-cluster]  • Ensuring node image (kindest/node:v1.32.1) 🖼  ...
[kubernetes:create-cluster]  ✓ Ensuring node image (kindest/node:v1.32.1) 🖼
[kubernetes:create-cluster]  • Preparing nodes 📦 📦   ...
[kubernetes:create-cluster]  ✓ Preparing nodes 📦 📦 
[kubernetes:create-cluster]  • Writing configuration 📜  ...
[kubernetes:create-cluster]  ✓ Writing configuration 📜
[kubernetes:create-cluster]  • Starting control-plane 🕹️  ...
[kubernetes:create-cluster]  ✓ Starting control-plane 🕹️
[kubernetes:create-cluster]  • Installing CNI 🔌  ...
[kubernetes:create-cluster]  ✓ Installing CNI 🔌
[kubernetes:create-cluster]  • Installing StorageClass 💾  ...
[kubernetes:create-cluster]  ✓ Installing StorageClass 💾
[kubernetes:create-cluster]  • Joining worker nodes 🚜  ...
[kubernetes:create-cluster]  ✓ Joining worker nodes 🚜
[kubernetes:create-cluster] Set kubectl context to "kind-my-cluster"
[kubernetes:create-cluster] You can now use your cluster with:
[kubernetes:create-cluster] 
[kubernetes:create-cluster] kubectl cluster-info --context kind-my-cluster
[kubernetes:create-cluster] 
[kubernetes:create-cluster] Have a question, bug, or feature request? Let us know! https://kind.sigs.k8s.io/#community 🙂
[kubernetes:create-cluster] ✅ KinD cluster 'my-cluster' created successfully
[kubernetes:wait-for-ready] ⏳ Waiting for KinD cluster...
[kubernetes:wait-for-ready] Switched to context "kind-my-cluster".
[kubernetes:wait-for-ready] node/my-cluster-control-plane condition met
[kubernetes:wait-for-ready] node/my-cluster-worker condition met
[kubernetes:wait-for-ready] ✅ Cluster is ready
[kubernetes:set-control-plane-scheduling] 🔄 Enabling scheduling on control plane nodes...
[kubernetes:set-control-plane-scheduling] node/my-cluster-control-plane untainted
[kubernetes:set-control-plane-scheduling] ✅ Scheduling enabled on control plane nodes
[kubernetes:label-worker-nodes] 🔄 Labeling worker nodes...
[kubernetes:label-worker-nodes] node/my-cluster-worker labeled
[kubernetes:label-worker-nodes] ✅ Labeled node my-cluster-worker as worker
[kubernetes:list-nodes] 🔄 Listing cluster nodes...
[kubernetes:list-nodes] NAME                      STATUS   ROLES           AGE   VERSION
[kubernetes:list-nodes] my-cluster-control-plane   Ready    control-plane   25s   v1.32.1
[kubernetes:list-nodes] my-cluster-worker          Ready    worker          15s   v1.32.1
[kubernetes:list-nodes] ✅ Node list complete
[kubernetes:create-wildcard-cert] 🔄 Creating wildcard TLS certificate...
[kubernetes:create-wildcard-cert] secret/wildcard-tls created
[kubernetes:create-wildcard-cert] ✅ Wildcard TLS certificate created
[kubernetes:deploy-services] 🔄 Deploying core services...
[kubernetes:deploy-services]   📦 Installing/upgrading Helm charts for enabled services...
[kubernetes:deploy-services] Adding repo ingress-nginx https://kubernetes.github.io/ingress-nginx
[kubernetes:deploy-services] "ingress-nginx" has been added to your repositories
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Adding repo bitnami https://charts.bitnami.com/bitnami
[kubernetes:deploy-services] "bitnami" has been added to your repositories
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Adding repo bjw-s https://bjw-s.github.io/helm-charts/
[kubernetes:deploy-services] "bjw-s" has been added to your repositories
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Pulling ghcr.io/dragonflydb/dragonfly/helm/dragonfly:v1.26.2
[kubernetes:deploy-services] Listing releases matching ^ingress-nginx$
[kubernetes:deploy-services] Listing releases matching ^postgres$
[kubernetes:deploy-services] Listing releases matching ^dragonfly$
[kubernetes:deploy-services] Listing releases matching ^registry$
[kubernetes:deploy-services] Upgrading release=ingress-nginx, chart=ingress-nginx/ingress-nginx, namespace=ingress-nginx
[kubernetes:deploy-services] Release "ingress-nginx" does not exist. Installing it now.
[kubernetes:deploy-services] NAME: ingress-nginx
[kubernetes:deploy-services] LAST DEPLOYED: Thu Feb  6 21:23:13 2025
[kubernetes:deploy-services] NAMESPACE: ingress-nginx
[kubernetes:deploy-services] STATUS: deployed
[kubernetes:deploy-services] REVISION: 1
[kubernetes:deploy-services] TEST SUITE: None
[kubernetes:deploy-services] NOTES:
[kubernetes:deploy-services] The ingress-nginx controller has been installed.
[kubernetes:deploy-services] Get the application URL by running these commands:
[kubernetes:deploy-services]   export HTTP_NODE_PORT=$(kubectl get service --namespace ingress-nginx ingress-nginx-controller --output jsonpath="{.spec.ports[0].nodePort}")
[kubernetes:deploy-services]   export HTTPS_NODE_PORT=$(kubectl get service --namespace ingress-nginx ingress-nginx-controller --output jsonpath="{.spec.ports[1].nodePort}")
[kubernetes:deploy-services]   export NODE_IP="$(kubectl get nodes --output jsonpath="{.items[0].status.addresses[1].address}")"
[kubernetes:deploy-services] 
[kubernetes:deploy-services]   echo "Visit http://${NODE_IP}:${HTTP_NODE_PORT} to access your application via HTTP."
[kubernetes:deploy-services]   echo "Visit https://${NODE_IP}:${HTTPS_NODE_PORT} to access your application via HTTPS."
[kubernetes:deploy-services] 
[kubernetes:deploy-services] An example Ingress that makes use of the controller:
[kubernetes:deploy-services]   apiVersion: networking.k8s.io/v1
[kubernetes:deploy-services]   kind: Ingress
[kubernetes:deploy-services]   metadata:
[kubernetes:deploy-services]     name: example
[kubernetes:deploy-services]     namespace: foo
[kubernetes:deploy-services]   spec:
[kubernetes:deploy-services]     ingressClassName: nginx
[kubernetes:deploy-services]     rules:
[kubernetes:deploy-services]       - host: www.example.com
[kubernetes:deploy-services]         http:
[kubernetes:deploy-services]           paths:
[kubernetes:deploy-services]             - pathType: Prefix
[kubernetes:deploy-services]               backend:
[kubernetes:deploy-services]                 service:
[kubernetes:deploy-services]                   name: exampleService
[kubernetes:deploy-services]                   port:
[kubernetes:deploy-services]                     number: 80
[kubernetes:deploy-services]               path: /
[kubernetes:deploy-services]     # This section is only required if TLS is to be enabled for the Ingress
[kubernetes:deploy-services]     tls:
[kubernetes:deploy-services]       - hosts:
[kubernetes:deploy-services]         - www.example.com
[kubernetes:deploy-services]         secretName: example-tls
[kubernetes:deploy-services] 
[kubernetes:deploy-services] If TLS is enabled for the Ingress, a Secret containing the certificate and key must also be provided:
[kubernetes:deploy-services] 
[kubernetes:deploy-services]   apiVersion: v1
[kubernetes:deploy-services]   kind: Secret
[kubernetes:deploy-services]   metadata:
[kubernetes:deploy-services]     name: example-tls
[kubernetes:deploy-services]     namespace: foo
[kubernetes:deploy-services]   data:
[kubernetes:deploy-services]     tls.crt: <base64 encoded cert>
[kubernetes:deploy-services]     tls.key: <base64 encoded key>
[kubernetes:deploy-services]   type: kubernetes.io/tls
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Listing releases matching ^ingress-nginx$
[kubernetes:deploy-services] ingress-nginx      ingress-nginx   1               2025-02-06 21:23:13.182031 +0100 CET    deployed        ingress-nginx-4.12.0    1.12.0     
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Upgrading release=registry, chart=bjw-s/app-template, namespace=registry
[kubernetes:deploy-services] Release "registry" does not exist. Installing it now.
[kubernetes:deploy-services] NAME: registry
[kubernetes:deploy-services] LAST DEPLOYED: Thu Feb  6 21:24:50 2025
[kubernetes:deploy-services] NAMESPACE: registry
[kubernetes:deploy-services] STATUS: deployed
[kubernetes:deploy-services] REVISION: 1
[kubernetes:deploy-services] TEST SUITE: None
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Listing releases matching ^registry$
[kubernetes:deploy-services] registry   registry        1               2025-02-06 21:24:50.511222 +0100 CET    deployed        app-template-3.6.1                 
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Upgrading release=postgres, chart=bitnami/postgresql, namespace=postgres
[kubernetes:deploy-services] Upgrading release=dragonfly, chart=/var/folders/zf/1qdbnv1x48z5fdwqjlklkj2c0000gn/T/helmfile2616077620/dragonfly/dragonfly/dragonfly/v1.26.2/dragonfly, namespace=dragonfly
[kubernetes:deploy-services] Release "dragonfly" does not exist. Installing it now.
[kubernetes:deploy-services] NAME: dragonfly
[kubernetes:deploy-services] LAST DEPLOYED: Thu Feb  6 21:25:07 2025
[kubernetes:deploy-services] NAMESPACE: dragonfly
[kubernetes:deploy-services] STATUS: deployed
[kubernetes:deploy-services] REVISION: 1
[kubernetes:deploy-services] TEST SUITE: None
[kubernetes:deploy-services] NOTES:
[kubernetes:deploy-services] 1. Get the application URL by running these commands:
[kubernetes:deploy-services]   export POD_NAME=$(kubectl get pods --namespace dragonfly -l "app.kubernetes.io/name=dragonfly,app.kubernetes.io/instance=dragonfly" -o jsonpath="{.items[0].metadata.name}")
[kubernetes:deploy-services]   export CONTAINER_PORT=$(kubectl get pod --namespace dragonfly $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
[kubernetes:deploy-services]   echo "You can use redis-cli to connect against localhost:6379"
[kubernetes:deploy-services]   kubectl --namespace dragonfly port-forward $POD_NAME 6379:$CONTAINER_PORT
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Listing releases matching ^dragonfly$
[kubernetes:deploy-services] dragonfly  dragonfly       1               2025-02-06 21:25:07.00725 +0100 CET     deployed        dragonfly-v1.26.2       v1.26.2    
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Release "postgres" does not exist. Installing it now.
[kubernetes:deploy-services] NAME: postgres
[kubernetes:deploy-services] LAST DEPLOYED: Thu Feb  6 21:25:12 2025
[kubernetes:deploy-services] NAMESPACE: postgres
[kubernetes:deploy-services] STATUS: deployed
[kubernetes:deploy-services] REVISION: 1
[kubernetes:deploy-services] TEST SUITE: None
[kubernetes:deploy-services] NOTES:
[kubernetes:deploy-services] CHART NAME: postgresql
[kubernetes:deploy-services] CHART VERSION: 16.4.6
[kubernetes:deploy-services] APP VERSION: 17.2.0
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Did you know there are enterprise versions of the Bitnami catalog? For enhanced secure software supply chain features, unlimited pulls from Docker, LTS support, or application customization, see Bitnami Premium or Tanzu Application Catalog. See https://www.arrow.com/globalecs/na/vendors/bitnami for more information.
[kubernetes:deploy-services] 
[kubernetes:deploy-services] ** Please be patient while the chart is being deployed **
[kubernetes:deploy-services] 
[kubernetes:deploy-services] PostgreSQL can be accessed via port 5432 on the following DNS names from within your cluster:
[kubernetes:deploy-services] 
[kubernetes:deploy-services]     postgres.postgres.svc.cluster.local - Read/Write connection
[kubernetes:deploy-services] 
[kubernetes:deploy-services] To get the password for "postgres" run:
[kubernetes:deploy-services] 
[kubernetes:deploy-services]     export POSTGRES_PASSWORD=$(kubectl get secret --namespace postgres postgres -o jsonpath="{.data.postgres-password}" | base64 -d)
[kubernetes:deploy-services] 
[kubernetes:deploy-services] To connect to your database run the following command:
[kubernetes:deploy-services] 
[kubernetes:deploy-services]     kubectl run postgres-client --rm --tty -i --restart='Never' --namespace postgres --image docker.io/bitnami/postgresql:17.2.0-debian-12-r10 --env="PGPASSWORD=$POSTGRES_PASSWORD" \
[kubernetes:deploy-services]       --command -- psql --host postgres -U postgres -d postgres -p 5432
[kubernetes:deploy-services] 
[kubernetes:deploy-services]     > NOTE: If you access the container using bash, make sure that you execute "/opt/bitnami/scripts/postgresql/entrypoint.sh /bin/bash" in order to avoid the error "psql: local user with ID 1001} does not exist"
[kubernetes:deploy-services] 
[kubernetes:deploy-services] To connect to your database from outside the cluster execute the following commands:
[kubernetes:deploy-services] 
[kubernetes:deploy-services]     kubectl port-forward --namespace postgres svc/postgres 5432:5432 &
[kubernetes:deploy-services]     PGPASSWORD="$POSTGRES_PASSWORD" psql --host 127.0.0.1 -U postgres -d postgres -p 5432
[kubernetes:deploy-services] 
[kubernetes:deploy-services] WARNING: The configured password will be ignored on new installation in case when previous PostgreSQL release was deleted through the helm command. In that case, old PVC will have an old password, and setting it through helm won't take effect. Deleting persistent volumes (PVs) will solve the issue.
[kubernetes:deploy-services] 
[kubernetes:deploy-services] WARNING: There are "resources" sections in the chart not set. Using "resourcesPreset" is not recommended for production. For production installations, please set the following values according to your workload needs:
[kubernetes:deploy-services]   - primary.resources
[kubernetes:deploy-services]   - readReplicas.resources
[kubernetes:deploy-services] +info https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
[kubernetes:deploy-services] 
[kubernetes:deploy-services] Listing releases matching ^postgres$
[kubernetes:deploy-services] postgres   postgres        1               2025-02-06 21:25:12.666801 +0100 CET    deployed        postgresql-16.4.6       17.2.0     
[kubernetes:deploy-services] 
[kubernetes:deploy-services] 
[kubernetes:deploy-services] UPDATED RELEASES:
[kubernetes:deploy-services] NAME            NAMESPACE       CHART                                                VERSION   DURATION
[kubernetes:deploy-services] ingress-nginx   ingress-nginx   ingress-nginx/ingress-nginx                          4.12.0       1m33s
[kubernetes:deploy-services] registry        registry        bjw-s/app-template                                   3.6.1          22s
[kubernetes:deploy-services] dragonfly       dragonfly       oci://ghcr.io/dragonflydb/dragonfly/helm/dragonfly   v1.26.2        40s
[kubernetes:deploy-services] postgres        postgres        bitnami/postgresql                                   16.4.6       1m24s
[kubernetes:deploy-services] 
[kubernetes:deploy-services] ✅ Core services deployed successfully
[kubernetes:fetch-service-secrets] 🔄 Fetching service secrets...
[kubernetes:fetch-service-secrets] 🔑 Passwords for enabled password-protected services have been written to /Users/devuser/demo/.local/my-cluster/service-secrets.txt
[kubernetes:fetch-service-secrets] 🔑 Service secrets:
[kubernetes:fetch-service-secrets] Service postgres, Password: 9iCCKyUGHF
[kubernetes:fetch-service-secrets] ✅ Service secrets fetched successfully
[validate:tcp-services] 🔍 Validating enabled TCP services:
[validate:tcp-services] 🔄 Validating postgres on port 5432...
[validate:tcp-services] Connection to postgres.dev.me port 5432 [tcp/postgresql] succeeded!
[validate:tcp-services] ✅ postgres is reachable on port 5432
[validate:tcp-services] 🔄 Validating dragonfly on port 6379...
[validate:tcp-services] Connection to dragonfly.dev.me port 6379 [tcp/*] succeeded!
[validate:tcp-services] ✅ dragonfly is reachable on port 6379
[validate:tcp-services] ✅✅✅ All services are reachable
[validate:build-push-local-registry] 🔄 Building and pushing a sample image to local registry...
[validate:build-push-local-registry] #0 building with "orbstack" instance using docker driver
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #1 [internal] load build definition from Dockerfile
[validate:build-push-local-registry] #1 transferring dockerfile: 453B done
[validate:build-push-local-registry] #1 DONE 0.0s
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #2 [auth] library/busybox:pull token for registry-1.docker.io
[validate:build-push-local-registry] #2 DONE 0.0s
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #3 [internal] load metadata for docker.io/library/busybox:1.37.0-uclibc
[validate:build-push-local-registry] #3 DONE 1.1s
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #4 [internal] load .dockerignore
[validate:build-push-local-registry] #4 transferring context: 2B done
[validate:build-push-local-registry] #4 DONE 0.0s
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #5 [1/4] FROM docker.io/library/busybox:1.37.0-uclibc@sha256:f1a295688a1cad4f66e7f45484a882a8b45fbdea28fa0a889ac17146775ad1a2
[validate:build-push-local-registry] #5 DONE 0.0s
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #6 [internal] load build context
[validate:build-push-local-registry] #6 transferring context: 27B done
[validate:build-push-local-registry] #6 DONE 0.0s
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #7 [3/4] COPY ./ep.sh /ep.sh
[validate:build-push-local-registry] #7 CACHED
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #8 [2/4] RUN mkdir -p /www
[validate:build-push-local-registry] #8 CACHED
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #9 [4/4] RUN chmod +x /ep.sh
[validate:build-push-local-registry] #9 CACHED
[validate:build-push-local-registry] 
[validate:build-push-local-registry] #10 exporting to image
[validate:build-push-local-registry] #10 exporting layers done
[validate:build-push-local-registry] #10 writing image sha256:417289e5d8ec911a53542f5549bf805483cfe5c5b06a1d7453627c79724f1d5c done
[validate:build-push-local-registry] #10 naming to cr.dev.me/cr-test:7bc4005a done
[validate:build-push-local-registry] #10 DONE 0.0s
[validate:build-push-local-registry] The push refers to repository [cr.dev.me/cr-test]
[validate:build-push-local-registry] 1705ee5400b5: Preparing
[validate:build-push-local-registry] fa3766cdc445: Preparing
[validate:build-push-local-registry] c10ffe097875: Preparing
[validate:build-push-local-registry] 834128d4c634: Preparing
[validate:build-push-local-registry] fa3766cdc445: Pushed
[validate:build-push-local-registry] c10ffe097875: Pushed
[validate:build-push-local-registry] 834128d4c634: Pushed
[validate:build-push-local-registry] 1705ee5400b5: Pushed
[validate:build-push-local-registry] 7bc4005a: digest: sha256:923e124d807cce66b43366374179039e08f6f13278fb508abf6e25c8760b8894 size: 1148
[validate:build-push-local-registry] ✅ Sample image built and pushed successfully
[validate:deploy-test-helm-release] 🔄 Deploying a test Helm release...
[validate:deploy-test-helm-release] Sample values.yaml generated at /Users/devuser/demo/tests/registry/test-values.yaml
[validate:deploy-test-helm-release] Release "cr-test" does not exist. Installing it now.
[validate:deploy-test-helm-release] NAME: cr-test
[validate:deploy-test-helm-release] LAST DEPLOYED: Thu Feb  6 21:26:41 2025
[validate:deploy-test-helm-release] NAMESPACE: default
[validate:deploy-test-helm-release] STATUS: deployed
[validate:deploy-test-helm-release] REVISION: 1
[validate:deploy-test-helm-release] TEST SUITE: None
[validate:deploy-test-helm-release] ✅ Test Helm release deployed successfully
[validate:app] 🔄 Validating sample application...
[validate:app] 
[validate:app] 🌐 Registry Test (https://cr-test.dev.me/):
[validate:app] 
[validate:app] <html><head><title>Local Kubernetes Test</title></head><body><h1>Welcome to your local Kubernetes development environment!</h1><p>This container is running an image from the local container registry hosted inside the kubernetes cluster.</p><p>Pod Name: cr-test-9dcdb897c-kf8qj</p></body></html>
[validate:app] ✅ Sample application validation complete
```
</details>

## Prerequisites

The following are required:

-  macOS
- 🐳 Docker (or docker-compatible runtime, e.g. OrbStack)
- 🧰 [mise](https://mise.jdx.dev/) for tool version management
- (optional) nss (for macOS) or libnss3-tools (for Linux) 
   * to automatically trust mkcert-generated certificates in Firefox; alternatively you can manually configure Firefox to trust the certificates

NOTES: 
- Podman is not supported yet as it is not a first-class citizen with KinD 
- Running on Linux is not yet fully tested and might not work as expected

All other dependencies are automatically managed by mise:
- 🐍 Python
- 📦 kubectl
- 📦 kind
- 📦 Helm
- 📦 Helmfile
- 📦 mkcert
- 📦 go-task
- 📦 yq
- 📦 jq
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

# Install tools and dependencies
mise install
task deps
```

3. Configure your environment by editing `.k8s-env.yaml`:
```yaml
environment:
  name: my-local-env
  local-ip: 127.0.0.1 # Change to your IP
  local-domain: me.local # Change if desired
```

4. Create the environment:
```bash
task create-env
```

5. Verify the setup:
```bash
task validate-env
```

## Project Structure

```
.
├── .k8s-env.yaml           # Main configuration file
├── .mise.toml              # Tool version management
├── templates/              # Jinja2 templates for configuration
│   ├── containerd/         # Containerd configuration templates
│   ├── coredns/            # CoreDNS configuration templates
│   ├── dnsmasq/            # DNSmasq configuration templates
│   ├── helmfile/           # Helmfile configuration templates
│   ├── kind/               # KinD cluster configuration templates
│   ├── tests/              # Test configuration templates
│   └── presets.yaml        # Service presets and default values
├── .local/                 # Runtime data (git-ignored)
├── .scripts/               # Python scripts for configuration
├── .taskfiles/             # Task definitions
└── Taskfile.yaml           # Main task definitions
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
├── .k8s-env.yaml                      # Main configuration file
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
├── .scripts/                          # Setup and configuration scripts
├── .taskfiles/                        # Task definitions and variables
│   ├── help/                          # Help tasks
│   ├── kubernetes/                    # Kubernetes-related tasks
│   ├── validate/                      # Validation tasks
│   └── vars/                          # Common variables used in tasks
├── tests/                             # Test files for validation
└── Taskfile.yaml                      # Main task definitions
```

The `.local` directory (configurable via `base-dir` in `.k8s-env.yaml`) is created when you first run `task create-env` and contains all runtime data and configurations. Key points about the `.local` directory:

- **Location**: By default, it's created in the project root but can be configured via `base-dir` in `.k8s-env.yaml`
- **Persistence**: Contains all persistent data, including certificates, logs, and storage
- **Environment Isolation**: Each environment gets its own subdirectory (e.g., `.local/my-local-env/`)
- **Backup**: You may want to back up the `certs` and `config` directories
- **Cleanup**: The entire `.local` directory can be safely deleted to start fresh

> Note: The `.local` directory is git-ignored by default. If you need to preserve any configurations, consider committing them to a separate repository, being mindful of any sensitive data, such as passwords/keys/secrets/etc.

## Service Management

Services are defined in two places:

1. `.k8s-env.yaml`: Service enablement and specific configurations
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