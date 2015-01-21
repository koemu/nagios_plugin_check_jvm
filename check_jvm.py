#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------
# check_jvm
#
# Copyright(C) 2015 Yuichiro SAITO
# This software is released under the MIT License, see LICENSE.txt.
# ----------------------------------------------

import sys
import os
import re
import json
import os.path
import commands
import copy
import logging
import logging.config
from optparse import OptionParser

# ----------------------------------------------
# Global Variables
# ----------------------------------------------
LOG_FORMAT = '%(levelname)s\t%(asctime)s\t%(name)s\t%(funcName)s\t"%(message)s"'
PROGRAM_VERSION = "0.0.1"


# ----------------------------------------------
# Internal Class: _Jvm
# ----------------------------------------------
class _Jvm:

    STATE_OK = 0
    STATE_WARNING = 1
    STATE_CRITICAL = 2
    STATE_UNKNOWN = 3
    STATE_DEPENDENT = 4

    TEMPFILE_NAME = "jstat_%s.log"

    # ----------------------------------------------

    def __init__(self, java_bin, temp_dir, name, interval):
        """
        Constractor
        """
        self.log = logging.getLogger(self.__class__.__name__)

        self.log.debug("START")

        self.temp_dir = temp_dir
        self.interval = interval
        self.java_bin = java_bin
        self.pid = self._getJps(name)
        self.current_stat = self._getGcUtil()
        self.old_stat = self._getOldStat()
        self.time_warning = None
        self.time_critical = None
        self.count_warning = None
        self.count_critical = None

        self.log.debug("END")

    # ----------------------------------------------

    def __del__(self):
        """
        Destructor
        """
        self.log.debug("START")
        pass
        self.log.debug("END")

    # ----------------------------------------------

    def _printWarning(self, msg):

        print "WARNING: %s" % msg

        return self.STATE_WARNING

    # ----------------------------------------------

    def _printCritical(self, msg):

        print "CRITICAL: %s" % msg

        return self.STATE_CRITICAL

    # ----------------------------------------------

    def _printUnknown(self, msg):

        print "UNKNOWN: %s" % msg

        return self.STATE_UNKNOWN

    # ----------------------------------------------

    def _loadJson(self, path):

        self.log.debug("START")

        self.log.debug(path)

        if not os.path.exists(path):
            self.log.debug("Not found: %s" % path)
            self.log.debug("EXIT")
            return None

        f = open(path, "r")
        data = json.load(f)
        f.close()

        self.log.debug(data)

        self.log.debug("END")

        return data

    # ----------------------------------------------

    def _saveJson(self, path, data):

        self.log.debug("START")

        self.log.debug(path)
        self.log.debug(data)

        f = open(path, "w")
        json.dump(data, f, indent=4)
        f.close()

        self.log.debug("END")

        return 0

    # ----------------------------------------------

    def _parseGcUtil(self, stdout):

        self.log.debug("START")

        data = {}
        line = stdout.split("\n")
        headers = re.split(" +", line[0].strip())
        values = re.split(" +", line[1].strip())
        for i in range(0, len(headers)):
            self.log.debug("%s:%s" % (headers[i], values[i]))
            try:
                data[headers[i]] = float(values[i])
            except ValueError:
                data[headers[i]] = values[i]

        self.log.debug(data)

        self.log.debug("END")

        return data

    # ----------------------------------------------

    def _getGcUtil(self):

        self.log.debug("START")

        if self.pid is None:
            self.log.error("PID is not set.")
            self.log.debug("EXIT")
            return None

        jstat = os.path.join(self.java_bin, "jstat")
        cmd = "%s -gcutil -t %d" % (jstat, self.pid)
        stdout = commands.getoutput(cmd)
        self.log.debug(cmd)
        self.log.debug(stdout)
        data = self._parseGcUtil(stdout)

        self.log.debug("END")

        return data

    # ----------------------------------------------

    def _getJps(self, name):

        self.log.debug("START")

        jps = os.path.join(self.java_bin, "jps")
        cmd = "%s | grep %s | awk '{ print $1 }'" % (jps, name)
        stdout = commands.getoutput(cmd)
        self.log.debug(cmd)
        self.log.debug(stdout)
        pid = None
        try:
            pid = int(stdout)
        except ValueError:
            self.log.error("PID get failed.")
            pid = None

        self.log.debug("END")

        return pid

    # ----------------------------------------------

    def _setValue(self, value):

        self.log.debug("START")

        set_value = {}

        set_value["value"] = int(value)
        self.log.debug(set_value)

        self.log.debug("END")

        return set_value

    # ----------------------------------------------

    def _isValidThreshold(self, warning, critical):

        self.log.debug("START")

        if warning is None and critical is None:
            return self._printUnknown("Threshold is None.")
        elif warning is None:
            pass
        elif critical is None:
            pass
        elif warning > critical:
            return self._printUnknown("Warning value should be more than critical value.")

        self.log.debug("END")

        return self.STATE_OK

    # ----------------------------------------------

    def setTimeWarning(self, warning):

        self.log.debug("START")

        set_value = self._setValue(warning)
        self.time_warning = set_value["value"]

        ret = self._isValidThreshold(self.time_warning, self.time_critical)
        if ret != self.STATE_OK:
            self.log.debug("EXIT")
            return ret

        self.log.debug("END")

        return self.STATE_OK

    # ----------------------------------------------

    def setCountWarning(self, warning):

        self.log.debug("START")

        set_value = self._setValue(warning)
        self.count_warning = set_value["value"]

        ret = self._isValidThreshold(self.count_warning, self.count_critical)
        if ret != self.STATE_OK:
            self.log.debug("EXIT")
            return ret

        self.log.debug("END")

        return self.STATE_OK

    # ----------------------------------------------

    def setTimeCritical(self, ctitical):

        self.log.debug("START")

        set_value = self._setValue(ctitical)
        self.time_critical = set_value["value"]

        ret = self._isValidThreshold(self.time_warning, self.time_critical)
        if ret != self.STATE_OK:
            self.log.debug("EXIT")
            return ret

        self.log.debug("END")

        return self.STATE_OK

    # ----------------------------------------------

    def setCountCritical(self, ctitical):

        self.log.debug("START")

        set_value = self._setValue(ctitical)
        self.count_critical = set_value["value"]

        ret = self._isValidThreshold(self.count_warning, self.count_critical)
        if ret != self.STATE_OK:
            self.log.debug("EXIT")
            return ret

        self.log.debug("END")

        return self.STATE_OK

    # ----------------------------------------------

    def _getOldStat(self):

        self.log.debug("START")

        if self.current_stat is None:
            return 1

        history_filename = os.path.join(self.temp_dir, self.TEMPFILE_NAME)
        history1_filename = history_filename % "1"
        history2_filename = history_filename % "2"

        history1 = self._loadJson(history1_filename)
        history2 = self._loadJson(history2_filename)

        # check different process
        if history1 is not None and history1["pid"] != self.pid:
            self.log.debug("Target process is restarted (1).")
            history1 = None
            history2 = None
        if history2 is not None and history2["pid"] != self.pid:
            self.log.debug("Target process is restarted (2).")
            history1 = None
            history2 = None

        # choice history
        using = 0
        if history1 is None:
            self.log.debug("Initialize phase.")
        else:
            history1_diff = self.current_stat["Timestamp"] - history1["Timestamp"]
            history2_diff = self.current_stat["Timestamp"] - history2["Timestamp"]
            self.log.debug("history1: %d, history2: %d" % (history1_diff, history2_diff))
            if self.interval > history1_diff \
                    and (self.interval > history2_diff or history2_diff >= self.interval * 2):
                self.log.debug("Early phase (1).")
                self.log.debug("EXIT")
                return None
            elif self.interval > history2_diff \
                    and (self.interval > history1_diff or history1_diff >= self.interval * 2):
                self.log.debug("Early phase (2).")
                self.log.debug("EXIT")
                return None
            elif self.interval <= history1_diff and history1_diff < self.interval * 2:
                using = 1
            elif self.interval <= history2_diff and history2_diff < self.interval * 2:
                using = 2
            else:
                self.log.debug("Data is too old.")
                using = 0
        self.log.debug("Using %d" % using)

        # choice data
        history = None
        if using == 1:
            history = history1
        elif using == 2:
            history = history2
        self.log.debug(history)

        # save history
        save_stat = copy.deepcopy(self.current_stat)
        save_stat["pid"] = self.pid
        if using == 0:
            self._saveJson(history1_filename, save_stat)
            self._saveJson(history2_filename, save_stat)
        elif using == 1:
            if history2 is None or history1["Timestamp"] >= history2["Timestamp"]:
                self._saveJson(history2_filename, save_stat)
        elif using == 2:
            if history2["Timestamp"] >= history1["Timestamp"]:
                self._saveJson(history1_filename, save_stat)

        self.log.debug("END")

        return history

    # ----------------------------------------------

    def checkGc(self):

        self.log.debug("START")

        result = self._checkGc(self.current_stat, self.old_stat)

        self.log.debug("END")

        return result

    # ----------------------------------------------

    def _checkGc(self, current_stat, old_stat):

        self.log.debug("START")

        if current_stat is None:
            return self._printUnknown("Unable to get gcutil.")
        elif old_stat is None:
            print "OK: now collecting data."
            self.log.debug("EXIT")
            return self.STATE_OK

        # gc time
        time = current_stat["FGCT"] - old_stat["FGCT"]
        self.log.debug("GC time: %.03f", time)
        if self.time_critical <= time:
            self.log.debug("%d <= %.03f" % (self.time_critical, time))
            return self._printCritical("GC time is too long. (%d msec)" % time)
        elif self.time_warning <= time:
            self.log.debug("%d <= %.03f" % (self.time_warning, time))
            return self._printWarning("GC time is too long. (%d msec)" % time)

        # gc count
        count = current_stat["FGC"] - old_stat["FGC"]
        self.log.debug("GC count: %.03f", count)
        if self.count_critical <= count:
            self.log.debug("%d <= %.03f" % (self.count_critical, count))
            return self._printCritical("GC count is too occured. (%d times)" % count)
        elif self.count_warning <= count:
            self.log.debug("%d <= %.03f" % (self.count_warning, count))
            return self._printWarning("GC count is too occured. (%d times)" % count)

        print "OK: GC time is %.03f msec, GC count is %d." % (time, count)

        self.log.debug("END")

        return self.STATE_OK

    # ----------------------------------------------


# -----------------------------------------------
# Main
# -----------------------------------------------

def main():
    """
    Main
    """

    usage = "Usage: %prog [option ...]"
    version = "%%prog %s\nCopyright (C) 2014 Yuichiro SAITO." % (
        PROGRAM_VERSION)
    parser = OptionParser(usage=usage, version=version)
    parser.add_option("-w", "--time-warning",
                      type="int",
                      dest="time_warning",
                      default=200,
                      metavar="<msec>",
                      help="Exit with WARNING status if more than value of full gc time.")
    parser.add_option("-c", "--time-critical",
                      type="int",
                      dest="time_critical",
                      default=1000,
                      metavar="<msec>",
                      help="Exit with CRITICAL status if more than value of full gc time.")
    parser.add_option("-W", "--count-warning",
                      type="int",
                      dest="count_warning",
                      default=3,
                      metavar="<count>",
                      help="Exit with WARNING status if more than value of full gc count.")
    parser.add_option("-C", "--count-critical",
                      type="int",
                      dest="count_critical",
                      default=10,
                      metavar="<count>",
                      help="Exit with CRITICAL status if more than value of full gc count.")
    parser.add_option("-n", "--name",
                      type="string",
                      dest="name",
                      metavar="<name>",
                      help="Java process name.")
    parser.add_option("-i", "--interval",
                      type="int",
                      dest="interval",
                      default=600,
                      metavar="<path>",
                      help="Monitoring interval (sec).")
    parser.add_option("-t", "--tempdir",
                      type="string",
                      dest="tempdir",
                      default="/tmp",
                      metavar="<path>",
                      help="Temporary directory.")
    parser.add_option("-b", "--bin",
                      type="string",
                      dest="bin",
                      default="/usr/bin",
                      metavar="<path>",
                      help="Java bin directory.")
    parser.add_option("-V", "--verbose",
                      action="store_true",
                      dest="verbose",
                      default=False,
                      help="Verbose mode. (For debug only)")
    (options, args) = parser.parse_args()

    if options.verbose:
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    else:
        logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT)

    logging.debug("START")

    if options.name is None:
        logging.error("'--name' is required.")
        logging.debug("EXIT")
        return _Jvm.STATE_UNKNOWN

    checker = _Jvm(
        options.bin, options.tempdir, options.name, options.interval)

    ret = checker.setTimeWarning(options.time_warning)
    if ret != _Jvm.STATE_OK:
        logging.debug("EXIT")
        return ret
    ret = checker.setTimeCritical(options.time_critical)
    if ret != _Jvm.STATE_OK:
        logging.debug("EXIT")
        return ret
    ret = checker.setCountWarning(options.count_warning)
    if ret != _Jvm.STATE_OK:
        logging.debug("EXIT")
        return ret
    ret = checker.setCountCritical(options.count_critical)
    if ret != _Jvm.STATE_OK:
        logging.debug("EXIT")
        return ret

    ret = checker.checkGc()

    logging.debug("END")

    return ret


# ----------------------------------------------

if __name__ == '__main__':
    sys.exit(main())
