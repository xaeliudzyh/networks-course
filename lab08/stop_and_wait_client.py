import socket
import time
import os
from stop_and_wait import (
    PACKET_DATA_SIZE,
    LOSS_PROB,
    TIMEOUT,
    CLIENT_DIR,
    make_packet,
    parse_packet,
    udt_send,
    PKT_TYPE_DATA,
    PKT_TYPE_ACK,
    PKT_TYPE_GET,
    PKT_TYPE_END,
)

def ensure_client_dir():
    os.makedirs(CLIENT_DIR, exist_ok=True)

def stop_and_wait_client(server_host: str = "127.0.0.1", server_port: int = 12000, filename: str = None):
    ensure_client_dir()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = (server_host, server_port)

    if filename is None:
        print("[Client] No filename specified for upload.")
        sock.close()
        return

    filepath = os.path.join(CLIENT_DIR, filename)
    if not os.path.isfile(filepath):
        print(f"[Client] File not found: {filepath}")
        sock.close()
        return

    print(f"[Client] Sending file '{filename}' to server {server_addr}...")
    seq = 0
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(PACKET_DATA_SIZE)
            if not chunk:
                break
            pkt = make_packet(seq, PKT_TYPE_DATA, chunk)
            while True:
                udt_send(sock, server_addr, pkt)
                print(f"[Client→Server] Sent DATA seq={seq}, {len(chunk)} bytes.")
                sock.settimeout(TIMEOUT)
                try:
                    resp, _ = sock.recvfrom(2048)
                    rseq, rtype, _ = parse_packet(resp)
                    if rtype == PKT_TYPE_ACK and rseq == seq:
                        print(f"[Client←Server] Got ACK seq={rseq}")
                        seq = 1 - seq
                        break
                    else:
                        print(f"[Client] Unexpected packet type {rtype} or seq {rseq}, resending.")
                except socket.timeout:
                    print(f"[Client] Timeout on seq={seq}, resending DATA.")
                    continue

    end_pkt = make_packet(seq, PKT_TYPE_END, b"")
    udt_send(sock, server_addr, end_pkt)
    print(f"[Client→Server] Sent END seq={seq}. Upload complete.\n")
    print(f"[Client] Requesting GET '{filename}' from server...")
    get_pkt = make_packet(0, PKT_TYPE_GET, filename.encode())
    udt_send(sock, server_addr, get_pkt)

    recv_file_buffer = bytearray()
    expected_seq = 0
    while True:
        try:
            packet, _ = sock.recvfrom(2048)
            seq_r, ttype_r, data_r = parse_packet(packet)
        except socket.timeout:
            print("[Client] Timeout waiting for server response. Aborting GET.")
            break
        except ValueError:
            continue

        if ttype_r == PKT_TYPE_DATA:
            if seq_r == expected_seq:
                recv_file_buffer.extend(data_r)
                print(f"[Client] Received DATA seq={seq_r}, {len(data_r)} bytes.")
                # Отправляем ACK
                ack_pkt = make_packet(seq_r, PKT_TYPE_ACK, b"")
                udt_send(sock, server_addr, ack_pkt)
                print(f"[Client] Sent ACK seq={seq_r}.")
                expected_seq = 1 - expected_seq
            else:
                last_ack = 1 - expected_seq
                ack_pkt = make_packet(last_ack, PKT_TYPE_ACK, b"")
                udt_send(sock, server_addr, ack_pkt)
                print(f"[Client] Received duplicate DATA seq={seq_r}, resent ACK seq={last_ack}.")
            continue

        if ttype_r == PKT_TYPE_END:
            print("[Client] Received END from server. Saving file as 'client_received.dat'")
            out_path = os.path.join(CLIENT_DIR, "client_received.dat")
            with open(out_path, "wb") as f:
                f.write(recv_file_buffer)
            print(f"[Client] File saved as {out_path}.")
            break

    sock.close()

if __name__ == "__main__":
    stop_and_wait_client(server_host="127.0.0.1", server_port=12000, filename="testfile.bin")
