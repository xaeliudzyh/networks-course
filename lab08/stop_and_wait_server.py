import socket
import os
import argparse
from stop_and_wait import (
    PACKET_DATA_SIZE,
    LOSS_PROB,
    TIMEOUT,
    SERVER_DIR,
    make_packet,
    parse_packet,
    udt_send,
    PKT_TYPE_DATA,
    PKT_TYPE_ACK,
    PKT_TYPE_GET,
    PKT_TYPE_END,
)

def ensure_server_dir():
    os.makedirs(SERVER_DIR, exist_ok=True)

def stop_and_wait_server(bind_host: str = "0.0.0.0", bind_port: int = 12000):
    ensure_server_dir()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_host, bind_port))
    print(f"[Server] Listening on {bind_host}:{bind_port}, LOSS={LOSS_PROB*100:.0f}%")

    expected_seq = 0
    recv_buffer = bytearray()

    while True:
        packet, client_addr = sock.recvfrom(2048)
        try:
            seq, ttype, data = parse_packet(packet)
        except ValueError as e:
            print(f"[Server] Received corrupted packet from {client_addr}: {e}")
            continue

        if ttype == PKT_TYPE_GET:
            filename = data.decode(errors="ignore")
            filepath = os.path.join(SERVER_DIR, filename)
            if not os.path.isfile(filepath):
                print(f"[Server] File not found: {filename}, ignore GET.")
                continue
            print(f"[Server] Client requested GET '{filename}'. Starting to send file...")
            server_send_file(sock, client_addr, filepath)
            continue

        if ttype == PKT_TYPE_DATA:
            if seq == expected_seq:
                recv_buffer.extend(data)
                print(f"[Server] Received DATA seq={seq}, {len(data)} bytes.")
                # Отправляем ACK с тем же seq
                ack_pkt = make_packet(seq, PKT_TYPE_ACK, b"")
                udt_send(sock, client_addr, ack_pkt)
                print(f"[Server] Sent ACK seq={seq}.")
                expected_seq = 1 - expected_seq
            else:
                last_ack = 1 - expected_seq
                ack_pkt = make_packet(last_ack, PKT_TYPE_ACK, b"")
                udt_send(sock, client_addr, ack_pkt)
                print(f"[Server] Received out-of-order DATA (seq={seq}), resent ACK seq={last_ack}.")
            continue

        if ttype == PKT_TYPE_END:
            print(f"[Server] Received END from {client_addr}. Writing file...")
            out_path = os.path.join(SERVER_DIR, "final_received.dat")
            with open(out_path, "wb") as f:
                f.write(recv_buffer)
            print(f"[Server] File saved as {out_path}. Resetting state.")
            expected_seq = 0
            recv_buffer = bytearray()
            continue

def server_send_file(sock: socket.socket, client_addr: tuple, filepath: str):
    seq = 0
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(PACKET_DATA_SIZE)
            if not chunk:
                break
            pkt = make_packet(seq, PKT_TYPE_DATA, chunk)
            while True:
                udt_send(sock, client_addr, pkt)
                print(f"[Server→Client] Sent DATA seq={seq}, {len(chunk)} bytes.")
                sock.settimeout(TIMEOUT)
                try:
                    resp, _ = sock.recvfrom(2048)
                    rseq, rtype, _ = parse_packet(resp)
                    if rtype == PKT_TYPE_ACK and rseq == seq:
                        print(f"[Server←Client] Got ACK seq={rseq}")
                        seq = 1 - seq
                        break
                    else:
                        print(f"[Server] Unexpected packet type={rtype} or seq={rseq}, resending.")
                except socket.timeout:
                    print(f"[Server] Timeout on seq={seq}, resending DATA.")
                    continue
    end_pkt = make_packet(seq, PKT_TYPE_END, b"")
    udt_send(sock, client_addr, end_pkt)
    print(f"[Server→Client] Sent END seq={seq}. Done sending file.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stop-and-Wait UDP Server")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host/IP для прослушивания (по умолчанию 0.0.0.0)")
    parser.add_argument("--port", type=int, default=12000,
                        help="UDP-порт для прослушивания (по умолчанию 12000)")
    args = parser.parse_args()

    stop_and_wait_server(bind_host=args.host, bind_port=args.port)
