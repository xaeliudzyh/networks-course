import sys
import socket

def http_get(server_host: str, server_port: int, filename: str):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_host, server_port))
    except Exception as e:
        print(f"[ERROR] Не удалось подключиться к {server_host}:{server_port}: {e}")
        return
    if not filename.startswith("/"):
        filename = "/" + filename
    request_lines = [
        f"GET {filename} HTTP/1.0",
        f"Host: {server_host}",
        "",
        ""
    ]
    request_data = "\r\n".join(request_lines).encode('utf-8')
    client_socket.sendall(request_data)
    response = b""
    try:
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response += chunk
    except Exception as e:
        print(f"[ERROR] Ошибка при чтении ответа: {e}")
    finally:
        client_socket.close()
    sys.stdout.buffer.write(response)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("ne xvataet arg: python3 simple_http_client.py <server_host> <server_port> <filename>")
        sys.exit(1)
    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        sys.exit(1)
    fname = sys.argv[3]
    http_get(host, port, fname)
