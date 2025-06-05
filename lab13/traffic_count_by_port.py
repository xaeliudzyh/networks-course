from scapy.layers.inet import TCP, UDP, IP
from scapy.all import sniff
import threading
import time
from collections import defaultdict

class PortTrafficCounter:
    def __init__(self, iface=None):
        self.iface = iface
        self.lock = threading.Lock()
        self.in_by_port = defaultdict(int)
        self.out_by_port = defaultdict(int)

    def start(self):
        t = threading.Thread(target=self.sniff_traffic, daemon=True)
        t.start()

    def sniff_traffic(self):
        sniff(iface=self.iface, prn=self.process_packet, store=False)

    def process_packet(self, pkt):
        try:
            if not pkt.haslayer(IP):
                return
            ip_layer = pkt[IP]
            raw_len = len(pkt)
            if not hasattr(self, 'local_ip'):
                self.local_ip = self.determine_local_ip(ip_layer.src, ip_layer.dst)

            port = None
            direction = None
            if pkt.haslayer(TCP):
                l4 = pkt[TCP]
                if ip_layer.src == self.local_ip:
                    direction = 'out'
                    port = l4.dport
                else:
                    direction = 'in'
                    port = l4.dport
            elif pkt.haslayer(UDP):
                l4 = pkt[UDP]
                if ip_layer.src == self.local_ip:
                    direction = 'out'
                    port = l4.dport
                else:
                    direction = 'in'
                    port = l4.dport
            else:
                return

            with self.lock:
                if direction == 'in':
                    self.in_by_port[port] += raw_len
                else:
                    self.out_by_port[port] += raw_len
        except:
            pass

    def determine_local_ip(self, a, b):
        for c in (a, b):
            if c.startswith("192.") or c.startswith("10.") or c.startswith("172."):
                return c
        return a

    def get_port_counters(self):
        with self.lock:
            return dict(self.in_by_port), dict(self.out_by_port)

def main():
    print("=== Traffic Counter by Port ===")
    tc = PortTrafficCounter(iface=None)
    tc.start()
    try:
        while True:
            time.sleep(5)
            in_ports, out_ports = tc.get_port_counters()
            print("\n-- Incoming by Port --")
            for port, cnt in sorted(in_ports.items()):
                print(f"Port {port:5d}: {cnt:10d} bytes")
            print("-- Outgoing by Port --")
            for port, cnt in sorted(out_ports.items()):
                print(f"Port {port:5d}: {cnt:10d} bytes")
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()