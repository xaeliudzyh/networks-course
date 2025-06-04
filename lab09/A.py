import psutil
import socket
import struct

def ipv4_netmask_from_prefix(prefix_length: int) -> str:
    mask = (0xffffffff >> (32 - prefix_length)) << (32 - prefix_length)
    return socket.inet_ntoa(struct.pack(">I", mask))


addrs = psutil.net_if_addrs()
stats = psutil.net_if_stats()

for iface_name, iface_addrs in addrs.items():
    if iface_name not in stats or not stats[iface_name].isup:
        continue

    ipv4_info = [addr for addr in iface_addrs if addr.family == socket.AF_INET]
    if not ipv4_info:
        continue

    for addr in ipv4_info:
        ip = addr.address
        prefix_len = addr.netmask
        try:
            mask = prefix_len
        except Exception:
            mask = ipv4_netmask_from_prefix(int(prefix_len))

        print(f"Интерфейс: {iface_name}")
        print(f"  IPv4-адрес: {ip}")
        print(f"  Маска сети: {mask}")
        print()