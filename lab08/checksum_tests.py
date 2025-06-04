import os
import struct
import random

from stop_and_wait import compute_checksum, verify_checksum

def make_test_packet(data: bytes) -> bytes:
    if len(data) % 2 == 1:
        data_padded = data + b'\x00'
    else:
        data_padded = data
    cs = compute_checksum(data_padded)

    pkt = data_padded + struct.pack("!H", cs)
    return pkt

def make_tampered_packet(good_pkt: bytes) -> bytes:
    if len(good_pkt) == 0:
        return b"\x00\x00"
    bad = bytearray(good_pkt)
    bad[0] ^= 0xFF
    return bytes(bad)

def main():
    print("=== Checksum tests ===\n")

    test_vectors = [
        b"",
        b"A",
        b"Hello, World!",
        b"ABCDE",
        b"ABCDEFGH",
        os.urandom(1023),
        os.urandom(1024),
    ]

    for idx, data in enumerate(test_vectors, start=1):
        good_pkt = make_test_packet(data)
        ok_good = verify_checksum(good_pkt)
        bad_pkt = make_tampered_packet(good_pkt)
        ok_bad = verify_checksum(bad_pkt)
        cs = struct.unpack("!H", good_pkt[-2:])[0]

        print(f"Test #{idx}: len(data)={len(data):4d}  checksum=0x{cs:04X}")
        print(f"   verify on correct packet → {ok_good}")
        print(f"   verify on tampered packet → {ok_bad}\n")

    print("=== All checksum tests completed ===")

if __name__ == "__main__":
    main()
