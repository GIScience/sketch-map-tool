class MapGenerationError(Exception):
    pass


class QRCodeError(Exception):
    pass


class OQTReportError(Exception):
    pass


class UploadLimitsExceededError(Exception):
    pass


class DatabaseError(Exception):
    pass


class UUIDNotFoundError(DatabaseError):
    pass


class CustomFileNotFoundError(DatabaseError):
    pass
