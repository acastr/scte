"""Round-trip and golden-value tests for the SCTE-35 decoder.

xfail-marked tests document known bugs that have dedicated fix branches; they
flip to xpass once those branches land, signalling the marker can be removed.
"""
import base64
import json

import bitstring
import pytest

from scte.Scte35.SpliceEvent import SpliceEvent
from scte.Scte35.SpliceDescriptor import SpliceDescriptor
from scte.Scte35.SpliceInsert import SpliceInsert
from scte.Scte35.TimeSignal import TimeSignal

# Known-good SCTE-35 sample messages (base64), carried over from the original
# test.py. All four happen to be time_signal commands carrying a single
# segmentation_descriptor, which is why the tests below assert command_type 6.
# They cover a spread of UPID types (zero-length, URN, TVN) so the parser is
# exercised across the UPID variants it currently handles.
VECTORS = {
    "ts_zero_upid": "/DA6AAAAAsrbAP/wBQb+Bp8k9gAkAiJDVUVJAAAAAX//AAE07tIBDkVQMDAwMDExODk0OTU0AQUAONWP9g==",
    "ts_urn": "/DBIAAAAAsrbAP/wBQb/sbn3DQAyAjBDVUVJ/////3//AAAba98JHHVybjpuYmN1bmkuY29tOmJyYzozNTA3NTU4OTMxBQCk1C6w",
    "ts_tvn1": "/DAzAAAAAAAAAP/wBQb/4z6IEgAdAhtDVUVJE8WAEH+/AwxUVk5BMTAwMDAwMDEQAACj2jGV",
    "ts_tvn2": "/DAzAAAAAAAAAP/wBQb+M5DyeQAdAhtDVUVJAAABRX+/AwxUVk5BMTAwMDAwMDETAACr9xhM",
}

# A single segmentation_descriptor (hex), also from the original test.py. It is
# deliberately a delivery_not_restricted = True descriptor: in that case the
# parser/serializer skip the web/no-regional/archive/device sub-fields, so it
# round-trips cleanly and is NOT affected by bug #4 (the dropped
# archive_allowed_flag), which only bites when delivery_not_restricted = False.
DESCRIPTOR_HEX = "021B43554549000000027FBF030C54564E413130303030303031300000"


@pytest.mark.parametrize("b64", VECTORS.values(), ids=list(VECTORS))
def test_parse_time_signal_vectors(b64):
    """Every sample parses as a time_signal command and yields JSON-able output."""
    d = SpliceEvent(b64).as_dict
    # table_id is fixed at 0xFC for an SCTE-35 splice_info_section by the spec.
    assert d["table_id"] == 0xFC
    # 6 == time_signal (4 would be splice_schedule, 5 splice_insert, 0 null).
    assert d["splice_command_type"] == 6
    assert d["time_signal"]["time_specified_flag"] is True
    assert "pts_time" in d["time_signal"]
    # as_dict must survive a JSON round-trip (UPIDs rendered as str).
    assert json.loads(json.dumps(d))["splice_command_type"] == 6


def test_parse_golden_fields():
    """Exact field values for the primary vector guard against parser drift.

    Every literal below was obtained by decoding ts_zero_upid once and pinning
    the result -- they are not spec constants but a captured snapshot, so a
    change here means the bit-level parsing shifted and must be reviewed.
    """
    d = SpliceEvent(VECTORS["ts_zero_upid"]).as_dict
    assert d["table_id"] == 252
    assert d["pts_adjustment"] == 183003
    assert d["time_signal"]["pts_time"] == 111092982
    # descriptor_loop_length is a byte count; 36 matches the single descriptor.
    assert d["descriptor_loop_length"] == 36
    sd = d["splice_descriptors"][0]
    # segmentation_type_id 1 maps to "Content Identification" via scte35_enums;
    # asserting both pins the id->message lookup as well as the parse.
    assert sd["segmentation_type_id"] == 1
    assert sd["segmentation_message"] == "Content Identification"
    assert sd["segmentation_upid_type"] == 1
    assert sd["segmentation_upid_length"] == 14  # len("EP000011894954") == 14


def test_hex_and_b64_parse_equivalent():
    """from_hex_string and the base64 constructor produce the same structure."""
    b64 = VECTORS["ts_zero_upid"]
    hex_str = base64.standard_b64decode(b64).hex()
    assert SpliceEvent.from_hex_string(hex_str).as_dict == SpliceEvent(b64).as_dict


def test_descriptor_parse_golden():
    sd = SpliceDescriptor.from_hex_string(DESCRIPTOR_HEX).as_dict(upid_as_str=True)
    # tag 2 == segmentation_descriptor (0 avail, 1 DTMF, 3 time).
    assert sd["splice_descriptor_tag"] == 2
    # 0x30 == "Provider Advertisement Start" -- the leading 0x30 byte of the UPID
    # region in DESCRIPTOR_HEX; asserted as hex to mirror the SCTE-35 tables.
    assert sd["segmentation_type_id"] == 0x30
    assert sd["segmentation_message"] == "Provider Advertisement Start"
    # See DESCRIPTOR_HEX note: this vector is the unrestricted variant on purpose.
    assert sd["delivery_not_restricted_flag"] is True


def test_descriptor_structural_roundtrip():
    """parse -> serialize -> parse reproduces the same dict (reserved-bit agnostic)."""
    first = SpliceDescriptor.from_hex_string(DESCRIPTOR_HEX)
    second = SpliceDescriptor.from_hex_string(first.hex_string)
    assert second.as_dict() == first.as_dict()


def test_time_signal_serialize_roundtrip():
    # pts_time is an arbitrary 33-bit value (must fit < 2**33); the exact number
    # doesn't matter -- the point is that whatever goes in survives serialize.
    # 3588538282 is reused from the original test.py example for familiarity.
    original = {"time_specified_flag": True, "pts_time": 3588538282}
    bits = TimeSignal.from_dict(original).serialize()
    reparsed = TimeSignal(bitstring.BitStream(bytes=bits.tobytes())).as_dict
    assert reparsed == original


@pytest.mark.xfail(
    reason="bug #3: SpliceEvent.serialize() inits splice_descriptors_bs=None then "
    "adds it -> TypeError. Fix branch: fix/splice-event-descriptors.",
    strict=False,
)
def test_splice_event_serialize_roundtrip():
    ev = SpliceEvent(VECTORS["ts_zero_upid"])
    reserialized = ev.serialize().tobytes()
    assert SpliceEvent.from_hex_string(reserialized.hex()).as_dict == ev.as_dict


@pytest.mark.xfail(
    reason="bug #2: SpliceInsert.serialize() broken on this base. "
    "Fix branch: fix/splice-insert-serialize.",
    strict=False,
)
def test_splice_insert_serialize_roundtrip():
    # Minimal program-splice insert: program_splice_flag + non-immediate is the
    # combination that requires a splice_time(), so this dict exercises the
    # nested-structure path that the broken serializer cannot reach. Flags not
    # relevant here (duration, components) are off to keep the fixture small.
    si = {
        "splice_event_id": 1,
        "splice_event_cancel_indicator": False,
        "out_of_network_indicator": True,
        "program_splice_flag": True,
        "duration_flag": False,
        "splice_immediate_flag": False,
        "splice_time": {"time_specified_flag": True, "pts_time": 3600000},
        "unique_program_id": 1,
        "avail_num": 0,
        "avails_expected": 0,
    }
    bits = SpliceInsert.from_dict(si).serialize()
    reparsed = SpliceInsert(bitstring.BitStream(bytes=bits.tobytes())).as_dict
    assert reparsed == si


@pytest.mark.xfail(
    reason="bug #4: segmentation descriptor serialize drops archive_allowed_flag when "
    "delivery_not_restricted=False, misaligning all following bytes.",
    strict=False,
)
def test_descriptor_delivery_not_restricted_false_roundtrip():
    # Constructed (no sample vector among VECTORS has delivery_not_restricted =
    # False) precisely to trigger bug #4. The restriction sub-fields below only
    # appear on the wire when delivery_not_restricted is False, so all five must
    # be present:
    #   web_delivery_allowed_flag, no_regional_blackout_flag,
    #   archive_allowed_flag, device_restrictions (2 bits)
    # identifier 0x43554549 is "CUEI" (the standard SCTE-35 identifier).
    # device_restrictions is "11" (a 2-char bin string) to match what the parser
    # produces from bitstring's "bin:2" read. descriptor_length is nominal: the
    # serializer never validates it. archive_allowed_flag is the field the
    # serializer drops, so re-parsing recovers a wrong value (or shifts off the
    # end) -- hence the xfail.
    desc = {
        "splice_descriptor_tag": 2,
        "descriptor_length": 0x14,
        "identifier": 0x43554549,
        "segmentation_event_id": 1,
        "segmentation_event_cancel_indicator": False,
        "program_segmentation_flag": True,
        "segmentation_duration_flag": False,
        "delivery_not_restricted_flag": False,
        "web_delivery_allowed_flag": False,
        "no_regional_blackout_flag": True,
        "archive_allowed_flag": True,
        "device_restrictions": "11",
        "segmentation_upid_type": 1,
        "segmentation_upid_length": 0,
        "segmentation_upid": b"",
        "segmentation_type_id": 0x30,
        "segment_num": 0,
        "segments_expected": 0,
    }
    first = SpliceDescriptor.from_dict(desc)
    reparsed = SpliceDescriptor.from_hex_string(first.hex_string).as_dict()
    assert reparsed["archive_allowed_flag"] == desc["archive_allowed_flag"]
