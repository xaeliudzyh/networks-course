import socket
import threading
import logging
import os
import sys
import json
import urllib.parse

BUFFER_SIZE = 4096
CACHE_DIR = "cache"
LOG_FILE = "proxy.log"
BLACKLIST_FILE = "blacklist.txt"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")


def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    with open(BLACKLIST_FILE, "r", encoding="utf‑8") as f:
        return {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}

BLACKLIST = load_blacklist()


def in_blacklist(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    url_l = url.lower()
    return any(pat in host or pat in url_l for pat in BLACKLIST)


def cache_path(url: str) -> str:
    fname = urllib.parse.quote_plus(url)
    return os.path.join(CACHE_DIR, fname)


def meta_path(url: str) -> str:
    return cache_path(url) + ".meta"


def save_response_to_cache(url: str, raw: bytes, headers: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path(url), "wb") as f:
        f.write(raw)
    etag = headers.get("etag")
    lm = headers.get("last-modified")
    if etag or lm:
        with open(meta_path(url), "w", encoding="utf‑8") as m:
            json.dump({"etag": etag, "last-modified": lm}, m)


def cached_response(url: str):
    p = cache_path(url)
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f.read()
    return None


def conditional_headers(url: str) -> dict:
    p = meta_path(url)
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf‑8") as m:
        meta = json.load(m)
    hdrs = {}
    if meta.get("etag"):
        hdrs["If-None-Match"] = meta["etag"]
    if meta.get("last-modified"):
        hdrs["If-Modified-Since"] = meta["last-modified"]
    return hdrs


def recv_all(sock):
    data = bytearray()
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def forward_http(method: str, url: str, version: str, hdrs: dict, body: bytes):
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path or "/"
    print(f"[DEBUG] forward_http() called with method={method}, url={url}")

    if parsed.query:
        path += "?" + parsed.query

    hdrs = {k: v for k, v in hdrs.items() if k.lower() != "proxy-connection"}
    hdrs["Host"] = host
    hdrs["Connection"] = "close"
    if method == "GET":
        hdrs.update(conditional_headers(url))

    req_lines = [f"{method} {path} {version}"] + [f"{k}: {v}" for k, v in hdrs.items()] + ["", ""]
    raw_req = "\r\n".join(req_lines).encode() + body

    with socket.create_connection((host, port)) as upstream:
        upstream.sendall(raw_req)
        return recv_all(upstream)

def handle_client(client, addr):
    print(f"[DEBUG] New connection from {addr}")
    try:
        buff = bytearray()
        while b"\r\n\r\n" not in buff:
            chunk = client.recv(BUFFER_SIZE)
            if not chunk:
                client.close()
                return
            buff.extend(chunk)
        hdr_part, body = buff.split(b"\r\n\r\n", 1)
        lines = hdr_part.decode(errors="replace").split("\r\n")
        if len(lines) < 1:
            client.close()
            return
        method, url, version = lines[0].split()
        if url.startswith("/"):
            url = url.lstrip("/")
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()

        if method.upper() == "POST":
            need = int(headers.get("Content-Length", "0"))
            while len(body) < need:
                body += client.recv(BUFFER_SIZE)
        else:
            body = b""
        method = method.upper()

        if in_blacklist(url):
            msg = b"HTTP/1.1 403 Forbidden\r\nContent-Length: 25\r\nContent-Type: text/plain\r\n\r\nBlocked by proxy server."
            client.sendall(msg)
            logging.info(f"BLOCK {url}")
            return

        if method == "GET":
            cached = cached_response(url)
            if cached:
                resp = forward_http(method, url, version, headers, b"")
                code = int(resp.split(b" ")[1])
                if code == 304:  # Not Modified
                    client.sendall(cached)
                    logging.info(f"CACHE‑HIT {url} -> 200 (304)")
                    return
                else:
                    # Обновляем кеш
                    head = resp.split(b"\r\n\r\n", 1)[0]
                    save_response_to_cache(url, resp, parse_headers(head))
                    client.sendall(resp)
                    logging.info(f"CACHE‑UPDATE {url} -> {code}")
                    return

        resp = forward_http(method, url, version, headers, body)
        code = int(resp.split(b" ")[1])
        client.sendall(resp)

        if method == "GET" and code == 200:
            head = resp.split(b"\r\n\r\n", 1)[0]
            save_response_to_cache(url, resp, parse_headers(head))

        logging.info(f"{method} {url} -> {code}")


    except Exception as e:

        import traceback

        print("[DEBUG] Exception in handle_client():")

        traceback.print_exc()

        logging.exception("handler-error")

        try:

            client.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")

        except Exception:

            pass

        return
    finally:
        client.close()

def parse_headers(raw: bytes) -> dict:
    headers = {}
    for line in raw.decode(errors="replace").split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.lower()] = v.strip()
    return headers

def main():
    if len(sys.argv) != 2:
        print("Usage: python proxy_server.py <port>")
        return
    port = int(sys.argv[1])
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", port))
    server.listen(100)
    print(f"[+] Proxy listening on port {port}")

    try:
        while True:
            client, addr = server.accept()
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down…")
    finally:
        server.close()

if __name__ == "__main__":
    main()

