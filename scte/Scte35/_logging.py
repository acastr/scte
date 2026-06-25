import logging


def resolve_logger(logger=None):
    """Return the provided logger, or the root logger when none is given.

    Factors out the ``if logger is not None: ... else: logging.getLogger()``
    boilerplate repeated across the SCTE-35 classes. Preserves the historical
    default of the root logger (no ``__name__`` argument).
    """
    if logger is not None:
        return logger
    return logging.getLogger()
