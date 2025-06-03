import socket
import threading
import subprocess

HOST = "0.0.0.0"
PORT = 50000
BUFFER_SIZE = 4096

def handle_client(conn, addr):
    print(f"[+] Connected by {addr}")
    try:
        raw_len = conn.recv(4)
        if not raw_len:
            conn.close()
            return
        cmd_len = int.from_bytes(raw_len, byteorder='big')

        data = bytearray()
        while len(data) < cmd_len:
            chunk = conn.recv(min(BUFFER_SIZE, cmd_len - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        cmd = data.decode('utf-8', errors='ignore')
        print(f"[>] Executing command: {cmd}")

        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output = result.stdout
        resp_len = len(output)
        conn.sendall(resp_len.to_bytes(4, byteorder='big'))
        conn.sendall(output)
        print(f"[+] Sent {resp_len} bytes back to {addr}")

    except Exception as e:
        print(f"[!] Error while handling {addr}: {e}")
    finally:
        conn.close()
        print(f"[+] Connection with {addr} closed")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Remote exec server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    main()
