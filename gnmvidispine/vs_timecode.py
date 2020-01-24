class VSTimecode(object):
    """
    This class represents a Vidispine compatible timecode
    """

    def __init__(self, value, framerate):
        """
        Initialise a new timecode with the specified values
        :param value: either a number, datetime or timecode string
        :param framerate: integer or float representing the framerate of value
        :return:
        """
        from datetime import datetime
        import re
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.frames = 0
        self.framerate = framerate

        if isinstance(value,datetime):
            self.hour = value.hour
            self.minute = value.minute
            self.second = value.second
            self.frames = value.microsecond/(1000*framerate)
        elif isinstance(value,str):
            parts = re.match('(\d+):(\d{2}):(\d{2})[:;](\d{2})',value)
            if parts:
                self.hour = int(parts.group(1))
                self.minute = int(parts.group(2))
                self.second = int(parts.group(3))
                self.frames = int(parts.group(4))
            else:
                raise ValueError("Couldn't parse '{0}' as a timecode".format(value))
        elif isinstance(value,float):
            self.hour, remainder = divmod(value,3600)
            self.minute, remainder = divmod(remainder, 60)
            self.second = int(remainder)
            self.frames = (float(remainder) - int(remainder)) * self.framerate
        elif isinstance(value,int):
            self.hour, remainder = divmod(value,3600)
            self.minute, remainder = divmod(remainder, 60)
            self.second = int(remainder)
            self.frames = 0
        else:
            raise TypeError("value must be a datetime, timecode string or number")

    def to_vidispine(self):
        num = self.frames
        num += self.framerate * self.second
        num += self.framerate * 60 * self.minute
        num += self.framerate * 3600 * self.hour

        fr = self.framerate
        if self.framerate == 25 or self.framerate == 25.0:
            fr = "PAL"
        if self.framerate == 29.97:
            fr = "NTSC"

        return "{0}@{1}".format(num,fr)
