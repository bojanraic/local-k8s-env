#!/bin/sh
echo "<html><head><title>Local Kubernetes Test</title></head><body><h1>Welcome to your local Kubernetes development environment!</h1><p>This container is running an image from the local container registry hosted inside the kubernetes cluster.</p><p>Pod Name: ${HOSTNAME}</p><p>Image Tag: ${IMAGE_TAG}</p></body></html>" > /www/index.html
httpd -f -h /www
