import socket
import time

def udp_ping_client(server_host: str = "127.0.0.1", server_port: int = 12000):
    addr = (server_host, server_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)

    for seq in range(1, 11):
        send_time = time.time()
        msg = f"Ping {seq} {send_time}"
        sock.sendto(msg.encode(), addr)

        try:
            data, _ = sock.recvfrom(4096)
            recv_time = time.time()
            rtt = recv_time - send_time
            print(f"Received: {data.decode()} | RTT = {rtt:.6f} s")
        except socket.timeout:
            print("Request timed out")
        time.sleep(0.1)

    sock.close()

if __name__ == "__main__":
    udp_ping_client(server_host="127.0.0.1", server_port=12000)
