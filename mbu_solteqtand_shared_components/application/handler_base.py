"""This module handles the base functionality."""


class HandlerBase:
    """
    Base class for all feature‐handlers. Delegates unknown attributes
    (methods & properties) up to the main App instance.
    """

    def __init__(self, parent):
        self._parent = parent

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        parent = getattr(self, "_parent", None)
        if parent is not None:
            try:
                return object.__getattribute__(parent, name)
            except AttributeError as exc:
                raise AttributeError(
                    f"'{type(self).__name__}' object has no attribute '{name}'"
                ) from exc
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )
