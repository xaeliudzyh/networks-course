import socket
import sys
import ssl
import base64

def recv_all(sock):
    data = b""
    while True:
        chunk = sock.recv(1024)
        data += chunk
        lines = data.split(b"\r\n")
        if len(lines) >= 2 and len(lines[-2]) >= 4 and lines[-2][:3].isdigit() and lines[-2][3:4] == b" ":
            break
        if not chunk:
            break
    return data

def send_cmd(sock, cmd):
    sock.sendall(cmd.encode())
    reply = recv_all(sock).decode(errors="ignore")
    print(f">>> {cmd.strip()}")
    print(f"<<< {reply.strip()}")
    return reply

def main():
    if len(sys.argv) < 5:
        print("Usage: python smtp_client.py <smtp_host> <smtp_port> <recipient> <message_file.txt>")
        sys.exit(1)

    smtp_host = sys.argv[1]
    smtp_port = int(sys.argv[2])
    recipient = sys.argv[3]
    message_file = sys.argv[4]

    sender = "tsagol10@mail.ru"
    username = "tsagol10@mail.ru"
    password = "************"
    with open(message_file, "r", encoding="utf-8") as f:
        body = f.read()
    plain_sock = socket.create_connection((smtp_host, smtp_port), timeout=10)
    greeting = recv_all(plain_sock).decode(errors="ignore")
    print(f"<<< {greeting.strip()}")
    send_cmd(plain_sock, "EHLO localhost\r\n")
    send_cmd(plain_sock, "STARTTLS\r\n")
    context = ssl.create_default_context()
    tls_sock = context.wrap_socket(plain_sock, server_hostname=smtp_host)
    send_cmd(tls_sock, "EHLO localhost\r\n")
    send_cmd(tls_sock, "AUTH LOGIN\r\n")
    send_cmd(tls_sock, base64.b64encode(username.encode()).decode() + "\r\n")
    send_cmd(tls_sock, base64.b64encode(password.encode()).decode() + "\r\n")
    send_cmd(tls_sock, f"MAIL FROM:<{sender}>\r\n")
    send_cmd(tls_sock, f"RCPT TO:<{recipient}>\r\n")

    send_cmd(tls_sock, "DATA\r\n")
    data_lines = [
        f"Subject: Test via raw SMTP with TLS",
        f"From: {sender}",
        f"To: {recipient}",
        "",
        body
    ]
    data_str = "\r\n".join(data_lines) + "\r\n.\r\n"
    tls_sock.sendall(data_str.encode())
    reply = recv_all(tls_sock).decode(errors="ignore")
    print(f">>> (message data sent)\n<<< {reply.strip()}")
    send_cmd(tls_sock, "QUIT\r\n")
    tls_sock.close()

if __name__ == "__main__":
    main()
