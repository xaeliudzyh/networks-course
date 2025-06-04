import socket
import time
import statistics

def udp_ping_client_with_stats(server_host: str = "127.0.0.1", server_port: int = 12000):
    addr = (server_host, server_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)

    rtts = []
    sent = 10
    received = 0

    for seq in range(1, 11):
        send_time = time.time()
        msg = f"Ping {seq} {send_time}"
        sock.sendto(msg.encode(), addr)

        try:
            data, _ = sock.recvfrom(4096)
            recv_time = time.time()
            rtt = recv_time - send_time
            rtts.append(rtt)
            received += 1
            print(f"Reply from {server_host}:{server_port}: seq={seq}  RTT={rtt*1000:.3f} ms")
        except socket.timeout:
            print(f"Request timed out for seq={seq}")

        time.sleep(0.1)

    sock.close()

    lost = sent - received
    loss_pct = (lost / sent) * 100

    print("\n--- Ping statistics ---")
    print(f"{sent} packets transmitted, {received} packets received, {loss_pct:.0f}% packet loss")

    if rtts:
        rtts_ms = [r * 1000 for r in rtts]
        rtt_min = min(rtts_ms)
        rtt_max = max(rtts_ms)
        rtt_avg = statistics.mean(rtts_ms)
        print(f"rtt min/avg/max = {rtt_min:.3f} ms / {rtt_avg:.3f} ms / {rtt_max:.3f} ms")
    else:
        print("No RTT data (all packets lost).")


if __name__ == "__main__":
    udp_ping_client_with_stats(server_host="127.0.0.1", server_port=12000)
