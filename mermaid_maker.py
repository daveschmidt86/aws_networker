import json
from typing import Dict, List

class NetworkDiagramGenerator:
    def __init__(self, network_data: Dict):
        self.data = network_data
        self.diagram = []

    def generate_diagram(self) -> str:
        """Generate complete Mermaid diagram from network data."""
        self.diagram = ['graph TB']
        
        # Process each VPC
        for vpc in self.data['vpcs']:
            self._process_vpc(vpc)
            
        # Add styling classes
        self._add_styling()
        
        return '\n    '.join(self.diagram)

    def _process_vpc(self, vpc: Dict) -> None:
        """Process VPC and its components."""
        vpc_id = vpc['id'].replace('-', '_')
        
        # Start VPC subgraph
        self.diagram.extend([
            f'    subgraph {vpc_id}["{vpc["name"]} ({vpc["cidr"]})"]'
        ])
        
        # Group subnets by AZ
        az_subnets = {}
        for subnet in vpc['subnets']:
            az = subnet['az']
            if az not in az_subnets:
                az_subnets[az] = []
            az_subnets[az].append(subnet)
        
        # Process each AZ
        for az, subnets in az_subnets.items():
            self._process_az(az, subnets, vpc)
        
        self.diagram.append('    end')
        
        # Add Internet Gateway
        self.diagram.extend([
            f'    igw_{vpc_id}["Internet Gateway"]'
        ])
        
        # Connect IGW to public subnets
        for subnet in vpc['subnets']:
            if subnet.get('public'):
                subnet_id = subnet['id'].replace('-', '_')
                self.diagram.append(f'    igw_{vpc_id} --> subnet_{subnet_id}')

    def _process_az(self, az: str, subnets: List[Dict], vpc: Dict) -> None:
        """Process Availability Zone and its subnets."""
        az_id = az.replace('-', '_')
        
        self.diagram.extend([
            f'        subgraph {az_id}["{az}"]'
        ])
        
        for subnet in subnets:
            self._process_subnet(subnet, vpc)
            
        self.diagram.append('        end')

    def _process_subnet(self, subnet: Dict, vpc: Dict) -> None:
        """Process subnet and its components."""
        subnet_id = subnet['id'].replace('-', '_')
        subnet_type = "Public" if subnet.get('public') else "Private"
        
        self.diagram.extend([
            f'            subgraph subnet_{subnet_id}["{subnet_type} Subnet ({subnet["cidr"]})"]'
        ])
        
        # Add route tables
        for rt in vpc['route_tables']:
            if subnet['id'] in rt.get('subnet_associations', []):
                self._add_route_table(rt, subnet_id)
        
        # Add security groups
        for sg in vpc['security_groups']:
            self._add_security_group(sg, subnet_id)
            
        self.diagram.append('            end')

    def _add_route_table(self, rt: Dict, subnet_id: str) -> None:
        """Add route table to diagram."""
        rt_id = rt['id'].replace('-', '_')
        routes_str = '<br/>'.join([
            f"- {route['destination']} → {route['target']}"
            for route in rt['routes']
        ])
        
        self.diagram.extend([
            f'                rt_{rt_id}["Route Table<br/>{routes_str}"]',
            f'                rt_{rt_id} --> subnet_{subnet_id}'
        ])

    def _add_security_group(self, sg: Dict, subnet_id: str) -> None:
        """Add security group to diagram."""
        sg_id = sg['id'].replace('-', '_')
        rules_str = '<br/>'.join([
            f"- {rule['protocol'].upper()} {rule['port_range']} from {', '.join(rule['sources'])}"
            for rule in sg['rules_ingress']
        ])
        
        self.diagram.extend([
            f'                sg_{sg_id}["{sg["name"]}<br/>Inbound:<br/>{rules_str}"]',
            f'                sg_{sg_id} --> subnet_{subnet_id}'
        ])

    def _add_styling(self) -> None:
        """Add styling classes to diagram."""
        self.diagram.extend([
            '    %% Styling',
            '    classDef vpc fill:#f5f5f5,stroke:#333,stroke-width:2px',
            '    classDef az fill:#e6f3ff,stroke:#333,stroke-width:1px',
            '    classDef subnet fill:#fff,stroke:#333,stroke-width:1px',
            '    classDef component fill:#fff,stroke:#666,stroke-width:1px,stroke-dasharray: 5 5',
            '',
            '    %% Apply styles',
            '    class vpc vpc',
            '    class az1 az',
            '    class pub_subnet,priv_subnet subnet',
            '    class pub_rt,web_sg,igw component'
        ])

def main():
    # Sample usage
    with open('network_data.json', 'r') as f:
        network_data = json.load(f)
    
    generator = NetworkDiagramGenerator(network_data)
    mermaid_diagram = generator.generate_diagram()
    
    # Print the diagram
    print(mermaid_diagram)
    
    # Optionally save to file
    with open('network_diagram.mmd', 'w') as f:
        f.write(mermaid_diagram)

if __name__ == "__main__":
    main()
