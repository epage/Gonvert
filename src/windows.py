#!/usr/bin/env python

from __future__ import with_statement
from __future__ import division

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import constants
import maeqt
from util import misc as misc_utils
import unit_data


_moduleLogger = logging.getLogger(__name__)


class FavoritesWindow(object):

	def __init__(self, parent, app, source, hidden):
		self._app = app
		self._source = list(source)
		self._hidden = hidden

		self._categories = QtGui.QTreeWidget()
		self._categories.setHeaderLabels(["Categories"])
		self._categories.setHeaderHidden(True)
		self._categories.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
		if not constants.IS_MAEMO:
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

		if constants.IS_MAEMO:
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
		if not constants.IS_MAEMO:
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

		if constants.IS_MAEMO:
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
		if not constants.IS_MAEMO:
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

		if constants.IS_MAEMO:
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
