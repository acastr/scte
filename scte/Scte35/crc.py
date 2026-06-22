"""CRC-32/MPEG-2 -- the CRC carried in the SCTE-35 splice_info_section.

Parameters: polynomial 0x04C11DB7, initial value 0xFFFFFFFF, no input or
output reflection, and no final XOR. This is the MPEG-2 systems CRC, distinct
from the reflected CRC-32 in zlib/binascii, so it is implemented here directly.
"""

POLYNOMIAL = 0x04C11DB7


def crc32_mpeg2(data):
    """Return the CRC-32/MPEG-2 of ``data`` (bytes) as a 32-bit int."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = ((crc << 1) ^ POLYNOMIAL) & 0xFFFFFFFF
            else:
                crc = (crc << 1) & 0xFFFFFFFF
    return crc
