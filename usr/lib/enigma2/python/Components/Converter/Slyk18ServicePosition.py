from Converter import Converter
from Components.Sources.Clock import Clock
from time import time as getTime, localtime, strftime
from Poll import Poll
from enigma import iPlayableService
from Components.Element import cached, ElementError
from Components.config import config
import os.path


# Remaining = sign / %d Min / %d Mins
# Position = sign / %d Min" / %d Mins
# MovieRemaining = %d Min / %d Mins
# MovieLength = %ds / %dm / &dh / %dh / %dh %dm
# MoviePosition = %ds / %dm / &dh / %dh / %dh %dm
# TimeshiftStart = (0-12)hour - (00-59)min - am/pm : 4.28pm
# TimeshiftPosition = %ds / %dm / &dh / %dh / %dh %dm

hours24 = False
filename = '/usr/share/enigma2/slyk-common/timeformat.txt'

if os.path.exists(filename):
	with open(filename, "r") as myfile:
		if 'Time = 24' in myfile.read():
			hours24 = True
		else:
			hours24 = False
			
			
class Slyk18ServicePosition(Poll, Converter, object):
    TYPE_LENGTH = 0
    TYPE_POSITION = 1
    TYPE_REMAINING = 2
    TYPE_GAUGE = 3
    TYPE_MOVIEREMAINING = 4
    TYPE_MOVIELENGTH = 5
    TYPE_MOVIEPOSITION = 6
    TYPE_TIMESHIFTSTART = 7
    TYPE_TIMESHIFTPOSITION = 8
    TYPE_REMAINING2 = 9

    def __init__(self, type):
        Poll.__init__(self)
        Converter.__init__(self, type)

        args = type.split(',')
        type = args.pop(0)

        self.detailed = 'Detailed' in args

        if type == "Remaining":
            self.type = self.TYPE_REMAINING
        elif type == "Remaining2":
            self.type = self.TYPE_REMAINING2
        elif type == "Position":
            self.type = self.TYPE_POSITION
        elif type == "MovieRemaining":
            self.type = self.TYPE_MOVIEREMAINING
        elif type == "MovieLength":
            self.type = self.TYPE_MOVIELENGTH
        elif type == "MoviePosition":
            self.type = self.TYPE_MOVIEPOSITION
        elif type == "TimeshiftStart":
            self.type = self.TYPE_TIMESHIFTSTART
        elif type == "TimeshiftPosition":
            self.type = self.TYPE_TIMESHIFTPOSITION

        self.poll_interval = 500
        self.poll_enabled = True

    def getSeek(self):
        s = self.source.service
        return s and s.seek()

    @cached
    def getPosition(self):
        seek = self.getSeek()
        if seek is None:
            return None
        pos = seek.getPlayPosition()
        if pos[0]:
            return 0
        return pos[1]

    @cached
    def getLength(self):
        seek = self.getSeek()
        if seek is None:
            return None
        length = seek.getLength()
        if length[0]:
            return 0
        return length[1]

    @cached
    def getCutlist(self):
        service = self.source.service
        cue = service and service.cueSheet()
        return cue and cue.getCutList()

    @cached
    def getText(self):
        seek = self.getSeek()
        if seek is None:
            return ""

        if self.type == self.TYPE_TIMESHIFTSTART:
            time = getTime()
            l = (self.length / 90000)
            t = localtime(time-l)
            if int(strftime("%H", t)) >= 12:
                timesuffix = _('pm')
            else:
                timesuffix = _('am')
            if hours24:
				d = _("%H.%M")
            else:
				d = _("%l.%M") + _(timesuffix)
            timetext = strftime(d, t)
            return timetext.lstrip(' ')

        if self.type == self.TYPE_TIMESHIFTPOSITION:
            time = getTime()
            l = (self.length / 90000)
            s = self.position / 90000
            t = localtime(time-l+s)
            if int(strftime("%H", t)) >= 12:
                timesuffix = _('pm')
            else:
                timesuffix = _('am')
            if hours24:
				d = _("%H.%M")
            else:
				d = _("%l.%M") + _(timesuffix)
            timetext = strftime(d, t)
            return timetext.lstrip(' ')

        if self.type == self.TYPE_REMAINING:
            s = self.position / 90000
            e = (self.length / 90000) - s
            sign_n = ""
            if (e/60) > 0:
                sign_n = "-"
            return sign_n + ngettext("%d Min", "%d Mins", (e/60)) % (e/60)

        if self.type == self.TYPE_REMAINING2:
            s = self.position / 90000
            e = self.length / 90000 - s
            sign_n = ''
            if e % 60 > 0:
                sign_n = '-'
            if e / 60 < 1:
                return sign_n + '%d Secs' % (e % 60)
            else:
                return sign_n + ngettext('%d Min', '%d Mins', e / 60) % (e / 60)

        if self.type == self.TYPE_POSITION:
            p = self.position / 90000
            sign_p = "+"
            return sign_p + ngettext("%d Min", "%d Mins", (p / 60)) % (p / 60)

        if self.type == self.TYPE_MOVIEREMAINING:
            s = self.position / 90000
            e = (self.length / 90000) - s
            return ngettext("%d Min", "%d Mins", (e / 60)) % (e / 60)

        l = self.length

        if l < 0:
                return ""

        if not self.detailed:
            l /= 90000

        if self.type == self.TYPE_MOVIELENGTH:
                if l/3600 < 1:
                    if l / 60 < 1:
                        return "%ds" % (l % 60)
                    else:
                        return "%dm" % (l / 60)
                elif l / 60 % 60 == 0:
                    return "%dh" % (l / 3600)
                else:
                    return "%dh %2dm" % (l / 3600, l / 60 % 60)

        if self.type == self.TYPE_MOVIEPOSITION:
            p = self.position / 90000
            if p/3600 < 1:
                if p/60 < 1:
                    return "%ds" % (p % 60)
                else:
                    return "%dm" % (p / 60)
            elif p / 60 % 60 == 0:
                return "%dh" % (p/3600)
            else:
                return "%dh %2dm" % (p / 3600, p / 60 % 60)

    # range/value are for the Progress renderer
    range = 10000

    @cached
    def getValue(self):
        pos = self.position
        len = self.length
        if pos is None or len is None or len <= 0:
            return None
        return pos * 10000 / len

    position = property(getPosition)
    length = property(getLength)
    cutlist = property(getCutlist)
    text = property(getText)
    value = property(getValue)

    def changed(self, what):
        cutlist_refresh = what[0] != self.CHANGED_SPECIFIC or what[1] in (iPlayableService.evCuesheetChanged,)
        time_refresh = what[0] == self.CHANGED_POLL or what[0] == self.CHANGED_SPECIFIC and what[1] in (iPlayableService.evCuesheetChanged,)

        if cutlist_refresh:
            if self.type == self.TYPE_GAUGE:
                self.downstream_elements.cutlist_changed()

        if time_refresh:
            self.downstream_elements.changed(what)
