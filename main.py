import ipaddress
import json
from typing import List, Dict

def generate_subnets(base_network: str, subnet_count: int) -> List[ipaddress.IPv4Network]:
    network = ipaddress.ip_network(base_network)
    return list(network.subnets(prefixlen_diff=(network.prefixlen + (subnet_count - 1).bit_length()) - network.prefixlen))[:subnet_count]

def get_node_ip(subnet: ipaddress.IPv4Network, node_index: int) -> str:
    return str(list(subnet.hosts())[node_index - 1])

def get_tcp_ip_settings(subnet: ipaddress.IPv4Network, node_indices: List[int]) -> List[Dict[str, str]]:
    settings = []
    gateway = str(list(subnet.hosts())[0])
    mask = str(subnet.netmask)
    for idx in node_indices:
        ip = get_node_ip(subnet, idx)
        settings.append({
            "ip": ip,
            "subnet_mask": mask,
            "gateway": gateway
        })
    return settings

def generate_static_route(dest_subnet: ipaddress.IPv4Network, via_subnet: ipaddress.IPv4Network) -> str:
    gateway = str(list(via_subnet.hosts())[0])
    return f"route add {dest_subnet.network_address} mask {dest_subnet.netmask} {gateway}"

def process_variant(data: Dict):
    base_network = "192.168.0.0/16"
    N, S, H = data['N'], data['S'], data['H']
    A, B = data['A'], data['B']
    a_nodes, b_nodes = data['a_nodes'], data['b_nodes']

    subnets = generate_subnets(base_network, S)

    result = {
        "variant_input": data,
        "tcpip_settings": {},
        "static_routes": {},
    }

    # Task 1: IPs for selected nodes
    task1 = {
        f"subnet_{A}": [get_node_ip(subnets[A - 1], idx) for idx in a_nodes],
        f"subnet_{B}": [get_node_ip(subnets[B - 1], idx) for idx in b_nodes]
    }

    # Task 2: TCP/IP for subnet A and B
    result['tcpip_settings'][f"subnet_{A}"] = get_tcp_ip_settings(subnets[A - 1], a_nodes)
    result['tcpip_settings'][f"subnet_{B}"] = get_tcp_ip_settings(subnets[B - 1], b_nodes)

    # Subnet C = the one not in A or B
    all_indices = {1, 2, 3}
    C = list(all_indices - {A, B})[0]
    c_nodes = [1, 2, 3]  # assuming first 3 nodes in C

    result['tcpip_settings'][f"subnet_{C}"] = get_tcp_ip_settings(subnets[C - 1], c_nodes)
    result['static_routes'][f"to_subnet_{C}_via_{A}"] = generate_static_route(subnets[C - 1], subnets[A - 1])
    result['static_routes'][f"to_subnet_{C}_via_{B}"] = generate_static_route(subnets[C - 1], subnets[B - 1])

    return task1, result['tcpip_settings'], result['static_routes']

if __name__ == "__main__":
    user_input = {
        "N": 200,
        "S": 3,
        "H": 120,
        "A": 1,
        "B": 2,
        "a_nodes": [1, 2, 3],
        "b_nodes": [4, 5, 6]
    }

    task1_output, tcpip_output, static_output = process_variant(user_input)

    print("--Sample input--")
    print(f"number of nodes: {user_input['N']}, number of subnets: {user_input['S']}, nodes in subnets: {user_input['H']}")
    print(f"subnet indexes - A: {user_input['A']}, B: {user_input['B']}")
    print(f"subnet node indexes to calculate - A nodes: {user_input['a_nodes']}, B nodes: {user_input['b_nodes']}")

    print("Task 1: Node IP Addresses")
    for subnet, ips in task1_output.items():
        print(f"{subnet}: {', '.join(ips)}")

    print("\nTask 2: TCP/IP Settings for Subnet A and B")
    for subnet, configs in tcpip_output.items():
        if subnet != "subnet_3":
            print(f"{subnet}:")
            for i, cfg in enumerate(configs, 1):
                print(f"  Node {i}: IP={cfg['ip']}, Mask={cfg['subnet_mask']}, Gateway={cfg['gateway']}")

    print("\nTask 3: Static Routes and TCP/IP Settings for Subnet C")
    for route_label, cmd in static_output.items():
        print(f"{route_label}: {cmd}")

    print("subnet_3:")
    for i, cfg in enumerate(tcpip_output["subnet_3"], 1):
        print(f"  Node {i}: IP={cfg['ip']}, Mask={cfg['subnet_mask']}, Gateway={cfg['gateway']}")

    # Save to JSON
    with open("results.json", "w") as f:
        json.dump({
            "node_ip_addresses": task1_output,
            "tcpip_settings": tcpip_output,
            "static_routes": static_output
        }, f, indent=2)