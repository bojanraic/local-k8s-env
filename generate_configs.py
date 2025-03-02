#!/usr/bin/env python3
import os
import sys
import yaml
import jinja2
import subprocess
from pathlib import Path

CACERT_FILE = "/etc/ssl/certs/mkcert-ca.pem"

def load_presets():
    """Load service ports and presets from service_presets.yaml"""
    preset_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'service_presets.yaml')
    with open(preset_file) as f:
        presets = yaml.safe_load(f)
    return (
        presets.get('service_ports', {}),
        presets.get('service_values_presets', {}),
        presets.get('service_auth_presets', {})
    )

def load_config(config_file):
    with open(config_file) as f:
        return yaml.safe_load(f)

def setup_jinja_env():
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=['jinja2.ext.do']
    )
    
    # Custom YAML dumper class to handle multiline strings
    class MyDumper(yaml.Dumper):
        def represent_scalar(self, tag, value, style=None):
            if isinstance(value, str) and '\n' in value:
                style = '|'
            return super().represent_scalar(tag, value, style)
    
    # Modified YAML dumper to handle multiline strings
    def custom_yaml_dump(value):
        return yaml.dump(value, 
                        Dumper=MyDumper,
                        default_flow_style=False,
                        default_style=None,
                        allow_unicode=True)
    
    # Add custom filters
    env.filters['to_yaml'] = custom_yaml_dump
    
    return env

def render_template(template_name, context):
    env = setup_jinja_env()
    template = env.get_template(template_name)
    return template.render(**context)

def prepare_context(config):
    # Load service ports and presets from file
    service_ports, service_values_presets, service_auth_presets = load_presets()
    
    # Get services and use-service-presets flag
    services = config['environment'].get('services', [])
    use_service_presets = config['environment'].get('use-service-presets', True)
    
    # Process each service
    enabled_services = []
    for service in services:
        if not service.get('enabled', False):
            continue

        service_name = service['name']
        service_namespace = service.get('namespace', service_name)
        
        # Initialize base_values
        base_values = {}
        
        # Apply presets if enabled
        if use_service_presets and service_name in service_values_presets:
            base_values = service_values_presets[service_name].copy()
            # Add standard configurations
            base_values.update({
                'fullNameOverride': service_name,
                'nameOverride': service_name
            })
            
            # Add persistence configuration
            if 'primary' in service_values_presets[service_name]:
                base_values['primary'] = {
                    'persistence': {
                        'enabled': True,
                        'size': service['storage']['size']
                    }
                }
            elif 'persistence' in service_values_presets[service_name]:
                base_values['persistence'] = {
                    'enabled': True,
                    'size': service['storage']['size']
                }
            elif 'storage' in service_values_presets[service_name]:
                base_values['storage'] = {
                    'enabled': service_values_presets[service_name]['storage'].get('enabled', False),
                    'requests': service['storage']['size']
                }
        
        # Merge custom values from config if they exist
        custom_values = service.get('config', {}).get('values', {})
        if custom_values:
            # Store custom values separately to ensure they override base values
            service['custom_values'] = custom_values
            # Also update base_values with custom values to ensure they take precedence
            base_values.update(custom_values)
        
        # Store base values
        service['base_values'] = base_values
        service['namespace'] = service_namespace
        enabled_services.append(service)
    
    def get_internal_component(env, key):
        for comp in env.get('internal-components', []):
            if key in comp:
                return comp[key]
        return None

    env = config['environment']
    provider_name = env['provider']['name']
    
    # Set provider-specific paths and settings
    storage_path = '/var/local-path-provisioner'
    log_path = '/var/log'
    internal_domain = 'kind.internal'
    internal_host = 'localhost.kind.internal'
    # Expand base directory variables for KinD
    base_dir = env['base-dir']
    if env['expand-base-dir-vars']:
        pwd = os.getcwd()
        base_dir = base_dir.replace('${PWD}', pwd)
    
    context = {
        'env_name': env['name'],
        'local_ip': env['local-ip'],
        'local_domain': env['local-domain'],
        'kubernetes': env['kubernetes'],
        'api_port': env['kubernetes']['api-port'],
        'nodes': env['nodes'],
        'runtime': env['provider']['runtime'],
        # Separate ingress and service ports for better control
        'ingress_ports': env['local-lb-ports'],  # 80/443 for ingress
        'services': [s for s in enabled_services if s.get('enabled', False)],  # Only enabled services
        'registry': env['registry'],
        'registry_name': env['registry']['name'],
        'registry_version': get_internal_component(env, 'registry'),
        'app_template_version': get_internal_component(env, 'app-template'),
        'nginx_ingress_version': get_internal_component(env, 'nginx-ingress'),
        'cert_manager_version': get_internal_component(env, 'cert-manager'),
        'dnsmasq_version': get_internal_component(env, 'dnsmasq'),
        'service_ports': service_ports,
        'service_values_presets': service_values_presets,
        'use_service_presets': use_service_presets,
        'cacert_file': CACERT_FILE,
        'k8s_dir': f"{base_dir}/{env['name']}",
        'mounts': [
            {'local_path': 'logs', 'node_path': log_path},
            {'local_path': 'storage', 'node_path': storage_path}
        ],
        'internal_domain': internal_domain,
        'internal_host': internal_host,
        'provider': env['provider'],
        'allow_cp_scheduling': env['nodes'].get('allow-scheduling-on-control-plane', False),
    }
    
    # Ensure all paths in mounts are absolute for KinD
    for mount in context['mounts']:
        if 'local_path' in mount:
            mount['hostPath'] = os.path.abspath(f"{context['k8s_dir']}/{mount['local_path']}")
    
    # Add root CA path, absolute for KinD
    context['root_ca_path'] = os.path.abspath(f"{context['k8s_dir']}/certs/rootCA.pem")
    
    # Add DNS-specific context with default value if not present
    context['dns_port'] = env.get('dns', {}).get('port', 53)
    
    # Combine Kubernetes image and tag into a full image reference
    kubernetes_image = env.get('kubernetes', {}).get('image', '')
    kubernetes_tag = env.get('kubernetes', {}).get('tag', '')
    if kubernetes_tag:
        full_image = f"{kubernetes_image}:{kubernetes_tag}"
    else:
        full_image = kubernetes_image
    context['kubernetes_full_image'] = full_image
    
    return context

def generate_resolver_file_mac(config, local_domain, local_ip):
    resolver_dir = "/etc/resolver"
    resolver_file = f"{resolver_dir}/{local_domain}"
    
    if not os.path.exists(resolver_dir):
        subprocess.run(['sudo', 'mkdir', '-p', resolver_dir], check=True)
    
    resolver_content = f"search {local_domain}\nnameserver {local_ip}"
    
    with open(f'/tmp/resolver_file_{local_domain}', 'w') as f:
        f.write(resolver_content)
    
    subprocess.run(['sudo', 'mv', f'/tmp/resolver_file_{local_domain}', resolver_file], check=True)
    subprocess.run(['sudo', 'chown', 'root:wheel', resolver_file], check=True)
    subprocess.run(['sudo', 'chmod', '644', resolver_file], check=True)
    
    print(f"✅ Resolver file created at {resolver_file}")

def generate_resolver_file_linux(config, local_domain, local_ip):
    # Check systemd-resolved
    try:
        subprocess.run(['systemctl', 'is-enabled', 'systemd-resolved'], 
                      capture_output=True, text=True, check=True)
        
        # Disable stub listener
        print("🔧 Configuring systemd-resolved...")
        subprocess.run(['sudo', 'sed', '-i', 's/#DNSStubListener=yes/DNSStubListener=no/', 
                       '/etc/systemd/resolved.conf'], check=True)
        subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-resolved'], check=True)
    except subprocess.CalledProcessError:
        print("⚠️  Warning: systemd-resolved not found")
    
    # Create drop-in directory
    dropin_dir = '/etc/systemd/resolved.conf.d'
    subprocess.run(['sudo', 'mkdir', '-p', dropin_dir], check=True)
    
    # Generate config
    resolver_content = f"[Resolve]\nDNS={local_ip}\nDomains={local_domain}"
    temp_file = f'/tmp/resolver_{local_domain}.conf'
    final_file = f'{dropin_dir}/{local_domain}.conf'
    
    with open(temp_file, 'w') as f:
        f.write(resolver_content)
    
    # Install config
    subprocess.run(['sudo', 'mv', temp_file, final_file], check=True)
    subprocess.run(['sudo', 'chown', 'root:root', final_file], check=True)
    subprocess.run(['sudo', 'chmod', '644', final_file], check=True)
    subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-resolved'], check=True)
    
    print(f"✅ Resolver configuration created at {final_file}")

def generate_resolver_file(config, os_name):
    local_domain = config['environment']['local-domain']
    local_ip = config['environment']['local-ip']
    
    print(f"🔧 Setting up DNS resolver for {local_domain}...")
    
    if os_name.lower() == 'darwin':
        generate_resolver_file_mac(config, local_domain, local_ip)
    elif os_name.lower() == 'linux':
        generate_resolver_file_linux(config, local_domain, local_ip)
    else:
        print(f"⚠️  Resolver file generation not implemented for {os_name}")

def generate_configs(config_file, os_name):
    """Generate all configuration files"""
    config = load_config(config_file)
    context = prepare_context(config)
    
    # Create config directory
    k8s_dir = context['k8s_dir']
    config_dir = f"{k8s_dir}/config"
    os.makedirs(config_dir, exist_ok=True)
    
    # Generate cluster config
    cluster_config = render_template('kind/cluster.yaml.j2', context)
    with open(f"{config_dir}/cluster.yaml", 'w') as f:
        f.write(cluster_config)
    
    # Generate containerd config
    containerd_config = render_template('containerd/config.yaml.j2', context)
    with open(f"{config_dir}/containerd.yaml", 'w') as f:
        f.write(containerd_config)
    
    # Generate dnsmasq config
    dnsmasq_config = render_template('dnsmasq/config.conf.j2', context)
    with open(f"{config_dir}/dnsmasq.conf", 'w') as f:
        f.write(dnsmasq_config)
    
    # Generate helmfile config
    helmfile_config = render_template('helmfile/helmfile.yaml.j2', context)
    with open(f"{config_dir}/helmfile.yaml", 'w') as f:
        f.write(helmfile_config)
    
    # Generate cert-manager cluster-issuer config
    cluster_issuer_config = render_template('cert-manager/cluster-issuer.yaml.j2', context)
    with open(f"{config_dir}/cluster-issuer.yaml", 'w') as f:
        f.write(cluster_issuer_config)
    
    print("✅ Configuration files generated successfully")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_configs.py <config_file> <os>")
        sys.exit(1)
    
    try:
        generate_configs(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1) 