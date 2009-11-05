#!/usr/bin/env python
# -*- coding: UTF8 -*-

"""
@todo Look into using two columns for displaying the value, split by the
decimal place.  The left one would be right aligned and the right would be left
aligned (only if not in exponential notation
OR display everything in engineering notation

@tood Add a unit description dialog for when hildonized

@todo Add support for custom units

@todo Add support for compound units
"""

import os
import pickle
import logging

import pango
import gobject
import gtk
import gtk.glade
import gtk.gdk

import constants
import hildonize
import unit_data

try:
	import gettext
except ImportError:
	_ = lambda x: x
	gettext = None
else:
	_ = gettext.gettext


_moduleLogger = logging.getLogger("gonvert_glade")
PROFILE_STARTUP = False
FORCE_HILDON_LIKE = True

if gettext is not None:
	gettext.bindtextdomain('gonvert', '/usr/share/locale')
	gettext.textdomain('gonvert')


def change_menu_label(widgets, labelname, newtext):
	item_label = widgets.get_widget(labelname).get_children()[0]
	item_label.set_text(newtext)


class Gonvert(object):

	_glade_files = [
		os.path.join(os.path.dirname(__file__), "gonvert.glade"),
		os.path.join(os.path.dirname(__file__), "../data/gonvert.glade"),
		os.path.join(os.path.dirname(__file__), "../lib/gonvert.glade"),
		'/usr/share/gonvert/gonvert.glade',
		'/usr/lib/gonvert/gonvert.glade',
	]

	UNITS_NAME_IDX = 0
	UNITS_VALUE_IDX = 1
	UNITS_SYMBOL_IDX = 2

	def __init__(self):
		self._unitDataInCategory = None
		self._unit_sort_direction = False
		self._value_sort_direction = False
		self._units_sort_direction = False
		self._isFullScreen = False

		self._find_result = [] # empty find result list
		self._findIndex = 0 # default to find result number zero

		self._selectedCategoryName = '' # preset to no selected category
		self._defaultUnitForCategory = {} # empty dictionary for later use

		#check to see if glade file is in current directory (user must be
		# running from download untar directory)
		for gladePath in self._glade_files:
			if os.path.isfile(gladePath):
				homepath = os.path.dirname(gladePath)
				pixmapspath = "/".join((homepath, "pixmaps"))
				widgets = gtk.glade.XML(gladePath)
				break
		else:
			_moduleLogger.error("UI Descriptor not found!")
			gtk.main_quit()
			return

		self._mainWindow = widgets.get_widget('mainWindow')
		self._app = hildonize.get_app_class()()
		self._mainWindow = hildonize.hildonize_window(self._app, self._mainWindow)

		change_menu_label(widgets, 'fileMenuItem', _('File'))
		change_menu_label(widgets, 'exitMenuItem', _('Exit'))
		change_menu_label(widgets, 'toolsMenuItem', _('Tools'))
		change_menu_label(widgets, 'clearSelectionMenuItem', _('Clear selections'))
		change_menu_label(widgets, 'helpMenuItem', _('Help'))
		change_menu_label(widgets, 'aboutMenuItem', _('About'))
		change_menu_label(widgets, 'findButton', _('Find'))

		self._shortlistcheck = widgets.get_widget('shortlistcheck')
		self._toggleShortList = widgets.get_widget('toggleShortList')

		self._categorySelectionButton = widgets.get_widget("categorySelectionButton")
		self._categoryView = widgets.get_widget('categoryView')

		self._unitsView = widgets.get_widget('unitsView')
		self._unitsView.set_property('rules_hint', 1)
		self._unitsView_selection = self._unitsView.get_selection()

		self._unitName = widgets.get_widget('unitName')
		self._unitValue = widgets.get_widget('unitValue')
		self._previousUnitName = widgets.get_widget('previousUnitName')
		self._previousUnitValue = widgets.get_widget('previousUnitValue')

		self._unitSymbol = widgets.get_widget('unitSymbol')
		self._previousUnitSymbol = widgets.get_widget('previousUnitSymbol')

		self._unitDescription = widgets.get_widget('unitDescription')

		self._searchLayout = widgets.get_widget('searchLayout')
		self._searchLayout.hide()
		self._findEntry = widgets.get_widget('findEntry')
		self._findLabel = widgets.get_widget('findLabel')
		self._findButton = widgets.get_widget('findButton')

		#insert a self._categoryColumnumn into the units list even though the heading will not be seen
		renderer = gtk.CellRendererText()
		renderer.set_property("ellipsize", pango.ELLIPSIZE_END)
		renderer.set_property("width-chars", len("grams per cubic cm plus some"))
		hildonize.set_cell_thumb_selectable(renderer)
		self._unitNameColumn = gtk.TreeViewColumn(_('Name'), renderer)
		self._unitNameColumn.set_property('resizable', 1)
		self._unitNameColumn.add_attribute(renderer, 'text', self.UNITS_NAME_IDX)
		self._unitNameColumn.set_clickable(True)
		self._unitNameColumn.connect("clicked", self._on_click_unit_column)
		self._unitsView.append_column(self._unitNameColumn)

		renderer = gtk.CellRendererText()
		hildonize.set_cell_thumb_selectable(renderer)
		self._unitValueColumn = gtk.TreeViewColumn(_('Value'), renderer)
		self._unitValueColumn.set_property('resizable', 1)
		self._unitValueColumn.add_attribute(renderer, 'text', self.UNITS_VALUE_IDX)
		self._unitValueColumn.set_clickable(True)
		self._unitValueColumn.connect("clicked", self._on_click_unit_column)
		self._unitsView.append_column(self._unitValueColumn)

		renderer = gtk.CellRendererText()
		renderer.set_property("ellipsize", pango.ELLIPSIZE_END)
		renderer.set_property("width-chars", len("G ohm plus some"))
		hildonize.set_cell_thumb_selectable(renderer)
		self._unitSymbolColumn = gtk.TreeViewColumn(_('Units'), renderer)
		self._unitSymbolColumn.set_property('resizable', 1)
		self._unitSymbolColumn.add_attribute(renderer, 'text', self.UNITS_SYMBOL_IDX)
		self._unitSymbolColumn.set_clickable(True)
		self._unitSymbolColumn.connect("clicked", self._on_click_unit_column)
		self._unitsView.append_column(self._unitSymbolColumn)

		self._unitModel = gtk.ListStore(
			gobject.TYPE_STRING, # UNITS_NAME_IDX
			gobject.TYPE_STRING, # UNITS_VALUE_IDX
			gobject.TYPE_STRING, # UNITS_SYMBOL_IDX
		)
		self._sortedUnitModel = gtk.TreeModelSort(self._unitModel)
		columns = self._get_column_sort_stuff()
		for columnIndex, (column, sortDirection, col_cmp) in enumerate(columns):
			self._sortedUnitModel.set_sort_func(columnIndex, col_cmp)
		self._unitsView.set_model(self._sortedUnitModel)

		#Insert a column into the category list even though the heading will not be seen
		renderer = gtk.CellRendererText()
		self._categoryColumn = gtk.TreeViewColumn('Title', renderer)
		self._categoryColumn.set_property('resizable', 1)
		self._categoryColumn.add_attribute(renderer, 'text', 0)
		self._categoryView.append_column(self._categoryColumn)

		self._categoryModel = gtk.ListStore(gobject.TYPE_STRING)
		self._categoryView.set_model(self._categoryModel)
		#colourize each row differently for easier reading
		self._categoryView.set_property('rules_hint', 1)

		#Populate the catagories list
		for key in unit_data.UNIT_CATEGORIES:
			row = (key, )
			self._categoryModel.append(row)

		#--------- connections to GUI ----------------
		self._mainWindow.connect("delete-event", self._on_user_exit)
		self._mainWindow.connect("key-press-event", self._on_key_press)
		self._mainWindow.connect("window-state-event", self._on_window_state_change)
		self._categorySelectionButton.connect("clicked", self._on_category_selector_clicked)
		self._categoryView.connect("cursor-changed", self._on_click_category)
		self._findButton.connect("clicked", self._on_find_activate)
		self._findEntry.connect("activate", self._on_find_activate)
		self._findEntry.connect("changed", self._on_findEntry_changed)
		self._previousUnitValue.connect("changed", self._on_previous_unit_value_changed)
		self._shortlistcheck.connect("toggled", self._on_shortlist_changed)
		self._unitValue.connect("changed", self._on_unit_value_changed)
		self._unitsView.connect("cursor-changed", self._on_click_unit)
		if hildonize.GTK_MENU_USED:
			widgets.get_widget("aboutMenuItem").connect("activate", self._on_about_clicked)
			widgets.get_widget("clearSelectionMenuItem").connect("activate", self._on_user_clear_selections)
			widgets.get_widget("editShortListMenuItem").connect("activate", self._on_edit_shortlist)
			widgets.get_widget("exitMenuItem").connect("activate", self._on_user_exit)

		for scrollingWidgetName in (
			"unitsViewScrolledWindow",
		):
			scrollingWidget = widgets.get_widget(scrollingWidgetName)
			assert scrollingWidget is not None, scrollingWidgetName
			hildonize.hildonize_scrollwindow_with_viewport(scrollingWidget)

		if hildonize.IS_HILDON_SUPPORTED or FORCE_HILDON_LIKE:
			self._categoryView.get_parent().hide()
			self._unitsView.set_headers_visible(False)
			self._previousUnitName.get_parent().hide()
			self._unitDescription.get_parent().get_parent().hide()
		else:
			self._categorySelectionButton.hide()

		replacementButtons = []
		menu = hildonize.hildonize_menu(
			self._mainWindow,
			widgets.get_widget("mainMenuBar"),
			replacementButtons
		)

		if not hildonize.IS_HILDON_SUPPORTED:
			_moduleLogger.info("No hildonization support")

		hildonize.set_application_title(
			self._mainWindow, "%s - Unit Conversion Utility" % constants.__pretty_app_name__
		)
		iconPath = pixmapspath + '/gonvert.png'
		if os.path.exists(iconPath):
			self._mainWindow.set_icon(gtk.gdk.pixbuf_new_from_file(iconPath))
		else:
			_moduleLogger.warn("Error: Could not find gonvert icon: %s" % iconPath)

		self._load_settings()
		self._mainWindow.show()

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
				self._mainWindow.resize(a, b)

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
			'size': self._mainWindow.get_size()
		}
		windowDatPath = "/".join((constants._data_path_, "window.dat"))
		pickle.dump(window_settings, open(windowDatPath, 'w'))

	def _clear_find(self):
		# switch to "new find" state
		self._find_result = []
		self._findIndex = 0

		# Clear our user message
		self._findLabel.set_text('')

	def _find_first(self):
		assert len(self._find_result) == 0
		assert self._findIndex == 0
		findString = self._findEntry.get_text().strip().lower()
		if not findString:
			return

		# Gather info on all the matching units from all categories
		for catIndex, category in enumerate(unit_data.UNIT_CATEGORIES):
			units = unit_data.get_units(category)
			for unitIndex, unit in enumerate(units):
				loweredUnit = unit.lower()
				if loweredUnit in findString or findString in loweredUnit:
					self._find_result.append((category, unit, catIndex, unitIndex))

	def _update_find_selection(self):
		assert 0 < len(self._find_result)

		#check if next find is in a new category (prevent category changes when unnecessary
		searchCategoryName = self._find_result[self._findIndex][0]
		if self._selectedCategoryName != searchCategoryName:
			self._categorySelectionButton.get_child().set_markup("<big>%s</big>" % searchCategoryName)
			self._categoryView.set_cursor(
				self._find_result[self._findIndex][2], self._categoryColumn, False
			)

		self._unitsView.set_cursor(
			self._find_result[self._findIndex][3], self._unitNameColumn, True
		)

	def _find_next(self):
		if len(self._find_result) == 0:
			self._find_first()
		else:
			if self._findIndex == len(self._find_result)-1:
				self._findIndex = 0
			else:
				self._findIndex += 1

		if not self._find_result:
			self._findLabel.set_text('Text not found')
		else:
			self._update_find_selection()
			resultsLeft = len(self._find_result) - self._findIndex - 1
			self._findLabel.set_text(
				'%s result(s) left' % (resultsLeft, )
			)

	def _find_previous(self):
		if len(self._find_result) == 0:
			self._find_first()
		else:
			if self._findIndex == 0:
				self._findIndex = len(self._find_result)-1
			else:
				self._findIndex -= 1

		if not self._find_result:
			self._findLabel.set_text('Text not found')
		else:
			self._update_find_selection()
			resultsLeft = len(self._find_result) - self._findIndex - 1
			self._findLabel.set_text(
				'%s result(s) left' % (resultsLeft, )
			)

	def _toggle_find(self):
		if self._searchLayout.get_property("visible"):
			self._searchLayout.hide()
			self._unitsView.grab_focus()
		else:
			self._searchLayout.show()
			self._findEntry.grab_focus()

	def _unit_model_cmp(self, sortedModel, leftItr, rightItr):
		leftUnitText = self._unitModel.get_value(leftItr, 0)
		rightUnitText = self._unitModel.get_value(rightItr, 0)
		return cmp(leftUnitText, rightUnitText)

	def _symbol_model_cmp(self, sortedModel, leftItr, rightItr):
		leftSymbolText = self._unitModel.get_value(leftItr, 2)
		rightSymbolText = self._unitModel.get_value(rightItr, 2)
		return cmp(leftSymbolText, rightSymbolText)

	def _value_model_cmp(self, sortedModel, leftItr, rightItr):
		#special sorting exceptions for ascii values (instead of float values)
		if self._selectedCategoryName == "Computer Numbers":
			leftValue = self._unitModel.get_value(leftItr, 1)
			rightValue = self._unitModel.get_value(rightItr, 1)
		else:
			leftValueText = self._unitModel.get_value(leftItr, 1)
			leftValue = float(leftValueText) if leftValueText else 0.0

			rightValueText = self._unitModel.get_value(rightItr, 1)
			rightValue = float(rightValueText) if rightValueText else 0.0
		return cmp(leftValue, rightValue)

	def _get_column_sort_stuff(self):
		columns = (
			(self._unitNameColumn, "_unit_sort_direction", self._unit_model_cmp),
			(self._unitValueColumn, "_value_sort_direction", self._value_model_cmp),
			(self._unitSymbolColumn, "_units_sort_direction", self._symbol_model_cmp),
		)
		return columns

	def _switch_category(self, category):
		self._selectedCategoryName = category
		self._unitDataInCategory = unit_data.UNIT_DESCRIPTIONS[self._selectedCategoryName]

		#Fill up the units descriptions and clear the value cells
		self._clear_visible_unit_data()
		for key in unit_data.get_units(self._selectedCategoryName):
			iter = self._unitModel.append()
			self._unitModel.set(iter, 0, key, 1, '', 2, self._unitDataInCategory[key][1])
		self._sortedUnitModel.sort_column_changed()

		self._select_default_unit()

	def _clear_visible_unit_data(self):
		self._unitDescription.get_buffer().set_text("")
		self._unitName.set_text('')
		self._unitValue.set_text('')
		self._unitSymbol.set_text('')

		self._previousUnitName.set_text('')
		self._previousUnitValue.set_text('')
		self._previousUnitSymbol.set_text('')

		self._unitModel.clear()

	def _select_default_unit(self):
		# Restore the previous historical settings of previously selected units
		# in this newly selected category
		defaultPrimary = unit_data.get_base_unit(self._selectedCategoryName)
		defaultSecondary = ""
		if self._selectedCategoryName in self._defaultUnitForCategory:
			if self._defaultUnitForCategory[self._selectedCategoryName][0]:
				defaultPrimary = self._defaultUnitForCategory[self._selectedCategoryName][0]
			if self._defaultUnitForCategory[self._selectedCategoryName][1]:
				defaultSecondary = self._defaultUnitForCategory[self._selectedCategoryName][1]

		units = unit_data.get_units(self._selectedCategoryName)

		#Restore oldest selection first.
		if defaultPrimary:
			try:
				unitIndex = units.index(defaultPrimary)
			except ValueError:
				unitIndex = 0
			self._unitsView.set_cursor(unitIndex, self._unitNameColumn, True)

		#Restore newest selection second.
		if defaultSecondary:
			try:
				unitIndex = units.index(defaultSecondary)
			except ValueError:
				unitIndex = 0
			self._unitsView.set_cursor(unitIndex, self._unitNameColumn, True)

		# select the text so user can start typing right away
		self._unitValue.grab_focus()
		self._unitValue.select_region(0, -1)

	def _sanitize_value(self, userEntry):
		if self._selectedCategoryName == "Computer Numbers":
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

	def _on_shortlist_changed(self, *args):
		try:
			raise NotImplementedError("%s" % self._shortlistcheck.get_active())
		except Exception:
			_moduleLogger.exception("_on_shortlist_changed")

	def _on_edit_shortlist(self, *args):
		try:
			raise NotImplementedError("%s" % self._toggleShortList.get_active())
		except Exception:
			_moduleLogger.exception("_on_edit_shortlist")

	def _on_user_clear_selections(self, *args):
		try:
			selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
			os.remove(selectionsDatPath)
			self._defaultUnitForCategory = {}
		except Exception:
			_moduleLogger.exception("_on_user_clear_selections")

	def _on_key_press(self, widget, event, *args):
		"""
		@note Hildon specific
		"""
		RETURN_TYPES = (gtk.keysyms.Return, gtk.keysyms.ISO_Enter, gtk.keysyms.KP_Enter)
		try:
			if (
				event.keyval == gtk.keysyms.F6 or
				event.keyval in RETURN_TYPES and event.get_state() & gtk.gdk.CONTROL_MASK
			):
				if self._isFullScreen:
					self._mainWindow.unfullscreen()
				else:
					self._mainWindow.fullscreen()
			elif event.keyval == gtk.keysyms.f and event.get_state() & gtk.gdk.CONTROL_MASK:
				self._toggle_find()
			elif event.keyval == gtk.keysyms.p and event.get_state() & gtk.gdk.CONTROL_MASK:
				self._find_previous()
			elif event.keyval == gtk.keysyms.n and event.get_state() & gtk.gdk.CONTROL_MASK:
				self._find_next()
		except Exception, e:
			_moduleLogger.exception("_on_key_press")

	def _on_window_state_change(self, widget, event, *args):
		"""
		@note Hildon specific
		"""
		try:
			if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
				self._isFullScreen = True
			else:
				self._isFullScreen = False
		except Exception, e:
			_moduleLogger.exception("_on_window_state_change")

	def _on_findEntry_changed(self, *args):
		"""
		Clear out find results since the user wants to look for something new
		"""
		try:
			self._clear_find()
		except Exception:
			_moduleLogger.exception("_on_findEntry_changed")

	def _on_find_activate(self, *args):
		try:
			self._find_next()
			self._findButton.grab_focus()
		except Exception:
			_moduleLogger.exception("_on_find_activate")

	def _on_click_unit_column(self, col):
		"""
		Sort the contents of the col when the user clicks on the title.
		"""
		try:
			#Determine which column requires sorting
			columns = self._get_column_sort_stuff()
			for columnIndex, (maybeCol, directionName, col_cmp) in enumerate(columns):
				if col is maybeCol:
					direction = getattr(self, directionName)
					gtkDirection = gtk.SORT_ASCENDING if direction else gtk.SORT_DESCENDING

					# cause a sort
					self._sortedUnitModel.set_sort_column_id(columnIndex, gtkDirection)

					# set the visual for sorting
					col.set_sort_indicator(True)
					col.set_sort_order(not direction)

					setattr(self, directionName, not direction)
					break
				else:
					maybeCol.set_sort_indicator(False)
			else:
				assert False, "Unknown column: %s" % (col.get_title(), )
		except Exception:
			_moduleLogger.exception("_on_click_unit_column")

	def _on_category_selector_clicked(self, *args):
		try:
			currenntIndex = unit_data.UNIT_CATEGORIES.index(self._selectedCategoryName)
			newIndex = hildonize.touch_selector(
				self._mainWindow,
				"Categories",
				unit_data.UNIT_CATEGORIES,
				currenntIndex,
			)

			selectedCategoryName = unit_data.UNIT_CATEGORIES[newIndex]
			self._categorySelectionButton.set_label(selectedCategoryName)
			self._categoryView.set_cursor(newIndex, self._categoryColumn, False)
			self._categoryView.grab_focus()
		except Exception:
			_moduleLogger.exception("_on_category_selector_clicked")

	def _on_click_category(self, *args):
		try:
			selected, iter = self._categoryView.get_selection().get_selected()
			if iter is None:
				# User is typing in an invalid string, not selecting any category
				return
			selectedCategory = self._categoryModel.get_value(iter, 0)
			self._switch_category(selectedCategory)
		except Exception:
			_moduleLogger.exception("_on_click_category")

	def _on_click_unit(self, *args):
		try:
			selected, iter = self._unitsView.get_selection().get_selected()
			selected_unit = selected.get_value(iter, 0)
			unit_spec = self._unitDataInCategory[selected_unit]

			showSymbol = False

			if self._unitName.get_text() != selected_unit:
				self._previousUnitName.set_text(self._unitName.get_text())
				self._previousUnitValue.set_text(self._unitValue.get_text())
				self._previousUnitSymbol.set_text(self._unitSymbol.get_text())
				if self._unitSymbol.get_text():
					showSymbol = True

			self._unitName.set_text(selected_unit)
			self._unitValue.set_text(selected.get_value(iter, 1))
			buffer = self._unitDescription.get_buffer()
			buffer.set_text(unit_spec[2])
			self._unitSymbol.set_text(unit_spec[1]) # put units into label text
			if unit_spec[1]:
				showSymbol = True
			else:
				showSymbol = False

			if showSymbol:
				self._unitSymbol.show()
				self._previousUnitSymbol.show()
			else:
				self._unitSymbol.hide()
				self._previousUnitSymbol.hide()

			if self._unitValue.get_text() == '':
				if self._selectedCategoryName == "Computer Numbers":
					self._unitValue.set_text("0")
				else:
					self._unitValue.set_text("0.0")

			self._defaultUnitForCategory[self._selectedCategoryName] = [
				self._unitName.get_text(), self._previousUnitName.get_text()
			]

			# select the text so user can start typing right away
			self._unitValue.grab_focus()
			self._unitValue.select_region(0, -1)
		except Exception:
			_moduleLogger.exception("_on_click_unit")

	def _on_unit_value_changed(self, *args):
		try:
			if self._unitName.get_text() == '':
				return
			if not self._unitValue.is_focus():
				return

			#retrieve the conversion function and value from the selected unit
			value = self._sanitize_value(self._unitValue.get_text())
			func, arg = self._unitDataInCategory[self._unitName.get_text()][0]
			base = func.to_base(value, arg)

			#point to the first row
			for row in self._unitModel:
				func, arg = self._unitDataInCategory[row[0]][0]
				row[1] = str(func.from_base(base, arg))

			# Update the secondary unit entry
			if self._previousUnitName.get_text() != '':
				func, arg = self._unitDataInCategory[self._previousUnitName.get_text()][0]
				self._previousUnitValue.set_text(str(func.from_base(base, arg, )))
		except Exception:
			_moduleLogger.exception("_on_unit_value_changed")

	def _on_previous_unit_value_changed(self, *args):
		try:
			if self._previousUnitName.get_text() == '':
				return
			if not self._previousUnitValue.is_focus():
				return

			#retrieve the conversion function and value from the selected unit
			value = self._sanitize_value(self._previousUnitValue.get_text())
			func, arg = self._unitDataInCategory[self._previousUnitName.get_text()][0]
			base = func.to_base(value, arg)

			#point to the first row
			for row in self._unitModel:
				func, arg = self._unitDataInCategory[row[0]][0]
				row[1] = str(func.from_base(base, arg))

			# Update the primary unit entry
			func, arg = self._unitDataInCategory[self._unitName.get_text()][0]
			self._unitValue.set_text(str(func.from_base(base, arg, )))
		except Exception:
			_moduleLogger.exception("_on_previous_unit_value_changed")

	def _on_about_clicked(self, a):
		dlg = gtk.AboutDialog()
		dlg.set_name(constants.__pretty_app_name__)
		dlg.set_version("%s-%d" % (constants.__version__, constants.__build__))
		dlg.set_copyright("Copyright 2009 - GPL")
		dlg.set_comments("")
		dlg.set_website("http://unihedron.com/projects/gonvert/gonvert.php")
		dlg.set_authors(["Anthony Tekatch <anthony@unihedron.com>", "Ed Page <edpage@byu.net>"])
		dlg.run()
		dlg.destroy()

	def _on_user_exit(self, *args):
		try:
			self._save_settings()
		except Exception:
			_moduleLogger.exception("_on_user_exit")
		finally:
			gtk.main_quit()


def run_gonvert():
	gtk.gdk.threads_init()
	if hildonize.IS_HILDON_SUPPORTED:
		gtk.set_application_name(constants.__pretty_app_name__)
	handle = Gonvert()
	if not PROFILE_STARTUP:
		gtk.main()


if __name__ == "__main__":
	logging.basicConfig(level = logging.DEBUG)
	try:
		os.makedirs(constants._data_path_)
	except OSError, e:
		if e.errno != 17:
			raise

	run_gonvert()
