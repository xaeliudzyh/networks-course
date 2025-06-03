import socket
import sys

def main():
    if len(sys.argv) < 4:
        print("Usage: python remote_exec_client.py <server_ip> <server_port> <command ...>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    cmd = " ".join(sys.argv[3:])

    sock = socket.create_connection((server_ip, server_port), timeout=10)

    cmd_bytes = cmd.encode('utf-8')
    sock.sendall(len(cmd_bytes).to_bytes(4, byteorder='big'))

    sock.sendall(cmd_bytes)

    raw_len = sock.recv(4)
    if not raw_len:
        print("[!] No response from server")
        sock.close()
        return
    resp_len = int.from_bytes(raw_len, byteorder='big')

    received = bytearray()
    while len(received) < resp_len:
        chunk = sock.recv(min(4096, resp_len - len(received)))
        if not chunk:
            break
        received.extend(chunk)

    print("=== Command output ===")
    print(received.decode('utf-8', errors='ignore'))

    sock.close()

if __name__ == "__main__":
    main()
