import binascii

def crc32(data: bytes) -> int:
    return binascii.crc32(data) & 0xFFFFFFFF

def flip_bit_in_bytes(data: bytearray, byte_index: int, bit_index: int) -> None:
    mask = 1 << bit_index
    data[byte_index] ^= mask

def simulate_packets(text: str, packet_size: int = 5, corrupt_indices: list = None):
    if corrupt_indices is None:
        corrupt_indices = []

    data_bytes = text.encode('utf-8')
    packets = []
    total_len = len(data_bytes)
    idx = 0
    pkt_num = 0

    while idx < total_len:
        chunk = data_bytes[idx: idx + packet_size]
        idx += packet_size
        pkt_num += 1
        orig = chunk
        crc_val = crc32(orig)
        crc_bytes = crc_val.to_bytes(4, byteorder='big')
        packet_bytes = bytearray(orig + crc_bytes)

        corrupted = False
        if pkt_num in corrupt_indices:
            flip_bit_in_bytes(packet_bytes, 0, 0)
            corrupted = True

        packets.append({
            'pkt_no':       pkt_num,
            'data_bytes':   orig,
            'crc_val':      crc_val,
            'full_packet':  bytes(packet_bytes),
            'corrupted':    corrupted
        })

    return packets

def check_packets(packets_list):
    results = []
    for pkt in packets_list:
        full = pkt['full_packet']
        if len(full) < 4:
            results.append((pkt['pkt_no'], False, None, None))
            continue
        data = full[:-4]
        recv_crc = int.from_bytes(full[-4:], byteorder='big')
        calc_crc = crc32(data)
        ok = (recv_crc == calc_crc)
        results.append((pkt['pkt_no'], ok, recv_crc, calc_crc))
    return results

def pretty_print_packets(packets_list, check_results):
    print("=" * 60)
    print("Пакетов всего:", len(packets_list))
    print("=" * 60)
    for pkt, cr in zip(packets_list, check_results):
        pkt_no, ok, recv_crc, calc_crc = cr
        data = pkt['data_bytes']
        data_str = repr(data.decode('utf-8', errors='replace'))
        data_hex = data.hex()
        full_hex = pkt['full_packet'].hex()
        print(f"Packet #{pkt_no}:")
        print(f"  Data (utf-8)         : {data_str}")
        print(f"  Data (hex)           : {data_hex}")
        print(f"  Sent CRC-32 (hex)    : {pkt['crc_val']:08x}")
        print(f"  Full packet (hex)    : {full_hex}")
        print(f"  Проверка CRC         : {'OK' if ok else 'ERROR'}")
        if not ok:
            print(f"    → Получено CRC: {recv_crc:08x}, Счёт CRC: {calc_crc:08x}")
        print("-" * 60)

def main():
    print("=== CRC Checker ===")
    text = input("Введите текст: ")
    corrupt_input = input("Номера пакетов для порчи (через запятую, пусто для none): ")
    if corrupt_input.strip() == "":
        corrupt_indices = []
    else:
        corrupt_indices = [int(x.strip()) for x in corrupt_input.split(",")]

    packets = simulate_packets(text, packet_size=5, corrupt_indices=corrupt_indices)
    results = check_packets(packets)
    pretty_print_packets(packets, results)

if __name__ == "__main__":
    main()