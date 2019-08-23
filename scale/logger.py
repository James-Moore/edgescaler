import datetime
import logging

class Logger:
    def __init__(self, name: str):
        # create logging
        self.logger = logging.getLogger(name)
        self.level = logging.INFO

    def setupLogger(self, loglevel: int):
        if loglevel == 0:
            self.level = logging.DEBUG
        elif loglevel == 1:
            self.level = logging.INFO
        elif loglevel >= 2:
            self.level = logging.WARNING

        self.logger.setLevel(self.level)
        ch = logging.StreamHandler()
        ch.setLevel(self.level)
        ch.terminator = ""
        self.logger.addHandler(ch)

    def timestamp(self) -> str:
        return "[" + str(datetime.datetime.now()).split('.')[0] + "]\t"

    def generateOutString(self, out, timestamp = True, newline = False) -> str:
        output = ""
        strout = ""

        if isinstance(out, str):
            strout += out
        else:
            strout += str(out)

        if timestamp:
            output += self.timestamp() + strout
        else:
            output += strout

        if newline:
            output += "\n"

        return output

    def debug(self, out, timestamp = True, newline = False):
        output = self.generateOutString(out, timestamp, newline)
        self.logger.debug(output)

    def info(self, out, timestamp = True, newline = False):
        output = self.generateOutString(out, timestamp, newline)
        self.logger.info(output)

    def warning(self, out, timestamp = True, newline = False):
        output = self.generateOutString(out, timestamp, newline)
        self.logger.warning(output)

    def error(self, out, timestamp = True, newline = False):
        output = self.generateOutString(out, timestamp, newline)
        self.logger.error(output)