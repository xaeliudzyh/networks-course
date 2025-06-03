import socket
import time

BROADCAST_IP = "255.255.255.255"
PORT = 50001

def main():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"[*] UDP time server broadcasting on {BROADCAST_IP}:{PORT}")

    try:
        while True:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            message = current_time.encode("utf-8")
            udp.sendto(message, (BROADCAST_IP, PORT))
            print(f"[>] Broadcast: {current_time}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] UDP time server stopped")
    finally:
        udp.close()

if __name__ == "__main__":
    main()
