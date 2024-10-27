#!/bin/sh
echo "<html><head><title>Local Image Registry Test</title></head><body><h1>Welcome to Local Development Environment!</h1><p>This container is running an image from the local container registry hosted on the local kubernetes cluster.</p><p>Pod Name: ${HOSTNAME}</p></body></html>" > /www/index.html
httpd -f -h /www
