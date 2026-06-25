from scte.Scte35._logging import resolve_logger


class SpliceNull:
    def __init__(self, bitarray_data, logger=None):
        self._log = resolve_logger(logger)
