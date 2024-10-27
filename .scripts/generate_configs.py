#!/usr/bin/env python3

import sys
import yaml  # type: ignore
import os
from collections import OrderedDict
import subprocess

CACERT_FILE = "/etc/ssl/certs/mkcert-ca.pem"

SERVICE_VALUES_PRESETS = {
    'mysql': {'fullNameOverride': 'mysql', 'nameOverride': 'mysql', 'primary': {'persistence': {'enabled': True, 'size': None}}},
    'postgres': {'fullNameOverride': 'postgres', 'nameOverride': 'postgres', 'primary': {'persistence': {'enabled': True, 'size': None}}},
    'mongodb': {'fullNameOverride': 'mongodb', 'nameOverride': 'mongodb', 'useStatefulSet': True, 'persistence': {'enabled': True, 'size': None}},
    'dragonfly': {'fullNameOverride': 'dragonfly', 'nameOverride': 'dragonfly', 'storage': {'enabled': True, 'requests': None}},
    'rabbitmq': {'fullNameOverride': 'rabbitmq', 'nameOverride': 'rabbitmq', 'persistence': {'enabled': True, 'size': None}}
}

SERVICE_PORTS = {'mysql': 3306, 'postgres': 5432, 'mongodb': 27017, 'dragonfly': 6379, 'rabbitmq': 5672}

class OrderedDumper(yaml.Dumper):
    def represent_dict(self, data):
        return self.represent_mapping('tag:yaml.org,2002:map', data.items())

    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str) and '\n' in value:
            style = '|'
        return super().represent_scalar(tag, value, style)

OrderedDumper.add_representer(OrderedDict, OrderedDumper.represent_dict)

def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def generate_ports(local_lb_ports, services):
    ports = []
    # Iterate over the local-lb-ports and create port mappings
    for lb_port in local_lb_ports:
        ports.append(OrderedDict([
            ('port', f"{lb_port}:{lb_port}"),
            ('nodeFilters', ['loadbalancer'])
        ]))
    for service in services:
        if service.get('enabled', True):
            for port in service.get('ports', []):
                ports.append(OrderedDict([
                    ('port', f"{port}:{port}"),
                    ('nodeFilters', ['loadbalancer'])
                ]))
    return ports

def generate_volumes(config, root_ca_path):
    mounts = [
        {'name': 'logs', 'local-path': 'logs', 'node-path': '/var/log/'},
        {'name': 'storage', 'local-path': 'storage', 'node-path': '/var/lib/rancher/k3s/storage'}
    ]
    volumes = []

    def generate_node_volumes(node_type, node_index):
        for mount in mounts:
            volumes.append(OrderedDict([
                ('volume', f"${{K8S_DIR}}/{mount['local-path']}/{node_type}-{node_index}:{mount['node-path']}"),
                ('nodeFilters', [f"{node_type}:{node_index}"])
            ]))

    for i in range(config['environment']['nodes']['servers']):
        generate_node_volumes('server', i)
    for i in range(config['environment']['nodes']['workers']):
        generate_node_volumes('agent', i)

    extra_volumes = [
        OrderedDict([
            ('volume', f"{root_ca_path}:{CACERT_FILE}"),
            ('nodeFilters', ['server:*', 'agent:*'])
        ]),
        OrderedDict([
            ('volume', f"${{K8S_DIR}}/config/containerd.yaml:/var/lib/rancher/k3s/agent/etc/containerd/certs.d/{config['environment']['local-domain']}/host.yml"),
            ('nodeFilters', ['server:*', 'agent:*'])
        ])
    ]
    volumes.extend(extra_volumes)
    return volumes

def generate_k3d_config(config, root_ca_path):
    runtime = config['environment']['provider']['runtime']
    env_name = config['environment']['name']
    local_ip = config['environment']['local-ip']
    local_lb_ports = config['environment']['local-lb-ports']
    api_port = config['environment']['kubernetes']['api-port']
    k8s_image = config['environment']['kubernetes']['image']
    app_template_version = config['environment']['app-template-version']
    dnsmasq_version = config['environment']['dnsmasq-version']
    services = config['environment']['services']

    ports = generate_ports(local_lb_ports, services)
    volumes = generate_volumes(config, root_ca_path)

    k3d_config = OrderedDict([
        ('apiVersion', 'k3d.io/v1alpha5'),
        ('kind', 'Simple'),
        ('metadata', OrderedDict([('name', env_name)])),
        ('servers', config['environment']['nodes']['servers']),
        ('agents', config['environment']['nodes']['workers']),
        ('kubeAPI', OrderedDict([('host', local_ip), ('hostPort', str(api_port))])),
        ('image', k8s_image),
        ('network', 'podman' if runtime == 'podman' else f'k3d-{env_name}-net'),
        ('ports', ports),
        ('volumes', volumes),
        ('options', OrderedDict([
            ('k3d', OrderedDict([
                ('wait', True),
                ('timeout', "180s"),
                ('loadbalancer', OrderedDict([
                    ('configOverrides', ['settings.workerConnections=2048'])
                ]))
            ])),
            ('k3s', OrderedDict([
                ('extraArgs', [
                    OrderedDict([('arg', f"--tls-san={local_ip}"), ('nodeFilters', ['server:*'])]),
                    OrderedDict([('arg', f"--tls-san={env_name}.{config['environment']['local-domain']}"), ('nodeFilters', ['server:*'])]),
                    OrderedDict([('arg', '--disable=traefik'), ('nodeFilters', ['server:*'])]),
                    OrderedDict([('arg', '--disable-network-policy'), ('nodeFilters', ['server:*'])]),
                    OrderedDict([('arg', '--disable-helm-controller'), ('nodeFilters', ['server:*'])]),
                    OrderedDict([('arg', '--disable-cloud-controller'), ('nodeFilters', ['server:*'])]),
                    OrderedDict([('arg', '--secrets-encryption=true'), ('nodeFilters', ['server:*'])])
                ])
            ])),
            ('kubeconfig', OrderedDict([
                ('updateDefaultKubeconfig', True),
                ('switchCurrentContext', True)
            ]))
        ]))
    ])
    return k3d_config

def generate_containerd_config(config):
    registry_name = config['environment']['registry']['name']
    local_domain = config['environment']['local-domain']
    return {
        f"host.\"https://{registry_name}.{local_domain}\"": {
            "capabilities": ["pull", "resolve", "push"],
            "ca_file": CACERT_FILE
        }
    }

def generate_dnsmasq_config(config):
    return f"address=/{config['environment']['local-domain']}/{config['environment']['local-ip']}"

def generate_coredns_config(config):
    local_domain = config['environment']['local-domain']
    return OrderedDict([
        ('apiVersion', 'v1'),
        ('kind', 'ConfigMap'),
        ('metadata', OrderedDict([('name', 'coredns-custom'), ('namespace', 'kube-system')])),
        ('data', OrderedDict([('rewrite.override', f"rewrite name regex (.*)\\.{local_domain} host.k3d.internal")]))
    ])

def generate_ingress_nginx_release(config):
    tcp_services = {}
    for service in config['environment'].get('services', []):
        if service.get('enabled', True):
            for port in service.get('ports', []):
                tcp_services[str(port)] = f"{service.get('namespace', service['name'])}/{service['name']}:{SERVICE_PORTS[service['name']]}"

    return {
        'name': 'ingress-nginx',
        'chart': 'ingress-nginx/ingress-nginx',
        'namespace': 'ingress-nginx',
        'version': config['environment']['nginx-ingress-version'],
        'values': [
            {
                'controller': {'extraArgs': {'default-ssl-certificate': f"kube-system/wildcard-tls"}},
                'tcp': tcp_services
            }
        ]
    }

def generate_registry_release(config):
    local_domain = config['environment']['local-domain']
    registry_name = config['environment']['registry']['name']
    registry_storage_size = config['environment']['registry']['storage']['size']

    return OrderedDict([
        ('name', 'registry'),
        ('namespace', 'registry'),
        ('chart', 'bjw-s/app-template'),
        ('version', config['environment']['app-template-version']),
        ('needs', ['ingress-nginx/ingress-nginx']),
        ('values', [{
            'controllers': {'registry': {'type': 'statefulset', 'containers': {'app': {'image': {'repository': 'registry', 'tag': '2'}}}}},
            'service': {'app': {'controller': 'registry', 'ports': {'http': {'port': 5000}}}},
            'ingress': {'app': {'className': 'nginx', 'annotations': {
                'nginx.ingress.kubernetes.io/ssl-redirect': "true",
                'nginx.ingress.kubernetes.io/force-ssl-redirect': "true",
                'kubernetes.io/ingress.allow-http': "false",
                'nginx.ingress.kubernetes.io/proxy-body-size': "4096m"
            }, 'hosts': [{'host': f"{registry_name}.{local_domain}", 'paths': [{'path': '/', 'service': {'identifier': 'app', 'port': 'http'}}]}],
                'tls': [{'hosts': [f"{registry_name}.{local_domain}"]}]}},
            'persistence': {'data': {'enabled': True, 'size': registry_storage_size, 'retain': True, 'type': 'persistentVolumeClaim', 'accessMode': 'ReadWriteOnce', 'globalMounts': [{'path': '/var/lib/registry'}]}},
            'env': {'REGISTRY_HTTP_ADDR': ':5000', 'REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY': '/var/lib/registry'}
        }])
    ])

def generate_service_release(service):
    service_config = service.get('config', {})
    service_values = service_config.get('values', {})
    storage_size = service.get('storage', {}).get('size')

    # Copy the preset and update the size
    service_values_preset = SERVICE_VALUES_PRESETS.get(service['name'], {}).copy()
    if 'primary' in service_values_preset:
        service_values_preset['primary']['persistence']['size'] = storage_size
    elif 'storage' in service_values_preset:
        service_values_preset['storage']['requests'] = storage_size
    elif 'persistence' in service_values_preset:
        service_values_preset['persistence']['size'] = storage_size

    return OrderedDict([
        ('name', service['name']),
        ('namespace', service.get('namespace', service['name'])),
        ('chart', service_config.get('chart', None)),
        ('version', service_config.get('version', None)),
        ('values', [service_values_preset, service_values])
    ])

def generate_helmfile(config):
    helmfile_content = OrderedDict([
        ('repositories', [
            OrderedDict([('name', 'ingress-nginx'), ('url', 'https://kubernetes.github.io/ingress-nginx')]),
            OrderedDict([('name', 'bitnami'), ('url', 'https://charts.bitnami.com/bitnami')]),
            OrderedDict([('name', 'bjw-s'), ('url', 'https://bjw-s.github.io/helm-charts/')])
        ]),
        ('helmDefaults', OrderedDict([
            ('createNamespace', True),
            ('wait', True),
            ('atomic', True),
            ('timeout', 900)
        ])),
        ('releases', [
            generate_ingress_nginx_release(config),
            generate_registry_release(config)
        ])
    ])

    for service in config['environment'].get('services', []):
        if service.get('enabled', True):
            helmfile_content['releases'].append(generate_service_release(service))
    return helmfile_content

def generate_mac_resolver_file(config):
    local_domain = config['environment']['local-domain']
    local_ip = config['environment']['local-ip']
    resolver_dir = "/etc/resolver"
    resolver_file = f"{resolver_dir}/{local_domain}"

    if not os.path.exists(resolver_dir):
        subprocess.run(['sudo', 'mkdir', '-p', resolver_dir], check=True)

    resolver_content = f"""\
search {local_domain}
nameserver {local_ip}
"""

    with open(f'/tmp/resolver_file_{local_domain}', 'w') as f:
        f.write(resolver_content)

    subprocess.run(['sudo', 'mv', f'/tmp/resolver_file_{local_domain}', resolver_file], check=True)
    subprocess.run(['sudo', 'chown', 'root:wheel', resolver_file], check=True)
    subprocess.run(['sudo', 'chmod', '644', resolver_file], check=True)

    print(f"Resolver file created at {resolver_file}")

def generate_linux_resolver_file(config):
    local_domain = config['environment']['local-domain']
    local_ip = config['environment']['local-ip']
    
    # Check if systemd-resolved is using stub listener
    try:
        resolved_config = subprocess.run(['systemctl', 'is-enabled', 'systemd-resolved'], 
                                      capture_output=True, text=True, check=True)
        if resolved_config.stdout.strip() == 'enabled':
            # Disable stub listener and restart systemd-resolved
            print("Disabling systemd-resolved stub listener...")
            subprocess.run(['sudo', 'sed', '-i', 's/#DNSStubListener=yes/DNSStubListener=no/', '/etc/systemd/resolved.conf'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-resolved'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not check systemd-resolved status: {e}")

    # Create drop-in directory if it doesn't exist
    dropin_dir = '/etc/systemd/resolved.conf.d'
    subprocess.run(['sudo', 'mkdir', '-p', dropin_dir], check=True)

    # Create the drop-in file content
    resolver_content = f"""\
[Resolve]
DNS={local_ip}
Domains={local_domain}
"""

    # Write to temporary file first
    temp_file = f'/tmp/resolver_{local_domain}.conf'
    with open(temp_file, 'w') as f:
        f.write(resolver_content)

    # Move file to final location and set permissions
    final_file = f'{dropin_dir}/{local_domain}.conf'
    subprocess.run(['sudo', 'mv', temp_file, final_file], check=True)
    subprocess.run(['sudo', 'chown', 'root:root', final_file], check=True)
    subprocess.run(['sudo', 'chmod', '644', final_file], check=True)

    # Restart systemd-resolved to apply changes
    subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-resolved'], check=True)

    print(f"Resolver configuration created at {final_file}")

def generate_resolver_file(config, os):
    if os == 'Darwin':
        generate_mac_resolver_file(config)
    elif os == 'Linux':
        generate_linux_resolver_file(config)
    else:
        print(f"Resolver file for {os} not implemented")

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_configs.py <config_file> <os>")
        sys.exit(1)

    config_file = sys.argv[1]
    os_name = sys.argv[2]
    print(f"Generating configs for {os_name} based on {config_file}")
    config = load_config(config_file)
    base_dir = config['environment']['base-dir']
    if config['environment']['expand-base-dir-vars']:
        base_dir = os.path.expandvars(base_dir)

    env_name = config['environment']['name']
    config_dir = f"{base_dir}/{env_name}/config"
    certs_dir = f"${{K8S_DIR}}/certs"
    root_ca_path = f"{certs_dir}/rootCA.pem"

    configs = {
        "helmfile.yaml": generate_helmfile(config),
        "cluster.yaml": generate_k3d_config(config, root_ca_path),
        "containerd.yaml": generate_containerd_config(config),
        "dnsmasq.conf": generate_dnsmasq_config(config),
        "coredns-custom.yaml": generate_coredns_config(config)
    }

    for filename, content in configs.items():
        with open(f"{config_dir}/{filename}", 'w') as f:
            if isinstance(content, (dict, list)):
                yaml.dump(content, f, Dumper=OrderedDumper, default_flow_style=False)
            else:
                f.write(content)

    generate_resolver_file(config, os_name)

if __name__ == "__main__":
    main()
