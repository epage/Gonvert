#!/usr/bin/env python
# -*- coding: UTF8 -*-

#@todo Research Fn
#@todo Research optimizations

from __future__ import with_statement

import sys
import os
import math
import simplejson
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import constants
import maeqt
from util import misc as misc_utils
import unit_data


_moduleLogger = logging.getLogger(__name__)


IS_MAEMO = True


def split_number(number):
	if number == 0.0:
		# Optimize the startup case
		return "0.", "0"

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
		elif "e-" in fractionalDisplay:
			if 0.0 < integer:
				integerDisplay = number
				fractionalDisplay = ""
			else:
				integerDisplay = ""
				fractionalDisplay = number
		else:
			integerDisplay = integerDisplay[0:-2] + "."
			fractionalDisplay = fractionalDisplay[2:]

	return integerDisplay, fractionalDisplay


class Gonvert(object):

	_DATA_PATHS = [
		os.path.dirname(__file__),
		os.path.join(os.path.dirname(__file__), "../share"),
		os.path.join(os.path.dirname(__file__), "../data"),
		'/usr/share/gonvert',
		'/opt/gonvert/share',
	]

	def __init__(self, app):
		self._dataPath = ""
		for dataPath in self._DATA_PATHS:
			appIconPath = os.path.join(dataPath, "pixmaps", "gonvert.png")
			if os.path.isfile(appIconPath):
				self._dataPath = dataPath
				break
		else:
			raise RuntimeError("UI Descriptor not found!")
		self._app = app
		self._appIconPath = appIconPath
		self._recent = []
		self._hiddenCategories = set()
		self._hiddenUnits = {}
		self._clipboard = QtGui.QApplication.clipboard()

		self._jumpWindow = None
		self._recentWindow = None
		self._mainWindow = None
		self._catWindow = None
		self._quickWindow = None

		self._on_jump_close = lambda obj = None: self._on_child_close("_jumpWindow", obj)
		self._on_recent_close = lambda obj = None: self._on_child_close("_recentWindow", obj)
		self._on_cat_close = lambda obj = None: self._on_child_close("_catWindow", obj)
		self._on_quick_close = lambda obj = None: self._on_child_close("_quickWindow", obj)

		self._condensedAction = QtGui.QAction(None)
		self._condensedAction.setText("Condensed View")
		self._condensedAction.setCheckable(True)
		self._condensedAction.triggered.connect(self._on_condensed_start)

		self._jumpAction = QtGui.QAction(None)
		self._jumpAction.setText("Quick Jump")
		self._jumpAction.setStatusTip("Search for a unit and jump straight to it")
		self._jumpAction.setToolTip("Search for a unit and jump straight to it")
		self._jumpAction.setShortcut(QtGui.QKeySequence("CTRL+j"))
		self._jumpAction.triggered.connect(self._on_jump_start)

		self._recentAction = QtGui.QAction(None)
		self._recentAction.setText("Recent Units")
		self._recentAction.setStatusTip("View the recent units")
		self._recentAction.setToolTip("View the recent units")
		self._recentAction.setShortcut(QtGui.QKeySequence("CTRL+r"))
		self._recentAction.triggered.connect(self._on_recent_start)

		self._fullscreenAction = QtGui.QAction(None)
		self._fullscreenAction.setText("Fullscreen")
		self._fullscreenAction.setCheckable(True)
		self._fullscreenAction.setShortcut(QtGui.QKeySequence("CTRL+Enter"))
		self._fullscreenAction.toggled.connect(self._on_toggle_fullscreen)

		self._showFavoritesAction = QtGui.QAction(None)
		self._showFavoritesAction.setCheckable(True)
		self._showFavoritesAction.setText("Favorites Only")

		self._sortActionGroup = QtGui.QActionGroup(None)
		self._sortByNameAction = QtGui.QAction(self._sortActionGroup)
		self._sortByNameAction.setText("Sort By Name")
		self._sortByNameAction.setStatusTip("Sort the units by name")
		self._sortByNameAction.setToolTip("Sort the units by name")
		self._sortByNameAction.setCheckable(True)
		self._sortByValueAction = QtGui.QAction(self._sortActionGroup)
		self._sortByValueAction.setText("Sort By Value")
		self._sortByValueAction.setStatusTip("Sort the units by value")
		self._sortByValueAction.setToolTip("Sort the units by value")
		self._sortByValueAction.setCheckable(True)
		self._sortByUnitAction = QtGui.QAction(self._sortActionGroup)
		self._sortByUnitAction.setText("Sort By Unit")
		self._sortByUnitAction.setStatusTip("Sort the units by unit")
		self._sortByUnitAction.setToolTip("Sort the units by unit")
		self._sortByUnitAction.setCheckable(True)

		self._sortByNameAction.setChecked(True)

		self._logAction = QtGui.QAction(None)
		self._logAction.setText("Log")
		self._logAction.setShortcut(QtGui.QKeySequence("CTRL+l"))
		self._logAction.triggered.connect(self._on_log)

		self._quitAction = QtGui.QAction(None)
		self._quitAction.setText("Quit")
		self._quitAction.setShortcut(QtGui.QKeySequence("CTRL+q"))
		self._quitAction.triggered.connect(self._on_quit)

		self._app.lastWindowClosed.connect(self._on_app_quit)
		self.load_settings()

		self.request_category()
		if self._recent:
			self._mainWindow.select_category(self._recent[-1][0])

	def request_category(self):

		if self._condensedAction.isChecked():
			if self._catWindow is not None:
				self._catWindow.hide()

			if self._quickWindow is None:
				self._quickWindow = QuickConvert(None, self)
				self._quickWindow.window.destroyed.connect(self._on_quick_close)
			else:
				self._quickWindow.show()

			self._mainWindow = self._quickWindow
		else:
			if self._quickWindow is not None:
				self._quickWindow.hide()

			if self._catWindow is None:
				self._catWindow = CategoryWindow(None, self)
				self._catWindow.window.destroyed.connect(self._on_cat_close)
			else:
				self._catWindow.window.show()

			self._mainWindow = self._catWindow

		return self._mainWindow

	def search_units(self):
		jumpWindow = QuickJump(None, self)
		jumpWindow.window.destroyed.connect(self._on_jump_close)
		self._jumpWindow = jumpWindow
		return self._jumpWindow

	def show_recent(self):
		recentWindow = Recent(None, self)
		recentWindow.window.destroyed.connect(self._on_recent_close)
		self._recentWindow = recentWindow
		return self._recentWindow

	def add_recent(self, categoryName, unitName):
		catUnit = categoryName, unitName
		try:
			self._recent.remove(catUnit)
		except ValueError:
			pass # ignore if its not already in the recent history
		assert catUnit not in self._recent
		self._recent.append(catUnit)

	def get_recent_unit(self, categoryName, fromMostRecent = 0):
		recentUnitName = ""
		for catName, unitName in reversed(self._recent):
			if catName == categoryName:
				recentUnitName = unitName
				if fromMostRecent <= 0:
					break
				else:
					fromMostRecent -= 1
		return recentUnitName

	def get_recent(self):
		return reversed(self._recent)

	@property
	def hiddenCategories(self):
		return self._hiddenCategories

	def get_hidden_units(self, categoryName):
		try:
			return self._hiddenUnits[categoryName]
		except KeyError:
			self._hiddenUnits[categoryName] = set()
			return self._hiddenUnits[categoryName]

	def load_settings(self):
		try:
			with open(constants._user_settings_, "r") as settingsFile:
				settings = simplejson.load(settingsFile)
		except IOError, e:
			_moduleLogger.info("No settings")
			settings = {}
		except ValueError:
			_moduleLogger.info("Settings were corrupt")
			settings = {}

		self._fullscreenAction.setChecked(settings.get("isFullScreen", False))

		sortBy = settings.get("sortBy", "name")
		if sortBy not in ["name", "value", "unit"]:
			_moduleLogger.info("Setting sortBy is not a valid value: %s" % sortBy)
			sortBy = "name"
		if sortBy == "name":
			self._sortByNameAction.setChecked(True)
			self._sortByValueAction.setChecked(False)
			self._sortByUnitAction.setChecked(False)
		elif sortBy == "value":
			self._sortByNameAction.setChecked(False)
			self._sortByValueAction.setChecked(True)
			self._sortByUnitAction.setChecked(False)
		elif sortBy == "unit":
			self._sortByNameAction.setChecked(False)
			self._sortByValueAction.setChecked(False)
			self._sortByUnitAction.setChecked(True)
		else:
			raise RuntimeError("How did this sortBy come about? %s" % sortBy)

		recent = settings.get("recent", self._recent)
		for category, unit in recent:
			self.add_recent(category, unit)

		self._hiddenCategories = set(settings.get("hiddenCategories", set()))
		self._hiddenUnits = dict(
			(catName, set(units))
			for (catName, units) in settings.get("hiddenUnits", {}).iteritems()
		)

		self._showFavoritesAction.setChecked(settings.get("showFavorites", True))

		self._condensedAction.setChecked(settings.get("useQuick", self._condensedAction.isChecked()))

	def save_settings(self):
		if self._sortByNameAction.isChecked():
			sortBy = "name"
		elif self._sortByValueAction.isChecked():
			sortBy = "value"
		elif self._sortByUnitAction.isChecked():
			sortBy = "unit"
		else:
			raise RuntimeError("Unknown sorting value")
		settings = {
			"isFullScreen": self._fullscreenAction.isChecked(),
			"recent": self._recent,
			"hiddenCategories": list(self._hiddenCategories),
			"hiddenUnits": dict(
				(catName, list(units))
				for (catName, units) in self._hiddenUnits.iteritems()
			),
			"showFavorites": self._showFavoritesAction.isChecked(),
			"useQuick": self._condensedAction.isChecked(),
			"sortBy": sortBy,
		}
		with open(constants._user_settings_, "w") as settingsFile:
			simplejson.dump(settings, settingsFile)

	@property
	def appIconPath(self):
		return self._appIconPath

	@property
	def jumpAction(self):
		return self._jumpAction

	@property
	def recentAction(self):
		return self._recentAction

	@property
	def fullscreenAction(self):
		return self._fullscreenAction

	@property
	def condensedAction(self):
		return self._condensedAction

	@property
	def sortByNameAction(self):
		return self._sortByNameAction

	@property
	def sortByValueAction(self):
		return self._sortByValueAction

	@property
	def sortByUnitAction(self):
		return self._sortByUnitAction

	@property
	def logAction(self):
		return self._logAction

	@property
	def quitAction(self):
		return self._quitAction

	@property
	def showFavoritesAction(self):
		return self._showFavoritesAction

	def _walk_children(self):
		if self._catWindow is not None:
			yield self._catWindow
		if self._quickWindow is not None:
			yield self._quickWindow
		if self._jumpWindow is not None:
			yield self._jumpWindow
		if self._recentWindow is not None:
			yield self._recentWindow

	def _close_windows(self):
		if self._catWindow is not None:
			self._catWindow.window.destroyed.disconnect(self._on_cat_close)
			self._catWindow.close()
			self._catWindow = None
		if self._quickWindow is not None:
			self._quickWindow.window.destroyed.disconnect(self._on_quick_close)
			self._quickWindow.close()
			self._quickWindow = None
		if self._jumpWindow is not None:
			self._jumpWindow.window.destroyed.disconnect(self._on_jump_close)
			self._jumpWindow.close()
			self._jumpWindow = None
		if self._recentWindow is not None:
			self._recentWindow.window.destroyed.disconnect(self._on_recent_close)
			self._recentWindow.close()
			self._recentWindow = None

	@misc_utils.log_exception(_moduleLogger)
	def _on_app_quit(self, checked = False):
		self.save_settings()

	@misc_utils.log_exception(_moduleLogger)
	def _on_child_close(self, name, obj = None):
		if not hasattr(self, name):
			_moduleLogger.info("Something weird going on when we don't have a %s" % name)
			return
		setattr(self, name, None)

	@misc_utils.log_exception(_moduleLogger)
	def _on_toggle_fullscreen(self, checked = False):
		for window in self._walk_children():
			window.set_fullscreen(checked)

	@misc_utils.log_exception(_moduleLogger)
	def _on_condensed_start(self, checked = False):
		self.request_category()
		if self._recent:
			self._mainWindow.select_category(self._recent[-1][0])

	@misc_utils.log_exception(_moduleLogger)
	def _on_jump_start(self, checked = False):
		self.search_units()

	@misc_utils.log_exception(_moduleLogger)
	def _on_recent_start(self, checked = False):
		self.show_recent()

	@misc_utils.log_exception(_moduleLogger)
	def _on_log(self, checked = False):
		with open(constants._user_logpath_, "r") as f:
			logLines = f.xreadlines()
			log = "".join(logLines)
			self._clipboard.setText(log)

	@misc_utils.log_exception(_moduleLogger)
	def _on_quit(self, checked = False):
		self._close_windows()


class QuickJump(object):

	MINIMAL_ENTRY = 3

	def __init__(self, parent, app):
		self._app = app

		self._searchLabel = QtGui.QLabel("Search:")
		self._searchEntry = QtGui.QLineEdit("")
		self._searchEntry.textEdited.connect(self._on_search_edited)

		self._entryLayout = QtGui.QHBoxLayout()
		self._entryLayout.addWidget(self._searchLabel)
		self._entryLayout.addWidget(self._searchEntry)

		self._resultsBox = QtGui.QTreeWidget()
		self._resultsBox.setHeaderLabels(["Categories", "Units"])
		self._resultsBox.setHeaderHidden(True)
		if not IS_MAEMO:
			self._resultsBox.setAlternatingRowColors(True)
		self._resultsBox.itemClicked.connect(self._on_result_clicked)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addLayout(self._entryLayout)
		self._layout.addWidget(self._resultsBox)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s - Quick Jump" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(self._app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		if IS_MAEMO:
			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.fullscreenAction)

		self._window.addAction(self._app.logAction)

		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def show(self):
		self._window.show()

	def hide(self):
		self._window.hide()

	def close(self):
		self._window.close()

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_result_clicked(self, item, columnIndex):
		categoryName = unicode(item.text(0))
		unitName = unicode(item.text(1))
		catWindow = self._app.request_category()
		unitsWindow = catWindow.select_category(categoryName)
		unitsWindow.select_unit(unitName)
		self.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_search_edited(self, *args):
		userInput = self._searchEntry.text()
		if len(userInput) <  self.MINIMAL_ENTRY:
			return

		self._resultsBox.clear()
		lowerInput = str(userInput).lower()
		for catIndex, category in enumerate(unit_data.UNIT_CATEGORIES):
			units = unit_data.get_units(category)
			for unitIndex, unit in enumerate(units):
				loweredUnit = unit.lower()
				if lowerInput in loweredUnit:
					twi = QtGui.QTreeWidgetItem(self._resultsBox)
					twi.setText(0, category)
					twi.setText(1, unit)


class Recent(object):

	def __init__(self, parent, app):
		self._app = app

		self._resultsBox = QtGui.QTreeWidget()
		self._resultsBox.setHeaderLabels(["Categories", "Units"])
		self._resultsBox.setHeaderHidden(True)
		if not IS_MAEMO:
			self._resultsBox.setAlternatingRowColors(True)
		self._resultsBox.itemClicked.connect(self._on_result_clicked)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addWidget(self._resultsBox)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s - Recent" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(self._app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		for cat, unit in self._app.get_recent():
			twi = QtGui.QTreeWidgetItem(self._resultsBox)
			twi.setText(0, cat)
			twi.setText(1, unit)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		if IS_MAEMO:
			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.fullscreenAction)

		self._window.addAction(self._app.logAction)

		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def show(self):
		self._window.show()

	def hide(self):
		self._window.hide()

	def close(self):
		self._window.close()

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_result_clicked(self, item, columnIndex):
		categoryName = unicode(item.text(0))
		unitName = unicode(item.text(1))
		catWindow = self._app.request_category()
		unitsWindow = catWindow.select_category(categoryName)
		unitsWindow.select_unit(unitName)
		self.close()


class QuickConvert(object):

	def __init__(self, parent, app):
		self._app = app
		self._categoryName = ""
		self._inputUnitName = ""
		self._outputUnitName = ""
		self._unitNames = []
		self._favoritesWindow = None

		self._inputUnitValue = QtGui.QLineEdit()
		maeqt.mark_numbers_preferred(self._inputUnitValue)
		self._inputUnitValue.textEdited.connect(self._on_value_edited)
		self._inputUnitSymbol = QtGui.QLabel()

		self._outputUnitValue = QtGui.QLineEdit()
		maeqt.mark_numbers_preferred(self._outputUnitValue)
		self._outputUnitValue.textEdited.connect(self._on_output_value_edited)
		self._outputUnitSymbol = QtGui.QLabel()

		self._conversionLayout = QtGui.QHBoxLayout()
		self._conversionLayout.addWidget(self._inputUnitValue)
		self._conversionLayout.addWidget(self._inputUnitSymbol)
		self._conversionLayout.addWidget(self._outputUnitValue)
		self._conversionLayout.addWidget(self._outputUnitSymbol)

		self._categoryView = QtGui.QTreeWidget()
		self._categoryView.setHeaderLabels(["Categories"])
		self._categoryView.setHeaderHidden(False)
		if not IS_MAEMO:
			self._categoryView.setAlternatingRowColors(True)
		self._categoryView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._categoryView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		for catName in unit_data.UNIT_CATEGORIES:
			twi = QtGui.QTreeWidgetItem(self._categoryView)
			twi.setText(0, catName)
		self._categorySelection = self._categoryView.selectionModel()
		self._categorySelection.selectionChanged.connect(self._on_category_selection_changed)

		self._inputView = QtGui.QTreeWidget()
		self._inputView.setHeaderLabels(["From", "Name"])
		self._inputView.setHeaderHidden(False)
		self._inputView.header().hideSection(1)
		if not IS_MAEMO:
			self._inputView.setAlternatingRowColors(True)
		self._inputView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._inputView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self._inputSelection = self._inputView.selectionModel()
		self._inputSelection.selectionChanged.connect(self._on_input_selection_changed)

		self._outputView = QtGui.QTreeWidget()
		self._outputView.setHeaderLabels(["To", "Name"])
		self._outputView.setHeaderHidden(False)
		self._outputView.header().hideSection(1)
		if not IS_MAEMO:
			self._outputView.setAlternatingRowColors(True)
		self._outputView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._outputView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self._outputWidgets = []
		self._outputSelection = self._outputView.selectionModel()
		self._outputSelection.selectionChanged.connect(self._on_output_selection_changed)

		self._selectionLayout = QtGui.QHBoxLayout()
		self._selectionLayout.addWidget(self._categoryView)
		self._selectionLayout.addWidget(self._inputView)
		self._selectionLayout.addWidget(self._outputView)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addLayout(self._conversionLayout)
		self._layout.addLayout(self._selectionLayout)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s - Quick Convert" % (constants.__pretty_app_name__, ))
		self._window.setWindowIcon(QtGui.QIcon(app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._chooseCatFavoritesAction = QtGui.QAction(None)
		self._chooseCatFavoritesAction.setText("Select Categories")
		self._chooseCatFavoritesAction.triggered.connect(self._on_choose_category_favorites)

		self._chooseUnitFavoritesAction = QtGui.QAction(None)
		self._chooseUnitFavoritesAction.setText("Select Units")
		self._chooseUnitFavoritesAction.triggered.connect(self._on_choose_unit_favorites)
		self._chooseUnitFavoritesAction.setEnabled(False)

		self._app.showFavoritesAction.toggled.connect(self._on_show_favorites)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close Window")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		if IS_MAEMO:
			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)

			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._chooseCatFavoritesAction)
			fileMenu.addAction(self._chooseUnitFavoritesAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.showFavoritesAction)
			viewMenu.addAction(self._app.condensedAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.jumpAction)
			viewMenu.addAction(self._app.recentAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._chooseCatFavoritesAction)
			fileMenu.addAction(self._chooseUnitFavoritesAction)
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.showFavoritesAction)
			viewMenu.addAction(self._app.condensedAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.jumpAction)
			viewMenu.addAction(self._app.recentAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.fullscreenAction)

		self._window.addAction(self._app.logAction)

		self._update_favorites()
		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def show(self):
		self._window.show()

	def hide(self):
		self._window.hide()

	def close(self):
		self._window.close()

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()

	def select_category(self, categoryName):
		self._select_category(categoryName)

		i = unit_data.UNIT_CATEGORIES.index(categoryName)
		rootIndex = self._categoryView.rootIndex()
		currentIndex = self._categoryView.model().index(i, 0, rootIndex)
		self._categoryView.scrollTo(currentIndex)
		self._categoryView.setItemSelected(self._categoryView.topLevelItem(i), True)

		return self

	def select_unit(self, name):
		self.select_input(name)
		return self

	def select_input(self, name):
		self._select_input(name)

		i = self._unitNames.index(name)
		rootIndex = self._inputView.rootIndex()
		currentIndex = self._inputView.model().index(i, 0, rootIndex)
		self._inputView.scrollTo(currentIndex)
		self._inputView.setItemSelected(self._inputView.topLevelItem(i), True)

	def select_output(self, name):
		self._select_output(name)

		i = self._unitNames.index(name)
		rootIndex = self._outputView.rootIndex()
		currentIndex = self._outputView.model().index(i, 0, rootIndex)
		self._outputView.scrollTo(currentIndex)
		self._outputView.setItemSelected(self._outputView.topLevelItem(i), True)

	def _select_category(self, categoryName):
		self._inputUnitName = ""
		self._outputUnitName = ""
		self._inputUnitValue.setText("")
		self._inputUnitSymbol.setText("")
		self._inputView.clear()
		self._outputUnitValue.setText("")
		self._outputUnitSymbol.setText("")
		self._outputView.clear()
		self._categoryName = categoryName
		self._chooseUnitFavoritesAction.setEnabled(True)

		unitData = unit_data.UNIT_DESCRIPTIONS[categoryName]
		self._unitNames = list(unit_data.get_units(categoryName))
		self._unitNames.sort()
		for key in self._unitNames:
			conversion, unit, description = unitData[key]
			unit = key

			twi = QtGui.QTreeWidgetItem(self._inputView)
			twi.setText(0, unit)
			twi.setText(1, key)

			twi = QtGui.QTreeWidgetItem(self._outputView)
			twi.setText(0, unit)
			twi.setText(1, key)

		defaultInputUnitName = self._app.get_recent_unit(categoryName)
		if defaultInputUnitName:
			self.select_input(defaultInputUnitName)
			defaultOutputUnitName = self._app.get_recent_unit(categoryName, 1)
			assert defaultOutputUnitName
			self.select_output(defaultOutputUnitName)

	def _select_input(self, name):
		self._app.add_recent(self._categoryName, name)
		self._inputUnitName = name

		unitData = unit_data.UNIT_DESCRIPTIONS[self._categoryName]
		conversion, unit, description = unitData[name]

		self._inputUnitSymbol.setText(unit if unit else name)

		if "" not in [self._categoryName, self._inputUnitName, self._outputUnitName]:
			self._update_output()

	def _select_output(self, name):
		# Add the output to recent but don't make things weird by making it the most recent
		self._app.add_recent(self._categoryName, name)
		self._app.add_recent(self._categoryName, self._inputUnitName)
		self._outputUnitName = name

		unitData = unit_data.UNIT_DESCRIPTIONS[self._categoryName]
		conversion, unit, description = unitData[name]

		self._outputUnitSymbol.setText(unit if unit else name)

		if "" not in [self._categoryName, self._inputUnitName, self._outputUnitName]:
			self._update_output()

	def _sanitize_value(self, userEntry):
		if self._categoryName == "Computer Numbers":
			if userEntry == '':
				value = '0'
			else:
				value = userEntry
		else:
			if userEntry == '':
				value = 0.0
			else:
				value = float(userEntry)
		return value

	def _update_output(self):
		assert self._categoryName
		assert self._inputUnitName
		assert self._outputUnitName

		userInput = str(self._inputUnitValue.text())
		value = self._sanitize_value(userInput)

		unitData = unit_data.UNIT_DESCRIPTIONS[self._categoryName]
		inputConversion, _, _ = unitData[self._inputUnitName]
		outputConversion, _, _ = unitData[self._outputUnitName]

		func, arg = inputConversion
		base = func.to_base(value, arg)

		func, arg = outputConversion
		newValue = func.from_base(base, arg)
		self._outputUnitValue.setText(str(newValue))

	def _update_input(self):
		assert self._categoryName
		assert self._inputUnitName
		assert self._outputUnitName

		userOutput = str(self._outputUnitValue.text())
		value = self._sanitize_value(userOutput)

		unitData = unit_data.UNIT_DESCRIPTIONS[self._categoryName]
		inputConversion, _, _ = unitData[self._inputUnitName]
		outputConversion, _, _ = unitData[self._outputUnitName]

		func, arg = outputConversion
		base = func.to_base(value, arg)

		func, arg = inputConversion
		newValue = func.from_base(base, arg)
		self._inputUnitValue.setText(str(newValue))

	def _update_favorites(self):
		if self._app.showFavoritesAction.isChecked():
			assert self._categoryView.topLevelItemCount() == len(unit_data.UNIT_CATEGORIES)
			for i, catName in enumerate(unit_data.UNIT_CATEGORIES):
				if catName in self._app.hiddenCategories:
					self._categoryView.setRowHidden(i, self._categoryView.rootIndex(), True)
				else:
					self._categoryView.setRowHidden(i, self._categoryView.rootIndex(), False)

			for i, unitName in enumerate(self._unitNames):
				if unitName in self._app.get_hidden_units(self._categoryName):
					self._inputView.setRowHidden(i, self._inputView.rootIndex(), True)
					self._outputView.setRowHidden(i, self._outputView.rootIndex(), True)
				else:
					self._inputView.setRowHidden(i, self._inputView.rootIndex(), False)
					self._outputView.setRowHidden(i, self._outputView.rootIndex(), False)
		else:
			for i in xrange(self._categoryView.topLevelItemCount()):
				self._categoryView.setRowHidden(i, self._categoryView.rootIndex(), False)

			for i in xrange(len(self._unitNames)):
				self._inputView.setRowHidden(i, self._inputView.rootIndex(), False)
				self._outputView.setRowHidden(i, self._outputView.rootIndex(), False)

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_show_favorites(self, checked = True):
		if checked:
			assert self._categoryView.topLevelItemCount() == len(unit_data.UNIT_CATEGORIES)
			for i, catName in enumerate(unit_data.UNIT_CATEGORIES):
				if catName in self._app.hiddenCategories:
					self._categoryView.setRowHidden(i, self._categoryView.rootIndex(), True)

			for i, unitName in enumerate(self._unitNames):
				if unitName in self._app.get_hidden_units(self._categoryName):
					self._inputView.setRowHidden(i, self._inputView.rootIndex(), True)
					self._outputView.setRowHidden(i, self._outputView.rootIndex(), True)
		else:
			for i in xrange(self._categoryView.topLevelItemCount()):
				self._categoryView.setRowHidden(i, self._categoryView.rootIndex(), False)

			for i in xrange(len(self._unitNames)):
				self._inputView.setRowHidden(i, self._inputView.rootIndex(), False)
				self._outputView.setRowHidden(i, self._outputView.rootIndex(), False)

	@misc_utils.log_exception(_moduleLogger)
	def _on_choose_category_favorites(self, obj = None):
		assert self._favoritesWindow is None
		self._favoritesWindow = FavoritesWindow(
			self._window,
			self._app,
			unit_data.UNIT_CATEGORIES,
			self._app.hiddenCategories
		)
		self._favoritesWindow.window.destroyed.connect(self._on_close_favorites)
		return self._favoritesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_choose_unit_favorites(self, obj = None):
		assert self._favoritesWindow is None
		self._favoritesWindow = FavoritesWindow(
			self._window,
			self._app,
			unit_data.get_units(self._categoryName),
			self._app.get_hidden_units(self._categoryName)
		)
		self._favoritesWindow.window.destroyed.connect(self._on_close_favorites)
		return self._favoritesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_favorites(self, obj = None):
		self._favoritesWindow = None
		self._update_favorites()

	@misc_utils.log_exception(_moduleLogger)
	def _on_value_edited(self, *args):
		self._update_output()

	@misc_utils.log_exception(_moduleLogger)
	def _on_output_value_edited(self, *args):
		self._update_input()

	@misc_utils.log_exception(_moduleLogger)
	def _on_category_selection_changed(self, selected, deselected):
		selectedNames = [
			str(item.text(0))
			for item in self._categoryView.selectedItems()
		]
		assert len(selectedNames) == 1
		self._select_category(selectedNames[0])

	@misc_utils.log_exception(_moduleLogger)
	def _on_input_selection_changed(self, selected, deselected):
		selectedNames = [
			str(item.text(1))
			for item in self._inputView.selectedItems()
		]
		if selectedNames:
			assert len(selectedNames) == 1
			name = selectedNames[0]
			self._select_input(name)
		else:
			pass

	@misc_utils.log_exception(_moduleLogger)
	def _on_output_selection_changed(self, selected, deselected):
		selectedNames = [
			str(item.text(1))
			for item in self._outputView.selectedItems()
		]
		if selectedNames:
			assert len(selectedNames) == 1
			name = selectedNames[0]
			self._select_output(name)
		else:
			pass


class FavoritesWindow(object):

	def __init__(self, parent, app, source, hidden):
		self._app = app
		self._source = list(source)
		self._hidden = hidden

		self._categories = QtGui.QTreeWidget()
		self._categories.setHeaderLabels(["Categories"])
		self._categories.setHeaderHidden(True)
		self._categories.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
		if not IS_MAEMO:
			self._categories.setAlternatingRowColors(True)
		self._childWidgets = []
		for catName in self._source:
			twi = QtGui.QTreeWidgetItem(self._categories)
			twi.setText(0, catName)
			self._childWidgets.append(twi)
			if catName in self._hidden:
				twi.setCheckState(0, QtCore.Qt.Unchecked)
			else:
				twi.setCheckState(0, QtCore.Qt.Checked)
		self._categories.itemChanged.connect(self._on_item_changed)

		self._allButton = QtGui.QPushButton("All")
		self._allButton.clicked.connect(self._on_select_all)
		self._invertButton = QtGui.QPushButton("Invert")
		self._invertButton.clicked.connect(self._on_invert_selection)
		self._noneButton = QtGui.QPushButton("None")
		self._noneButton.clicked.connect(self._on_select_none)

		self._buttonLayout = QtGui.QHBoxLayout()
		self._buttonLayout.addWidget(self._allButton)
		self._buttonLayout.addWidget(self._invertButton)
		self._buttonLayout.addWidget(self._noneButton)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addWidget(self._categories)
		self._layout.addLayout(self._buttonLayout)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s - Favorites" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(self._app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		if IS_MAEMO:
			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.fullscreenAction)

		self._window.addAction(self._app.logAction)

		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def show(self):
		self._window.show()

	def hide(self):
		self._window.hide()

	def close(self):
		self._window.close()

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()

	@misc_utils.log_exception(_moduleLogger)
	def _on_select_all(self, checked = False):
		for child in self._childWidgets:
			child.setCheckState(0, QtCore.Qt.Checked)

	@misc_utils.log_exception(_moduleLogger)
	def _on_invert_selection(self, checked = False):
		for child in self._childWidgets:
			state = child.checkState(0)
			if state == QtCore.Qt.Unchecked:
				newState = QtCore.Qt.Checked
			elif state == QtCore.Qt.Checked:
				newState = QtCore.Qt.Unchecked
			else:
				raise RuntimeError("Bad check state %r" % state)
			child.setCheckState(0, newState)

	@misc_utils.log_exception(_moduleLogger)
	def _on_select_none(self, checked = False):
		for child in self._childWidgets:
			child.setCheckState(0, QtCore.Qt.Unchecked)

	@misc_utils.log_exception(_moduleLogger)
	def _on_item_changed(self, item, column):
		state = item.checkState(column)
		if state == QtCore.Qt.Unchecked:
			name = str(item.text(column))
			self._hidden.add(name)
		elif state == QtCore.Qt.Checked:
			name = str(item.text(column))
			self._hidden.remove(name)
		else:
			raise RuntimeError("Bad check state %r" % state)

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self.close()


class CategoryWindow(object):

	def __init__(self, parent, app):
		self._app = app
		self._unitWindow = None
		self._favoritesWindow = None

		self._categories = QtGui.QTreeWidget()
		self._categories.setHeaderLabels(["Categories"])
		self._categories.itemClicked.connect(self._on_category_clicked)
		self._categories.setHeaderHidden(True)
		self._categories.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._categories.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		if not IS_MAEMO:
			self._categories.setAlternatingRowColors(True)
		for catName in unit_data.UNIT_CATEGORIES:
			twi = QtGui.QTreeWidgetItem(self._categories)
			twi.setText(0, catName)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addWidget(self._categories)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s - Categories" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(self._app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._chooseFavoritesAction = QtGui.QAction(None)
		self._chooseFavoritesAction.setText("Select Favorites")
		self._chooseFavoritesAction.setShortcut(QtGui.QKeySequence("CTRL+f"))
		self._chooseFavoritesAction.triggered.connect(self._on_choose_favorites)

		self._app.showFavoritesAction.toggled.connect(self._on_show_favorites)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		if IS_MAEMO:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._chooseFavoritesAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.showFavoritesAction)
			viewMenu.addAction(self._app.condensedAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.jumpAction)
			viewMenu.addAction(self._app.recentAction)

			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._chooseFavoritesAction)
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.showFavoritesAction)
			viewMenu.addAction(self._app.condensedAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.jumpAction)
			viewMenu.addAction(self._app.recentAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.fullscreenAction)

		self._window.addAction(self._app.logAction)

		self._update_favorites()
		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def walk_children(self):
		if self._unitWindow is not None:
			yield self._unitWindow
		if self._favoritesWindow is not None:
			yield self._favoritesWindow

	def show(self):
		self._window.show()
		for child in self.walk_children():
			child.show()

	def hide(self):
		for child in self.walk_children():
			child.hide()
		self._window.hide()

	def close(self):
		for child in self.walk_children():
			child.window.destroyed.disconnect(self._on_child_close)
			child.close()
		self._window.close()

	def select_category(self, categoryName):
		self._select_category(categoryName)

		i = unit_data.UNIT_CATEGORIES.index(categoryName)
		rootIndex = self._categories.rootIndex()
		currentIndex = self._categories.model().index(i, 0, rootIndex)
		self._categories.scrollTo(currentIndex)
		self._categories.setItemSelected(self._categories.topLevelItem(i), True)
		return self._unitWindow

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()
		for child in self.walk_children():
			child.set_fullscreen(isFullscreen)

	def _select_category(self, categoryName):
		for child in self.walk_children():
			child.window.destroyed.disconnect(self._on_child_close)
			child.close()
		self._unitWindow = UnitWindow(self._window, categoryName, self._app)
		self._unitWindow.window.destroyed.connect(self._on_child_close)

	def _update_favorites(self):
		if self._app.showFavoritesAction.isChecked():
			assert self._categories.topLevelItemCount() == len(unit_data.UNIT_CATEGORIES)
			for i, catName in enumerate(unit_data.UNIT_CATEGORIES):
				if catName in self._app.hiddenCategories:
					self._categories.setRowHidden(i, self._categories.rootIndex(), True)
				else:
					self._categories.setRowHidden(i, self._categories.rootIndex(), False)
		else:
			for i in xrange(self._categories.topLevelItemCount()):
				self._categories.setRowHidden(i, self._categories.rootIndex(), False)

	@misc_utils.log_exception(_moduleLogger)
	def _on_show_favorites(self, checked = True):
		if checked:
			assert self._categories.topLevelItemCount() == len(unit_data.UNIT_CATEGORIES)
			for i, catName in enumerate(unit_data.UNIT_CATEGORIES):
				if catName in self._app.hiddenCategories:
					self._categories.setRowHidden(i, self._categories.rootIndex(), True)
		else:
			for i in xrange(self._categories.topLevelItemCount()):
				self._categories.setRowHidden(i, self._categories.rootIndex(), False)

	@misc_utils.log_exception(_moduleLogger)
	def _on_choose_favorites(self, obj = None):
		assert self._favoritesWindow is None
		self._favoritesWindow = FavoritesWindow(
			self._window,
			self._app,
			unit_data.UNIT_CATEGORIES,
			self._app.hiddenCategories
		)
		self._favoritesWindow.window.destroyed.connect(self._on_close_favorites)
		return self._favoritesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_favorites(self, obj = None):
		self._favoritesWindow = None
		self._update_favorites()

	@misc_utils.log_exception(_moduleLogger)
	def _on_child_close(self, obj = None):
		self._unitWindow = None

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_category_clicked(self, item, columnIndex):
		categoryName = unicode(item.text(0))
		self.select_category(categoryName)


class UnitData(object):

	HEADERS = ["Name", "Value", "", "Unit"]
	ALIGNMENT = [QtCore.Qt.AlignLeft, QtCore.Qt.AlignRight, QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft]
	NAME_COLUMN = 0
	VALUE_COLUMN_0 = 1
	VALUE_COLUMN_1 = 2
	UNIT_COLUMN = 3

	__slots__ = [
		"_name", "_unit", "_description", "_conversion",
		"_value", "_integerDisplay", "_fractionalDisplay",
	]

	def __init__(self, name, unit, description, conversion):
		self._name = name
		self._unit = unit
		self._description = description
		self._conversion = conversion

		self._value = 0.0
		self._integerDisplay, self._fractionalDisplay = split_number(self._value)

	@property
	def name(self):
		return self._name

	@property
	def value(self):
		return self._value

	def update_value(self, newValue):
		self._value = newValue
		self._integerDisplay, self._fractionalDisplay = split_number(newValue)

	@property
	def unit(self):
		return self._unit

	@property
	def conversion(self):
		return self._conversion

	def data(self, column):
		try:
			return [self._name, self._integerDisplay, self._fractionalDisplay, self._unit][column]
		except IndexError:
			return None


class UnitModel(QtCore.QAbstractItemModel):

	def __init__(self, categoryName, parent=None):
		super(UnitModel, self).__init__(parent)
		self._categoryName = categoryName
		self._unitData = unit_data.UNIT_DESCRIPTIONS[self._categoryName]
		if self._categoryName == "Computer Numbers":
			self._sanitize_value = self._sanitize_alpha_value
		else:
			self._sanitize_value = self._sanitize_numeric_value

		self._children = []
		for key in unit_data.get_units(self._categoryName):
			conversion, unit, description = self._unitData[key]
			self._children.append(UnitData(key, unit, description, conversion))
		self._sortSettings = None

	@misc_utils.log_exception(_moduleLogger)
	def columnCount(self, parent):
		if parent.isValid():
			return 0
		else:
			return len(UnitData.HEADERS)

	@misc_utils.log_exception(_moduleLogger)
	def data(self, index, role):
		#if not index.isValid():
		#	return None

		if role == QtCore.Qt.DisplayRole:
			item = index.internalPointer()
			if isinstance(item, UnitData):
				return item.data(index.column())
			elif item is UnitData.HEADERS:
				return item[index.column()]
		elif role == QtCore.Qt.TextAlignmentRole:
			return UnitData.ALIGNMENT[index.column()]
		else:
			return None

	@misc_utils.log_exception(_moduleLogger)
	def sort(self, column, order = QtCore.Qt.AscendingOrder):
		self._sortSettings = column, order
		isReverse = order == QtCore.Qt.AscendingOrder
		if column == UnitData.NAME_COLUMN:
			key_func = lambda item: item.name
		elif column in [UnitData.VALUE_COLUMN_0, UnitData.VALUE_COLUMN_1]:
			key_func = lambda item: item.value
		elif column == UnitData.UNIT_COLUMN:
			key_func = lambda item: item.unit
		self._children.sort(key=key_func, reverse = isReverse)

		self._all_changed()

	@misc_utils.log_exception(_moduleLogger)
	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.NoItemFlags

		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	@misc_utils.log_exception(_moduleLogger)
	def headerData(self, section, orientation, role):
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return UnitData.HEADERS[section]

		return None

	@misc_utils.log_exception(_moduleLogger)
	def index(self, row, column, parent):
		#if not self.hasIndex(row, column, parent):
		#	return QtCore.QModelIndex()
		#elif parent.isValid():
		#	return QtCore.QModelIndex()

		parentItem = UnitData.HEADERS
		childItem = self._children[row]
		if childItem:
			return self.createIndex(row, column, childItem)
		else:
			return QtCore.QModelIndex()

	@misc_utils.log_exception(_moduleLogger)
	def parent(self, index):
		if not index.isValid():
			return QtCore.QModelIndex()

		childItem = index.internalPointer()
		if isinstance(childItem, UnitData):
			return QtCore.QModelIndex()
		elif childItem is UnitData.HEADERS:
			return None

	@misc_utils.log_exception(_moduleLogger)
	def rowCount(self, parent):
		if 0 < parent.column():
			return 0

		if not parent.isValid():
			return len(self._children)
		else:
			return len(self._children)

	def get_unit(self, index):
		assert 0 <= index
		return self._children[index]

	def get_unit_names(self):
		for child in self._children:
			yield child.name

	def index_unit(self, unitName):
		for i, child in enumerate(self._children):
			if child.name == unitName:
				return i
		else:
			raise RuntimeError("Unit not found")

	def update_values(self, fromIndex, userInput):
		value = self._sanitize_value(userInput)
		func, arg = self._children[fromIndex].conversion
		base = func.to_base(value, arg)
		for i, child in enumerate(self._children):
			func, arg = child.conversion
			newValue = func.from_base(base, arg)
			child.update_value(newValue)

		if (
			self._sortSettings is not None and
			self._sortSettings[0]  in [UnitData.VALUE_COLUMN_0, UnitData.VALUE_COLUMN_1]
		):
			# Sort takes care of marking everything as changed
			self.sort(*self._sortSettings)
			return True
		else:
			self._values_changed()
			return False

	def __len__(self):
		return len(self._children)

	def _values_changed(self):
		topLeft = self.createIndex(0, UnitData.VALUE_COLUMN_0, self._children[0])
		bottomRight = self.createIndex(len(self._children)-1, UnitData.VALUE_COLUMN_1, self._children[-1])
		self.dataChanged.emit(topLeft, bottomRight)

	def _all_changed(self):
		topLeft = self.createIndex(0, 0, self._children[0])
		bottomRight = self.createIndex(len(self._children)-1, len(UnitData.HEADERS)-1, self._children[-1])
		self.dataChanged.emit(topLeft, bottomRight)

	def _sanitize_alpha_value(self, userEntry):
		if userEntry:
			value = userEntry
		else:
			value = '0'
		return value

	def _sanitize_numeric_value(self, userEntry):
		if userEntry:
			value = float(userEntry)
		else:
			value = 0.0
		return value


class UnitWindow(object):

	def __init__(self, parent, category, app):
		self._app = app
		self._categoryName = category
		self._selectedIndex = 0
		self._favoritesWindow = None

		self._selectedUnitName = QtGui.QLabel()
		self._selectedUnitValue = QtGui.QLineEdit()
		self._selectedUnitValue.textEdited.connect(self._on_value_edited)
		maeqt.mark_numbers_preferred(self._selectedUnitValue)
		self._selectedUnitSymbol = QtGui.QLabel()
		self._updateDelayTimer = QtCore.QTimer()
		self._updateDelayTimer.setInterval(100)
		self._updateDelayTimer.setSingleShot(True)
		self._updateDelayTimer.timeout.connect(self._on_value_edited_delayed)

		self._selectedUnitLayout = QtGui.QHBoxLayout()
		self._selectedUnitLayout.addWidget(self._selectedUnitName)
		self._selectedUnitLayout.addWidget(self._selectedUnitValue)
		self._selectedUnitLayout.addWidget(self._selectedUnitSymbol)

		self._unitsModel = UnitModel(self._categoryName)
		self._unitsView = QtGui.QTreeView()
		self._unitsView.setModel(self._unitsModel)
		self._unitsView.setUniformRowHeights(True)
		self._unitsView.setSortingEnabled(True)
		self._unitsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self._unitsView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self._unitsView.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self._unitsView.setHeaderHidden(True)
		self._unitsView.clicked.connect(self._on_unit_clicked)
		if not IS_MAEMO:
			self._unitsView.setAlternatingRowColors(True)

		viewHeader = self._unitsView.header()
		viewHeader.setSortIndicatorShown(True)
		viewHeader.setClickable(True)

		viewHeader.setResizeMode(UnitData.NAME_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setResizeMode(UnitData.VALUE_COLUMN_0, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setResizeMode(UnitData.VALUE_COLUMN_1, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setResizeMode(UnitData.UNIT_COLUMN, QtGui.QHeaderView.ResizeToContents)
		viewHeader.setStretchLastSection(False)

		# Trying to make things faster by locking in the initial size of the immutable columns
		nameSize = min(viewHeader.sectionSize(UnitData.NAME_COLUMN), 300)
		viewHeader.setResizeMode(UnitData.NAME_COLUMN, QtGui.QHeaderView.Fixed)
		viewHeader.resizeSection(UnitData.NAME_COLUMN, nameSize)
		unitSize = min(viewHeader.sectionSize(UnitData.UNIT_COLUMN), 150)
		viewHeader.setResizeMode(UnitData.UNIT_COLUMN, QtGui.QHeaderView.Fixed)
		viewHeader.resizeSection(UnitData.UNIT_COLUMN, unitSize)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addLayout(self._selectedUnitLayout)
		self._layout.addWidget(self._unitsView)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s - %s" % (constants.__pretty_app_name__, category))
		self._window.setWindowIcon(QtGui.QIcon(app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		defaultUnitName = self._app.get_recent_unit(self._categoryName)
		if defaultUnitName:
			self.select_unit(defaultUnitName)
		else:
			self._select_unit(0)

		if self._app.sortByNameAction.isChecked():
			sortColumn = UnitData.NAME_COLUMN
		elif self._app.sortByValueAction.isChecked():
			sortColumn = UnitData.VALUE_COLUMN_0
		elif self._app.sortByUnitAction.isChecked():
			sortColumn = UnitData.UNIT_COLUMN
		else:
			raise RuntimeError("No sort column selected")
		if sortColumn != 0:
			# By default it sorts by he first column (name)
			self._unitsModel.sort(sortColumn)

		self._chooseFavoritesAction = QtGui.QAction(None)
		self._chooseFavoritesAction.setText("Select Favorites")
		self._chooseFavoritesAction.setShortcut(QtGui.QKeySequence("CTRL+f"))
		self._chooseFavoritesAction.triggered.connect(self._on_choose_favorites)

		self._app.showFavoritesAction.toggled.connect(self._on_show_favorites)

		self._previousUnitAction = QtGui.QAction(None)
		self._previousUnitAction.setText("Previous Unit")
		self._previousUnitAction.setShortcut(QtGui.QKeySequence("Up"))
		self._previousUnitAction.triggered.connect(self._on_previous_unit)

		self._nextUnitAction = QtGui.QAction(None)
		self._nextUnitAction.setText("Next Unit")
		self._nextUnitAction.setShortcut(QtGui.QKeySequence("Down"))
		self._nextUnitAction.triggered.connect(self._on_next_unit)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close Window")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		if IS_MAEMO:
			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)

			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._chooseFavoritesAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.showFavoritesAction)
			viewMenu.addAction(self._app.condensedAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.sortByNameAction)
			viewMenu.addAction(self._app.sortByValueAction)
			viewMenu.addAction(self._app.sortByUnitAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.jumpAction)
			viewMenu.addAction(self._app.recentAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._chooseFavoritesAction)
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.showFavoritesAction)
			viewMenu.addAction(self._app.condensedAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.sortByNameAction)
			viewMenu.addAction(self._app.sortByValueAction)
			viewMenu.addAction(self._app.sortByUnitAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.jumpAction)
			viewMenu.addAction(self._app.recentAction)
			viewMenu.addSeparator()
			viewMenu.addAction(self._app.fullscreenAction)

		self._app.sortByNameAction.triggered.connect(self._on_sort_by_name)
		self._app.sortByValueAction.triggered.connect(self._on_sort_by_value)
		self._app.sortByUnitAction.triggered.connect(self._on_sort_by_unit)

		self._window.addAction(self._app.logAction)
		self._window.addAction(self._nextUnitAction)
		self._window.addAction(self._previousUnitAction)
		self._window.addAction(self._chooseFavoritesAction)

		self._update_favorites()
		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def show(self):
		for child in self.walk_children():
			child.hide()
		self._window.show()

	def hide(self):
		for child in self.walk_children():
			child.hide()
		self._window.hide()

	def close(self):
		for child in self.walk_children():
			child.window.destroyed.disconnect(self._on_child_close)
			child.close()
		self._window.close()

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()

	def select_unit(self, unitName):
		index = self._unitsModel.index_unit(unitName)
		self._select_unit(index)

		qindex = self._unitsModel.createIndex(index, 0, self._unitsModel.get_unit(index))
		self._unitsView.scrollTo(qindex)

	def walk_children(self):
		if self._favoritesWindow is not None:
			yield self._favoritesWindow

	def _update_favorites(self, force = False):
		if self._app.showFavoritesAction.isChecked():
			unitNames = list(self._unitsModel.get_unit_names())
			for i, unitName in enumerate(unitNames):
				if unitName in self._app.get_hidden_units(self._categoryName):
					self._unitsView.setRowHidden(i, self._unitsView.rootIndex(), True)
				else:
					self._unitsView.setRowHidden(i, self._unitsView.rootIndex(), False)
		else:
			if force:
				for i in xrange(len(self._unitsModel)):
					self._unitsView.setRowHidden(i, self._unitsView.rootIndex(), False)

	@misc_utils.log_exception(_moduleLogger)
	def _on_show_favorites(self, checked = True):
		if checked:
			unitNames = list(self._unitsModel.get_unit_names())
			for i, unitName in enumerate(unitNames):
				if unitName in self._app.get_hidden_units(self._categoryName):
					self._unitsView.setRowHidden(i, self._unitsView.rootIndex(), True)
		else:
			for i in xrange(len(self._unitsModel)):
				self._unitsView.setRowHidden(i, self._unitsView.rootIndex(), False)

	@misc_utils.log_exception(_moduleLogger)
	def _on_choose_favorites(self, obj = None):
		assert self._favoritesWindow is None
		self._favoritesWindow = FavoritesWindow(
			self._window,
			self._app,
			unit_data.get_units(self._categoryName),
			self._app.get_hidden_units(self._categoryName)
		)
		self._favoritesWindow.window.destroyed.connect(self._on_close_favorites)
		return self._favoritesWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_favorites(self, obj = None):
		self._favoritesWindow = None
		self._update_favorites(force=True)

	@misc_utils.log_exception(_moduleLogger)
	def _on_previous_unit(self, checked = True):
		self._select_unit(self._selectedIndex - 1)

	@misc_utils.log_exception(_moduleLogger)
	def _on_next_unit(self, checked = True):
		self._select_unit(self._selectedIndex + 1)

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_sort_by_name(self, checked = False):
		self._unitsModel.sort(UnitData.NAME_COLUMN, QtCore.Qt.DescendingOrder)

	@misc_utils.log_exception(_moduleLogger)
	def _on_sort_by_value(self, checked = False):
		self._unitsModel.sort(UnitData.VALUE_COLUMN_0)

	@misc_utils.log_exception(_moduleLogger)
	def _on_sort_by_unit(self, checked = False):
		self._unitsModel.sort(UnitData.UNIT_COLUMN, QtCore.Qt.DescendingOrder)

	@misc_utils.log_exception(_moduleLogger)
	def _on_unit_clicked(self, index):
		self._select_unit(index.row())

	@misc_utils.log_exception(_moduleLogger)
	def _on_value_edited(self, *args):
		if not self._updateDelayTimer.isActive():
			self._updateDelayTimer.start()

	@misc_utils.log_exception(_moduleLogger)
	def _on_value_edited_delayed(self, *args):
		userInput = str(self._selectedUnitValue.text())
		orderChanged = self._unitsModel.update_values(self._selectedIndex, userInput)
		if orderChanged:
			self._update_favorites()

	def _select_unit(self, index):
		unit = self._unitsModel.get_unit(index)
		self._selectedUnitName.setText(unit.name)
		self._selectedUnitValue.setText(str(unit.value))
		self._selectedUnitSymbol.setText(unit.unit)

		self._selectedIndex = index
		self._app.add_recent(self._categoryName, self._unitsModel.get_unit(index).name)


def run_gonvert():
	app = QtGui.QApplication([])
	handle = Gonvert(app)
	if constants.PROFILE_STARTUP:
		return 0
	else:
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
