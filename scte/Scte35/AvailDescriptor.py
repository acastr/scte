from scte.Scte35 import scte35_enums
from scte.Scte35._logging import resolve_logger


class AvailDescriptor:
    def __init__(self, bitarray_data, logger=None):
        self._log = resolve_logger(logger)
        new_descriptor = {}
        new_descriptor["provider_avail_id"] = bitarray_data.read("uint:32")
        self.as_dict = new_descriptor
