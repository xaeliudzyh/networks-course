import socket

HOST = '::'
PORT = 12345

with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)
    print(f"Сервер IPv6 запущен на [{HOST}]:{PORT}")

    conn, addr = server_sock.accept()
    with conn:
        print(f"Клиент подключился: {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                print("Клиент отключился.")
                break

            text = data.decode('utf-8')
            print(f"Получено от клиента: {text}")

            resp = text.upper().encode('utf-8')
            conn.sendall(resp)