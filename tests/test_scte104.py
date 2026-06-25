"""Round-trip tests for the SCTE-104 decoder/encoder.

Guards the SCTE-104 write path (`SpliceEvent.to_binary` and the per-op
`*_encode` helpers in `read_splice_event.py`), which previously had no test
coverage. The byte-exact round-trip exercises the standalone `manipulate_bits`
helper used by every op encoder; the unit test pins that helper directly.
"""
import bitstring
import pytest

from scte.Scte104.SpliceEvent import SpliceEvent
from scte.Scte104.read_splice_event import manipulate_bits, hex_string

# Known-good SCTE-104 messages (hex), carried over from the original
# scte/Scte104/test104.py scratch script. Between them they exercise five
# distinct op encoders.
VECTORS = {
    # splice_request + insert_DTMF_descriptor
    "splice_dtmf": "FFFF00280001F600000000020101000E01000000F600001F4802580000000109000650043132312A",
    # time_signal_request + insert_segmentation_descriptor + insert_tier
    "timesignal_segmentation_tier": (
        "FFFF004C00014D0000000003010400020000010B0030FFFFFFFF0000DB011E"
        "30303030324D413030303030303033383834395430343234313931363030"
        "0105011D010101000B010F0002000C"
    ),
}

EXPECTED_OPS = {
    "splice_dtmf": ["splice_request_data", "insert_DTMF_descriptor_request_data"],
    "timesignal_segmentation_tier": [
        "time_signal_request_data",
        "insert_segmentation_descriptor_request_data",
        "insert_tier_data",
    ],
}


@pytest.mark.parametrize("name", VECTORS, ids=list(VECTORS))
def test_parse_op_types(name):
    bs = bitstring.BitStream(bytes=bytes.fromhex(VECTORS[name]))
    event = SpliceEvent(bs)
    assert [op["type"] for op in event.as_dict["ops"]] == EXPECTED_OPS[name]


@pytest.mark.parametrize("name", VECTORS, ids=list(VECTORS))
def test_to_binary_roundtrip_byte_exact(name):
    hex_in = VECTORS[name]
    bs = bitstring.BitStream(bytes=bytes.fromhex(hex_in))
    event = SpliceEvent(bs)
    hex_out = event.to_binary().tobytes().hex().upper()
    assert hex_out == hex_in


def test_manipulate_bits_int_value():
    # An int value is hex-encoded to num_bytes width before being written.
    bit_array = bitstring.BitArray(length=16)
    consumed = manipulate_bits(bit_array, 0x1F, 0, num_bytes=2)
    assert consumed == 16  # num_bytes * 8
    assert bit_array.tobytes().hex() == "001f"


def test_manipulate_bits_preformatted_value():
    # A non-int (already-formatted) value is written through unchanged.
    bit_array = bitstring.BitArray(length=16)
    manipulate_bits(bit_array, "0x00ff", 0, num_bytes=2)
    assert bit_array.tobytes().hex() == "00ff"


def test_hex_string_zero_pads_to_width():
    assert hex_string(0x1F, num_bytes=2) == "0x001f"
