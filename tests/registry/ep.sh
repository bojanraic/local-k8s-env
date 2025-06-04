#!/bin/sh

# Detect which chart is being used based on environment variables
CHART_TYPE="unknown"
CHART_INFO=""

# Check if we're running via app-template (bjw-s) chart
# App-template typically sets these environment variables
if [ -n "$SERVICE_NAME" ] || [ -n "$CONTROLLER_NAME" ] || [ -n "$APP_TEMPLATE_CHART" ]; then
    CHART_TYPE="app-template"
    CHART_INFO="<p><strong>Chart:</strong> BJW-S App Template (bjw-s-labs/app-template)</p>"
    if [ -n "$SERVICE_NAME" ]; then
        CHART_INFO="$CHART_INFO<p><strong>Service:</strong> $SERVICE_NAME</p>"
    fi
    if [ -n "$CONTROLLER_NAME" ]; then
        CHART_INFO="$CHART_INFO<p><strong>Controller:</strong> $CONTROLLER_NAME</p>"
    fi
    if [ -n "$HELM_RELEASE_NAME" ]; then
        CHART_INFO="$CHART_INFO<p><strong>Release:</strong> $HELM_RELEASE_NAME</p>"
    fi
    if [ -n "$CHART_VERSION" ]; then
        CHART_INFO="$CHART_INFO<p><strong>Version:</strong> $CHART_VERSION</p>"
    fi
# Check for our custom demo-app chart environment variables
elif [ -n "$DEMO_APP_CHART" ] || [ "$CHART_NAME" = "demo-app" ]; then
    CHART_TYPE="demo-app"
    CHART_INFO="<p><strong>Chart:</strong> Demo App OCI Helm Chart</p>"
    if [ -n "$HELM_RELEASE_NAME" ]; then
        CHART_INFO="$CHART_INFO<p><strong>Release:</strong> $HELM_RELEASE_NAME</p>"
    fi
    if [ -n "$CHART_VERSION" ]; then
        CHART_INFO="$CHART_INFO<p><strong>Version:</strong> $CHART_VERSION</p>"
    fi
else
    # Try to detect based on common Helm environment variables
    if [ -n "$HELM_RELEASE_NAME" ]; then
        CHART_TYPE="helm-release"
        CHART_INFO="<p><strong>Chart:</strong> Helm Release</p><p><strong>Release:</strong> $HELM_RELEASE_NAME</p>"
    else
        CHART_INFO="<p><strong>Chart:</strong> Unable to detect chart type</p>"
    fi
fi

# Additional deployment info
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
    <title>Local Kubernetes Test - $CHART_TYPE</title>
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
            <p><strong>Chart Type Detected:</strong> $CHART_TYPE</p>
        </div>
        
        <div class="info pod-info">
            <h3>Pod Information</h3>
            <p><strong>Pod Name:</strong> $HOSTNAME</p>
            <p><strong>Image Tag:</strong> ${IMAGE_TAG:-latest}</p>
        </div>
        
        <div class="info">
            <h3>Registry Information</h3>
EOF

# Add registry information based on chart type
if [ "$CHART_TYPE" = "demo-app" ]; then
    cat >> /www/index.html << EOF
            <p>This container is running an image from the local container registry hosted inside the kubernetes cluster.</p>
            <p>Additionally, this deployment uses an OCI Helm chart that is also packaged and hosted in the same local registry.</p>
EOF
else
    cat >> /www/index.html << EOF
            <p>This container is running an image from the local container registry hosted inside the kubernetes cluster.</p>
EOF
fi

cat >> /www/index.html << EOF
        </div>
        
        <div class="info env-info">
            <h3>Environment Variables</h3>
            <p><strong>Available vars:</strong></p>
            <ul>
EOF

# Add some key environment variables for debugging
for var in SERVICE_NAME CONTROLLER_NAME DEMO_APP_CHART CHART_NAME HELM_RELEASE_NAME CHART_VERSION; do
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
