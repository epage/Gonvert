#!/usr/bin/python

import os
import sys
import logging


_moduleLogger = logging.getLogger("gonvert")
sys.path.append("/usr/lib/gonvert/")


import constants
import gonvert_qt


try:
	os.makedirs(constants._data_path_)
except OSError, e:
	if e.errno != 17:
		raise

logging.basicConfig(level=logging.DEBUG, filename=constants._user_logpath_)
_moduleLogger.info("gonvert %s-%s" % (constants.__version__, constants.__build__))
_moduleLogger.info("OS: %s" % (os.uname()[0], ))
_moduleLogger.info("Kernel: %s (%s) for %s" % os.uname()[2:])
_moduleLogger.info("Hostname: %s" % os.uname()[1])


gonvert_qt.run_gonvert()
