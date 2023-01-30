class MapGenerationError(Exception):
    pass


class QRCodeError(Exception):
    pass


class OQTReportError(Exception):
    pass


class DatabaseError(Exception):
    pass


class UUIDNotFoundError(DatabaseError):
    pass


class FileNotFoundError_(DatabaseError):
    pass
