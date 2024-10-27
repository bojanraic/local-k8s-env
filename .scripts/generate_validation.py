#!/usr/bin/env python3
import yaml # type: ignore
import sys

def generate_values_yaml(registry_host, image_name, image_tag, ingress_host):
    return {
        'controllers': {
            'app': {
                'containers': {
                    'app': {
                        'image': {
                            'repository': f'{registry_host}/{image_name}',
                            'tag': image_tag
                        }
                    }
                }
            }
        },
        'service': {
            'app': {
                'controller': 'app',
                'ports': {'http': {'port': 80}}
            }
        },
        'ingress': {
            'app': {
                'className': 'nginx',
                'annotations': {
                    'nginx.ingress.kubernetes.io/ssl-redirect': "true",
                    'nginx.ingress.kubernetes.io/force-ssl-redirect': "true",
                    'kubernetes.io/ingress.allow-http': "false"
                },
                'hosts': [{
                    'host': ingress_host,
                    'paths': [{
                        'path': '/',
                        'service': {'identifier': 'app', 'port': 'http'}
                    }]
                }],
                'tls': [{'hosts': [ingress_host]}]
            }
        }
    }

def main():
    if len(sys.argv) != 6:
        print("Usage: generate_validation.py <registry-host> <image-name> <image-tag> <ingress-host> <output-file>")
        sys.exit(1)

    registry_host, image_name, image_tag, ingress_host, output_file = sys.argv[1:]
    values_yaml = generate_values_yaml(registry_host, image_name, image_tag, ingress_host)

    with open(output_file, 'w') as f:
        yaml.dump(values_yaml, f, default_flow_style=False)

    print(f"Sample values.yaml generated at {output_file}")

if __name__ == "__main__":
    main()
