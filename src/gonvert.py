#!/usr/bin/python

import sys
import logging


_moduleLogger = logging.getLogger(__name__)
sys.path.append("/opt/gonvert/lib")


import gonvert_qt


if __name__ == "__main__":
	gonvert_qt.run_gonvert()
