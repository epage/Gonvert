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

	ORIENTATION_HORIZONTAL = "ORIENTATION_HORIZONTAL"
	ORIENTATION_VERTICAL = "ORIENTATION_VERTICAL"

	_DATA_PATHS = [
		os.path.dirname(__file__),
		os.path.join(os.path.dirname(__file__), "../data"),
		os.path.join(os.path.dirname(__file__), "../lib"),
		'/usr/share/gonvert',
		'/usr/lib/gonvert',
	]

	def __init__(self):
		self.__isPortrait = False
		self._dataPath = ""
		for dataPath in self._DATA_PATHS:
			appIconPath = os.path.join(dataPath, "pixmaps", "gonvert.png")
			if os.path.isfile(appIconPath):
				self._dataPath = dataPath
				break
		else:
			raise RuntimeError("UI Descriptor not found!")

		self._unitCategory = QtGui.QPushButton()

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
		self._layout.addWidget(self._unitCategory)
		self._layout.addLayout(self._selectedUnitLayout)
		self._layout.addWidget(self._units)
		self._layout.addLayout(self._searchLayout)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow()
		self._window.setWindowTitle("%s - Unit Conversion Utility" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(appIconPath))
		self._window.setCentralWidget(centralWidget)
		self._load_settings()

		self._window.show()
		self._hide_search()

	def _load_settings(self):
		#Restore window size from previously saved settings if it exists and is valid.
		windowDatPath = "/".join((constants._data_path_, "window.dat"))
		if os.path.exists(windowDatPath):
			saved_window = pickle.load(open(windowDatPath, "r"))
			try:
				a, b = saved_window['size']
			except KeyError:
				pass
			else:
				self._window.resize(a, b)
			try:
				isFullscreen = saved_window["isFullscreen"]
			except KeyError:
				pass
			else:
				if isFullscreen:
					self._window.fullscreen()
			try:
				isPortrait = saved_window["isPortrait"]
			except KeyError:
				pass
			else:
				if isPortrait ^ self.__isPortrait:
					if isPortrait:
						orientation = self.ORIENTATION_VERTICAL
					else:
						orientation = self.ORIENTATION_HORIZONTAL
					self.set_orientation(orientation)

		#Restore selections from previously saved settings if it exists and is valid.
		categoryIndex = 0
		selectedCategoryName = unit_data.UNIT_CATEGORIES[0]
		selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
		if os.path.exists(selectionsDatPath):
			selections = pickle.load(open(selectionsDatPath, 'r'))
			try:
				self._defaultUnitForCategory = selections['selected_units']
			except KeyError:
				pass

			try:
				selectedCategoryName = selections['selected_category']
			except KeyError:
				pass
			else:
				try:
					categoryIndex = unit_data.UNIT_CATEGORIES.index(selectedCategoryName)
				except ValueError:
					_moduleLogger.warn("Unknown category: %s" % selectedCategoryName)

		if False:
			self._categorySelectionButton.get_child().set_markup("<big>%s</big>" % selectedCategoryName)
			self._categoryView.set_cursor(categoryIndex, self._categoryColumn, False)
			self._categoryView.grab_focus()

			self._select_default_unit()

	def _save_settings(self):
		"""
		This routine saves the selections to a file, and
		should therefore only be called when exiting the program.

		Update selections dictionary which consists of the following keys:
		'self._selectedCategoryName': full name of selected category
		'self._defaultUnitForCategory': self._defaultUnitForCategory dictionary which contains:
		[categoryname: #1 displayed unit, #2 displayed unit]
		"""
		if False:
			#Determine the contents of the selected category row
			selected, iter = self._categoryView.get_selection().get_selected()
			self._selectedCategoryName = self._categoryModel.get_value(iter, 0)

			selections = {
				'selected_category': self._selectedCategoryName,
				'selected_units': self._defaultUnitForCategory
			}
			selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
			pickle.dump(selections, open(selectionsDatPath, 'w'))

		#Get last size of app and save it
		window_settings = {
			'size': self._window.get_size(),
			"isFullscreen": self._isFullScreen,
			"isPortrait": self.__isPortrait,
		}
		windowDatPath = "/".join((constants._data_path_, "window.dat"))
		pickle.dump(window_settings, open(windowDatPath, 'w'))

	def set_orientation(self, orientation):
		pass

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
