from gettext import gettext


class TranslatableError(Exception):
    """Works only for error which expect one argument."""

    def __repr__(self):
        self.repr(translate=False)

    def translate(self):
        return self.repr(translate=True)

    def repr(self, translate: bool):
        if not self.args:
            return str(self.__class__)
        if translate:
            message = gettext(self.args[0])
        else:
            message = self.args[0]
        if len(self.args) == 2:
            message = message.format(**self.args[1])
        return "{class_}: {message}".format(class_=self.__class__, message=message)
        # else:
        #     if len(self.args) < 2:
        #         return repr(message)
        #     elif len(self.args) == 2:
        #         message = self.args[0].format(**self.args[1])
        #         return repr(message)
        #     else:
        #         NotImplementedError()

        # if len(self.args) < 2:
        #     message = gettext(self.args[0])
        #     return repr(message)
        # elif len(self.args) == 2:
        #     message = gettext(self.args[0]).format(**self.args[1])
        #     return repr(message)
        # else:
        #     NotImplementedError()


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


class DatabaseError(TranslatableError):
    pass


class UUIDNotFoundError(TranslatableError):
    pass


class CustomFileNotFoundError(TranslatableError):
    pass
