#!/usr/bin/env python
# -*- coding: UTF8 -*-

from __future__ import with_statement

import sys
import os
import math
import pickle
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import constants
import unit_data

try:
	import gettext
except ImportError:
	_ = lambda x: x
	gettext = None
else:
	_ = gettext.gettext


_moduleLogger = logging.getLogger("gonvert_glade")

if gettext is not None:
	gettext.bindtextdomain('gonvert', '/usr/share/locale')
	gettext.textdomain('gonvert')


def change_menu_label(widgets, labelname, newtext):
	item_label = widgets.get_widget(labelname).get_children()[0]
	item_label.set_text(newtext)


def split_number(number):
	try:
		fractional, integer = math.modf(number)
	except TypeError:
		integerDisplay = number
		fractionalDisplay = ""
	else:
		integerDisplay = str(integer)
		fractionalDisplay = str(fractional)
		if "e+" in integerDisplay:
			integerDisplay = number
			fractionalDisplay = ""
		elif "e-" in fractionalDisplay and 0.0 < integer:
			integerDisplay = number
			fractionalDisplay = ""
		elif "e-" in fractionalDisplay:
			integerDisplay = ""
			fractionalDisplay = number
		else:
			integerDisplay = integerDisplay.split(".", 1)[0] + "."
			fractionalDisplay = fractionalDisplay.rsplit(".", 1)[-1]

	return integerDisplay, fractionalDisplay


class Gonvert(object):

	_DATA_PATHS = [
		os.path.dirname(__file__),
		os.path.join(os.path.dirname(__file__), "../data"),
		os.path.join(os.path.dirname(__file__), "../lib"),
		'/usr/share/gonvert',
		'/usr/lib/gonvert',
	]

	def __init__(self):
		self._dataPath = ""
		for dataPath in self._DATA_PATHS:
			appIconPath = os.path.join(dataPath, "pixmaps", "gonvert.png")
			if os.path.isfile(appIconPath):
				self._dataPath = dataPath
				break
		else:
			raise RuntimeError("UI Descriptor not found!")

		self._catWindow = CategoryWindow(None, appIconPath)


class CategoryWindow(object):

	def __init__(self, parent, appIconPath):
		self._categories = QtGui.QTreeWidget()

		self._layout = QtGui.QVBoxLayout()
		self._layout.addWidget(self._categories)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow()
		self._window.setWindowTitle("%s - Categories" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._window.show()


class UnitWindow(object):

	def __init__(self, parent, category, appIconPath):
		self._selectedUnitName = QtGui.QLabel()
		self._selectedUnitValue = QtGui.QLineEdit()
		self._selectedUnitSymbol = QtGui.QLabel()

		self._selectedUnitLayout = QtGui.QHBoxLayout()
		self._selectedUnitLayout.addWidget(self._selectedUnitName)
		self._selectedUnitLayout.addWidget(self._selectedUnitValue)
		self._selectedUnitLayout.addWidget(self._selectedUnitSymbol)

		self._units = QtGui.QTreeWidget()

		self._searchButton = QtGui.QPushButton()
		self._searchEntry = QtGui.QLineEdit()
		self._searchCloseButton = QtGui.QPushButton()

		self._searchLayout = QtGui.QHBoxLayout()
		self._searchLayout.addWidget(self._searchButton)
		self._searchLayout.addWidget(self._searchEntry)
		self._searchLayout.addWidget(self._searchCloseButton)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addLayout(self._selectedUnitLayout)
		self._layout.addWidget(self._units)
		self._layout.addLayout(self._searchLayout)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow()
		self._window.setWindowTitle("%s - %s" % (constants.__pretty_app_name__, category))
		self._window.setWindowIcon(QtGui.QIcon(appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._window.show()
		self._hide_search()

	def _hide_search(self):
		self._searchButton.hide()
		self._searchEntry.hide()
		self._searchCloseButton.hide()


def run_gonvert():
	app = QtGui.QApplication([])
	handle = Gonvert()
	return app.exec_()


if __name__ == "__main__":
	logging.basicConfig(level = logging.DEBUG)
	try:
		os.makedirs(constants._data_path_)
	except OSError, e:
		if e.errno != 17:
			raise

	val = run_gonvert()
	sys.exit(val)
