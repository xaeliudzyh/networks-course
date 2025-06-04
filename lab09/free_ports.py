import socket
import argparse

def is_port_free(ip: str, port: int, timeout: float = 0.3) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
    except (socket.timeout, ConnectionRefusedError, OSError):
        return True
    finally:
        s.close()
    return False


parser = argparse.ArgumentParser(
    description="Проверка свободных портов на указанном IP-адресе"
)
parser.add_argument(
    "ip",
    help="IP-адрес, на котором проверяем порты (пример: 127.0.0.1 или 192.168.1.10)"
)
parser.add_argument(
    "start_port", type=int, help="Начальный порт диапазона (целое от 1 до 65535)"
)
parser.add_argument(
    "end_port", type=int, help="Конечный порт диапазона (целое от 1 до 65535)"
)

args = parser.parse_args()
ip = args.ip
start = args.start_port
end = args.end_port

if start < 1 or end > 65535 or start > end:
    Exception("Неверный диапазон портов. Убедитесь, что 1 ≤ start ≤ end ≤ 65535.")


print(f"Проверяем свободные порты на {ip} с {start} по {end}...\n")

free_ports = []
for port in range(start, end + 1):
    if is_port_free(ip, port):
        free_ports.append(port)

if free_ports:
    print(f"Свободные порты ({len(free_ports)} шт.):")
    # Выводим список последовательно, по 10 портов в строке
    for i, p in enumerate(free_ports, 1):
        print(f"{p:5d}", end="  ")
        if i % 10 == 0:
            print()
    print()
else:
    print("Нет свободных портов в указанном диапазоне.")

