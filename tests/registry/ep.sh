#!/bin/sh
echo "<html><head><title>Local Kubernetes Container Registry Test</title></head><body><h1>Welcome to the Kubernetes Local Development Environment!</h1><p>This container is running an image from the local container registry hosted inside the kubernetes cluster.</p><p>Pod Name: ${HOSTNAME}</p></body></html>" > /www/index.html
httpd -f -h /www
