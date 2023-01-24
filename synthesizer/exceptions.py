

class InconsistentParameter(Exception):
    """
    Generic exception class for inconsistent parameters.
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return '{0} '.format(self.message)
        return 'Inconsistent parameter choice'


class InconsistentArguments(Exception):
    """
    Generic exception class for inconsistent combinations of arguments.
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return '{0} '.format(self.message)
        return 'Inconsistent parameter choice'


class UnimplementedFunctionality(Exception):
    """
    Generic exception class for functionality not yet implemented.
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return '{0} '.format(self.message)
        return 'Unimplemented functionality!'


class UnknownImageType(Exception):
    """
    Generic exception class for functionality not yet implemented.
    """

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            return 'Inconsistent parameter choice'


class InconsistentAddition(Exception):
    """
    Generic exception class for when adding two objects is impossible.
    """
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return '{0} '.format(self.message)
        else:
            return 'Unable to add'


class InconsistentCoordinates(Exception):
    """
    Generic exception class for when coordinates are inconsistent.
    """
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return '{0} '.format(self.message)
        else:
            return 'Coordinates are inconsistent'