"""Custom Domain Exceptions for user-friendly feedback."""

class UPIQRError(Exception):
    """Base exception for all UPI QR CLI operations."""
    pass

class ConfigurationError(UPIQRError):
    """Raised when there's an issue with the user config."""
    pass

class ExcelProcessingError(UPIQRError):
    """Raised when an error occurs reading or manipulating the Excel logic."""
    pass

class InvalidAmountError(UPIQRError):
    """Raised when an amount parsed from the sheet is invalid."""
    pass

class QRGenerationError(UPIQRError):
    """Raised when the QR Code generation fails."""
    pass

class DatabaseError(UPIQRError):
    """Raised on critical session DB failure."""
    pass
