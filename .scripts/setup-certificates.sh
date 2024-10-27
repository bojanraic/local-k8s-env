#!/bin/bash
set -e

if [ $# -ne 3 ]; then
    echo "Usage: $0 <local-domain> <local-ip> <cert-dir>"
    exit 1
fi

LOCAL_DOMAIN=$1
LOCAL_IP=$2
CERT_DIR=$3

# Ensure mkcert is installed and the local CA is set up
if ! command -v mkcert &> /dev/null; then
    echo "mkcert is required but not installed"
    exit 1
fi

# Create certificates directory
mkdir -p "${CERT_DIR}"

# Install the local CA if not already installed
mkcert -install

# Generate wildcard certificate for the domain and local ip
if [ ! -f "${CERT_DIR}/${LOCAL_DOMAIN}.pem" ]; then
    echo "Generating certificates for *.${LOCAL_DOMAIN}"
    mkcert -cert-file "${CERT_DIR}/${LOCAL_DOMAIN}.pem" \
           -key-file "${CERT_DIR}/${LOCAL_DOMAIN}-key.pem" \
           "*.${LOCAL_DOMAIN}" "${LOCAL_DOMAIN}" \
           "*.${LOCAL_IP}" "${LOCAL_IP}" \
           "*.k3d.internal" "host.k3d.internal"
fi

# Copy the root CA to the cert directory
cp "$(mkcert -CAROOT)/rootCA.pem" "${CERT_DIR}/rootCA.pem"

# Create a combined PEM file for services that need it
cat "${CERT_DIR}/${LOCAL_DOMAIN}.pem" "${CERT_DIR}/${LOCAL_DOMAIN}-key.pem" > "${CERT_DIR}/${LOCAL_DOMAIN}-combined.pem"

echo "Certificate setup completed successfully"
