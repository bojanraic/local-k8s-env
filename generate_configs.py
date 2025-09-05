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

def generate_random_password(length=16):
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

def deep_merge_dicts(source, destination):
    """Deep merge two dictionaries."""
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create it
            node = destination.setdefault(key, {})
            deep_merge_dicts(value, node)
        else:
            destination[key] = value
    return destination

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

def expand_os_variables(obj, expand_vars=True):
    """
    Recursively expand OS environment variables in objects.
    Supports ${PWD}, ${HOME}, ${USER}, etc.
    """
    if not expand_vars:
        return obj
        
    if isinstance(obj, dict):
        return {k: expand_os_variables(v, expand_vars) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_os_variables(item, expand_vars) for item in obj]
    elif isinstance(obj, str):
        import os
        return os.path.expandvars(obj)
    else:
        return obj

def expand_k8s_env_variables(obj, k8s_env_vars, expand_vars=True):
    """
    Recursively expand k8s-env specific variables in values objects.
    Supports ${LOCAL_DOMAIN}, ${ENV_NAME}, ${REGISTRY_HOST}, etc.
    """
    if not expand_vars:
        return obj
        
    if isinstance(obj, dict):
        return {k: expand_k8s_env_variables(v, k8s_env_vars, expand_vars) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_k8s_env_variables(item, k8s_env_vars, expand_vars) for item in obj]
    elif isinstance(obj, str):
        result = obj
        for var_name, var_value in k8s_env_vars.items():
            result = result.replace(f'${{{var_name}}}', str(var_value))
        return result
    else:
        return obj

def process_system_services(system_services, service_ports, service_values_presets, use_service_presets, k8s_env_vars, expand_vars=True):
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
            
            # Apply persistence configuration using deep merge
            if 'storage' in service and 'size' in service['storage']:
                storage_config = {}
                # For groundhog2k charts, use 'storage.requestedSize'
                if 'storage' in service_values_presets[service_name]:
                    storage_config['storage'] = storage_config.get('storage', {})
                    storage_config['storage']['requestedSize'] = service['storage']['size']
                # Legacy support for Bitnami-style charts (if any remain)
                elif 'primary' in service_values_presets[service_name]:
                    storage_config['primary'] = storage_config.get('primary', {})
                    storage_config['primary']['persistence'] = {
                        'enabled': True,
                        'size': service['storage']['size']
                    }
                elif 'persistence' in service_values_presets[service_name]:
                    storage_config['persistence'] = {
                        'enabled': True,
                        'size': service['storage']['size']
                    }
                deep_merge_dicts(storage_config, base_values)
            
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
            # First expand OS variables, then k8s-env variables
            expanded_custom_values = expand_os_variables(custom_values, expand_vars)
            expanded_custom_values = expand_k8s_env_variables(expanded_custom_values, k8s_env_vars, expand_vars)
            service['custom_values'] = expanded_custom_values
            base_values.update(expanded_custom_values)
        
        # Store processed values
        service['base_values'] = base_values
        service['namespace'] = service_namespace
        service['service_type'] = 'system'
        
        # Ensure ports are available for system services
        if service_name in service_ports:
            service['default_port'] = service_ports[service_name]
        
        processed_services.append(service)
    
    return processed_services

def process_user_services(user_services, k8s_env_vars, expand_vars=True):
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
        if not isinstance(repo, dict) or not (
            ('name' in repo and 'url' in repo) or 'ref' in repo
        ):
            raise ValueError(f"User service '{service_name}' must have either repo.name and repo.url, or repo.ref configured")
        
        # For user services, use values from config with variable expansion
        base_values = config.get('values', {})
        
        # Replace instances of ${APPS_SUBDOMAIN}.${LOCAL_DOMAIN} with ${LOCAL_APPS_DOMAIN}
        # This simplifies configuration and makes it more intuitive
        if 'ingress' in base_values and isinstance(base_values['ingress'], dict):
            ingress_config = base_values['ingress']
            
            # Process hosts if they exist
            if 'hosts' in ingress_config and isinstance(ingress_config['hosts'], list):
                for i, host_entry in enumerate(ingress_config['hosts']):
                    if isinstance(host_entry, dict) and 'host' in host_entry:
                        host = host_entry['host']
                        # Handle both old and new variable names for backward compatibility
                        if '${USER_SUBDOMAIN}.${LOCAL_DOMAIN}' in host:
                            # Replace with the new variable
                            host_entry['host'] = host.replace('${USER_SUBDOMAIN}.${LOCAL_DOMAIN}', '${LOCAL_APPS_DOMAIN}')
                        elif '${APPS_SUBDOMAIN}.${LOCAL_DOMAIN}' in host:
                            # Replace with the new variable
                            host_entry['host'] = host.replace('${APPS_SUBDOMAIN}.${LOCAL_DOMAIN}', '${LOCAL_APPS_DOMAIN}')
            
            # Process TLS hosts if they exist
            if 'tls' in ingress_config and isinstance(ingress_config['tls'], list):
                for tls_entry in ingress_config['tls']:
                    if isinstance(tls_entry, dict) and 'hosts' in tls_entry and isinstance(tls_entry['hosts'], list):
                        for i, host in enumerate(tls_entry['hosts']):
                            if isinstance(host, str):
                                # Handle both old and new variable names for backward compatibility
                                if '${USER_SUBDOMAIN}.${LOCAL_DOMAIN}' in host:
                                    # Replace with the new variable
                                    tls_entry['hosts'][i] = host.replace('${USER_SUBDOMAIN}.${LOCAL_DOMAIN}', '${LOCAL_APPS_DOMAIN}')
                                elif '${APPS_SUBDOMAIN}.${LOCAL_DOMAIN}' in host:
                                    # Replace with the new variable
                                    tls_entry['hosts'][i] = host.replace('${APPS_SUBDOMAIN}.${LOCAL_DOMAIN}', '${LOCAL_APPS_DOMAIN}')
        
        # First expand OS variables, then k8s-env variables
        expanded_values = expand_os_variables(base_values, expand_vars)
        expanded_values = expand_k8s_env_variables(expanded_values, k8s_env_vars, expand_vars)
        service['base_values'] = expanded_values
        service['namespace'] = service_namespace
        service['service_type'] = 'user'
        
        processed_services.append(service)
    
    return processed_services

def collect_helm_repositories(config, services):
    """Collect helm repositories from centralized config and resolve service references"""
    # Get centralized repositories
    centralized_repos = config['environment'].get('helm-repositories', [])
    repositories = {}
    
    # Add centralized repositories
    for repo in centralized_repos:
        if isinstance(repo, dict) and 'name' in repo and 'url' in repo:
            repo_name = repo['name']
            repo_url = repo['url']
            repositories[repo_name] = repo_url
    
    # Also collect any inline repo configs (for backward compatibility)
    for service in services:
        repo_config = service.get('config', {}).get('repo', {})
        if isinstance(repo_config, dict) and 'name' in repo_config and 'url' in repo_config:
            repo_name = repo_config['name']
            repo_url = repo_config['url']
            repositories[repo_name] = repo_url
    
    return repositories

def resolve_repo_references(services, helm_repositories):
    """Resolve repo.ref references to actual repository configurations"""
    centralized_repo_map = {repo['name']: repo for repo in helm_repositories if isinstance(repo, dict) and 'name' in repo}
    
    for service in services:
        repo_config = service.get('config', {}).get('repo', {})
        if isinstance(repo_config, dict) and 'ref' in repo_config:
            ref_name = repo_config['ref']
            if ref_name in centralized_repo_map:
                # Replace ref with actual repo config
                service['config']['repo'] = centralized_repo_map[ref_name].copy()
            else:
                raise ValueError(f"Repository reference '{ref_name}' not found in helm-repositories for service '{service.get('name', 'unknown')}'")


def prepare_context(config):
    # Load service ports and presets from file
    service_ports, service_values_presets = load_presets()
    
    # Get services configuration
    services_config = config['environment'].get('services', {})
    system_services = services_config.get('system', [])
    user_services = services_config.get('user', [])
    use_service_presets = config['environment'].get('use-service-presets', True)
    
    # Get centralized helm repositories
    helm_repositories_config = config['environment'].get('helm-repositories', [])
    
    # Resolve repository references in services
    resolve_repo_references(system_services, helm_repositories_config)
    resolve_repo_references(user_services, helm_repositories_config)
    
    # Process services separately
    # Create k8s-env variables dictionary for expansion
    env = config['environment']
    expand_vars = env.get('expand-env-vars', True)
    
    # Get apps subdomain configuration
    use_apps_subdomain = env.get('use-apps-subdomain', True)
    apps_subdomain = env.get('apps-subdomain', 'apps')
    
    # Build k8s-env variables dictionary (most commonly used in helm values)
    # Create LOCAL_APPS_DOMAIN based on use_apps_subdomain setting
    local_apps_domain = f"{apps_subdomain}.{env['local-domain']}" if use_apps_subdomain else env['local-domain']
    
    k8s_env_vars = {
        'ENV_NAME': env['name'],
        'LOCAL_DOMAIN': env['local-domain'],
        'LOCAL_IP': env['local-ip'],
        'REGISTRY_NAME': env['registry']['name'],
        'REGISTRY_HOST': f"{env['registry']['name']}.{env['local-domain']}",
        'APPS_SUBDOMAIN': apps_subdomain,
        'USE_APPS_SUBDOMAIN': str(use_apps_subdomain).lower(),
        'LOCAL_APPS_DOMAIN': local_apps_domain,
    }
    
    processed_system_services = process_system_services(
        system_services, service_ports, service_values_presets, use_service_presets, k8s_env_vars, expand_vars
    )
    processed_user_services = process_user_services(user_services, k8s_env_vars, expand_vars)
    
    # Combine all enabled services
    all_services = processed_system_services + processed_user_services
    
    # Collect helm repositories
    helm_repositories = collect_helm_repositories(config, all_services)
    
    def get_internal_component(env, key):
        for comp in env.get('internal-components', []):
            if key in comp:
                return comp[key]
        return None

    provider_name = env['provider']['name']
    
    # Set provider-specific paths and settings
    storage_path = '/var/local-path-provisioner'
    log_path = '/var/log'
    internal_domain = 'kind.internal'
    internal_host = 'localhost.kind.internal'
    # Expand base directory variables for KinD  
    base_dir = env['base-dir']
    if env.get('expand-env-vars', True):
        import os
        base_dir = os.path.expandvars(base_dir)
    
    context = {
        'env_name': env['name'],
        'local_ip': env['local-ip'],
        'local_domain': env['local-domain'],
        'apps_subdomain': apps_subdomain,
        'use_apps_subdomain': use_apps_subdomain,
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

        'dnsmasq_version': get_internal_component(env, 'dnsmasq'),
        'service_ports': service_ports,
        'service_values_presets': service_values_presets,
        'use_service_presets': use_service_presets,
        'run_services_on_workers_only': env.get('run-services-on-workers-only', False),
        'deploy_metrics_server': env.get('enable-metrics-server', True),
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
    
    resolver_content = f"search {local_domain}\nnameserver {local_ip} 1.1.1.1"
    
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
    except subprocess.CalledProcessError:
        print("⚠️  Warning: systemd-resolved not found")
        return
    
    # Create drop-in directory
    dropin_dir = '/etc/systemd/resolved.conf.d'
    subprocess.run(['sudo', 'mkdir', '-p', dropin_dir], check=True)
    
    # Generate config with simpler split DNS setup
    # Use local_ip as primary DNS for local_domain
    # Use public DNS servers as fallback for all other domains
    resolver_content = f"[Resolve]\nDNS={local_ip}\nDomains={local_domain}\nFallbackDNS=1.1.1.1 8.8.8.8"
    temp_file = f'/tmp/resolver_{local_domain}.conf'
    final_file = f'{dropin_dir}/{local_domain}.conf'
    
    with open(temp_file, 'w') as f:
        f.write(resolver_content)
    
    # Install config
    subprocess.run(['sudo', 'mv', temp_file, final_file], check=True)
    subprocess.run(['sudo', 'chown', 'root:root', final_file], check=True)
    subprocess.run(['sudo', 'chmod', '644', final_file], check=True)
    subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-resolved'], check=True)
    
    # Restore the symlink to stub-resolv.conf if it's not already set up
    try:
        subprocess.run(['sudo', 'ln', '-sf', '/run/systemd/resolve/stub-resolv.conf', '/etc/resolv.conf'], check=True)
        print("✅ Restored resolv.conf symlink to use systemd-resolved")
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Could not restore resolv.conf symlink")
    
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