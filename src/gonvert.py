#!/usr/bin/python

import os
import sys
import logging


_moduleLogger = logging.getLogger("gonvert")
sys.path.append("/usr/lib/gonvert/")


import constants
import gonvert_glade


try:
	os.makedirs(constants._data_path_)
except OSError, e:
	if e.errno != 17:
		raise

userLogPath = "%s/gonvert.log" % constants._data_path_
logging.basicConfig(level=logging.DEBUG, filename=userLogPath)
_moduleLogger.info("gonvert %s-%s" % (constants.__version__, constants.__build__))


gonvert_glade.run_gonvert()
