#!/usr/bin/env python3
import sys
from jinja2 import Environment, FileSystemLoader
import os

def generate_values_yaml(registry, name, tag, hostname, output_file):
    """Generate values.yaml for registry test deployment
    
    Args:
        registry: Registry hostname (e.g. cr.dev.me)
        name: Image name (e.g. cr-test)
        tag: Image tag (e.g. latest)
        hostname: Ingress hostname (e.g. cr-test.dev.me)
        output_file: Path to output values.yaml
    """
    # Create Jinja2 environment with updated template path
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'tests', 'registry')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Load the template
    template = env.get_template('values.yaml.j2')
    
    # Render the template with our variables
    rendered = template.render(
        registry=registry,
        name=name,
        tag=tag,
        hostname=hostname
    )
    
    # Write the rendered template to file
    with open(output_file, 'w') as f:
        f.write(rendered)

def main():
    if len(sys.argv) != 6:
        print("Usage: generate_validation.py <registry> <name> <tag> <hostname> <output-file>")
        sys.exit(1)

    registry, name, tag, hostname, output_file = sys.argv[1:]
    generate_values_yaml(registry, name, tag, hostname, output_file)
    print(f"Sample values.yaml generated at {output_file}")

if __name__ == "__main__":
    main()
