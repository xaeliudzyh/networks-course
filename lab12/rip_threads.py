import json
import random
import socket
import threading
import time
from typing import Dict, Tuple, List

INFINITY = 9999
BASE_PORT = 50000
print_lock = threading.Lock()


class RIPRouterThread(threading.Thread):
    def __init__(self, ip: str, neighbors: List[str], all_ips: List[str], idx: int):
        super().__init__(daemon=True)
        self.ip = ip
        self.neighbors = neighbors
        self.idx = idx
        self.port = BASE_PORT + idx
        self.address = ('127.0.0.1', self.port)

        self.routing_table: Dict[str, Tuple[str,int]] = {}
        self.routing_table[self.ip] = (self.ip, 0)
        for nb in neighbors:
            self.routing_table[nb] = (nb, 1)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.address)
        self.sock.settimeout(1.0)

        self.all_ips = all_ips
        self.updated = True

    def run(self):
        rounds = 0
        while True:
            rounds += 1
            if not self.updated and rounds > 3:
                break
            self.updated = False
            packet = json.dumps(self.routing_table).encode('utf-8')
            for nb in self.neighbors:
                nb_idx = self.all_ips.index(nb)
                nb_addr = ('127.0.0.1', BASE_PORT + nb_idx)
                try:
                    self.sock.sendto(packet, nb_addr)
                except:
                    pass

            t0 = time.time()
            while time.time() - t0 < 1.0:
                try:
                    data, addr = self.sock.recvfrom(4096)
                except socket.timeout:
                    break
                except ConnectionResetError:
                    continue
                try:
                    neighbor_table = json.loads(data.decode('utf-8'))
                except:
                    continue
                nb_ip = None
                for ip in self.all_ips:
                    if BASE_PORT + self.all_ips.index(ip) == addr[1]:
                        nb_ip = ip
                        break
                if not nb_ip:
                    continue

                for dest, (nh, m) in neighbor_table.items():
                    if dest == self.ip:
                        continue
                    via_m = m + 1
                    if dest not in self.routing_table or via_m < self.routing_table[dest][1]:
                        self.routing_table[dest] = (nb_ip, via_m)
                        self.updated = True

        with print_lock:
            print(f"\nFinal state of router {self.ip} (port {self.port}):")
            print("[Destination]  [NextHop]  [Metric]")
            for dest, (nh, m) in sorted(self.routing_table.items()):
                print(f"{dest:12s} {nh:8s} {m:6d}")
        self.sock.close()


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


def main():
    n = 5
    neighbors = random_topology(n, avg_degree=2)
    all_ips = list(neighbors.keys())

    threads = []
    for idx, ip in enumerate(all_ips):
        r = RIPRouterThread(ip, neighbors[ip], all_ips, idx)
        threads.append(r)
        r.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()