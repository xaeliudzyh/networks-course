#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import struct
import time
import select
import sys
import os

ICMP_ECHO_REQUEST   = 8
ICMP_ECHO_REPLY     = 0
ICMP_TIME_EXCEEDED  = 11

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

def make_packet(pid: int, seq: int) -> bytes:
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, pid, seq)
    payload = struct.pack('!d', time.time()) + (b'Q' * 24)
    chksum = checksum(header + payload)
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, chksum, pid, seq)
    return header + payload

def parse_icmp(packet: bytes, my_pid: int) -> tuple:
    ip_header = packet[:20]
    ihl = (ip_header[0] & 0x0F) * 4
    icmp_header = packet[ihl:ihl+8]
    typ, code, chksum, recv_id, recv_seq = struct.unpack('!BBHHH', icmp_header)
    send_ts = None
    if typ == ICMP_ECHO_REPLY and recv_id == my_pid:
        payload = packet[ihl+8:]
        send_ts = struct.unpack('!d', payload[:8])[0]
    return typ, code, recv_id, recv_seq, send_ts

def traceroute(dest_name: str, max_hops: int = 30, count: int = 3):
    try:
        dest_addr = socket.gethostbyname(dest_name)
    except socket.gaierror:
        print(f"Не удалось разрешить {dest_name}")
        return

    print(f"traceroute to {dest_name} ({dest_addr}), {max_hops} hops max, {count} probes per hop")

    try:
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        print("Ошибка: нужен root/админ для RAW socket.")
        return
    try:
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except PermissionError:
        print("Ошибка: нужен root/админ для RAW socket.")
        recv_sock.close()
        return

    pid = os.getpid() & 0xFFFF
    seq = 0

    for ttl in range(1, max_hops + 1):
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        print(f"{ttl:2d} ", end='', flush=True)

        hop_ip = None
        hop_name = None
        rtts = []

        for probe in range(count):
            seq += 1
            packet = make_packet(pid, seq)
            send_time = time.time()
            try:
                send_sock.sendto(packet, (dest_addr, 0))
            except Exception:
                rtts.append(None)
                print(" *", end='', flush=True)
                continue
            ready = select.select([recv_sock], [], [], 1.0)
            if ready[0]:
                recv_packet, addr = recv_sock.recvfrom(1024)
                recv_time = time.time()
                typ, code, rid, rseq, send_ts = parse_icmp(recv_packet, pid)
                if typ == ICMP_TIME_EXCEEDED:
                    rtt = (recv_time - send_time) * 1000
                    hop_ip = addr[0]
                    rtts.append(rtt)
                    print(f" {rtt:.1f} ms", end='', flush=True)
                elif typ == ICMP_ECHO_REPLY and rid == pid and rseq == seq:
                    rtt = (recv_time - send_ts) * 1000
                    hop_ip = addr[0]
                    rtts.append(rtt)
                    print(f" {rtt:.1f} ms", end='', flush=True)
                    rtts += [None] * (count - len(rtts))
                    break

                else:
                    rtts.append(None)
                    print(" !", end='', flush=True)
            else:
                # таймаут
                rtts.append(None)
                print(" *", end='', flush=True)
        if hop_ip:
            try:
                hop_name = socket.gethostbyaddr(hop_ip)[0]
            except socket.herror:
                hop_name = None

            if hop_name:
                print(f"  {hop_ip}  ({hop_name})")
            else:
                print(f"  {hop_ip}")
        else:
            print("  *")
        if hop_ip == dest_addr:
            break

    recv_sock.close()
    send_sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Использование: {sys.argv[0]} <host> [max_hops] [count]")
        sys.exit(1)
    host = sys.argv[1]
    maxh = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
    cnt  = int(sys.argv[3]) if len(sys.argv) >= 4 else 3
    traceroute(host, maxh, cnt)