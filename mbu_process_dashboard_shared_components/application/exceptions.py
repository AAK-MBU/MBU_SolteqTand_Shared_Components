"""Module containing custom exceptions for the Solteq Tand application."""


class ManualProcessingRequiredError(Exception):
    """Raised when manual intervention is required (e.g., booking save warning)."""
    def __init__(self, message="Error occurred during booking; manual processing required."):
        super().__init__(message)


class NotMatchingError(Exception):
    """Raised when an input SSN doesn’t match the one in the patient record."""
    def __init__(self, in_msg=""):
        message = "Error occurred while opening the patient. " + in_msg
        super().__init__(message)


class PatientNotFoundError(Exception):
    """Raised when no patient is found with the given SSN."""
    def __init__(self, message="Error occurred while opening the patient. Patient not found"):
        super().__init__(message)
