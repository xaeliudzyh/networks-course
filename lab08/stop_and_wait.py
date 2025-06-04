import socket
import random
import time
import threading
import os
from typing import Tuple

PACKET_DATA_SIZE = 1024
LOSS_PROB = 0.3
TIMEOUT = 0.5
SERVER_DIR = "server_files"
CLIENT_DIR = "client_files"

PKT_TYPE_DATA = 0
PKT_TYPE_ACK  = 1
PKT_TYPE_GET  = 2
PKT_TYPE_END  = 3
import struct


def make_packet(seq: int, ttype: int, data: bytes) -> bytes:
    length = len(data)
    header = struct.pack("!BBH", seq, ttype, length)  # seq:1, ttype:1, length:2
    pseudo = header + b"\x00\x00" + data  # пробросим 2 байта 0 (для чексума)
    cs = compute_checksum(pseudo)
    packet = header + struct.pack("!H", cs) + data
    return packet


def parse_packet(packet: bytes) -> Tuple[int, int, bytes]:
    if len(packet) < 6:
        raise ValueError("Packet too short")
    seq, ttype, length = struct.unpack("!BBH", packet[:4])
    recv_cs = struct.unpack("!H", packet[4:6])[0]
    data = packet[6:]
    if len(data) != length:
        raise ValueError("Declared length doesn't match actual data length")
    if not verify_checksum(packet):
        raise ValueError("Checksum mismatch")
    return seq, ttype, data

def compute_checksum(data_bytes: bytes) -> int:
    if len(data_bytes) % 2 == 1:
        data_bytes += b'\x00'
    checksum = 0
    for i in range(0, len(data_bytes), 2):
        word = (data_bytes[i] << 8) + data_bytes[i+1]
        checksum = checksum + word
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    # Инвертируем биты
    checksum = ~checksum & 0xFFFF
    return checksum

def verify_checksum(packet: bytes) -> bool:
    if len(packet) % 2 == 1:
        packet += b'\x00'
    total = 0
    for i in range(0, len(packet), 2):
        word = (packet[i] << 8) + packet[i+1]
        total = total + word
        total = (total & 0xFFFF) + (total >> 16)
    return total == 0xFFFF
def udt_send(sock: socket.socket, addr: Tuple[str,int], packet: bytes) -> None:
    if random.random() < LOSS_PROB:
        # пакета "не было"
        print(f"[UDT_SEND] Simulating LOSS of packet to {addr}")
        return
    sock.sendto(packet, addr)