#!/usr/bin/env python
# -*- coding: UTF8 -*-

import os
import pickle
import string
import gettext
import logging

import gobject
import gtk
import gtk.glade
import gtk.gdk

import constants
import unit_data


_moduleLogger = logging.getLogger("gonvert_glade")

gettext.bindtextdomain('gonvert', '/usr/share/locale')
gettext.textdomain('gonvert')
_ = gettext.gettext


def change_menu_label(widgets, labelname, newtext):
	item_label = widgets.get_widget(labelname).get_children()[0]
	item_label.set_text(newtext)


class Gonvert(object):

	_glade_files = [
		os.path.join(os.path.dirname(__file__), "gonvert.glade"),
		os.path.join(os.path.dirname(__file__), "../data/gonvert.glade"),
		os.path.join(os.path.dirname(__file__), "../lib/gonvert.glade"),
		'/usr/lib/gonvert/gonvert.glade',
	]

	def __init__(self):
		self._unitDataInCategory = None
		self._calcsuppress = False
		self._unit_sort_direction = False
		self._value_sort_direction = False
		self._units_sort_direction = False

		self._find_result = [] # empty find result list
		self._find_count = 0 # default to find result number zero

		self._selected_category = '' # preset to no selected category
		self._selected_units = {} # empty dictionary for later use

		#check to see if glade file is in current directory (user must be
		# running from download untar directory)
		for gladePath in self._glade_files:
			if os.path.isfile(gladePath):
				homepath = os.path.dirname(gladePath)
				pixmapspath = "/".join((homepath, "pixmaps"))
				widgets = gtk.glade.XML(gladePath)
				break
		else:
			return

		self._mainWindow = widgets.get_widget('mainWindow')

		change_menu_label(widgets, 'fileMenuItem', _('File'))
		change_menu_label(widgets, 'exitMenuItem', _('Exit'))
		change_menu_label(widgets, 'toolsMenuItem', _('Tools'))
		change_menu_label(widgets, 'clearSelectionMenuItem', _('Clear selections'))
		change_menu_label(widgets, 'writeUnitsMenuItem', _('Write Units'))
		change_menu_label(widgets, 'helpMenuItem', _('Help'))
		change_menu_label(widgets, 'aboutMenuItem', _('About'))
		change_menu_label(widgets, 'findButton', _('Find'))

		self._shortlistcheck = widgets.get_widget('shortlistcheck')
		self._toggleShortList = widgets.get_widget('toggleShortList')

		self._categoryView = widgets.get_widget('categoryView')

		self._unitsView = widgets.get_widget('unitsView')
		self._unitsView_selection = self._unitsView.get_selection()

		self._unitName = widgets.get_widget('unitName')
		self._unitValue = widgets.get_widget('unitValue')
		self._previousUnitName = widgets.get_widget('previousUnitName')
		self._previousUnitValue = widgets.get_widget('previousUnitValue')
		messagebox = widgets.get_widget('msgbox')
		messageboxtext = widgets.get_widget('msgboxtext')

		self._unitSymbol = widgets.get_widget('unitSymbol')
		self._previousUnitSymbol = widgets.get_widget('previousUnitSymbol')

		self._unitDescription = widgets.get_widget('unitDescription')

		self._findEntry = widgets.get_widget('findEntry')
		self._findLabel = widgets.get_widget('findLabel')
		findButton = widgets.get_widget('findButton')
		ToolTips = gtk.Tooltips()
		ToolTips.set_tip(findButton, _(u'Find unit (F6)'))

		#insert a self._categoryColumnumn into the units list even though the heading will not be seen
		renderer = gtk.CellRendererText()
		self._unitNameColumn = gtk.TreeViewColumn(_('Unit Name'), renderer)
		self._unitNameColumn.set_property('resizable', 1)
		self._unitNameColumn.add_attribute(renderer, 'text', 0)
		self._unitNameColumn.set_clickable(True)
		self._unitNameColumn.connect("clicked", self._on_click_unit_column)
		self._unitsView.append_column(self._unitNameColumn)

		self._unitValueColumn = gtk.TreeViewColumn(_('Value'), renderer)
		self._unitValueColumn.set_property('resizable', 1)
		self._unitValueColumn.add_attribute(renderer, 'text', 1)
		self._unitValueColumn.set_clickable(True)
		self._unitValueColumn.connect("clicked", self._on_click_unit_column)
		self._unitsView.append_column(self._unitValueColumn)

		self._unitSymbolColumn = gtk.TreeViewColumn(_('Units'), renderer)
		self._unitSymbolColumn.set_property('resizable', 1)
		self._unitSymbolColumn.add_attribute(renderer, 'text', 2)
		self._unitSymbolColumn.set_clickable(True)
		self._unitSymbolColumn.connect("clicked", self._on_click_unit_column)
		self._unitsView.append_column(self._unitSymbolColumn)

		self._unitModel = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
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
			iter = self._categoryModel.append()
			self._categoryModel.set(iter, 0, key)

		#--------- connections to GUI ----------------
		dic = {
			"on_exit_menu_activate": self._on_user_exit,
			"on_main_window_destroy": self._on_user_exit,
			"on_categoryView_select_row": self._on_click_category,
			"on_unitValue_changed": self._on_unit_value_changed,
			"on_previousUnitValue_changed": self._on_previous_unit_value_changed,
			"on_writeUnitsMenuItem_activate": self._on_user_write_units,
			"on_findButton_clicked": self._on_find_activate,
			"on_findEntry_activated": self._on_find_activate,
			"on_findEntry_changed": self._on_findEntry_changed,
			"on_aboutMenuItem_activate": self._on_about_clicked,
			"on_messagebox_ok_clicked": self.messagebox_ok_clicked,
			"on_clearSelectionMenuItem_activate": self._on_user_clear_selections,
			"on_unitsView_cursor_changed": self._on_click_unit,
			"on_shortlistcheck_toggled": self._on_shortlist_changed,
			"on_toggleShortList_activate": self._on_edit_shortlist,
		}
		widgets.signal_autoconnect(dic)

		self._mainWindow.set_title('gonvert- %s - Unit Conversion Utility' % constants.__version__)
		iconPath = pixmapspath + '/gonvert.png'
		if os.path.exists(iconPath):
			self._mainWindow.set_icon(gtk.gdk.pixbuf_new_from_file(iconPath))
		else:
			_moduleLogger.warn("Error: Could not find gonvert icon: %s" % iconPath)

		self._load_settings()

	def _load_settings(self):
		#Restore window size from previously saved settings if it exists and is valid.
		windowDatPath = "/".join((constants._data_path_, "window.dat"))
		if os.path.exists(windowDatPath):
			#Retrieving previous window settings from ~/.gonvert/window.dat
			saved_window = pickle.load(open(windowDatPath, "r"))
			#If the 'size' has been stored, then extract size from saved_window.
			if 'size' in saved_window:
				a, b = saved_window['size']
				self._mainWindow.resize(a, b)
			else:
				#Maximize if no previous size was found
				#self._mainWindow.maximize()
				pass
		else:
			#Maximize if no previous window.dat file was found
			#self._mainWindow.maximize()
			pass

		#Restore selections from previously saved settings if it exists and is valid.
		historical_catergory_found = False
		selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
		if os.path.exists(selectionsDatPath):
			#Retrieving previous selections from ~/.gonvert/selections.dat
			selections = pickle.load(open(selectionsDatPath, 'r'))
			#Restoring previous selections.
			#If the 'selected_unts' has been stored, then extract self._selected_units from selections.
			if 'selected_units' in selections:
				self._selected_units = selections['selected_units']
			#Make sure that the 'self._selected_category' has been stored.
			if 'selected_category' in selections:
				#Match an available category to the previously selected category.
				for counter in range(len(unit_data.UNIT_CATEGORIES)):
					if selections['selected_category'] == unit_data.UNIT_CATEGORIES[counter]:
						# Restore the previously selected category.
						self._categoryView.set_cursor(counter, self._categoryColumn, False)
						self._categoryView.grab_focus()
				historical_catergory_found = True

		if not historical_catergory_found:
			print "Couldn't find saved category, using default."
			#If historical records were not kept then default to
			# put the focus on the first category
			self._categoryView.set_cursor(0, self._categoryColumn, False)
			self._categoryView.grab_focus()

		self.restore_units()

	def _save_settings(self):
		"""
		This routine saves the selections to a file, and
		should therefore only be called when exiting the program.

		Update selections dictionary which consists of the following keys:
		'self._selected_category': full name of selected category
		'self._selected_units': self._selected_units dictionary which contains:
		[categoryname: #1 displayed unit, #2 displayed unit]
		"""
		#Determine the contents of the selected category row
		selected, iter = self._categoryView.get_selection().get_selected()
		self._selected_category = self._categoryModel.get_value(iter, 0)

		selections = {
			'selected_category': self._selected_category,
			'selected_units': self._selected_units
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
		self._find_count = 0

		# Clear our user message
		self._findLabel.set_text('')

	def _find_first(self):
		assert len(self._find_result) == 0
		assert self._find_count == 0
		findString = string.lower(string.strip(self._findEntry.get_text()))
		if not findString:
			return

		# Gather info on all the matching units from all categories
		for catIndex, category in enumerate(unit_data.UNIT_CATEGORIES):
			units = unit_data.get_units(category)
			for unitIndex, unit in enumerate(units):
				loweredUnit = unit.lower()
				if loweredUnit in findString or findString in loweredUnit:
					self._find_result.append((category, unit, catIndex, unitIndex))

		if not self._find_result:
			return

		self._select_found_unit()

	def _find_wrap_around(self):
		assert 0 < len(self._find_result)
		assert self._find_count + 1 == len(self._find_result)
		#select first result
		self._find_count = 0
		self._select_found_unit()

	def _find_next(self):
		assert 0 < len(self._find_result)
		assert self._find_count + 1 < len(self._find_result)
		self._find_count += 1
		self._select_found_unit()

	def _select_found_unit(self):
		assert 0 < len(self._find_result)

		#check if next find is in a new category (prevent category changes when unnecessary
		if self._selected_category != self._find_result[self._find_count][0]:
			self._categoryView.set_cursor(
				self._find_result[self._find_count][2], self._categoryColumn, False
			)

		self._unitsView.set_cursor(
			self._find_result[self._find_count][3], self._unitNameColumn, True
		)

	def _on_findEntry_changed(self, *args):
		"""
		Clear out find results since the user wants to look for something new
		"""
		try:
			self._clear_find()
		except Exception:
			_moduleLogger.exception()

	def _on_shortlist_changed(self, *args):
		try:
			raise NotImplementedError("%s" % self._shortlistcheck.get_active())
		except Exception:
			_moduleLogger.exception()

	def _on_edit_shortlist(self, *args):
		try:
			raise NotImplementedError("%s" % self._toggleShortList.get_active())
		except Exception:
			_moduleLogger.exception()

	def _on_user_clear_selections(self, *args):
		try:
			selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
			os.remove(selectionsDatPath)
			self._selected_units = {}
		except Exception:
			_moduleLogger.exception()

	def _on_find_activate(self, a):
		"""
		check if 'new find' or 'last find' or 'next-find'

		new-find = run the find algorithm which also selects the first found unit
		         = self._find_count = 0 and self._find_result = []

		last-find = restart from top again
		          = self._find_count = len(self._find_result)

		next-find = continue to next found location
		           = self._find_count = 0 and len(self._find_result)>0
		"""
		try:
			if len(self._find_result) == 0:
				self._find_first()
			else:
				if self._find_count == len(self._find_result)-1:
					self._find_wrap_around()
				else:
					self._find_next()

			if not self._find_result:
				self._findLabel.set_text('Text not found')
			else:
				resultsLeft = len(self._find_result) - self._find_count - 1
				self._findLabel.set_text(
					'%s result(s) left' % (resultsLeft, )
				)
		except Exception:
			_moduleLogger.exception()

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
		if self._selected_category == "Computer Numbers":
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

	def _on_click_unit_column(self, col):
		"""
		Sort the contents of the col when the user clicks on the title.
		"""
		try:
			#Determine which column requires sorting
			columns = self._get_column_sort_stuff()
			for column, directionName, col_cmp in columns:
				column.set_sort_indicator(False)
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
				assert False, "Unknown column: %s" % (col.get_title(), )
		except Exception:
			_moduleLogger.exception()

	def _on_click_category(self, row):
		#Colourize each row alternately for easier reading
		self._unitsView.set_property('rules_hint', 1)

		#Clear out the description
		text_model = gtk.TextBuffer(None)
		self._unitDescription.set_buffer(text_model)

		#Determine the contents of the selected category row
		selected, iter = row.get_selection().get_selected()

		self._selected_category = self._categoryModel.get_value(iter, 0)

		self._unit_sort_direction = False
		self._value_sort_direction = False
		self._units_sort_direction = False
		self._unitNameColumn.set_sort_indicator(False)
		self._unitValueColumn.set_sort_indicator(False)
		self._unitSymbolColumn.set_sort_indicator(False)

		self._unitDataInCategory = unit_data.UNIT_DESCRIPTIONS[selected.get_value(iter, 0)]
		keys = self._unitDataInCategory.keys()
		keys.sort()
		del keys[0] # do not display .base_unit description key

		#Fill up the units descriptions and clear the value cells
		self._unitModel.clear()
		for key in keys:
			iter = self._unitModel.append()
			self._unitModel.set(iter, 0, key, 1, '', 2, self._unitDataInCategory[key][1])
		self._sortedUnitModel.sort_column_changed()

		self._unitName.set_text('')
		self._unitValue.set_text('')
		self._previousUnitName.set_text('')
		self._previousUnitValue.set_text('')
		self._unitSymbol.set_text('')
		self._previousUnitSymbol.set_text('')

		self.restore_units()

	def restore_units(self):
		# Restore the previous historical settings of previously selected units in this newly selected category
		#Since category has just been clicked, the list will be sorted already.
		if self._selected_category in self._selected_units:
			if self._selected_units[self._selected_category][0]:
				#self._selected_units[self._selected_category] = [selected_unit, self._selected_units[self._selected_category][0]]

				units = unit_data.UNIT_DESCRIPTIONS[self._selected_category].keys()
				units.sort()
				del units[0] # do not display .base_unit description key

				#Restore oldest selection first.
				if self._selected_units[self._selected_category][1]:
					unit_no = 0
					for unit in units:
						if unit == self._selected_units[self._selected_category][1]:
							self._unitsView.set_cursor(unit_no, self._unitNameColumn, True)
						unit_no = unit_no+1

				#Restore newest selection second.
				unit_no = 0
				for unit in units:
					if unit == self._selected_units[self._selected_category][0]:
						self._unitsView.set_cursor(unit_no, self._unitNameColumn, True)
					unit_no = unit_no+1

		# select the text so user can start typing right away
		self._unitValue.grab_focus()
		self._unitValue.select_region(0, -1)

	def _on_click_unit(self, row):
		self._calcsuppress = True #suppress calculations

		#Determine the contents of the selected row.
		selected, iter = self._unitsView.get_selection().get_selected()

		selected_unit = selected.get_value(iter, 0)

		unit_spec = self._unitDataInCategory[selected_unit]

		#Clear out the description
		text_model = gtk.TextBuffer(None)
		self._unitDescription.set_buffer(text_model)

		enditer = text_model.get_end_iter()
		text_model.insert(enditer, unit_spec[2])

		if self._unitName.get_text() != selected_unit:
			self._previousUnitName.set_text(self._unitName.get_text())
			self._previousUnitValue.set_text(self._unitValue.get_text())
			if self._unitSymbol.get() == None:
				self._previousUnitSymbol.set_text('')
			else:
				self._previousUnitSymbol.set_text(self._unitSymbol.get())
		self._unitName.set_text(selected_unit)

		self._unitValue.set_text(selected.get_value(iter, 1))

		self._unitSymbol.set_text(unit_spec[1]) # put units into label text
		if self._unitValue.get_text() == '':
			if self._selected_category == "Computer Numbers":
				self._unitValue.set_text("0")
			else:
				self._unitValue.set_text("0.0")

		#For historical purposes, record this unit as the most recent one in this category.
		# Also, if a previous unit exists, then shift that previous unit to oldest unit.
		if self._selected_category in self._selected_units:
			if self._selected_units[self._selected_category][0]:
				self._selected_units[self._selected_category] = [selected_unit, self._selected_units[self._selected_category][0]]
		else:
			self._selected_units[self._selected_category] = [selected_unit, '']

		# select the text so user can start typing right away
		self._unitValue.grab_focus()
		self._unitValue.select_region(0, -1)

		self._calcsuppress = False #enable calculations

	def messagebox_ok_clicked(self, a):
		messagebox.hide()

	def _on_user_write_units(self, a):
		''"Write the list of categories and units to stdout for documentation purposes.''"
		messagebox_model = gtk.TextBuffer(None)
		messageboxtext.set_buffer(messagebox_model)
		messagebox_model.insert_at_cursor(_(u'The units are being written to stdout. You can capture this printout by starting gonvert from the command line as follows: \n$ gonvert > file.txt'), -1)
		messagebox.show()
		while gtk.events_pending():
			gtk.mainiteration(False)

		total_categories = 0
		total_units = 0
		print 'gonvert-%s%s' % (
			constants.__version__,
			_(u' - Unit Conversion Utility  - Convertible units listing: ')
		)
		for category_key in unit_data.UNIT_CATEGORIES:
			total_categories = total_categories + 1
			print category_key, ": "
			self._unitDataInCategory = unit_data.UNIT_DESCRIPTIONS[category_key]
			unit_keys = self._unitDataInCategory.keys()
			unit_keys.sort()
			del unit_keys[0] # do not display .base_unit description key
			for unit_key in unit_keys:
				total_units = total_units + 1
				print "\t", unit_key
		print total_categories, ' categories'
		print total_units, ' units'

	def _on_unit_value_changed(self, a):
		if self._calcsuppress:
			#self._calcsuppress = False
			return
		# determine if value to be calculated is empty
		if self._selected_category == "Computer Numbers":
			if self._unitValue.get_text() == '':
				value = '0'
			else:
				value = self._unitValue.get_text()
		else:
			if self._unitValue.get_text() == '':
				value = 0.0
			else:
				value = float(self._unitValue.get_text())

		if self._unitName.get_text() != '':
			func, arg = self._unitDataInCategory[self._unitName.get_text()][0] #retrieve the conversion function and value from the selected unit
			base = apply(func.to_base, (value, arg, )) #determine the base unit value

			keys = self._unitDataInCategory.keys()
			keys.sort()
			del keys[0]
			row = 0

			#point to the first row
			iter = self._unitModel.get_iter_first()

			while iter:
				#get the formula from the name at the row
				func, arg = self._unitDataInCategory[self._unitModel.get_value(iter, 0)][0]

				#set the result in the value column
				self._unitModel.set(iter, 1, str(apply(func.from_base, (base, arg, ))))

				#point to the next row in the self._unitModel
				iter = self._unitModel.iter_next(iter)

			# if the second row has a unit then update its value
			if self._previousUnitName.get_text() != '':
				self._calcsuppress = True
				func, arg = self._unitDataInCategory[self._previousUnitName.get_text()][0]
				self._previousUnitValue.set_text(str(apply(func.from_base, (base, arg, ))))
				self._calcsuppress = False

	def _on_previous_unit_value_changed(self, a):
		if self._calcsuppress == True:
			#self._calcsuppress = False
			return
		# determine if value to be calculated is empty
		if self._selected_category == "Computer Numbers":
			if self._previousUnitValue.get_text() == '':
				value = '0'
			else:
				value = self._previousUnitValue.get_text()
		else:
			if self._previousUnitValue.get_text() == '':
				value = 0.0
			else:
				value = float(self._previousUnitValue.get_text())

		if self._previousUnitName.get_text() != '':
			func, arg = self._unitDataInCategory[self._previousUnitName.get_text()][0] #retrieve the conversion function and value from the selected unit
			base = apply(func.to_base, (value, arg, )) #determine the base unit value

			keys = self._unitDataInCategory.keys()
			keys.sort()
			del keys[0]
			row = 0

			#point to the first row
			iter = self._unitModel.get_iter_first()

			while iter:
				#get the formula from the name at the row
				func, arg = self._unitDataInCategory[self._unitModel.get_value(iter, 0)][0]

				#set the result in the value column
				self._unitModel.set(iter, 1, str(apply(func.from_base, (base, arg, ))))

				#point to the next row in the self._unitModel
				iter = self._unitModel.iter_next(iter)

			# if the second row has a unit then update its value
			if self._unitName.get_text() != '':
				self._calcsuppress = True
				func, arg = self._unitDataInCategory[self._unitName.get_text()][0]
				self._unitValue.set_text(str(apply(func.from_base, (base, arg, ))))
				self._calcsuppress = False

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
			_moduleLogger.exception()
		finally:
			gtk.main_quit()


def main():
	logging.basicConfig(level = logging.DEBUG)
	try:
		os.makedirs(constants._data_path_)
	except OSError, e:
		if e.errno != 17:
			raise

	gonvert = Gonvert()
	gtk.main()


if __name__ == "__main__":
	main()
