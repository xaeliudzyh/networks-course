import socket
import struct
import time
import select
import sys
import os

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY   = 0

def checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b'\x00'
    s = 0
    for i in range(0, len(data), 2):
        w = (data[i] << 8) + data[i+1]
        s += w
    s = (s >> 16) + (s & 0xffff)
    s += (s >> 16)
    return (~s) & 0xffff

def create_packet(identifier: int, sequence: int) -> bytes:
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, identifier, sequence)
    timestamp = struct.pack('!d', time.time())
    payload = timestamp + (b'Q' * 32)
    chksum = checksum(header + payload)
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, chksum, identifier, sequence)
    return header + payload

def parse_icmp_packet(packet: bytes, identifier: int) -> tuple:
    ip_header = packet[:20]
    ihl = (ip_header[0] & 0x0F) * 4
    icmp_header = packet[ihl:ihl+8]
    typ, code, chksum, recv_id, recv_seq = struct.unpack('!BBHHH', icmp_header)
    payload = packet[ihl+8:]
    send_time = None
    if typ == ICMP_ECHO_REPLY and recv_id == identifier:
        send_time = struct.unpack('!d', payload[:8])[0]
    return typ, code, recv_id, recv_seq, send_time

def ping(host: str, count: int = None):
    try:
        dest_ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(f"Не удалось разрешить {host}")
        return
    print(f"PING {host} ({dest_ip}): 32 байт данных ICMP")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        return
    identifier = os.getpid() & 0xFFFF
    seq = 0
    sent_packets = 0
    recv_packets = 0
    rtt_list = []

    try:
        while True:
            seq += 1
            packet = create_packet(identifier, seq)
            send_time = time.time()
            try:
                sock.sendto(packet, (dest_ip, 0))
                sent_packets += 1
            except Exception as e:
                print(f"Ошибка при отправке: {e}")
                break
            timeout = 1.0
            ready = select.select([sock], [], [], timeout)
            if ready[0]:
                recv_packet, addr = sock.recvfrom(1024)
                recv_time = time.time()
                typ, code, r_id, r_seq, send_stamp = parse_icmp_packet(recv_packet, identifier)

                if typ == ICMP_ECHO_REPLY and r_id == identifier and r_seq == seq:
                    rtt = (recv_time - send_stamp) * 1000
                    rtt_list.append(rtt)
                    recv_packets += 1
                    print(f"{len(recv_packet)} байт от {addr[0]}: icmp_seq={seq} ttl={recv_packet[8]} time={rtt:.2f} ms")

                else:
                    if typ is not None:
                        print(f"ICMP type={typ} code={code} (пакет не является Echo Reply id={identifier})")
                    else:
                        print("Получен непонятный пакет ICMP")
            else:
                print(f"Превышен таймаут для icmp_seq={seq}")
            loss = ((sent_packets - recv_packets) / sent_packets) * 100
            if rtt_list:
                mn = min(rtt_list)
                mx = max(rtt_list)
                av = sum(rtt_list) / len(rtt_list)
                print(f"  Статистика: min={mn:.2f} ms  max={mx:.2f} ms  avg={av:.2f} ms  loss={loss:.1f}%\n")
            else:
                print(f"  Статистика: нет полученных пакетов  loss={loss:.1f}%\n")

            if count is not None and seq >= count:
                break
            time.sleep(max(0, 1.0 - (time.time() - send_time)))

    except KeyboardInterrupt:
        print("\nstop")
    print(f"\n--- {host} ping statistics ---")
    loss = ((sent_packets - recv_packets) / sent_packets) * 100 if sent_packets else 0
    print(f"{sent_packets} packets transmitted, {recv_packets} received, {loss:.1f}% packet loss")
    if rtt_list:
        mn = min(rtt_list)
        mx = max(rtt_list)
        av = sum(rtt_list) / len(rtt_list)
        ss = sum((x - av) ** 2 for x in rtt_list) / len(rtt_list)
        sd = ss ** 0.5
        print(f"rtt min/avg/max/stddev = {mn:.3f}/{av:.3f}/{mx:.3f}/{sd:.3f} ms")
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Использование: {sys.argv[0]} <host> [count]")
        sys.exit(1)
    target = sys.argv[1]
    cnt = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    ping(target, cnt)