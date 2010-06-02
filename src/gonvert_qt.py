#!/usr/bin/env python
# -*- coding: UTF8 -*-

from __future__ import with_statement

import sys
import os
import math
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import constants
from util import misc as misc_utils
import unit_data


_moduleLogger = logging.getLogger("gonvert_glade")


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
		self._appIconPath = appIconPath

		self._jumpWindow = None
		self._catWindow = None

		self._jumpAction = QtGui.QAction(None)
		self._jumpAction.setText("Quick Jump")
		self._jumpAction.setStatusTip("Search for a unit and jump straight to it")
		self._jumpAction.setToolTip("Search for a unit and jump straight to it")
		self._jumpAction.setShortcut(QtGui.QKeySequence("CTRL+j"))

		self.request_category()

	def request_category(self):
		if self._catWindow is not None:
			self._catWindow.close()
			self._catWindow = None
		self._catWindow = CategoryWindow(None, self)
		return self._catWindow

	def search_units(self):
		if self._jumpWindow is not None:
			self._jumpWindow.close()
			self._jumpWindow = None
		self._jumpWindow = QuickJump(None, self)
		return self._jumpWindow

	@property
	def appIconPath(self):
		return self._appIconPath

	@property
	def jumpAction(self):
		return self._jumpAction


class CategoryWindow(object):

	def __init__(self, parent, app):
		self._app = app
		self._unitWindow = None

		self._categories = QtGui.QTreeWidget()
		self._categories.setHeaderLabels(["Categories"])
		self._categories.itemClicked.connect(self._on_category_clicked)
		self._categories.setHeaderHidden(True)
		for catName in unit_data.UNIT_CATEGORIES:
			twi = QtGui.QTreeWidgetItem(self._categories)
			twi.setText(0, catName)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addWidget(self._categories)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		if parent is not None:
			self._window.setWindowModality(QtCore.Qt.WindowModal)
		self._window.setWindowTitle("%s - Categories" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(self._app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		viewMenu = self._window.menuBar().addMenu("&View")
		viewMenu.addAction(self._app.jumpAction)

		self._app.jumpAction.triggered.connect(self._on_jump_start)

		self._window.show()

	def close(self):
		self._window.close()

	def selectCategory(self, categoryName):
		if self._unitWindow is not None:
			self._unitWindow.close()
			self._unitWindow = None
		self._unitWindow = UnitWindow(self._window, categoryName, self._app)
		return self._unitWindow

	@misc_utils.log_exception(_moduleLogger)
	def _on_jump_start(self, checked = False):
		self._app.search_units()

	@misc_utils.log_exception(_moduleLogger)
	def _on_category_clicked(self, item, columnIndex):
		categoryName = unicode(item.text(0))
		self.selectCategory(categoryName)


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
		self._resultsBox.itemClicked.connect(self._on_result_clicked)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addLayout(self._entryLayout)
		self._layout.addWidget(self._resultsBox)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		if parent is not None:
			self._window.setWindowModality(QtCore.Qt.WindowModal)
		self._window.setWindowTitle("%s - Quick Jump" % constants.__pretty_app_name__)
		self._window.setWindowIcon(QtGui.QIcon(self._app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._window.show()

	def close(self):
		self._window.close()

	@misc_utils.log_exception(_moduleLogger)
	def _on_result_clicked(self, item, columnIndex):
		categoryName = unicode(item.text(0))
		unitName = unicode(item.text(1))
		catWindow = self._app.request_category()
		unitsWindow = catWindow.selectCategory(categoryName)
		unitsWindow.select_unit(unitName)

	@misc_utils.log_exception(_moduleLogger)
	def _on_search_edited(self, *args):
		userInput = self._searchEntry.text()
		if len(userInput) <  self.MINIMAL_ENTRY:
			return

		lowerInput = str(userInput).lower()
		for catIndex, category in enumerate(unit_data.UNIT_CATEGORIES):
			units = unit_data.get_units(category)
			for unitIndex, unit in enumerate(units):
				loweredUnit = unit.lower()
				if lowerInput in loweredUnit:
					twi = QtGui.QTreeWidgetItem(self._resultsBox)
					twi.setText(0, category)
					twi.setText(1, unit)


class UnitData(object):

	HEADERS = ["Name", "Value", "", "Unit"]
	ALIGNMENT = [QtCore.Qt.AlignLeft, QtCore.Qt.AlignRight, QtCore.Qt.AlignLeft, QtCore.Qt.AlignLeft]

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

		self._children = []
		for key in unit_data.get_units(self._categoryName):
			conversion, unit, description = self._unitData[key]
			self._children.append(UnitData(key, unit, description, conversion))

	@misc_utils.log_exception(_moduleLogger)
	def columnCount(self, parent):
		if parent.isValid():
			return 0
		else:
			return len(UnitData.HEADERS)

	@misc_utils.log_exception(_moduleLogger)
	def data(self, index, role):
		if not index.isValid():
			return None
		elif role == QtCore.Qt.TextAlignmentRole:
			return UnitData.ALIGNMENT[index.column()]
		elif role != QtCore.Qt.DisplayRole:
			return None

		item = index.internalPointer()
		if isinstance(item, UnitData):
			return item.data(index.column())
		elif item is UnitData.HEADERS:
			return item[index.column()]

	@misc_utils.log_exception(_moduleLogger)
	def sort(self, column, order = QtCore.Qt.AscendingOrder):
		isReverse = order == QtCore.Qt.AscendingOrder
		if column == 0:
			key_func = lambda item: item.name
		elif column in [1, 2]:
			key_func = lambda item: item.value
		elif column == 3:
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
		if not self.hasIndex(row, column, parent):
			return QtCore.QModelIndex()

		if parent.isValid():
			return QtCore.QModelIndex()

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
		return self._children[index]

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
			if i == fromIndex:
				continue
			func, arg = child.conversion
			newValue = func.from_base(base, arg)
			child.update_value(newValue)

		self._all_changed()

	def _all_changed(self):
		topLeft = self.createIndex(0, 1, self._children[0])
		bottomRight = self.createIndex(len(self._children)-1, 2, self._children[-1])
		self.dataChanged.emit(topLeft, bottomRight)

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


class UnitWindow(object):

	def __init__(self, parent, category, app):
		self._app = app
		self._categoryName = category
		self._selectedIndex = 0

		self._selectedUnitName = QtGui.QLabel()
		self._selectedUnitValue = QtGui.QLineEdit()
		self._selectedUnitValue.textEdited.connect(self._on_value_edited)
		self._selectedUnitSymbol = QtGui.QLabel()

		self._selectedUnitLayout = QtGui.QHBoxLayout()
		self._selectedUnitLayout.addWidget(self._selectedUnitName)
		self._selectedUnitLayout.addWidget(self._selectedUnitValue)
		self._selectedUnitLayout.addWidget(self._selectedUnitSymbol)

		self._unitsModel = UnitModel(self._categoryName)
		self._unitsView = QtGui.QTreeView()
		self._unitsView.setModel(self._unitsModel)
		self._unitsView.clicked.connect(self._on_unit_clicked)
		self._unitsView.setUniformRowHeights(True)
		self._unitsView.header().setSortIndicatorShown(True)
		self._unitsView.header().setClickable(True)
		self._unitsView.setSortingEnabled(True)
		if True:
			self._unitsView.setHeaderHidden(True)

		self._layout = QtGui.QVBoxLayout()
		self._layout.addLayout(self._selectedUnitLayout)
		self._layout.addWidget(self._unitsView)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		if parent is not None:
			self._window.setWindowModality(QtCore.Qt.WindowModal)
		self._window.setWindowTitle("%s - %s" % (constants.__pretty_app_name__, category))
		self._window.setWindowIcon(QtGui.QIcon(app.appIconPath))
		self._window.setCentralWidget(centralWidget)

		self._select_unit(0)

		self._sortActionGroup = QtGui.QActionGroup(None)
		self._sortByNameAction = QtGui.QAction(self._sortActionGroup)
		self._sortByNameAction.setText("Sort By Name")
		self._sortByNameAction.setStatusTip("Sort the units by name")
		self._sortByNameAction.setToolTip("Sort the units by name")
		self._sortByValueAction = QtGui.QAction(self._sortActionGroup)
		self._sortByValueAction.setText("Sort By Value")
		self._sortByValueAction.setStatusTip("Sort the units by value")
		self._sortByValueAction.setToolTip("Sort the units by value")
		self._sortByUnitAction = QtGui.QAction(self._sortActionGroup)
		self._sortByUnitAction.setText("Sort By Unit")
		self._sortByUnitAction.setStatusTip("Sort the units by unit")
		self._sortByUnitAction.setToolTip("Sort the units by unit")

		viewMenu = self._window.menuBar().addMenu("&View")
		viewMenu.addAction(self._app.jumpAction)
		viewMenu.addSeparator()
		viewMenu.addAction(self._sortByNameAction)
		viewMenu.addAction(self._sortByValueAction)
		viewMenu.addAction(self._sortByUnitAction)

		self._app.jumpAction.triggered.connect(self._on_jump_start)
		self._sortByNameAction.triggered.connect(self._on_sort_by_name)
		self._sortByValueAction.triggered.connect(self._on_sort_by_value)
		self._sortByUnitAction.triggered.connect(self._on_sort_by_unit)

		self._window.show()

	def close(self):
		self._window.close()

	def select_unit(self, unitName):
		index = self._unitsModel.index_unit(unitName)
		self._select_unit(index)

	@misc_utils.log_exception(_moduleLogger)
	def _on_sort_by_name(self, checked = False):
		self._unitsModel.sort(0, QtCore.Qt.DescendingOrder)

	@misc_utils.log_exception(_moduleLogger)
	def _on_sort_by_value(self, checked = False):
		self._unitsModel.sort(1)

	@misc_utils.log_exception(_moduleLogger)
	def _on_sort_by_unit(self, checked = False):
		self._unitsModel.sort(3, QtCore.Qt.DescendingOrder)

	@misc_utils.log_exception(_moduleLogger)
	def _on_jump_start(self, checked = False):
		self._app.search_units()

	@misc_utils.log_exception(_moduleLogger)
	def _on_unit_clicked(self, index):
		self._select_unit(index.row())

	@misc_utils.log_exception(_moduleLogger)
	def _on_value_edited(self, *args):
		userInput = self._selectedUnitValue.text()
		self._unitsModel.update_values(self._selectedIndex, str(userInput))

	def _select_unit(self, index):
		unit = self._unitsModel.get_unit(index)
		self._selectedUnitName.setText(unit.name)
		self._selectedUnitValue.setText(str(unit.value))
		self._selectedUnitSymbol.setText(unit.unit)

		self._selectedIndex = index
		qindex = self._unitsModel.createIndex(index, 0, self._unitsModel.get_unit(index))
		self._unitsView.scrollTo(qindex)


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
