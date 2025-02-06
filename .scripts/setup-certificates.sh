#!/bin/bash
set -e

if [ $# -ne 3 ]; then
    echo "Usage: $0 <local-domain> <local-ip> <cert-dir>"
    exit 1
fi

LOCAL_DOMAIN=$1
LOCAL_IP=$2
CERT_DIR=$3

mkdir -p $CERT_DIR
mkcert -install

if [ ! -f $CERT_DIR/$LOCAL_DOMAIN.pem ]; then
    mkcert -cert-file $CERT_DIR/$LOCAL_DOMAIN.pem -key-file $CERT_DIR/$LOCAL_DOMAIN-key.pem "*.$LOCAL_DOMAIN" "$LOCAL_DOMAIN" "*.$LOCAL_IP" "$LOCAL_IP"
fi

# Copy CA cert
cp "$(mkcert -CAROOT)/rootCA.pem" $CERT_DIR/rootCA.pem

# Create a combined PEM file for services that need it
cat "${CERT_DIR}/${LOCAL_DOMAIN}.pem" "${CERT_DIR}/${LOCAL_DOMAIN}-key.pem" > "${CERT_DIR}/${LOCAL_DOMAIN}-combined.pem"

echo "Certificates set up successfully"