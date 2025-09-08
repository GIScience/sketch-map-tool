from flask_babel import gettext


class TranslatableError(Exception):
    """Optional translation for errors.

    Add a translate method to Exception classes which uses gettext to translate
    the first argument of the exception. If a second argument is present it is
    expected to be a dictionary containing values for string interpolation.
    """

    def __init__(self, message: str, params: dict | None = None, *args):
        if params is not None:
            super().__init__(message, params, *args)
        else:
            super().__init__(message, *args)

    def _repr(self, translate: bool):
        if not self.args:
            return str(self.__class__.__name__)

        if translate:
            message = gettext(self.args[0])
        else:
            message = self.args[0]

        match len(self.args):
            case 1:
                pass
            case 2:
                message = message.format(**self.args[1])
            case _:
                raise ValueError(
                    "Unexpected arguments to " + str(self.__class__.__name__)
                )

        return "{class_}: {message}".format(
            class_=self.__class__.__name__, message=message
        )

    def translate(self):
        return self._repr(translate=True)


class ValidationError(ValueError, TranslatableError):
    pass


class MapGenerationError(TranslatableError):
    pass


class QRCodeError(TranslatableError):
    pass


class UploadLimitsExceededError(TranslatableError):
    pass


class UUIDNotFoundError(TranslatableError):
    pass


class CustomFileNotFoundError(TranslatableError):
    pass


class CustomFileDoesNotExistAnymoreError(TranslatableError):
    pass


class MarkingDetectionError(TranslatableError):
    pass
