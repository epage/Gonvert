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
import evil_globals
import unit_data


_moduleLogger = logging.getLogger("gonvert_glade")

gettext.bindtextdomain('gonvert', '/usr/share/locale')
gettext.textdomain('gonvert')
_ = gettext.gettext


def shortlist_changed(a):
	print "shortlist"
	if shortlistcheck.get_active():
		print "1"
	else:
		print "0"


def edit_shortlist(a):
	print "edit shortlist"
	if edit_shortlist1.get_active():
		print "1"
	else:
		print "0"


def app_size_changed(a,b):
	''"get current size of window as it changes.''"
	evil_globals.window_size=mainWindow.get_size()


def clear_selections(a):
	selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
	os.remove(selectionsDatPath)
	evil_globals.selected_units={}


def exitprogram(a):
	"""
	This routine saves the selections to a file, and 
	 should therefore only be called when exiting the program.
	
	 Update selections dictionary which consists of the following keys:
	 'evil_globals.selected_category': full name of selected category
	 'evil_globals.selected_units': evil_globals.selected_units dictionary which contains:
				[categoryname: #1 displayed unit, #2 displayed unit]
	"""
	#Determine the contents of the selected category row
	selected,iter= cat_clist.get_selection().get_selected()
	evil_globals.selected_category = cat_model.get_value(iter,0)

	selections = {'evil_globals.selected_category':evil_globals.selected_category, 'evil_globals.selected_units':evil_globals.selected_units}
	selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
	pickle.dump(selections, open(selectionsDatPath,'w'))

	#Get last size of app and save it
	window_settings = {'size':evil_globals.window_size}
	windowDatPath = "/".join((constants._data_path_, "window.dat"))
	pickle.dump(window_settings, open(windowDatPath,'w'))

	gtk.mainquit
	sys.exit()


def find_entry_changed(a):
	#Clear out find results since the user wants to look for something new
	evil_globals.find_result=[] #empty find result list
	evil_globals.find_count=0 #default to find result number zero
	find_label.set_text('') #clear result


def find_key_press(a,b):
	#Check if the key pressed was an ASCII key
	if len(b.string)>0:
		#Check if the key pressed was the 'Enter' key
		if ord(b.string[0])==13:
			#Execute the find units function
			find_units(1)


def about_clicked(a):
	about_box.show()


def about_hide(*args):
	about_box.hide()
	return gtk.TRUE


def messagebox_ok_clicked(a):
	messagebox.hide()


def find_units(a):
	global column1
	global col
	#check if 'new find' or 'last find' or 'next-find'

	#new-find = run the find algorithm which also selects the first found unit
	#         = evil_globals.find_count=0 and evil_globals.find_result=[]

	#last-find = restart from top again
	#          = evil_globals.find_count=len(evil_globals.find_result)

	#next-find = continue to next found location
	#           = evil_globals.find_count=0 and len(evil_globals.find_result)>0

	#check for new-find
	if len(evil_globals.find_result)==0:
		find_string = string.lower(string.strip(find_entry.get_text()))
		#Make sure that a valid find string has been requested
		if len(find_string)>0:
			categories = unit_data.list_dic.keys()
			categories.sort()
			found_a_unit=0 #reset the 'found-a-unit' flag
			cat_no=0
			for category in categories:
				units=unit_data.list_dic[category].keys()
				units.sort()
				del units[0] # do not display .base_unit description key
				unit_no=0
				for unit in units:
					if string.find(string.lower(unit), find_string)>=0:
						found_a_unit=1 #indicate that a unit was found
						#print "'",find_string,"'"," found at category=", category," unit =",unit
						evil_globals.find_result.append((category,unit,cat_no,unit_no))
					unit_no=unit_no+1
				cat_no=cat_no+1

			if found_a_unit==1:
				#select the first found unit
				evil_globals.find_count=0
				#check if next find is in a new category (prevent category changes when unnecessary
				if evil_globals.selected_category!=evil_globals.find_result[evil_globals.find_count][0]:
					cat_clist.set_cursor(evil_globals.find_result[0][2],col,False)
					clist1.set_cursor(evil_globals.find_result[0][3],column1,True)
					if len(evil_globals.find_result)>1:
						find_label.set_text(('Press Find for next unit. '+ str(len(evil_globals.find_result))+' result(s).'))
					else:
						find_label.set_text('Text not found') #Display error
	else: #must be next-find or last-find
		#check for last-find
		if evil_globals.find_count==len(evil_globals.find_result)-1:
			#select first result
			evil_globals.find_count=0
			cat_clist.set_cursor(evil_globals.find_result[evil_globals.find_count][2],col,False)
			clist1.set_cursor(evil_globals.find_result[evil_globals.find_count][3],column1,True)
		else: #must be next-find
			evil_globals.find_count=evil_globals.find_count+1
			#check if next find is in a new category (prevent category changes when unnecessary
			if evil_globals.selected_category!=evil_globals.find_result[evil_globals.find_count][0]:
				cat_clist.set_cursor(evil_globals.find_result[evil_globals.find_count][2],col,False)
			clist1.set_cursor(evil_globals.find_result[evil_globals.find_count][3],column1,True)


def click_column(col):
	''"Sort the contents of the column when the user clicks on the title.''"
	global column1, column2, unit_model

	#Determine which column requires sorting
	if col.get_title()==_(u"Unit Name"):
		selected_column=0
		column1.set_sort_indicator(True)
		column2.set_sort_indicator(False)
		column3.set_sort_indicator(False)
		column1.set_sort_order(not evil_globals.unit_sort_direction)
	elif col.get_title()==_(u"Value"):
		selected_column=1
		column1.set_sort_indicator(False)
		column2.set_sort_indicator(True)
		column3.set_sort_indicator(False)
		column2.set_sort_order(not evil_globals.value_sort_direction)
	else:
		selected_column=2
		column1.set_sort_indicator(False)
		column2.set_sort_indicator(False)
		column3.set_sort_indicator(True)
		column3.set_sort_order(not evil_globals.units_sort_direction)

	#declare a spot to hold the sorted list
	sorted_list = []

	#point to the first row
	iter=unit_model.get_iter_first()
	row=0

	while (iter):
		#grab all text from columns for sorting

		#get the text from each column
		unit_text = unit_model.get_value(iter,0)
		units_text = unit_model.get_value(iter,2)

		#do not bother sorting if the value column is empty
		if unit_model.get_value(iter,1)=='' and selected_column==1:
			return

		#special sorting exceptions for ascii values (instead of float values)
		if evil_globals.selected_category == "Computer Numbers":
			value_text = unit_model.get_value(iter,1)
		else:
			if unit_model.get_value(iter,1)==None or unit_model.get_value(iter,1)=='':
				value_text = ''
			else:
				value_text = float(unit_model.get_value(iter,1))

		if selected_column==0:
			sorted_list.append((unit_text,value_text,units_text))
		elif selected_column==1:
			sorted_list.append((value_text,unit_text,units_text))
		else:
			sorted_list.append((units_text,value_text,unit_text))

		#point to the next row in the unit_model
		iter=unit_model.iter_next(iter)
		row=row+1

	#check if no calculations have been made yet (don't bother sorting)
	if row==0:
		return
	else:
		if selected_column==0:
			if not evil_globals.unit_sort_direction:
				sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(x),string.lower(y)))
				evil_globals.unit_sort_direction=True
			else:
				sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(y),string.lower(x)))
				evil_globals.unit_sort_direction=False
		elif selected_column==1:
			sorted_list.sort()
			if not evil_globals.value_sort_direction:
				evil_globals.value_sort_direction=True
			else:
				sorted_list.reverse()
				evil_globals.value_sort_direction=False
		else:
			if not evil_globals.units_sort_direction:
				sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(x),string.lower(y)))
				evil_globals.units_sort_direction=True
			else:
				sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(y),string.lower(x)))
				evil_globals.units_sort_direction=False

		#Clear out the previous list of units
		unit_model = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)
		clist1.set_model(unit_model)

		#colourize each row differently for easier reading
		clist1.set_property( 'rules_hint',1)

		#Clear out the description
		text_model = gtk.TextBuffer(None)
		text1.set_buffer(text_model)

		if selected_column==0:
			for unit,value,units in sorted_list:
				iter = unit_model.append()
				unit_model.set(iter,0,unit,1,str(value),2,units)
		elif selected_column==1:
			for value,unit,units in sorted_list:
				iter = unit_model.append()
				unit_model.set(iter,0,unit,1,str(value),2,units)
		else:
			for units,value,unit in sorted_list:
				iter = unit_model.append()
				unit_model.set(iter,0,unit,1,str(value),2,units)
	return


def click_category(row):
	global unit_model, cat_model
	global unit_dic, list_dic

	#Clear out the previous list of units
	unit_model = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_STRING,gobject.TYPE_STRING)
	clist1.set_model(unit_model)

	#Colourize each row alternately for easier reading
	clist1.set_property( 'rules_hint',1)

	#Clear out the description
	text_model = gtk.TextBuffer(None)
	text1.set_buffer(text_model)

	#Determine the contents of the selected category row
	selected,iter= row.get_selection().get_selected()

	evil_globals.selected_category = cat_model.get_value(iter,0)

	evil_globals.unit_sort_direction = False
	evil_globals.value_sort_direction = False
	evil_globals.units_sort_direction = False
	column1.set_sort_indicator(False)
	column2.set_sort_indicator(False)
	column3.set_sort_indicator(False)

	unit_dic=unit_data.list_dic[selected.get_value(iter,0)]
	keys = unit_dic.keys()
	keys.sort()
	del keys[0] # do not display .base_unit description key

	#Fill up the units descriptions and clear the value cells
	for key in keys:
		iter = unit_model.append()
		unit_model.set(iter,0,key,1,'',2,unit_dic[key][1])

	unitName.set_text('')
	unitValue.set_text('')
	entry3.set_text('')
	entry4.set_text('')
	unitSymbol.set_text('')
	label2.set_text('')

	restore_units()


def restore_units():
	global unit_dic, list_dic

	# Restore the previous historical settings of previously selected units in this newly selected category
	#Since category has just been clicked, the list will be sorted already.
	if evil_globals.selected_units.has_key(evil_globals.selected_category):
		if evil_globals.selected_units[evil_globals.selected_category][0]:
			''"debug ''"
			#evil_globals.selected_units[evil_globals.selected_category]=[selected_unit,evil_globals.selected_units[evil_globals.selected_category][0]]

			units=unit_data.list_dic[evil_globals.selected_category].keys()
			units.sort()
			del units[0] # do not display .base_unit description key

			#Restore oldest selection first.
			if evil_globals.selected_units[evil_globals.selected_category][1]:
				unit_no=0
				for unit in units:
					if unit==evil_globals.selected_units[evil_globals.selected_category][1]:
						clist1.set_cursor(unit_no,column1,True)
					unit_no=unit_no+1

			#Restore newest selection second.
			unit_no=0
			for unit in units:
				if unit==evil_globals.selected_units[evil_globals.selected_category][0]:
					clist1.set_cursor(unit_no,column1,True)
				unit_no=unit_no+1

	# select the text so user can start typing right away
	unitValue.grab_focus()
	unitValue.select_region(0,-1)


def button_released(row,a):
	click_unit(row)


def click_unit(row):
	evil_globals.calcsuppress = 1 #suppress calculations

	#Determine the contents of the selected row.
	selected,iter= clist1.get_selection().get_selected()

	selected_unit=selected.get_value(iter,0)

	unit_spec=unit_dic[selected_unit]

	#Clear out the description
	text_model = gtk.TextBuffer(None)
	text1.set_buffer(text_model)

	enditer = text_model.get_end_iter()
	text_model.insert(enditer,unit_spec[2])

	if unitName.get_text() != selected_unit:
		entry3.set_text(unitName.get_text())
		entry4.set_text(unitValue.get_text())
		if unitSymbol.get() == None:
			label2.set_text('')
		else:
			label2.set_text(unitSymbol.get())
	unitName.set_text(selected_unit)

	unitValue.set_text(selected.get_value(iter,1))

	unitSymbol.set_text(unit_spec[1]) # put units into label text
	if unitValue.get_text() =='':
		if evil_globals.selected_category == "Computer Numbers":
			unitValue.set_text("0")
		else:
			unitValue.set_text("0.0")

	#For historical purposes, record this unit as the most recent one in this category.
	# Also, if a previous unit exists, then shift that previous unit to oldest unit.
	if evil_globals.selected_units.has_key(evil_globals.selected_category):
		if evil_globals.selected_units[evil_globals.selected_category][0]:
			evil_globals.selected_units[evil_globals.selected_category]=[selected_unit,evil_globals.selected_units[evil_globals.selected_category][0]]
	else:
		evil_globals.selected_units[evil_globals.selected_category]=[selected_unit,'']

	# select the text so user can start typing right away
	unitValue.grab_focus()
	unitValue.select_region(0,-1)

	evil_globals.calcsuppress = 0 #enable calculations


def write_units(a):
	''"Write the list of categories and units to stdout for documentation purposes.''"
	messagebox_model = gtk.TextBuffer(None)
	messageboxtext.set_buffer(messagebox_model)
	messagebox_model.insert_at_cursor(_(u'The units are being written to stdout. You can capture this printout by starting gonvert from the command line as follows:\n$ gonvert > file.txt'),-1)
	messagebox.show()
	while gtk.events_pending():
		gtk.mainiteration (False)
	category_keys=unit_data.list_dic.keys()
	category_keys.sort()
	total_categories = 0
	total_units = 0
	print 'gonvert-%s%s' % (
		constants.__version__,
		_(u' - Unit Conversion Utility  - Convertible units listing:')
	)
	for category_key in category_keys:
		total_categories = total_categories + 1
		print category_key,":"
		unit_dic=unit_data.list_dic[category_key]
		unit_keys = unit_dic.keys()
		unit_keys.sort()
		del unit_keys[0] # do not display .base_unit description key
		for unit_key in unit_keys:
			total_units = total_units + 1
			print "\t",unit_key
	print total_categories,' categories'
	print total_units,' units'
	messagebox_model = gtk.TextBuffer(None)
	messageboxtext.set_buffer(messagebox_model)
	messagebox_model.insert_at_cursor(_(u'The units list has been written to stdout. You can capture this printout by starting gonvert from the command line as follows:\n$ gonvert > file.txt'),-1)


class Ccalculate(object):

	def top(self,a):
		global unit_model
		global testvalue

		if evil_globals.calcsuppress == 1:
			#evil_globals.calcsuppress = 0
			return
		# determine if value to be calculated is empty
		if evil_globals.selected_category == "Computer Numbers":
			if unitValue.get_text() =='':
				value = '0'
			else:
				 value = unitValue.get_text()
		else:
			if unitValue.get_text() =='':
				value = 0.0
			else:
				value = float(unitValue.get_text())

		if unitName.get_text() != '':
			func,arg = unit_dic[unitName.get_text()][0] #retrieve the conversion function and value from the selected unit
			base = apply(func.to_base,(value,arg,)) #determine the base unit value

			keys = unit_dic.keys()
			keys.sort()
			del keys[0]
			row = 0

			#point to the first row
			iter=unit_model.get_iter_first()

			while (iter):
				#get the formula from the name at the row
				func,arg = unit_dic[unit_model.get_value(iter,0)][0]

				#set the result in the value column
				unit_model.set(iter,1,str(apply(func.from_base,(base,arg,))))

				#point to the next row in the unit_model
				iter=unit_model.iter_next(iter)

			# if the second row has a unit then update its value
			if entry3.get_text() != '':
				evil_globals.calcsuppress=1
				func,arg = unit_dic[entry3.get_text()][0]
				entry4.set_text(str(apply(func.from_base,(base,arg,))))
				evil_globals.calcsuppress=0

	def bottom(self,a):
		if evil_globals.calcsuppress == 1:
			#evil_globals.calcsuppress = 0
			return
		# determine if value to be calculated is empty
		if evil_globals.selected_category == "Computer Numbers":
			if entry4.get_text() =='':
				value = '0'
			else:
				value = entry4.get_text()
		else:
			if entry4.get_text() =='':
				value = 0.0
			else:
				value = float(entry4.get_text())

		if entry3.get_text() != '':
			func,arg = unit_dic[entry3.get_text()][0] #retrieve the conversion function and value from the selected unit
			base = apply(func.to_base,(value,arg,)) #determine the base unit value

			keys = unit_dic.keys()
			keys.sort()
			del keys[0]
			row = 0

			#point to the first row
			iter=unit_model.get_iter_first()

			while (iter):
				#get the formula from the name at the row
				func,arg = unit_dic[unit_model.get_value(iter,0)][0]

				#set the result in the value column
				unit_model.set(iter,1,str(apply(func.from_base,(base,arg,))))

				#point to the next row in the unit_model
				iter=unit_model.iter_next(iter)

			# if the second row has a unit then update its value
			if unitName.get_text() != '':
				evil_globals.calcsuppress=1
				func,arg = unit_dic[unitName.get_text()][0]
				unitValue.set_text(str(apply(func.from_base,(base,arg,))))
				evil_globals.calcsuppress=0


# vbox2 is mainLayout
# scrolledwindow4 is categoryScrolledWindow
# cat_clist is categoryView
# vbox1 is unitConversionLayout
# 	hbox1 is selectedUnitLayouta
# 		unitName is the unit name
# 		unitValue is the value
# 		unitSymbol is the unit
# 	hbox2 is previousSelectedUnitLayouta
# 		entry3 is the unit name
# 		entry4 is the value
# 		label2 is the unit
# 	vpand1 is unitsAndDescriptionPane
# 		scrolledWindow1 is unitListScrolledWindow
# 			clist1 is unitsView
# 		scrolledWindow2 is unitDescriptionScrolledWindow
# 			text1 is unitDescription
# 	hbox3 is the search box
def main():
	global mainWindow
	global cat_clist
	global cat_model
	global unitValue
	global unitName
	global unitSymbol
	global clist1
	global calculate
	global shortlistcheck
	global about_box
	global text1
	global column1
	global column2
	global column3
	global entry3
	global entry4
	global label2

	logging.basicConfig(level=logging.DEBUG)

	try:
		os.makedirs(constants._data_path_)
	except OSError, e:
		if e.errno != 17:
			raise

	#check to see if glade file is in current directory (user must be running from download untar directory)
	_glade_files = [
		os.path.join(os.path.dirname(__file__), "gonvert.glade"),
		os.path.join(os.path.dirname(__file__), "../data/gonvert.glade"),
		os.path.join(os.path.dirname(__file__), "../lib/gonvert.glade"),
		'/usr/lib/gonvert/gonvert.glade',
	]
	for gladePath in _glade_files:
		if os.path.isfile(gladePath):
			homepath = os.path.dirname(gladePath)
			pixmapspath = "/".join((homepath, "pixmaps"))
			widgets = gtk.glade.XML(gladePath)
			break
	else:
		return

	calculate = Ccalculate()
	mainWindow = widgets.get_widget('mainWindow')

	#Restore window size from previously saved settings if it exists and is valid.
	windowDatPath = "/".join((constants._data_path_, "window.dat"))
	if os.path.exists(windowDatPath):
		#Retrieving previous window settings from ~/.gonvert/window.dat
		saved_window = pickle.load(open(windowDatPath, "r"))
		#If the 'size' has been stored, then extract size from saved_window.
		if saved_window.has_key('size'):
			a, b = saved_window['size']
			mainWindow.resize(a, b)
		else:
			#Maximize if no previous size was found
			#mainWindow.maximize()
			pass
	else:
		#Maximize if no previous window.dat file was found
		#mainWindow.maximize()
		pass

	mainWindow.set_title('gonvert- %s - Unit Conversion Utility' % constants.__version__);
	iconPath = pixmapspath + '/gonvert.png'
	if os.path.exists(iconPath):
		mainWindow.set_icon(gtk.gdk.pixbuf_new_from_file(iconPath))
	else:
		_moduleLogger.warn("Error: Could not find gonvert icon: %s" % iconPath)

	#--------- connections to GUI ----------------
	dic = {
		"on_exitMenuItem_activate": exitprogram,
		"on_mainWindow_destroy": exitprogram,
		"on_cat_clist_select_row": click_category,
		"on_clist1_click_column": click_column,
		"on_unitValue_changed": calculate.top,
		"on_entry4_changed": calculate.bottom,
		"on_write_units1_activate": write_units,
		"on_find_button_clicked": find_units,
		"on_find_entry_key_press_event": find_key_press,
		"on_find_entry_changed": find_entry_changed,
		"on_about1_activate": about_clicked,
		"on_about_close_clicked": about_hide,
		"on_messagebox_ok_clicked": messagebox_ok_clicked,
		"on_clear_selections1_activate": clear_selections,
		"on_clist1_cursor_changed": click_unit,
		"on_clist1_button_released": button_released,
		"on_mainWindow_size_allocate": app_size_changed,
		"on_shortlistcheck_toggled": shortlist_changed,
		"on_edit_shortlist1_activate": edit_shortlist,
	 }

	widgets.signal_autoconnect (dic);
	mainWindow.connect("destroy", exitprogram)

	def change_menu_label(labelname,newtext):
		item_label = widgets.get_widget(labelname).get_children()[0]
		item_label.set_text(newtext)
	def change_label(labelname,newtext):
		item_label = widgets.get_widget(labelname)
		item_label.set_text(newtext)

	change_menu_label('fileMenuItem',_('File'))
	change_menu_label('exitMenuItem',_('Exit'))
	change_menu_label('toolsMenuItem',_('Tools'))
	change_menu_label('clear_selections1',_('Clear selections'))
	change_menu_label('write_units1',_('Write Units'))
	change_menu_label('helpMenuItem',_('Help'))
	change_menu_label('aboutMenuItem',_('About'))

	change_menu_label('find_button',_('Find'))

	shortlistcheck = widgets.get_widget('shortlistcheck')
	edit_shortlist1 = widgets.get_widget('edit_shortlist1')

	cat_clist = widgets.get_widget('cat_clist' )

	clist1 = widgets.get_widget('clist1')
	clist1_selection=clist1.get_selection()

	unitName = widgets.get_widget('unitName')
	unitValue = widgets.get_widget('unitValue')
	entry3 = widgets.get_widget('entry3')
	entry4 = widgets.get_widget('entry4')
	about_box = widgets.get_widget('about_box')
	messagebox = widgets.get_widget('msgbox')
	messageboxtext = widgets.get_widget('msgboxtext')

	about_image = widgets.get_widget('about_image')
	about_image.set_from_file(pixmapspath +'gonvert.png')
	versionlabel = widgets.get_widget('versionlabel')
	versionlabel.set_text(constants.__version__)

	unitSymbol =widgets.get_widget('unitSymbol')
	label2 =widgets.get_widget('label2')

	text1 = widgets.get_widget('text1' )

	find_entry = widgets.get_widget('find_entry')
	find_label = widgets.get_widget('find_label')

	#insert a column into the units list even though the heading will not be seen
	renderer = gtk.CellRendererText()
	column1 = gtk.TreeViewColumn( _('Unit Name'), renderer )
	column1.set_property( 'resizable', 1 )
	column1.add_attribute( renderer, 'text', 0 )
	column1.set_clickable(True)
	column1.connect("clicked",click_column)
	clist1.append_column( column1 )

	column2 = gtk.TreeViewColumn( _('Value'), renderer )
	column2.set_property( 'resizable', 1 )
	column2.add_attribute( renderer, 'text', 1 )
	column2.set_clickable(True)
	column2.connect("clicked",click_column)
	clist1.append_column( column2 )

	column3 = gtk.TreeViewColumn( _('Units'), renderer )
	column3.set_property( 'resizable', 1 )
	column3.add_attribute( renderer, 'text', 2 )
	column3.set_clickable(True)
	column3.connect("clicked",click_column)
	clist1.append_column( column3 )

	#Insert a column into the category list even though the heading will not be seen
	renderer = gtk.CellRendererText()
	col = gtk.TreeViewColumn( 'Title', renderer )
	col.set_property( 'resizable', 1 )
	col.add_attribute( renderer, 'text', 0 )
	cat_clist.append_column( col )

	cat_model = gtk.ListStore(gobject.TYPE_STRING)
	cat_clist.set_model(cat_model)
	#colourize each row differently for easier reading
	cat_clist.set_property( 'rules_hint',1)

	#Populate the catagories list
	keys = unit_data.list_dic.keys()
	keys.sort()
	for key in keys:
		iter = cat_model.append()
		cat_model.set(iter,0,key)

	ToolTips=gtk.Tooltips()
	find_button = widgets.get_widget('find_button')
	ToolTips.set_tip(find_button,_(u'Find unit (F6)'))

	#Restore selections from previously saved settings if it exists and is valid.
	historical_catergory_found=False
	selectionsDatPath = "/".join((constants._data_path_, "selections.dat"))
	if os.path.exists(selectionsDatPath):
		#Retrieving previous selections from ~/.gonvert/selections.dat
		selections=pickle.load(open(selectionsDatPath,'r'))
		#Restoring previous selections.
		#
		#Make a list of categories to determine which one to select
		categories=unit_data.list_dic.keys()
		categories.sort()
		#
		#If the 'selected_unts' has been stored, then extract evil_globals.selected_units from selections.
		if selections.has_key('evil_globals.selected_units'):
			evil_globals.selected_units=selections['evil_globals.selected_units']
		#Make sure that the 'evil_globals.selected_category' has been stored.
		if selections.has_key('evil_globals.selected_category'):
			#Match an available category to the previously selected category.
			for counter in range(len(categories)):
				if selections['evil_globals.selected_category']==categories[counter]:
					# Restore the previously selected category.
					cat_clist.set_cursor(counter, col, False )
					cat_clist.grab_focus()
			historical_catergory_found=True

	if not historical_catergory_found:
		print "Couldn't find saved category, using default."
		#If historical records were not kept then default to 
		# put the focus on the first category
		cat_clist.set_cursor(0, col, False)
		cat_clist.grab_focus()

	restore_units()

	gtk.main()


if __name__ == "__main__":
	main()
