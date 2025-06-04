#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys

if len(sys.argv) < 3:
    print(f"Использование: {sys.argv[0]} <IPv6-адрес> <порт>")
    sys.exit(1)

ipv6_addr = sys.argv[1]
port = int(sys.argv[2])

with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
    sock.connect((ipv6_addr, port))
    print(f"Подключено к [{ipv6_addr}]:{port}")
    while True:
        msg = input("Введите строку (или пустую для выхода): ")
        if not msg:
            break
        sock.sendall(msg.encode('utf-8'))
        data = sock.recv(1024)
        if not data:
            break
        print("Ответ сервера:", data.decode('utf-8'))