__segmentation_type_ids = {
    0: {
        "message": "Not Indicated"
    },
    1: {
        "message": "Content Identification"
    },
    16: {
        "message": "Program Start"
    },
    17: {
        "message": "Program End"
    },
    18: {
        "message": "Program Early Termination"
    },
    19: {
        "message": "Program Breakaway"
    },
    20: {
        "message": "Program Resumption"
    },
    21: {
        "message": "Program Runover Planned"
    },
    22: {
        "message": "Program Runover Unplanned"
    },
    23: {
        "message": "Program Overlap Start"
    },
    24: {
        "message": "Program Blackout Override"
    },
    25: {
        "message": "Program Start - In Progress"
    },
    32: {
        "message": "Chapter Start"
    },
    33: {
        "message": "Chapter End"
    },
    34: {
        "message": "Break Start"
    },
    35: {
        "message": "Break End"
    },
    48: {
        "message": "Provider Advertisement Start"
    },
    49: {
        "message": "Provider Advertisement End"
    },
    50: {
        "message": "Distributor Advertisement Start"
    },
    51: {
        "message": "Distributor Advertisement End"
    },
    52: {
        "message": "Provider Placement Opportunity Start"
    },
    53: {
        "message": "Provider Placement Opportunity End"
    },
    54: {
        "message": "Distributor Placement Opportunity Start"
    },
    55: {
        "message": "Distributor Placement Opportunity End"
    },
    64: {
        "message": "Unscheduled Event Start"
    },
    65: {
        "message": "Unscheduled Event End"
    },
    80: {
        "message": "Network Start"
    },
    81: {
        "message": "Network End"
    }
}


def get_message(type_id):
    return __segmentation_type_ids[type_id]["message"]


def get_hex_string(type_id):
    # TODO
    return None


def get_id_from_message(message):
    for type_id in __segmentation_type_ids:
        if __segmentation_type_ids[type_id]["message"] == message:
            return type_id


# segmentation_upid_type values (SCTE-35 Table: segmentation_upid_type).
__segmentation_upid_types = {
    0x00: "Not Used",
    0x01: "User Defined (deprecated)",
    0x02: "ISCI (deprecated)",
    0x03: "Ad-ID",
    0x04: "UMID",
    0x05: "ISAN (deprecated)",
    0x06: "ISAN",
    0x07: "TID",
    0x08: "TI",
    0x09: "ADI",
    0x0A: "EIDR",
    0x0B: "ATSC Content Identifier",
    0x0C: "MPU()",
    0x0D: "MID()",
    0x0E: "ADS Information",
    0x0F: "URI",
    0x10: "UUID",
    0x11: "SCR",
}

# UPID types whose payload is defined as an ASCII text string. Everything else
# (UMID, EIDR, UUID, MID, MPU, ...) is binary/structured and is left as hex for
# now -- structured decoders for those are future work.
__text_upid_types = frozenset({0x01, 0x03, 0x07, 0x09, 0x0E, 0x0F})


def get_upid_type_name(upid_type):
    return __segmentation_upid_types.get(upid_type, "Reserved/Unknown")


def decode_upid(upid_type, upid_bytes):
    """Decode a segmentation UPID payload to a JSON-safe structured value.

    Text-typed UPIDs (Ad-ID, TID, ADI, ADS Information, URI, User Defined) are
    returned as ASCII strings; any decode failure and every other (binary or
    structured) type fall back to a hex string. Always returns ``str``, so the
    result survives ``json.dumps``. The caller keeps the raw bytes separately
    for byte-exact serialization.
    """
    if upid_type in __text_upid_types:
        try:
            return upid_bytes.decode("ascii")
        except (UnicodeDecodeError, AttributeError):
            pass
    return upid_bytes.hex()
