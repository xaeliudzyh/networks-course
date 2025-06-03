import socket

PORT = 50001
BUFFER_SIZE = 1024

def main():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("", PORT))  # "" эквивалентно "0.0.0.0"

    print(f"[+] Listening for broadcasts on port {PORT}")

    try:
        while True:
            data, addr = udp.recvfrom(BUFFER_SIZE)
            now = data.decode("utf-8", errors="ignore")
            print(f"[{addr[0]}:{addr[1]}] Server time: {now}")
    except KeyboardInterrupt:
        print("\n[!] UDP time client stopped")
    finally:
        udp.close()

if __name__ == "__main__":
    main()
