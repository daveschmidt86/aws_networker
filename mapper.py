import boto3
import json
from typing import Dict, List, Any

def get_network_resources(event: Dict, context: Any) -> Dict:
    """
    Collects AWS networking resources and structures them for Mermaid diagram generation.
    Returns a dictionary with organized network infrastructure data.
    """
    ec2 = boto3.client('ec2')
    
    def get_name_tag(tags: List[Dict]) -> str:
        """Extract Name tag from resource tags."""
        if not tags:
            return "Unnamed"
        return next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), "Unnamed")

    # Collect VPCs
    vpcs_response = ec2.describe_vpcs()
    vpcs = []
    for vpc in vpcs_response['Vpcs']:
        vpc_data = {
            'id': vpc['VpcId'],
            'name': get_name_tag(vpc.get('Tags', [])),
            'cidr': vpc['CidrBlock'],
            'subnets': [],
            'route_tables': [],
            'security_groups': []
        }
        vpcs.append(vpc_data)
    
    # Collect Subnets for each VPC
    for vpc in vpcs:
        subnets_response = ec2.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc['id']]}]
        )
        for subnet in subnets_response['Subnets']:
            subnet_data = {
                'id': subnet['SubnetId'],
                'name': get_name_tag(subnet.get('Tags', [])),
                'cidr': subnet['CidrBlock'],
                'az': subnet['AvailabilityZone'],
                'public': subnet.get('MapPublicIpOnLaunch', False)
            }
            vpc['subnets'].append(subnet_data)
    
    # Collect Route Tables
    for vpc in vpcs:
        route_tables_response = ec2.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc['id']]}]
        )
        for rt in route_tables_response['RouteTables']:
            routes = []
            for route in rt['Routes']:
                route_data = {
                    'destination': route.get('DestinationCidrBlock', 'Unknown'),
                    'target': next((v for k, v in route.items() if k.endswith('Id')), 'Unknown')
                }
                routes.append(route_data)
            
            rt_data = {
                'id': rt['RouteTableId'],
                'name': get_name_tag(rt.get('Tags', [])),
                'routes': routes,
                'subnet_associations': [assoc['SubnetId'] for assoc in rt.get('Associations', []) if 'SubnetId' in assoc]
            }
            vpc['route_tables'].append(rt_data)
    
    # Collect Security Groups
    for vpc in vpcs:
        sg_response = ec2.describe_security_groups(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc['id']]}]
        )
        for sg in sg_response['SecurityGroups']:
            rules_ingress = []
            for rule in sg['IpPermissions']:
                port_range = f"{rule.get('FromPort', 'All')}-{rule.get('ToPort', 'All')}"
                sources = [ip_range['CidrIp'] for ip_range in rule.get('IpRanges', [])]
                rules_ingress.append({
                    'protocol': rule.get('IpProtocol', 'All'),
                    'port_range': port_range,
                    'sources': sources
                })
            
            sg_data = {
                'id': sg['GroupId'],
                'name': sg['GroupName'],
                'description': sg['Description'],
                'rules_ingress': rules_ingress
            }
            vpc['security_groups'].append(sg_data)
    
    # Create final structure
    network_data = {
        'timestamp': context.aws_request_id,
        'region': ec2.meta.region_name,
        'vpcs': vpcs
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(network_data, default=str)
    }
