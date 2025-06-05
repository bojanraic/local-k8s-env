# Demo App Helm Chart

A minimal demo application Helm chart for testing local registry and Helm OCI functionality.

## Description

This chart deploys a simple web application that displays:
- Welcome message
- Pod name (hostname)
- Image tag

The application is built from a minimal BusyBox image and serves a static HTML page on port 80.

## Features

- **Automatic TLS**: Uses cert-manager annotations for automatic certificate generation
- **Configurable domains**: Override default values using `--set` parameters
- **OCI registry support**: Can be packaged and deployed as OCI artifacts
- **Health checks**: Built-in liveness and readiness probes
- **Helm tests**: Connectivity tests included

## Installation

### From Local Files
```bash
helm install demo-app ./helm-chart \
  --set image.repository=cr.dev.me/cr-test \
  --set image.tag=latest \
  --set ingress.hosts[0].host=demo-app.dev.me \
  --set ingress.tls[0].hosts[0]=demo-app.dev.me
```

### From OCI Registry
```bash
helm install demo-app oci://cr.dev.me/helm-charts/demo-app --version 0.1.0 \
  --set image.repository=cr.dev.me/cr-test \
  --set image.tag=latest \
  --set ingress.hosts[0].host=demo-app.dev.me \
  --set ingress.tls[0].hosts[0]=demo-app.dev.me
```

### With Custom Domain
```bash
helm install demo-app ./helm-chart \
  --set image.repository=cr.dev.me/cr-test \
  --set image.tag=latest \
  --set ingress.hosts[0].host=my-app.example.com \
  --set ingress.tls[0].hosts[0]=my-app.example.com \
  --set ingress.tls[0].secretName=my-app-tls
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `demo-app` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `80` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Hostname | `registry-test.local` |
| `ingress.annotations` | Ingress annotations | cert-manager and nginx configs |

**Note**: The chart uses sensible defaults that should be overridden for your environment using `--set` parameters during deployment.

## TLS Configuration

The chart uses cert-manager annotations for automatic TLS certificate generation:

```yaml
annotations:
  cert-manager.io/cluster-issuer: "mkcert-issuer"
  cert-manager.io/duration: "72h"
  cert-manager.io/renew-before: "36h"
```

## Usage with Task

### Test Chart Locally
```bash
task validate:test-helm-chart
```

### Build and Deploy Demo App
```bash
task validate:demo-app-workflow
```

### Run Complete Validation
```bash
task validate:local-registry
```

### Validate Deployment
```bash
task validate:demo-app
```

### Clean Up
```bash
task validate:undeploy-demo-app
``` 