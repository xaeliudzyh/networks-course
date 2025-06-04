import socket
import random


def start_udp_echo_server(host: str = "0.0.0.0", port: int = 12000, loss_prob: float = 0.2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[Server] UDP echo server started on {host}:{port}, loss={loss_prob * 100:.0f}%\n")
    while True:
        data, addr = sock.recvfrom(4096)
        if not data:
            continue

        if random.random() < loss_prob:
            print(f"[Server] DROPPED packet from {addr!s} → {data.decode(errors='ignore')!r}")
            continue

        text = data.decode(errors="ignore")
        resp = text.upper().encode()
        sock.sendto(resp, addr)
        print(f"[Server] Echoed to {addr!s} : {resp.decode()}")


if __name__ == "__main__":
    start_udp_echo_server(host="0.0.0.0", port=12000, loss_prob=0.2)