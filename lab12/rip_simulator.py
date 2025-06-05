import json
import random
import copy
from typing import Dict, Tuple, List

INFINITY = 9999

class Router:
    def __init__(self, ip: str, neighbors: List[str]):
        self.ip = ip
        self.neighbors = neighbors[:]
        # routing_table[destination] = (next_hop, metric)
        self.routing_table: Dict[str, Tuple[str,int]] = {}
        self.routing_table[self.ip] = (self.ip, 0)
        for nb in neighbors:
            self.routing_table[nb] = (nb, 1)

    def send_update(self) -> Dict[str, Tuple[str,int]]:
        return copy.deepcopy(self.routing_table)

    def process_update(self, neighbor_ip: str, neighbor_table: Dict[str, Tuple[str,int]]):
        for dest, (nb_next_hop, nb_metric) in neighbor_table.items():
            if dest == self.ip:
                continue
            via_metric = nb_metric + 1
            if dest not in self.routing_table or via_metric < self.routing_table[dest][1]:
                self.routing_table[dest] = (neighbor_ip, via_metric)

def random_topology(n: int, avg_degree: int = 2) -> Dict[str, List[str]]:
    ips = [f"R{i+1}" for i in range(n)]
    neighbors: Dict[str, List[str]] = {ip: [] for ip in ips}
    for i in range(n-1):
        a, b = ips[i], ips[i+1]
        neighbors[a].append(b)
        neighbors[b].append(a)
    total_edges = n * avg_degree // 2
    existing = {(min(a,b), max(a,b)) for a in neighbors for b in neighbors[a]}
    while len(existing) < total_edges:
        a, b = random.sample(ips, 2)
        key = (min(a,b), max(a,b))
        if key not in existing:
            neighbors[a].append(b)
            neighbors[b].append(a)
            existing.add(key)

    return neighbors

def simulate_rip(routers: Dict[str, Router], verbose: bool = False):
    step = 0
    while True:
        step += 1
        updated = False

        sent_vectors: Dict[str, Dict[str, Tuple[str,int]]] = {}
        for ip, router in routers.items():
            sent_vectors[ip] = router.send_update()

        for ip, router in routers.items():
            for nb in router.neighbors:
                neighbor_table = sent_vectors[nb]
                old_table = copy.deepcopy(router.routing_table)
                router.process_update(nb, neighbor_table)
                if router.routing_table != old_table:
                    updated = True

        if verbose:
            print(f"\n--- Simulation step {step} ---")
            for ip, router in routers.items():
                print(f"Router {ip} table:")
                print("[Destination]  [NextHop]  [Metric]")
                for dest, (nh, m) in sorted(router.routing_table.items()):
                    print(f"{dest:12s} {nh:8s} {m:6d}")
                print()

        if not updated:
            break

def print_final_tables(routers: Dict[str, Router]):
    print("\n=== Final Routing Tables ===")
    for ip, router in routers.items():
        print(f"\nFinal state of router {ip} table:")
        print("[Source]        [Destination]    [NextHop]    [Metric]")
        for dest, (nh, m) in sorted(router.routing_table.items()):
            print(f"{ip:14s} {dest:14s} {nh:8s} {m:8d}")

def main():
    # {
    #   "routers": [
    #     {"ip": "R1", "neighbors":["R2","R3"]},
    #     {"ip": "R2", "neighbors":["R1","R4"]},
    #     ...
    #   ]
    # }
    # with open("topology.json", "r") as f:
    #     data = json.load(f)
    # routers = {r["ip"]: Router(r["ip"], r["neighbors"]) for r in data["routers"]}

    neighbors = random_topology(n=5, avg_degree=2)
    routers = {ip: Router(ip, neighbors[ip]) for ip in neighbors}
    simulate_rip(routers, verbose=True)
    print_final_tables(routers)

if __name__ == "__main__":
    main()