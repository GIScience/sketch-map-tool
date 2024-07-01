from gettext import gettext


class TranslatableError(Exception):
    """Optional translation for errors.

    Add a translate method to Exception classes which uses gettext to translate
    the first argument of the exception. If a second argument is present it is
    expected to be a dictionary containing values for string interpolation.
    """

    def __repr__(self):
        self._repr(translate=False)

    def _repr(self, translate: bool):
        if not self.args:
            return str(self.__class__.__name__)

        if len(self.args) > 2:
            raise ValueError("Unexpected arguments to " + str(self.__class__.__name__))

        if translate:
            message = gettext(self.args[0])
        else:
            message = self.args[0]

        if len(self.args) == 2:
            message = message.format(**self.args[1])

        return "{class_}: {message}".format(
            class_=self.__class__.__name__, message=message
        )

    def translate(self):
        return self._repr(translate=True)


class ValueError(ValueError, TranslatableError):
    pass


class MapGenerationError(TranslatableError):
    pass


class QRCodeError(TranslatableError):
    pass


class OQTReportError(TranslatableError):
    pass


class UploadLimitsExceededError(TranslatableError):
    pass


class UUIDNotFoundError(TranslatableError):
    pass


class CustomFileNotFoundError(TranslatableError):
    pass


class CustomFileDoesNotExistAnymoreError(TranslatableError):
    pass
