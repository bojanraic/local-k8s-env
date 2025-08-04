#!/usr/bin/env python3
import os
import sys
import yaml
import jinja2
import subprocess
import secrets
import string
from pathlib import Path

CACERT_FILE = "/etc/ssl/certs/mkcert-ca.pem"

def generate_random_password(length=24):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_chart_auth_config(service_name, chart_name):
    """Generate authentication configuration for specific charts"""
    auth_configs = {
        'mysql': {
            'settings': {
                'rootPassword': {
                    'value': generate_random_password()
                }
            }
        },
        'postgres': {
            'settings': {
                'superuserPassword': {
                    'value': generate_random_password()
                }
            }
        },
        'mongodb': {
            'settings': {
                'rootUsername': 'root',
                'rootPassword': generate_random_password()
            }
        },
        'rabbitmq': {
            'authentication': {
                'user': {
                    'value': 'admin'
                },
                'password': {
                    'value': generate_random_password()
                },
                'erlangCookie': {
                    'value': generate_random_password(32)
                }
            }
        },
        'valkey': {
            'useDeploymentWhenNonHA': False  # Use StatefulSet instead of Deployment
        }
    }
    
    # Extract chart name from full path (e.g., 'groundhog2k/mysql' -> 'mysql')
    chart_basename = chart_name.split('/')[-1] if '/' in chart_name else chart_name
    
    return auth_configs.get(chart_basename, {})

def load_presets():
    """Load service ports and presets from service_presets.yaml"""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    preset_file = os.path.join(script_dir, 'templates', 'service_presets.yaml')
    with open(preset_file) as f:
        presets = yaml.safe_load(f)
    return (
        presets.get('service_ports', {}),
        presets.get('service_values_presets', {})
    )

def load_config(config_file):
    with open(config_file) as f:
        return yaml.safe_load(f)

def setup_jinja_env():
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(script_dir, 'templates')
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
    try:
        env = setup_jinja_env()
        template = env.get_template(template_name)
        result = template.render(**context)
        return result
    except Exception as e:
        print(f"\n[ERROR] Error rendering template: {template_name}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Error details: {str(e)}")
        if hasattr(e, 'lineno') and hasattr(e, 'filename'):
            print(f"[ERROR] Error at {e.filename}, line {e.lineno}")
        if hasattr(e, 'message'):
            print(f"[ERROR] Message: {e.message}")
        raise

def process_system_services(system_services, service_ports, service_values_presets, use_service_presets):
    """Process system services with presets and port/storage management"""
    processed_services = []
    
    for service in system_services:
        if not service.get('enabled', False):
            continue

        service_name = service['name']
        service_namespace = service.get('namespace', service_name)
        
        # Initialize base_values
        base_values = {}
        
        # Apply presets if enabled and available
        if use_service_presets and service_name in service_values_presets:
            base_values = service_values_presets[service_name].copy()
            # Add standard configurations
            base_values.update({
                'fullNameOverride': service_name,
                'nameOverride': service_name
            })
            
            # Add persistence configuration based on service storage
            if 'storage' in service and 'size' in service['storage']:
                # For groundhog2k charts, use 'storage.requestedSize' instead of Bitnami's structure
                if 'storage' in service_values_presets[service_name]:
                    base_values['storage'] = base_values.get('storage', {})
                    base_values['storage']['requestedSize'] = service['storage']['size']
                # Legacy support for Bitnami-style charts (if any remain)
                elif 'primary' in service_values_presets[service_name]:
                    base_values['primary'] = base_values.get('primary', {})
                    base_values['primary']['persistence'] = {
                        'enabled': True,
                        'size': service['storage']['size']
                    }
                elif 'persistence' in service_values_presets[service_name]:
                    base_values['persistence'] = {
                        'enabled': True,
                        'size': service['storage']['size']
                    }
            
            # Generate and apply authentication configuration automatically
            chart_name = service.get('config', {}).get('chart', '')
            if chart_name:
                auth_config = generate_chart_auth_config(service_name, chart_name)
                if auth_config:
                    # Deep merge auth config into base_values
                    for key, value in auth_config.items():
                        if key in base_values and isinstance(base_values[key], dict) and isinstance(value, dict):
                            base_values[key].update(value)
                        elif key in base_values and isinstance(base_values[key], list) and isinstance(value, list):
                            base_values[key].extend(value)
                        else:
                            base_values[key] = value
                    print(f"🔐 Generated authentication configuration for {service_name}")
        
        # Merge custom values from config if they exist
        custom_values = service.get('config', {}).get('values', {})
        if custom_values:
            service['custom_values'] = custom_values
            base_values.update(custom_values)
        
        # Store processed values
        service['base_values'] = base_values
        service['namespace'] = service_namespace
        service['service_type'] = 'system'
        
        # Ensure ports are available for system services
        if service_name in service_ports:
            service['default_port'] = service_ports[service_name]
        
        processed_services.append(service)
    
    return processed_services

def process_user_services(user_services):
    """Process user services without presets - users provide complete configuration"""
    processed_services = []
    
    for service in user_services:
        if not service.get('enabled', False):
            continue

        service_name = service['name']
        service_namespace = service.get('namespace', service_name)
        
        # Validate required repo configuration for user services
        config = service.get('config', {})
        repo = config.get('repo', {})
        if not isinstance(repo, dict) or 'name' not in repo or 'url' not in repo:
            raise ValueError(f"User service '{service_name}' must have repo.name and repo.url configured")
        
        # For user services, use values as-is from config
        service['base_values'] = config.get('values', {})
        service['namespace'] = service_namespace
        service['service_type'] = 'user'
        
        processed_services.append(service)
    
    return processed_services

def collect_helm_repositories(services):
    """Collect unique helm repositories from all services"""
    repositories = {}
    
    for service in services:
        repo_config = service.get('config', {}).get('repo', {})
        if isinstance(repo_config, dict) and 'name' in repo_config and 'url' in repo_config:
            repo_name = repo_config['name']
            repo_url = repo_config['url']
            repositories[repo_name] = repo_url
    
    return repositories

def prepare_context(config):
    # Load service ports and presets from file
    service_ports, service_values_presets = load_presets()
    
    # Get services configuration
    services_config = config['environment'].get('services', {})
    system_services = services_config.get('system', [])
    user_services = services_config.get('user', [])
    use_service_presets = config['environment'].get('use-service-presets', True)
    
    # Process services separately
    processed_system_services = process_system_services(
        system_services, service_ports, service_values_presets, use_service_presets
    )
    processed_user_services = process_user_services(user_services)
    
    # Combine all enabled services
    all_services = processed_system_services + processed_user_services
    
    # Collect helm repositories
    helm_repositories = collect_helm_repositories(all_services)
    
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
        'services': all_services,  # All enabled services (system + user)
        'system_services': processed_system_services,  # Only system services
        'user_services': processed_user_services,  # Only user services
        'helm_repositories': helm_repositories,  # All unique helm repositories
        'registry': env['registry'],
        'registry_name': env['registry']['name'],
        'registry_version': get_internal_component(env, 'registry'),
        'app_template_version': get_internal_component(env, 'app-template'),
        'nginx_ingress_version': get_internal_component(env, 'nginx-ingress'),
        'metrics_server_version': get_internal_component(env, 'metrics-server'),
        'cert_manager_version': get_internal_component(env, 'cert-manager'),
        'dnsmasq_version': get_internal_component(env, 'dnsmasq'),
        'service_ports': service_ports,
        'service_values_presets': service_values_presets,
        'use_service_presets': use_service_presets,
        'run_services_on_workers_only': env.get('run-services-on-workers-only', False),
        'deploy_metrics_server': env.get('deploy-metrics-server', True),
        'cacert_file': CACERT_FILE,
        'k8s_dir': f"{base_dir}/{env['name']}",
        'mounts': [
            {'local_path': 'logs', 'node_path': log_path},
            {'local_path': 'storage', 'node_path': storage_path}
        ],
        'internal_domain': internal_domain,
        'internal_host': internal_host,
        'provider': env['provider'],
        'allow_control_plane_scheduling': env['nodes'].get('allow-scheduling-on-control-plane', False),
        'internal_components_on_control_plane': env['nodes'].get('internal-components-on-control-plane', False),
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

def create_output_directories(context):
    """Create all necessary output directories"""
    k8s_dir = context['k8s_dir']
    
    # Create main directories
    os.makedirs(f"{k8s_dir}/config", exist_ok=True)
    os.makedirs(f"{k8s_dir}/certs", exist_ok=True)
    os.makedirs(f"{k8s_dir}/logs", exist_ok=True)
    os.makedirs(f"{k8s_dir}/storage", exist_ok=True)
    
    # Create containerd config directory for registry certificates
    containerd_cert_dir = context.get('containerd_cert_dir')
    if containerd_cert_dir:
        os.makedirs(containerd_cert_dir, exist_ok=True)

def generate_config_files(context):
    """Generate all configuration files"""
    k8s_dir = context['k8s_dir']
    config_dir = f"{k8s_dir}/config"
    
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

def generate_configs(config_file, os_name):
    """Generate all configuration files"""
    print("🔄 Generating configuration files...")
    config = load_config(config_file)
    
    # Generate resolver file based on OS
    generate_resolver_file(config, os_name)
    
    # Generate all other configs
    context = prepare_context(config)
    
    # Create output directories
    create_output_directories(context)
    
    # Generate all configuration files
    generate_config_files(context)
    
    print("✅ Configuration files generated successfully")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  generate_configs.py k8s-env.yaml # Generate all configs")
        sys.exit(1)
    
    config_file = sys.argv[1]
    os_name = sys.platform
    
    generate_configs(config_file, os_name)
    sys.exit(0) 