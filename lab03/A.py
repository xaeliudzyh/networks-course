#!/usr/bin/env python3
"""
Однопоточный HTTP-сервер (store-and-forward style).
Принимает ровно один клиент (запрос) и закрывается.

Запуск:
    python3 simple_http_server.py <port>
Например:
    python3 simple_http_server.py 8080
"""

import sys
import socket
import os
import mimetypes

def make_http_response_headers(status_code: int, content_length: int, content_type: str) -> bytes:
    """
    Сформировать статусную строку и заголовки HTTP/1.0.
    Возвращает готовые байты, которые предшествуют телу сообщения.
    """
    reason = {
        200: "OK",
        404: "Not Found",
        500: "Internal Server Error"
    }.get(status_code, "Unknown")
    headers = [
        f"HTTP/1.0 {status_code} {reason}",
        f"Content-Type: {content_type}",
        f"Content-Length: {content_length}",
        "Connection: close",       # мы закрываем соединение после ответа
        "",                        # пустая строка означает конец блока заголовков
        ""
    ]
    return ("\r\n".join(headers)).encode('utf-8')

def serve_once(listen_port: int):
    """
    Запускаем сервер, принимаем ровно одно соединение, обрабатываем запрос и выходим.
    """
    # 1. Создаем TCP-сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", listen_port))
    server_socket.listen(1)
    print(f"[INFO] Simple HTTP server listening on port {listen_port} ...")

    # 2. Ждем ровно одного клиента
    conn, addr = server_socket.accept()
    print(f"[INFO] Connection from {addr}")

    try:
        # 3. Считываем HTTP-запрос (считать до двойного CRLF или пока данные приходят)
        request_data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            request_data += chunk
            # если мы увидели конец заголовков "\r\n\r\n", можно остановиться
            if b"\r\n\r\n" in request_data:
                break

        request_text = request_data.decode('utf-8', errors='ignore')
        # 4. Парсим первую строку вида "GET /path HTTP/1.0"
        request_lines = request_text.splitlines()
        if len(request_lines) == 0:
            print("[WARN] Пустой запрос от клиента")
            return

        request_line = request_lines[0]
        print(f"[DEBUG] request_line = {request_line}")

        parts = request_line.split()
        if len(parts) < 2 or parts[0].upper() != "GET":
            # Если не GET — возвращаем 500
            resp_head = make_http_response_headers(500, 0, "text/plain")
            conn.sendall(resp_head + b"500 Internal Server Error")
            return

        raw_path = parts[1]  # например, "/index.html" или "/"
        # Удалим ведущий "/"
        if raw_path.startswith("/"):
            raw_path = raw_path[1:]
        if raw_path == "":
            raw_path = "index.html"  # по умолчанию

        # 5. Проверяем наличие файла
        if not os.path.isfile(raw_path):
            # 404
            body = f"<html><body><h1>404 Not Found</h1><p>File {raw_path} not found.</p></body></html>".encode('utf-8')
            resp_head = make_http_response_headers(404, len(body), "text/html")
            conn.sendall(resp_head + body)
            print(f"[INFO] 404: {raw_path} not found")
        else:
            # 200: читаем файл и отдаем
            try:
                # Определяем mime-тип
                content_type, _ = mimetypes.guess_type(raw_path)
                if content_type is None:
                    content_type = "application/octet-stream"

                with open(raw_path, "rb") as f:
                    content = f.read()

                resp_head = make_http_response_headers(200, len(content), content_type)
                conn.sendall(resp_head + content)
                print(f"[INFO] 200: Served {raw_path} ({len(content)} bytes)")
            except Exception as e:
                # если произошла внутренняя ошибка чтения
                body = f"<html><body><h1>500 Internal Server Error</h1><p>{e}</p></body></html>".encode('utf-8')
                resp_head = make_http_response_headers(500, len(body), "text/html")
                conn.sendall(resp_head + body)
                print(f"[ERROR] Failed to read/send {raw_path}: {e}")

    finally:
        conn.close()
        server_socket.close()
        print("[INFO] Server shutdown.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python3 simple_http_server.py <port>")
        sys.exit(1)
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Порт должен быть целым числом.")
        sys.exit(1)

    serve_once(port)
