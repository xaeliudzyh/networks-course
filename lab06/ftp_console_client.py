#!/usr/bin/env python3
import socket
import os
import sys
import argparse

BUFFER_SIZE = 1024


class FTPClient:
    def __init__(self, server_host: str, server_port: int, user: str, passwd: str):
        self.server = (server_host, server_port)
        self.user = user
        self.passwd = passwd

        self.ctrl_sock = None

    def connect(self) -> None:
        print(f"[+] Подключаюсь к {self.server[0]}:{self.server[1]}…")

        self.ctrl_sock = socket.create_connection(self.server)

        greeting = self._recv_ctrl()
        print(f"[Сервер] {greeting.strip()}")

        self._login()  # USER/PASS и TYPE I

    def _recv_ctrl(self) -> str:
        data = b""

        while True:
            part = self.ctrl_sock.recv(BUFFER_SIZE)
            data += part
            if len(part) < BUFFER_SIZE:
                break
        return data.decode(errors="ignore")

    def _send_cmd(self, cmd: str) -> str:
        full_cmd = f"{cmd}\r\n".encode()
        self.ctrl_sock.sendall(full_cmd)
        return self._recv_ctrl()

    def _login(self) -> None:
        resp1 = self._send_cmd(f"USER {self.user}")
        # 331
        print(f"[Сервер] {resp1.strip()}")
        resp2 = self._send_cmd(f"PASS {self.passwd}")
        # 230
        print(f"[Сервер] {resp2.strip()}")
        resp3 = self._send_cmd("TYPE I")
        # "200 Type set to I"
        print(f"[Сервер] {resp3.strip()}")

    def _enter_pasv(self) -> tuple[str, int]:
        resp = self._send_cmd("PASV")
        start = resp.find("(") + 1
        end = resp.find(")")

        numbers = resp[start:end].split(",")
        nums = list(map(int, numbers))
        host = ".".join(map(str, nums[:4]))
        port = nums[4] * 256 + nums[5]

        return host, port

    @staticmethod
    def _recv_data_sock(dsock: socket.socket) -> bytes:
        data = b""
        while True:
            chunk = dsock.recv(BUFFER_SIZE)
            if not chunk:
                break
            data += chunk
        return data

    def list_files(self) -> None:
        host_data, port_data = self._enter_pasv()
        print(f"[+] Устанавливаю data-соединение для LIST → {host_data}:{port_data}")
        with socket.create_connection((host_data, port_data)) as data_sock:
            resp_list = self._send_cmd("LIST")
            print(f"[Сервер] {resp_list.strip()}")

            raw = self._recv_data_sock(data_sock)
            print("--- Список файлов/папок ---")
            print(raw.decode(errors="ignore").rstrip())
            print("---------------------------")


        final = self._recv_ctrl()
        print(f"[Сервер] {final.strip()}")

    def upload_file(self, local_path: str) -> None:
        if not os.path.isfile(local_path):
            print(f"[-] Ошибка: файл '{local_path}' не найден.")
            return

        filename = os.path.basename(local_path)
        host_data, port_data = self._enter_pasv()
        print(f"[+] Устанавливаю data-соединение для STOR → {host_data}:{port_data}")

        with socket.create_connection((host_data, port_data)) as data_sock:
            resp_stor = self._send_cmd(f"STOR {filename}")

            print(f"[Сервер] {resp_stor.strip()}")

            with open(local_path, "rb") as f:
                data_sock.sendfile(f)

        final = self._recv_ctrl()
        print(f"[Сервер] {final.strip()}")

    def download_file(self, remote_filename: str, save_as: str) -> None:
        host_data, port_data = self._enter_pasv()
        print(f"[+] Устанавливаю data-соединение для RETR → {host_data}:{port_data}")

        with socket.create_connection((host_data, port_data)) as data_sock:
            resp_retr = self._send_cmd(f"RETR {remote_filename}")

            print(f"[Сервер] {resp_retr.strip()}")

            file_bytes = self._recv_data_sock(data_sock)
            with open(save_as, "wb") as f:
                f.write(file_bytes)
            print(f"[+] Сохранено в '{save_as}'")

        final = self._recv_ctrl()
        print(f"[Сервер] {final.strip()}")

    def quit(self) -> None:
        if self.ctrl_sock:
            resp = self._send_cmd("QUIT")
            print(f"[Сервер] {resp.strip()}")
            self.ctrl_sock.close()
            self.ctrl_sock = None


def main():
    parser = argparse.ArgumentParser(description="Консольный FTP-клиент на сокетах")
    parser.add_argument("command",
                        choices=["ls", "upload", "download"],
                        help="ls – список, upload <локальный файл>, download <удалённый файл> [<сохранить как>]")
    parser.add_argument("filename", nargs="?", help="имя локального/удалённого файла")
    parser.add_argument("save_as", nargs="?", help="имя для сохранения при download")
    parser.add_argument("--host", default="ftp.dlptest.com", help="FTP-сервер (по умолчанию ftp.dlptest.com)")
    parser.add_argument("--port", type=int, default=21, help="порт (по умолчанию 21)")
    parser.add_argument("--user", default="dlpuser", help="логин (по умолчанию dlpuser)")
    parser.add_argument("--pass", dest="passwd", default="rNrKYTX9g7z3RgJRmxWuGHbeu",
                        help="пароль (по умолчанию rNrKYTX9g7z3RgJRmxWuGHbeu)")

    args = parser.parse_args()

    client = FTPClient(args.host, args.port, args.user, args.passwd)
    try:
        client.connect()
        if args.command == "ls":
            client.list_files()
        elif args.command == "upload":
            if not args.filename:
                print("[-] Не указано имя локального файла для upload.")
            else:
                client.upload_file(args.filename)
        elif args.command == "download":
            if not args.filename:
                print("[-] Не указано имя удалённого файла для download.")
            else:
                save_name = args.save_as if args.save_as else args.filename
                client.download_file(args.filename, save_name)
    except Exception as e:
        print(f"[-] Ошибка: {e}")

    finally:
        client.quit()


if __name__ == "__main__":
    main()
