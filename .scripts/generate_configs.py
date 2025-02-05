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
    
    # Add custom filters
    env.filters['to_yaml'] = lambda value: yaml.dump(value, default_flow_style=False)
    
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
        
        # Always apply auth presets as they contain critical security settings
        if service_name in service_auth_presets:
            service.update(service_auth_presets[service_name])
        
        # Initialize config if not present
        if 'config' not in service:
            service['config'] = {}
            
        # Handle service values based on use-service-presets flag
        if use_service_presets and service_name in service_values_presets:
            base_values = service_values_presets[service_name]
            # Store base values separately - they'll be used in the template
            service['base_values'] = base_values
            
            # If service has custom values, they'll be applied as an additional values block
            # in the template, which will override the base values
        else:
            # When presets are disabled, ensure we have an empty dict for values
            service['config']['values'] = service.get('config', {}).get('values', {})
            
        service['namespace'] = service_namespace
        enabled_services.append(service)
    
    def get_internal_component(env, key):
        for comp in env.get('internal-components', []):
            if key in comp:
                return comp[key]
        return None

    env = config['environment']
    context = {
        'env_name': env['name'],
        'local_ip': env['local-ip'],
        'local_domain': env['local-domain'],
        'kubernetes': env['kubernetes'],
        'nodes': env['nodes'],
        'runtime': env['provider']['runtime'],
        'services': enabled_services,
        'registry': env['registry'],
        'registry_name': env['registry']['name'],
        'registry_version': get_internal_component(env, 'registry'),
        'app_template_version': get_internal_component(env, 'app-template'),
        'nginx_ingress_version': get_internal_component(env, 'nginx-ingress'),
        'dnsmasq_version': get_internal_component(env, 'dnsmasq'),
        'local_lb_ports': env['local-lb-ports'],
        'service_ports': service_ports,
        'service_values_presets': service_values_presets,
        'use_service_presets': use_service_presets,
        'cacert_file': CACERT_FILE,
        'k8s_dir': f"{env['base-dir']}/{env['name']}",
        'mounts': [
            {'local_path': 'logs', 'node_path': '/var/log/'},
            {'local_path': 'storage', 'node_path': '/var/lib/rancher/k3s/storage'}
        ]
    }
    
    # Add root CA path
    context['root_ca_path'] = f"{context['k8s_dir']}/certs/rootCA.pem"
    
    # Add DNS-specific context with default value if not present
    context['dns_port'] = env.get('dns', {}).get('port', 53)
    
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
    
    if os_name == 'Darwin':
        generate_resolver_file_mac(config, local_domain, local_ip)
    elif os_name == 'Linux':
        generate_resolver_file_linux(config, local_domain, local_ip)
    else:
        print(f"⚠️  Resolver file generation not implemented for {os_name}")

def generate_configs(config_file, os_name):
    print(f"🚀 Generating configurations from {config_file}")
    config = load_config(config_file)
    context = prepare_context(config)
    
    # Create output directories
    base_dir = config['environment']['base-dir']
    if config['environment']['expand-base-dir-vars']:
        base_dir = os.path.expandvars(base_dir)
    
    env_name = config['environment']['name']
    config_dir = f"{base_dir}/{env_name}/config"
    os.makedirs(config_dir, exist_ok=True)
    
    # Define templates and their output files
    templates = {
        'k3d/cluster.yaml.j2': 'cluster.yaml',
        'helmfile/helmfile.yaml.j2': 'helmfile.yaml',
        'coredns/custom.yaml.j2': 'coredns-custom.yaml',
        'containerd/config.yaml.j2': 'containerd.yaml',
        'dnsmasq/config.conf.j2': 'dnsmasq.conf'
    }
    
    # Generate each configuration file
    for template_path, output_name in templates.items():
        print(f"📝 Generating {output_name}")
        content = render_template(template_path, context)
        output_path = f"{config_dir}/{output_name}"
        
        with open(output_path, 'w') as f:
            f.write(content)
        print(f"✅ Created {output_path}")
    
    # Generate resolver file based on OS
    generate_resolver_file(config, os_name)
    
    print("✨ Configuration generation complete!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_configs.py <config_file> <os>")
        sys.exit(1)
    
    try:
        generate_configs(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1) 