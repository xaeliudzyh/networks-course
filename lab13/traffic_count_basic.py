from scapy.all import sniff
import threading
import time

class TrafficCounter:
    def __init__(self, iface=None):
        self.iface = iface
        self.lock = threading.Lock()
        self.in_bytes = 0
        self.out_bytes = 0

    def start(self):
        t = threading.Thread(target=self.sniff_traffic, daemon=True)
        t.start()

    def sniff_traffic(self):
        sniff(iface=self.iface, prn=self.process_packet, store=False)

    def process_packet(self, pkt):
        try:
            ip_layer = pkt.getlayer("IP")
            raw_len = len(pkt)
            if not hasattr(self, 'local_ip'):
                self.local_ip = self.get_local_ip(ip_layer.src, ip_layer.dst)
            src = ip_layer.src
            dst = ip_layer.dst
            with self.lock:
                if src == self.local_ip:
                    self.out_bytes += raw_len
                else:
                    self.in_bytes += raw_len
        except:
            pass

    def get_local_ip(self, a, b):
        for candidate in (a, b):
            if candidate.startswith("192.") or candidate.startswith("10.") or candidate.startswith("172."):
                return candidate
        return a

    def get_counts(self):
        with self.lock:
            return self.in_bytes, self.out_bytes

def main():
    print("=== Basic Traffic Counter ===")
    tc = TrafficCounter(iface=None)
    tc.start()
    try:
        while True:
            time.sleep(2)
            inp, outp = tc.get_counts()
            print(f"Incoming: {inp} bytes | Outgoing: {outp} bytes")
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()