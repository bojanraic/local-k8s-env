#!/bin/bash
set -e

if [ $# -ne 4 ]; then
    echo "Usage: $0 <config-file> <local-domain> <local-ip> <dnsmasq-config> <dnsmasq-version>"
    exit 1
fi
CONFIG_FILE=$1
LOCAL_DOMAIN=$2
LOCAL_IP=$3
DNSMASQ_CONFIG=$4
DNSMASQ_VERSION=$5
ENV_NAME=$(yq e '.environment.name' $CONFIG_FILE)
DNS_PORT=$(yq e '.environment.dns.port' $CONFIG_FILE)
RUNTIME_BINARY=$(yq e '.environment.provider.runtime' $CONFIG_FILE)
# Ensure we're running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Create resolver directory if it doesn't exist
mkdir -p /etc/resolver

# Create resolver configuration for the local domain
cat > "/etc/resolver/${LOCAL_DOMAIN}" <<EOF
nameserver ${LOCAL_IP}
port ${DNS_PORT}
EOF

# Start dnsmasq container if not already running
CONTAINER_NAME="dnsmasq-${ENV_NAME}"
if ! ${RUNTIME_BINARY} ps | grep -q ${CONTAINER_NAME}; then
    echo "Starting dnsmasq container..."
    ${RUNTIME_BINARY} run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p ${LOCAL_IP}:${DNS_PORT}:53/udp \
        -p ${LOCAL_IP}:${DNS_PORT}:53/tcp \
        -v ${DNSMASQ_CONFIG}:/etc/dnsmasq.conf:ro \
        --cap-add=NET_ADMIN \
        dockurr/dnsmasq:${DNSMASQ_VERSION}
else
    echo "Dnsmasq container already running, reloading configuration..."
    ${RUNTIME_BINARY} cp ${DNSMASQ_CONFIG} ${CONTAINER_NAME}:/etc/dnsmasq.conf
    ${RUNTIME_BINARY} restart ${CONTAINER_NAME}
fi

# Verify DNS resolution
echo "Verifying DNS resolution..."
if [ "${RUNTIME_BINARY}" = "docker" ]; then
    NETWORK_NAME="kind"
else
    NETWORK_NAME="podman"
fi

dig @${LOCAL_IP} -p ${DNS_PORT} test.${LOCAL_DOMAIN} | grep -q "${LOCAL_IP}" || {
    echo "DNS resolution verification failed"
    exit 1
}

echo "DNS setup completed successfully"