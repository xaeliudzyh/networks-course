import socket
import threading
import tkinter as tk
from tkinter import ttk
from scapy.all import sniff
from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from collections import defaultdict

class PacketInfo:
    def __init__(self, pkt):
        self.pkt = pkt
        self.timestamp = pkt.time
        if pkt.haslayer(IP):
            self.ipv = 4
            ip_layer = pkt[IP]
        elif pkt.haslayer(IPv6):
            self.ipv = 6
            ip_layer = pkt[IPv6]
        else:
            self.ipv = None
            ip_layer = None

        if ip_layer:
            self.src_ip = ip_layer.src
            self.dst_ip = ip_layer.dst
            self.size = len(pkt)
        else:
            self.src_ip = None
            self.dst_ip = None
            self.size = len(pkt)

        if pkt.haslayer(TCP):
            self.proto = 'TCP'
            l4 = pkt[TCP]
            self.src_port = l4.sport
            self.dst_port = l4.dport
        elif pkt.haslayer(UDP):
            self.proto = 'UDP'
            l4 = pkt[UDP]
            self.src_port = l4.sport
            self.dst_port = l4.dport
        else:
            self.proto = None
            self.src_port = None
            self.dst_port = None

    def summary(self):
        return f"{self.src_ip} → {self.dst_ip} ({self.size} B)"

    def details(self):
        lines = []
        lines.append(f"Protocol     : {self.proto}")
        lines.append(f"IP version   : {self.ipv}")
        if self.src_port is not None:
            lines.append(f"Source Port  : {self.src_port}")
            lines.append(f"Dest Port    : {self.dst_port}")
        lines.append(f"Size         : {self.size} bytes")
        lines.append(f"Src IP       : {self.src_ip}")
        lines.append(f"Dst IP       : {self.dst_ip}")
        return "\n".join(lines)

class TrafficSnifferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Net traffic")

        top_frame = ttk.Frame(root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        mid_frame = ttk.Frame(root)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top_frame, text="Интерфейс (Leave empty for all):").pack(side=tk.LEFT)
        self.iface_entry = ttk.Entry(top_frame, width=15)
        self.iface_entry.pack(side=tk.LEFT, padx=5)
        self.iface_entry.insert(0, "")

        self.start_btn = ttk.Button(top_frame, text="Старт", command=self.start_sniffer)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(top_frame, text="Стоп", command=self.stop_sniffer, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="full")
        modes = [("Полный", "full"), ("По портам", "by_port"), ("По портам исходящей", "src_port")]
        for txt, val in modes:
            ttk.Radiobutton(top_frame, text=txt, variable=self.mode_var, value=val, command=self.update_display).pack(side=tk.LEFT)

        self.in_label = ttk.Label(bottom_frame, text="Входящий: 0 B")
        self.in_label.pack(side=tk.LEFT, padx=10)
        self.out_label = ttk.Label(bottom_frame, text="Исходящий: 0 B")
        self.out_label.pack(side=tk.LEFT, padx=10)

        columns = ("summary",)
        self.tree = ttk.Treeview(mid_frame, columns=columns, show="headings")
        self.tree.heading("summary", text="Пакеты / Порты")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_select)
        self.hint = tk.Text(mid_frame, height=6, state=tk.DISABLED)
        self.hint.pack(fill=tk.X, pady=5)
        self.packets = []
        self.in_bytes = 0
        self.out_bytes = 0
        self.by_port_in = defaultdict(int)
        self.by_port_out = defaultdict(int)

        self.sniff_thread = None
        self.running = False

    def start_sniffer(self):
        iface = self.iface_entry.get().strip() or None
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.sniff_thread = threading.Thread(target=self.sniff_packets, args=(iface,), daemon=True)
        self.sniff_thread.start()

    def stop_sniffer(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def sniff_packets(self, iface):
        def proc(pkt):
            if not self.running:
                return False
            pi = PacketInfo(pkt)
            self.packets.append(pi)
            if not hasattr(self, 'local_ip'):
                self.local_ip = self.determine_local_ip(pi.src_ip, pi.dst_ip)
            direction = 'out' if pi.src_ip == self.local_ip else 'in'
            if direction == 'in':
                self.in_bytes += pi.size
                if pi.dst_port:
                    self.by_port_in[pi.dst_port] += pi.size
            else:
                self.out_bytes += pi.size
                if pi.dst_port:
                    self.by_port_out[pi.dst_port] += pi.size
            self.root.after(1, self.update_display)
            return True

        sniff(iface=iface, prn=proc, store=False, stop_filter=lambda x: not self.running)

    def determine_local_ip(self, a, b):
        for c in (a, b):
            if c.startswith("192.") or c.startswith("10.") or c.startswith("172."):
                return c
        return a

    def update_display(self):
        mode = self.mode_var.get()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.in_label.config(text=f"Входящий: {self.in_bytes} B")
        self.out_label.config(text=f"Исходящий: {self.out_bytes} B")

        if mode == "full":
            for idx, pi in enumerate(self.packets, start=1):
                self.tree.insert("", "end", iid=str(idx), values=(pi.summary(),))
        elif mode == "by_port":
            ports = set(list(self.by_port_in.keys()) + list(self.by_port_out.keys()))
            for p in sorted(ports):
                in_b = self.by_port_in.get(p, 0)
                out_b = self.by_port_out.get(p, 0)
                text = f"Port {p} | In: {in_b} B | Out: {out_b} B"
                self.tree.insert("", "end", iid=f"port_{p}", values=(text,))
        elif mode == "src_port":
            return

    def on_select(self, event):
        mode = self.mode_var.get()
        sel = self.tree.selection()
        if not sel:
            return
        key = sel[0]
        if mode == "full" and key.isdigit():
            idx = int(key) - 1
            if 0 <= idx < len(self.packets):
                details = self.packets[idx].details()
                self.hint.config(state=tk.NORMAL)
                self.hint.delete(1.0, tk.END)
                self.hint.insert(tk.END, details)
                self.hint.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficSnifferGUI(root)
    root.mainloop()