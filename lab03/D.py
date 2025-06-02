import sys
import socket
import threading
import os
import mimetypes

def make_http_response_headers(status_code: int, content_length: int, content_type: str) -> bytes:
    reason = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error"
    }.get(status_code, "Unknown")
    headers = [
        f"HTTP/1.0 {status_code} {reason}",
        f"Content-Type: {content_type}",
        f"Content-Length: {content_length}",
        "Connection: close",
        "",
        ""
    ]
    return ("\r\n".join(headers)).encode('utf-8')

class LimitedThreadHTTPServer:
    def __init__(self, port: int, max_workers: int):
        self.port = port
        self.max_workers = max_workers

        # Семафор, который не позволит запустить больше max_workers потоков
        self.semaphore = threading.Semaphore(max_workers)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("", port))
        self.server_socket.listen(5)
        print(f"[INFO] Limited HTTP server listening on port {port}, max_workers={max_workers}")

    def serve_forever(self):
        try:
            while True:
                conn, addr = self.server_socket.accept()
                print(f"[INFO] Incoming connection from {addr}, waiting for a free worker...")
                self.semaphore.acquire()
                print(f"[INFO] {addr} allowed to proceed.")
                t = threading.Thread(
                    target=self._thread_worker,
                    args=(conn, addr),
                    daemon=True
                )
                t.start()

        except KeyboardInterrupt:
            print("\n[INFO] Shutting down server (KeyboardInterrupt).")
        finally:
            self.server_socket.close()
            print("[INFO] Server socket closed.")

    def _thread_worker(self, conn: socket.socket, addr):
        thread_name = threading.current_thread().name
        print(f"[THREAD {thread_name}] Handling {addr}")
        try:
            request_data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                if b"\r\n\r\n" in request_data:
                    break

            request_text = request_data.decode('utf-8', errors='ignore')
            request_lines = request_text.splitlines()
            if not request_lines:
                return

            request_line = request_lines[0]
            parts = request_line.split()
            if len(parts) < 2 or parts[0].upper() != "GET":
                resp_head = make_http_response_headers(500, 0, "text/plain")
                conn.sendall(resp_head + b"500 Internal Server Error")
                return

            raw_path = parts[1]
            if raw_path.startswith("/"):
                raw_path = raw_path[1:]
            if raw_path == "":
                raw_path = "index.html"

            if not os.path.isfile(raw_path):
                body = f"<html><body><h1>404 Not Found</h1><p>File {raw_path} not found.</p></body></html>".encode('utf-8')
                resp_head = make_http_response_headers(404, len(body), "text/html")
                conn.sendall(resp_head + body)
                print(f"[THREAD {thread_name}] 404: {raw_path}")
            else:
                try:
                    content_type, _ = mimetypes.guess_type(raw_path)
                    if content_type is None:
                        content_type = "application/octet-stream"
                    with open(raw_path, "rb") as f:
                        content = f.read()

                    resp_head = make_http_response_headers(200, len(content), content_type)
                    conn.sendall(resp_head + content)
                    print(f"[THREAD {thread_name}] 200: Served {raw_path}")
                except Exception as e:
                    body = f"<html><body><h1>500 Internal Server Error</h1><p>{e}</p></body></html>".encode('utf-8')
                    resp_head = make_http_response_headers(500, len(body), "text/html")
                    conn.sendall(resp_head + body)
                    print(f"[THREAD {thread_name}] ERROR: {e}")
        finally:
            conn.close()
            print(f"[THREAD {thread_name}] Closed connection.")
            self.semaphore.release()
            print(f"[THREAD {thread_name}] Released a worker slot. Available slots: {self.semaphore._value}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        max_workers = int(sys.argv[2])
        if max_workers <= 0:
            raise ValueError()
    except ValueError:
        sys.exit(1)

    server = LimitedThreadHTTPServer(port, max_workers)
    server.serve_forever()
