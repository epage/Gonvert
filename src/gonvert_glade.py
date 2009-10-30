#!/usr/bin/env python
# -*- coding: UTF8 -*-

import os
import pickle
import string
import sys
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
		keys = unit_data.list_dic.keys()
		keys.sort()
		for key in keys:
			iter = self._categoryModel.append()
			self._categoryModel.set(iter, 0, key)

		ToolTips = gtk.Tooltips()
		ToolTips.set_tip(findButton, _(u'Find unit (F6)'))

		#--------- connections to GUI ----------------
		dic = {
			"on_exit_menu_activate": self._on_user_exit,
			"on_main_window_destroy": self._on_user_exit,
			"on_categoryView_select_row": self._on_click_category,
			"on_unitsView__on_click_unit_column": self._on_click_unit_column,
			"on_unitValue_changed": self.top,
			"on_previousUnitValue_changed": self.bottom,
			"on_writeUnitsMenuItem_activate": self._on_user_write_units,
			"on_findButton_clicked": self._on_user_find_units,
			"on_findEntry_key_press_event": self._on_find_key_press,
			"on_findEntry_changed": self._findEntry_changed,
			"on_aboutMenuItem_activate": self._on_about_clicked,
			"on_messagebox_ok_clicked": self.messagebox_ok_clicked,
			"on_clearSelectionMenuItem_activate": self._on_user_clear_selections,
			"on_unitsView_cursor_changed": self._on_click_unit,
			"on_unitsView_button_released": self._on_button_released,
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
			#
			#Make a list of categories to determine which one to select
			categories = unit_data.list_dic.keys()
			categories.sort()
			#
			#If the 'selected_unts' has been stored, then extract self._selected_units from selections.
			if 'selected_units' in selections:
				self._selected_units = selections['selected_units']
			#Make sure that the 'self._selected_category' has been stored.
			if 'selected_category' in selections:
				#Match an available category to the previously selected category.
				for counter in range(len(categories)):
					if selections['selected_category'] == categories[counter]:
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

	def _on_shortlist_changed(self, a):
		print "shortlist"
		if self._shortlistcheck.get_active():
			print "1"
		else:
			print "0"

	def _on_edit_shortlist(self, a):
		print "edit shortlist"
		if self._toggleShortList.get_active():
			print "1"
		else:
			print "0"

	def _on_user_clear_selections(self, a):
		selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
		os.remove(selectionsDatPath)
		self._selected_units = {}

	def _on_user_exit(self, a):
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

		gtk.mainquit
		sys.exit()

	def _findEntry_changed(self, a):
		#Clear out find results since the user wants to look for something new
		self._find_result = [] #empty find result list
		self._find_count = 0 #default to find result number zero
		self._findLabel.set_text('') #clear result

	def _on_find_key_press(self, a, b):
		#Check if the key pressed was an ASCII key
		if len(b.string)>0:
			#Check if the key pressed was the 'Enter' key
			if ord(b.string[0]) == 13:
				#Execute the find units function
				self._on_user_find_units(1)

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

	def messagebox_ok_clicked(self, a):
		messagebox.hide()

	def _on_user_find_units(self, a):
		#check if 'new find' or 'last find' or 'next-find'

		#new-find = run the find algorithm which also selects the first found unit
		#         = self._find_count = 0 and self._find_result = []

		#last-find = restart from top again
		#          = self._find_count = len(self._find_result)

		#next-find = continue to next found location
		#           = self._find_count = 0 and len(self._find_result)>0

		#check for new-find
		if len(self._find_result) == 0:
			find_string = string.lower(string.strip(self._findEntry.get_text()))
			#Make sure that a valid find string has been requested
			if len(find_string)>0:
				categories = unit_data.list_dic.keys()
				categories.sort()
				found_a_unit = 0 #reset the 'found-a-unit' flag
				cat_no = 0
				for category in categories:
					units = unit_data.list_dic[category].keys()
					units.sort()
					del units[0] # do not display .base_unit description key
					unit_no = 0
					for unit in units:
						if string.find(string.lower(unit), find_string) >= 0:
							found_a_unit = 1 #indicate that a unit was found
							#print "'", find_string, "'", " found at category = ", category, " unit = ", unit
							self._find_result.append((category, unit, cat_no, unit_no))
						unit_no = unit_no+1
					cat_no = cat_no+1

				if found_a_unit == 1:
					#select the first found unit
					self._find_count = 0
					#check if next find is in a new category (prevent category changes when unnecessary
					if self._selected_category != self._find_result[self._find_count][0]:
						self._categoryView.set_cursor(self._find_result[0][2], self._categoryColumn, False)
						self._unitsView.set_cursor(self._find_result[0][3], self._unitNameColumn, True)
						if len(self._find_result)>1:
							self._findLabel.set_text(('Press Find for next unit. '+ str(len(self._find_result))+' result(s).'))
						else:
							self._findLabel.set_text('Text not found') #Display error
		else: #must be next-find or last-find
			#check for last-find
			if self._find_count == len(self._find_result)-1:
				#select first result
				self._find_count = 0
				self._categoryView.set_cursor(self._find_result[self._find_count][2], self._categoryColumn, False)
				self._unitsView.set_cursor(self._find_result[self._find_count][3], self._unitNameColumn, True)
			else: #must be next-find
				self._find_count = self._find_count+1
				#check if next find is in a new category (prevent category changes when unnecessary
				if self._selected_category != self._find_result[self._find_count][0]:
					self._categoryView.set_cursor(self._find_result[self._find_count][2], self._categoryColumn, False)
				self._unitsView.set_cursor(self._find_result[self._find_count][3], self._unitNameColumn, True)

	def _on_click_unit_column(self, col):
		"""
		Sort the contents of the col when the user clicks on the title.
		"""
		#Determine which column requires sorting
		if col is self._unitNameColumn:
			selectedUnitColumn = 0
			self._unitNameColumn.set_sort_indicator(True)
			self._unitValueColumn.set_sort_indicator(False)
			self._unitSymbolColumn.set_sort_indicator(False)
			self._unitNameColumn.set_sort_order(not self._unit_sort_direction)
		elif col is self._unitValueColumn:
			selectedUnitColumn = 1
			self._unitNameColumn.set_sort_indicator(False)
			self._unitValueColumn.set_sort_indicator(True)
			self._unitSymbolColumn.set_sort_indicator(False)
			self._unitValueColumn.set_sort_order(not self._value_sort_direction)
		elif col is self._unitSymbolColumn:
			selectedUnitColumn = 2
			self._unitNameColumn.set_sort_indicator(False)
			self._unitValueColumn.set_sort_indicator(False)
			self._unitSymbolColumn.set_sort_indicator(True)
			self._unitSymbolColumn.set_sort_order(not self._units_sort_direction)
		else:
			assert False, "Unknown column: %s" % (col.get_title(), )

		#declare a spot to hold the sorted list
		sorted_list = []

		#point to the first row
		iter = self._unitModel.get_iter_first()
		row = 0

		while iter:
			#grab all text from columns for sorting

			#get the text from each column
			unit_text = self._unitModel.get_value(iter, 0)
			units_text = self._unitModel.get_value(iter, 2)

			#do not bother sorting if the value column is empty
			if self._unitModel.get_value(iter, 1) == '' and selectedUnitColumn == 1:
				return

			#special sorting exceptions for ascii values (instead of float values)
			if self._selected_category == "Computer Numbers":
				value_text = self._unitModel.get_value(iter, 1)
			else:
				if self._unitModel.get_value(iter, 1) == None or unit_model.get_value(iter, 1) == '':
					value_text = ''
				else:
					value_text = float(self._unitModel.get_value(iter, 1))

			if selectedUnitColumn == 0:
				sorted_list.append((unit_text, value_text, units_text))
			elif selectedUnitColumn == 1:
				sorted_list.append((value_text, unit_text, units_text))
			else:
				sorted_list.append((units_text, value_text, unit_text))

			#point to the next row in the self._unitModel
			iter = self._unitModel.iter_next(iter)
			row = row+1

		#check if no calculations have been made yet (don't bother sorting)
		if row == 0:
			return
		else:
			if selectedUnitColumn == 0:
				if not self._unit_sort_direction:
					sorted_list.sort(lambda (x, xx, xxx), (y, yy, yyy): cmp(string.lower(x), string.lower(y)))
					self._unit_sort_direction = True
				else:
					sorted_list.sort(lambda (x, xx, xxx), (y, yy, yyy): cmp(string.lower(y), string.lower(x)))
					self._unit_sort_direction = False
			elif selectedUnitColumn == 1:
				sorted_list.sort()
				if not self._value_sort_direction:
					self._value_sort_direction = True
				else:
					sorted_list.reverse()
					self._value_sort_direction = False
			else:
				if not self._units_sort_direction:
					sorted_list.sort(lambda (x, xx, xxx), (y, yy, yyy): cmp(string.lower(x), string.lower(y)))
					self._units_sort_direction = True
				else:
					sorted_list.sort(lambda (x, xx, xxx), (y, yy, yyy): cmp(string.lower(y), string.lower(x)))
					self._units_sort_direction = False

			#Clear out the previous list of units
			self._unitModel = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
			self._unitsView.set_model(self._unitModel)

			#colourize each row differently for easier reading
			self._unitsView.set_property('rules_hint', 1)

			#Clear out the description
			text_model = gtk.TextBuffer(None)
			self._unitDescription.set_buffer(text_model)

			if selectedUnitColumn == 0:
				for unit, value, units in sorted_list:
					iter = self._unitModel.append()
					self._unitModel.set(iter, 0, unit, 1, str(value), 2, units)
			elif selectedUnitColumn == 1:
				for value, unit, units in sorted_list:
					iter = self._unitModel.append()
					self._unitModel.set(iter, 0, unit, 1, str(value), 2, units)
			else:
				for units, value, unit in sorted_list:
					iter = self._unitModel.append()
					self._unitModel.set(iter, 0, unit, 1, str(value), 2, units)
		return

	def _on_click_category(self, row):
		#Clear out the previous list of units
		self._unitModel = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self._unitsView.set_model(self._unitModel)

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

		self._unitDataInCategory = unit_data.list_dic[selected.get_value(iter, 0)]
		keys = self._unitDataInCategory.keys()
		keys.sort()
		del keys[0] # do not display .base_unit description key

		#Fill up the units descriptions and clear the value cells
		for key in keys:
			iter = self._unitModel.append()
			self._unitModel.set(iter, 0, key, 1, '', 2, self._unitDataInCategory[key][1])

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
				''"debug ''"
				#self._selected_units[self._selected_category] = [selected_unit, self._selected_units[self._selected_category][0]]

				units = unit_data.list_dic[self._selected_category].keys()
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

	def _on_button_released(self, row, a):
		self._on_click_unit(row)

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

	def _on_user_write_units(self, a):
		''"Write the list of categories and units to stdout for documentation purposes.''"
		messagebox_model = gtk.TextBuffer(None)
		messageboxtext.set_buffer(messagebox_model)
		messagebox_model.insert_at_cursor(_(u'The units are being written to stdout. You can capture this printout by starting gonvert from the command line as follows: \n$ gonvert > file.txt'), -1)
		messagebox.show()
		while gtk.events_pending():
			gtk.mainiteration(False)
		category_keys = unit_data.list_dic.keys()
		category_keys.sort()
		total_categories = 0
		total_units = 0
		print 'gonvert-%s%s' % (
			constants.__version__,
			_(u' - Unit Conversion Utility  - Convertible units listing: ')
		)
		for category_key in category_keys:
			total_categories = total_categories + 1
			print category_key, ": "
			self._unitDataInCategory = unit_data.list_dic[category_key]
			unit_keys = self._unitDataInCategory.keys()
			unit_keys.sort()
			del unit_keys[0] # do not display .base_unit description key
			for unit_key in unit_keys:
				total_units = total_units + 1
				print "\t", unit_key
		print total_categories, ' categories'
		print total_units, ' units'
		messagebox_model = gtk.TextBuffer(None)
		messageboxtext.set_buffer(messagebox_model)
		messagebox_model.insert_at_cursor(_(u'The units list has been written to stdout. You can capture this printout by starting gonvert from the command line as follows: \n$ gonvert > file.txt'), -1)

	def top(self, a):
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

	def bottom(self, a):
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
