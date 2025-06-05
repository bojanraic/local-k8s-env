#!/bin/sh

# Demo app chart
CHART_TYPE="demo-app"
CHART_INFO="<p><strong>Chart:</strong> Demo App OCI Helm Chart</p>"

if [ -n "$HELM_RELEASE_NAME" ]; then
    CHART_INFO="$CHART_INFO<p><strong>Release:</strong> $HELM_RELEASE_NAME</p>"
fi
if [ -n "$CHART_VERSION" ]; then
    CHART_INFO="$CHART_INFO<p><strong>Version:</strong> $CHART_VERSION</p>"
fi

# Deployment info
DEPLOYMENT_INFO=""
if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
    DEPLOYMENT_INFO="<p><strong>Deployment:</strong> Running in Kubernetes</p>"
fi

# Get namespace from service account mount (standard Kubernetes)
NAMESPACE="unknown"
if [ -f "/var/run/secrets/kubernetes.io/serviceaccount/namespace" ]; then
    NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
fi

cat > /www/index.html << EOF
<html>
<head>
    <title>Local Kubernetes Test - Demo App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .info { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .chart-info { background-color: #e8f5e8; border-left: 4px solid #27ae60; }
        .pod-info { background-color: #fff3cd; border-left: 4px solid #ffc107; }
        .env-info { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to your local Kubernetes development environment!</h1>
        
        <div class="info chart-info">
            <h3>Chart Information</h3>
            $CHART_INFO
            $DEPLOYMENT_INFO
            <p><strong>Namespace:</strong> $NAMESPACE</p>
            <p><strong>Chart Type:</strong> $CHART_TYPE</p>
        </div>
        
        <div class="info pod-info">
            <h3>Pod Information</h3>
            <p><strong>Pod Name:</strong> $HOSTNAME</p>
            <p><strong>Image Tag:</strong> ${IMAGE_TAG:-latest}</p>
        </div>
        
        <div class="info">
            <h3>Registry Information</h3>
            <p>This container is running an image from the local container registry hosted inside the kubernetes cluster.</p>
            <p>This deployment uses an OCI Helm chart that is also packaged and hosted in the same local registry.</p>
        </div>
        
        <div class="info env-info">
            <h3>Environment Variables</h3>
            <p><strong>Available vars:</strong></p>
            <ul>
EOF

# Add key environment variables for debugging
for var in CHART_NAME HELM_RELEASE_NAME CHART_VERSION; do
    if [ -n "$(eval echo \$$var)" ]; then
        echo "                <li><strong>$var:</strong> $(eval echo \$$var)</li>" >> /www/index.html
    fi
done

cat >> /www/index.html << EOF
            </ul>
        </div>
    </div>
</body>
</html>
EOF

httpd -f -h /www
