#!/usr/bin/env python
# -*- coding: UTF8 -*-

import os
import pickle
import math
import string
import sys
import gettext
from math import *

import gobject
import gtk
import gtk.glade
import gtk.gdk

import constants

#--------- variable definitions ---------------- 
nums = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' # used for Computer numbers base definitions.
global calcsuppress #semaphore used to suppress cyclic calculations when a unit is clicked.
global selected_category
global window_size #window size used for saving and restoring application window size

calcsuppress=0
unit_sort_direction  = False
value_sort_direction = False
units_sort_direction = False
find_result=[] #empty find result list
find_count=0 #default to find result number zero
selected_category='' #preset to no selected category
selected_units={} #empty dictionary for later use
window_size=(0,0) #empty tuple for filling later

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
	global window_size
	window_size=app1.get_size()

def clear_selections(a):
	global selected_units
	os.remove(home+'/.gonvert/selections.dat')
	selected_units={}

def exitprogram(a):
	"""
	This routine saves the selections to a file, and 
	 should therefore only be called when exiting the program.
	
	 Update selections dictionary which consists of the following keys:
	 'selected_category': full name of selected category
	    'selected_units': selected_units dictionary which contains:
				[categoryname: #1 displayed unit, #2 displayed unit]
	"""
	global selected_units

	#Determine the contents of the selected category row
	selected,iter= cat_clist.get_selection().get_selected()
	selected_category = cat_model.get_value(iter,0)

	selections = {'selected_category':selected_category, 'selected_units':selected_units}
	pickle.dump(selections,open(home+'/.gonvert/selections.dat','w'))

	#Get last size of app and save it
	window_settings = {'size':window_size}
	pickle.dump(window_settings,open(home+'/.gonvert/window.dat','w'))

	gtk.mainquit
	sys.exit()

def find_entry_changed(a):
	#Clear out find results since the user wants to look for something new
	global find_result
	find_result=[] #empty find result list
	find_count=0 #default to find result number zero
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
	global find_count
	global selected_category
	global column1,col

	#check if 'new find' or 'last find' or 'next-find'

	#new-find = run the find algorithm which also selects the first found unit
	#         = find_count=0 and find_result=[]

	#last-find = restart from top again
	#          = find_count=len(find_result)

	#next-find = continue to next found location
	#           = find_count=0 and len(find_result)>0

	#check for new-find
	if len(find_result)==0:
	  find_string = string.lower(string.strip(find_entry.get_text()))
	  #Make sure that a valid find string has been requested
	  if len(find_string)>0:
	    categories=list_dic.keys()
	    categories.sort()
	    found_a_unit=0 #reset the 'found-a-unit' flag
	    cat_no=0
	    for category in categories:
	      units=list_dic[category].keys()
	      units.sort()
	      del units[0] # do not display .base_unit description key
	      unit_no=0
	      for unit in units:
		if string.find(string.lower(unit), find_string)>=0:
		  found_a_unit=1 #indicate that a unit was found
		  #print "'",find_string,"'"," found at category=", category," unit =",unit
		  find_result.append((category,unit,cat_no,unit_no))
		unit_no=unit_no+1
	      cat_no=cat_no+1

	    if found_a_unit==1:
	      #select the first found unit
	      find_count=0
	      #check if next find is in a new category (prevent category changes when unnecessary
	      if selected_category!=find_result[find_count][0]:
		cat_clist.set_cursor(find_result[0][2],col,False)
	      clist1.set_cursor(find_result[0][3],column1,True)
	      if len(find_result)>1:
		find_label.set_text(('  Press Find for next unit. '+ str(len(find_result))+' result(s).'))
	    else:
	      find_label.set_text('  Text not found') #Display error
	else: #must be next-find or last-find
	  #check for last-find
	  if find_count==len(find_result)-1:
	    #select first result
	    find_count=0
	    cat_clist.set_cursor(find_result[find_count][2],col,False)
	    clist1.set_cursor(find_result[find_count][3],column1,True)
	  else: #must be next-find
	    find_count=find_count+1
	    #check if next find is in a new category (prevent category changes when unnecessary
	    if selected_category!=find_result[find_count][0]:
	      cat_clist.set_cursor(find_result[find_count][2],col,False)
	    clist1.set_cursor(find_result[find_count][3],column1,True)

def click_column(col):
	''"Sort the contents of the column when the user clicks on the title.''"
	global unit_sort_direction
	global value_sort_direction
	global units_sort_direction
	global column1, column2, unit_model

	#Determine which column requires sorting
	if col.get_title()==_(u"Unit Name"):
	  selected_column=0
	  column1.set_sort_indicator(True)
	  column2.set_sort_indicator(False)
	  column3.set_sort_indicator(False)
	  column1.set_sort_order(not unit_sort_direction)
	elif col.get_title()==_(u"Value"):
	  selected_column=1
	  column1.set_sort_indicator(False)
	  column2.set_sort_indicator(True)
	  column3.set_sort_indicator(False)
	  column2.set_sort_order(not value_sort_direction)
	else:
	  selected_column=2
	  column1.set_sort_indicator(False)
	  column2.set_sort_indicator(False)
	  column3.set_sort_indicator(True)
	  column3.set_sort_order(not units_sort_direction)

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
	  if selected_category == "Computer Numbers":	
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
	    if not unit_sort_direction:
	      sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(x),string.lower(y)))
	      unit_sort_direction=True
	    else:
	      sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(y),string.lower(x)))
	      unit_sort_direction=False
	  elif selected_column==1:
	    sorted_list.sort()
	    if not value_sort_direction:
	      value_sort_direction=True
	    else:
	      sorted_list.reverse()
	      value_sort_direction=False
	  else:
	    if not units_sort_direction:
	      sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(x),string.lower(y)))
	      units_sort_direction=True
	    else:
	      sorted_list.sort(lambda (x,xx,xxx), (y,yy,yyy): cmp(string.lower(y),string.lower(x)))
	      units_sort_direction=False

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
	global unit_sort_direction
	global value_sort_direction
	global units_sort_direction
	global unit_model, cat_model
	global selected_category, selected_units
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

	selected_category = cat_model.get_value(iter,0)

	unit_sort_direction  = False
	value_sort_direction = False
	units_sort_direction = False
	column1.set_sort_indicator(False)
	column2.set_sort_indicator(False)
	column3.set_sort_indicator(False)

	unit_dic=list_dic[selected.get_value(iter,0)]
	keys = unit_dic.keys()
	keys.sort()
	del keys[0] # do not display .base_unit description key

	#Fill up the units descriptions and clear the value cells
	for key in keys:
	  iter = unit_model.append()
	  unit_model.set(iter,0,key,1,'',2,unit_dic[key][1])

	entry1.set_text('')
	entry2.set_text('')
	entry3.set_text('')
	entry4.set_text('')
	label1.set_text('')
	label2.set_text('')

	restore_units()

def restore_units():
	global selected_category, selected_units
	global unit_dic, list_dic

	# Restore the previous historical settings of previously selected units in this newly selected category
	#Since category has just been clicked, the list will be sorted already.
	if selected_units.has_key(selected_category):
	  if selected_units[selected_category][0]:
		''"debug ''"
		#selected_units[selected_category]=[selected_unit,selected_units[selected_category][0]]

		units=list_dic[selected_category].keys()
		units.sort()
		del units[0] # do not display .base_unit description key

		#Restore oldest selection first.
		if selected_units[selected_category][1]:
			unit_no=0
			for unit in units:
				if unit==selected_units[selected_category][1]:
					clist1.set_cursor(unit_no,column1,True)
				unit_no=unit_no+1

		#Restore newest selection second.
		unit_no=0
		for unit in units:
			if unit==selected_units[selected_category][0]:
				clist1.set_cursor(unit_no,column1,True)
			unit_no=unit_no+1

	# select the text so user can start typing right away
	entry2.grab_focus()
	entry2.select_region(0,-1)

def button_released(row,a):
	click_unit(row)

def click_unit(row):
	global selected_category
	global calcsuppress
	global selected_units

	calcsuppress = 1 #suppress calculations

	#Determine the contents of the selected row.
	selected,iter= clist1.get_selection().get_selected()

	selected_unit=selected.get_value(iter,0)

	unit_spec=unit_dic[selected_unit]

	#Clear out the description
	text_model = gtk.TextBuffer(None)
	text1.set_buffer(text_model)

	enditer = text_model.get_end_iter()
	text_model.insert(enditer,unit_spec[2])

	if entry1.get_text() <> selected_unit:
		entry3.set_text(entry1.get_text())
		entry4.set_text(entry2.get_text())
		if label1.get() == None:
			label2.set_text('')
		else:
			label2.set_text(label1.get())
	entry1.set_text(selected_unit)

	entry2.set_text(selected.get_value(iter,1))

	label1.set_text(unit_spec[1]) # put units into label text
	if entry2.get_text() =='':
		if selected_category == "Computer Numbers":
			entry2.set_text("0")
		else:
			entry2.set_text("0.0")

	#For historical purposes, record this unit as the most recent one in this category.
	# Also, if a previous unit exists, then shift that previous unit to oldest unit.
	if selected_units.has_key(selected_category):
	  if selected_units[selected_category][0]:
	    selected_units[selected_category]=[selected_unit,selected_units[selected_category][0]]
	else:
	  selected_units[selected_category]=[selected_unit,'']

	# select the text so user can start typing right away
	entry2.grab_focus()
	entry2.select_region(0,-1)

	calcsuppress = 0 #enable calculations

def write_units(a):
	''"Write the list of categories and units to stdout for documentation purposes.''"
	messagebox_model = gtk.TextBuffer(None)
	messageboxtext.set_buffer(messagebox_model)
	messagebox_model.insert_at_cursor(_(u'The units are being written to stdout. You can capture this printout by starting gonvert from the command line as follows:\n$ gonvert > file.txt'),-1)
	messagebox.show()
	while gtk.events_pending():
          gtk.mainiteration (False)
	category_keys=list_dic.keys()
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
		unit_dic=list_dic[category_key]
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

def makeBase(x, base = len(nums), table=nums):
	''"Convert from base 10 to any other base. ''"
	d, m = divmod(x, base)
	if d:
		return makeBase(d,base, table) + table[int(m)]
	else:
		return table[int(m)]

# roman numerals
roman_group = { 1: ('i','v'),
	       10: ('x','l'),
	      100: ('c','d'),
	     1000: ('m','A'),
	    10000: ('B','C'),
	}

# functions that convert Arabic digits to roman numerals
roman_value = {
	0: lambda i,v,x: '',
	1: lambda i,v,x: i,
	2: lambda i,v,x: i+i,
	3: lambda i,v,x: i+i+i,
	4: lambda i,v,x: i+v,
	5: lambda i,v,x: v,
	6: lambda i,v,x: v+i,
	7: lambda i,v,x: v+i+i,
	8: lambda i,v,x: v+i+i+i,
	9: lambda i,v,x: i+x,
	}

def toroman( n ):
	''' convert a decimal number in [1,4000) to a roman numeral '''
	if n < 1:
	    return ''
	if n >= 4000:
	    return "Too large"
	base = 1
	s = ''
	while n > 0:
	    i,v = roman_group[base]
	    base = base * 10
	    x,l = roman_group[base]
	    digit = n % 10
	    n = (n-digit)/10
	    s = roman_value[digit](i,v,x) + s
	return s

def fromroman( s, rbase=1 ):
	''' convert a roman numeral (in lowercase) to a decimal integer '''
	if len(s) == 0:
	    return 0
	if rbase > 1000:
	    return 0
	i,v = roman_group[rbase]
	x,l = roman_group[rbase*10]
	if   s[-4:] == v+i+i+i: digit,s = 8,s[:-4]
	elif s[-4:] == i+i+i+i: digit,s = 4,s[:-4]
	elif s[-3:] == v+i+i  : digit,s = 7,s[:-3]
	elif s[-3:] == i+i+i  : digit,s = 3,s[:-3]
	elif s[-2:] == v+i    : digit,s = 6,s[:-2]
	elif s[-2:] == i+x    : digit,s = 9,s[:-2]
	elif s[-2:] == i+v    : digit,s = 4,s[:-2]
	elif s[-2:] == i+i    : digit,s = 2,s[:-2]
	elif s[-1:] == i      : digit,s = 1,s[:-1]
	elif s[-1:] == v      : digit,s = 5,s[:-1]
	else                  : digit,s = 0,s
	return digit*rbase + fromroman(s,rbase*10)

class Ccalculate:
	def top(self,a):
	  global calcsuppress
	  global unit_model
	  global testvalue

	  if calcsuppress == 1:
	    #calcsuppress = 0
	    return
	  # determine if value to be calculated is empty
	  if selected_category == "Computer Numbers":
	    if entry2.get_text() =='':
	      value = '0'
	    else:
	       value = entry2.get_text()
	  else:
	    if entry2.get_text() =='':
	      value = 0.0
	    else:
	      value = float(entry2.get_text())

	  if entry1.get_text() <> '':
	    func,arg = unit_dic[entry1.get_text()][0] #retrieve the conversion function and value from the selected unit
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
	    if entry3.get_text() <> '':
	      calcsuppress=1
	      func,arg = unit_dic[entry3.get_text()][0]
	      entry4.set_text(str(apply(func.from_base,(base,arg,))))
	      calcsuppress=0

	def bottom(self,a):
	  global calcsuppress
	  if calcsuppress == 1:
	    #calcsuppress = 0
	    return
	  # determine if value to be calculated is empty
	  if selected_category == "Computer Numbers":
	    if entry4.get_text() =='':
	      value = '0'
	    else:
	      value = entry4.get_text()
	  else:
	    if entry4.get_text() =='':
	      value = 0.0
	    else:
	      value = float(entry4.get_text())

	  if entry3.get_text() <> '':
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
	    if entry1.get_text() <> '':
	      calcsuppress=1
	      func,arg = unit_dic[entry1.get_text()][0]
	      entry2.set_text(str(apply(func.from_base,(base,arg,))))
	      calcsuppress=0


#All classes for conversions are defined below:
# each class should have one method for converting "to_base and another for converting "from_base"
#the return value is the converted value to or from base
class simple_multiplier:
	def to_base(self,value,multiplier):
		return value * (multiplier)
	def from_base(self,value,multiplier):
		if multiplier == 0:
			return 0.0
		else:
			return value / (multiplier)

class simple_inverter:
	def to_base(self,value,multiplier):
		if value == 0:
			return 0.0
		else:
			return (multiplier) / value
	def from_base(self,value,multiplier):
		if value == 0:
			return 0.0
		else:
			return (multiplier) / value
class simple_gain_offset:
	def to_base(self,value,(gain,offset)):
		return (value * (gain)) + offset
	def from_base(self,value,(gain,offset)):
		if gain == 0:
			return 0.0
		else:
			return (value - offset) / gain

class simple_offset_gain:
	def to_base(self,value,(offset,gain)):
		return (value + offset) * gain
	def from_base(self,value,(offset,gain)):
		if gain == 0:
			return 0.0
		else:
			return (value / gain) - offset

class slope_offset:
	''"convert using points on a graph''"
	def to_base(self,value,((low_in,high_in),(low_out,high_out))):
		gain = (high_out-low_out)/(high_in-low_in)
		offset = low_out - gain*low_in
		return gain*value+offset
	def from_base(self,value,((low_out,high_out),(low_in,high_in))):
		gain = (high_out-low_out)/(high_in-low_in)
		offset = low_out - gain*low_in
		return gain*value+offset

class double_slope_offset:
	''"convert using points on a graph, graph split into two slopes''"
	def to_base(self,value,((low1_in,high1_in),(low1_out,high1_out),(low2_in,high2_in),(low2_out,high2_out))):
		if low1_in<=value<=high1_in:
			gain = (high1_out-low1_out)/(high1_in-low1_in)
			offset = low1_out - gain*low1_in
			return gain*value+offset
		if low2_in<=value<=high2_in:
			gain = (high2_out-low2_out)/(high2_in-low2_in)
			offset = low2_out - gain*low2_in
			return gain*value+offset
		return 0.0
	def from_base(self,value,((low1_in,high1_in),(low1_out,high1_out),(low2_in,high2_in),(low2_out,high2_out))):
		if low1_out<=value<=high1_out:
			gain = (high1_in-low1_in)/(high1_out-low1_out)
			offset = low1_in - gain*low1_out
			return gain*value+offset
		if low2_out<=value<=high2_out:
			gain = (high2_in-low2_in)/(high2_out-low2_out)
			offset = low2_in - gain*low2_out
			return gain*value+offset
		return 0.0

class base_converter:
        #Convert from any base to base 10 (decimal)
        def to_base(self,value,base):
                result   = 0L #will contain the long base-10 (decimal) number to be returned
                position = len(value)   #length of the string that is to be converted
                for x in value:
                        position = position-1
                        result = long(result + long(long(string.find(nums,x))*(long(base)**long(position))))
                return result
        #Convert from decimal to any base
        def from_base(self,value,base):
                return makeBase(value,base)

class roman_numeral:
	#Convert from roman numeral to base 10 (decimal)
	def to_base(self,value,junk):
		if value=="0":
			return 0L
		else:
			return fromroman(value)
	#Convert from decimal to roman numeral
	def from_base(self,value,junk):
		return toroman(value)

class function:
	''"defined simple function can be as complicated as you like, however, both to/from base must be defined.''"
	#value is assumed to be a string
	#convert from a defined function to base
	def to_base(self,value,(to_base,from_base)):
		exec "y="+to_base[:string.find(to_base,'x')]+str(value)+to_base[string.find(to_base,'x')+1:]
		return y
	def from_base(self,value,(to_base,from_base)):
		exec "y="+from_base[:string.find(from_base,'x')]+str(value)+from_base[string.find(from_base,'x')+1:]
		return y


#----------- Program starts below ----------------
#Prepare to read in previous category, units placemenmts, window size
home = os.environ['HOME']
#check for users gonvert directories
if not os.path.exists(home+'/.gonvert'):
	print "Creating ~/.gonvert directory to hold settings."
	os.mkdir(home+'/.gonvert')


#check to see if glade file is in current directory (user must be running from download untar directory)
if os.path.exists('gonvert.glade'):
	homepath=''
	pixmapspath='pixmaps/'
elif os.path.exists('/usr/local/share/gonvert/gonvert.glade'):
	homepath='/usr/local/share/gonvert/'
	pixmapspath='/usr/local/share/pixmaps/'
else:
	#look for it in the installed directory
	homepath=sys.path[0] + '/../share/gonvert/'
	if  os.path.exists('/usr/share/pixmaps/gonvert.png'): #Check fedora pixmaps directory
		pixmapspath='/usr/share/pixmaps/'
	else:
		pixmapspath=homepath  +'/../pixmaps/'

#print pixmapspath #debug
gladefile=homepath+'gonvert.glade'

widgets = gtk.glade.XML(gladefile)
app1 = widgets.get_widget('app1')

#Restore window size from previously saved settings if it exists and is valid.
if os.path.exists(home+'/.gonvert/window.dat'):
  #Retrieving previous window settings from ~/.gonvert/window.dat
  saved_window=pickle.load(open(home+'/.gonvert/window.dat','r'))
  #If the 'size' has been stored, then extract size from saved_window.
  if saved_window.has_key('size'):
    a,b=saved_window['size']
    app1.resize(a,b)
  else:
    #Maximize if no previous size was found
    app1.maximize()
else:
  #Maximize if no previous window.dat file was found
  app1.maximize()

app1.set_title('gonvert- %s - Unit Conversion Utility' % constants.__version__);
if  os.path.exists(pixmapspath  + 'gonvert.png'):
	app1.set_icon(gtk.gdk.pixbuf_new_from_file(pixmapspath  + 'gonvert.png'))
else:
	print "Error: Could find gonvert icon, it should be here: "
	print pixmapspath

#--------- function definitions from classes ------------
m=simple_multiplier()
inv=simple_inverter()
gof=simple_gain_offset()
ofg=simple_offset_gain()
slo=slope_offset()
dso=double_slope_offset()
b=base_converter()
r=roman_numeral()
f=function()
calculate=Ccalculate()


#--------- connections to GUI ----------------
dic = {"on_exit1_activate": exitprogram,
       "on_app1_destroy": exitprogram,
       "on_cat_clist_select_row": click_category,
       "on_clist1_click_column": click_column,
       "on_entry2_changed": calculate.top,
       "on_entry4_changed": calculate.bottom,
       "on_write_units1_activate":write_units,
       "on_find_button_clicked":find_units,
       "on_find_entry_key_press_event":find_key_press,
       "on_find_entry_changed":find_entry_changed,
       "on_about1_activate":about_clicked,
       "on_about_close_clicked":about_hide,
       "on_messagebox_ok_clicked":messagebox_ok_clicked,
       "on_clear_selections1_activate":clear_selections,
       "on_clist1_cursor_changed":click_unit,
       "on_clist1_button_released":button_released,
       "on_app1_size_allocate":app_size_changed,
       "on_shortlistcheck_toggled":shortlist_changed,
       "on_edit_shortlist1_activate":edit_shortlist,

       }

widgets.signal_autoconnect (dic);

def change_menu_label(labelname,newtext):
	item_label  = widgets.get_widget(labelname).get_children()[0]
	item_label.set_text(newtext)
def change_label(labelname,newtext):
	item_label  = widgets.get_widget(labelname)
	item_label.set_text(newtext)

change_menu_label('file1',_('File'))
change_menu_label('exit1',_('Exit'))
change_menu_label('tools1',_('Tools'))
change_menu_label('clear_selections1',_('Clear selections'))
change_menu_label('write_units1',_('Write Units'))
change_menu_label('help1',_('Help'))
change_menu_label('about1',_('About'))

change_menu_label('find_button',_('Find'))

shortlistcheck = widgets.get_widget('shortlistcheck')
edit_shortlist1 = widgets.get_widget('edit_shortlist1')

cat_clist  = widgets.get_widget('cat_clist' )

clist1 = widgets.get_widget('clist1')
clist1_selection=clist1.get_selection()

entry1 = widgets.get_widget('entry1')
entry2 = widgets.get_widget('entry2')
entry3 = widgets.get_widget('entry3')
entry4 = widgets.get_widget('entry4')
about_box = widgets.get_widget('about_box')
messagebox = widgets.get_widget('msgbox')
messageboxtext = widgets.get_widget('msgboxtext')

about_image = widgets.get_widget('about_image')
about_image.set_from_file(pixmapspath  +'gonvert.png')
versionlabel = widgets.get_widget('versionlabel')
versionlabel.set_text(constants.__version__)

label1 =widgets.get_widget('label1')
label2 =widgets.get_widget('label2')

text1  = widgets.get_widget('text1' )

find_entry = widgets.get_widget('find_entry')
find_label = widgets.get_widget('find_label')




#----- main dictionary of unit descriptions below ------------
# first entry defines base unit
# remaining entries define unit specifications [(function,argument), units, description]
# 	where function can be m and argument is the multiplying factor to_base
# 	or function can be any other arbitrary function and argument can be a single argument
list_dic = {
	_(u"Acceleration"):{".base_unit":_(u"meter per second squared"),
		_(u"free fall"):
			[(m,9.80665),_(u"gn"),_(u"The ideal falling motion of a body that is subject only to the earth's gravitational field.")],
		_(u"meter per second squared"):
			[(m,1.0),u"m/s\xb2",u''],
		_(u"foot per second squared"):
			[(m,30.48/100),u"ft/s\xb2",u''],
		_(u"centimeter per second squared"):
			[(m,1/100.0),u"cm/s\xb2",''],
		_(u"gal"):
			[(m,1/100.0),_(u"Gal"),_(u"A unit of gravitational acceleration equal to one centimeter per second per second (named after Galileo)")],
		_(u"millimeter per second squared"):
			[(m,1/1000.0),u"mm/s\xb2",'']
	},

	_(u"Angle"):{".base_unit":_(u"radian"),
		_(u"revolution / circle / perigon / turn"):
			[(m,2.0*pi),"r",_(u"The act of revolving, or turning round on an axis or a center; the motion of a body round a fixed point or line; rotation; as, the revolution of a wheel, of a top, of the earth on its axis, etc.")],
		_(u"right angle"):
			[(m,pi/2.0),"L",_(u"The angle formed by one line meeting another perpendicularly")],
		_(u"radian"):
			[(m,1.0),_(u"rad"),_(u"An arc of a circle which is equal in length to the radius, or the angle measured by such an arc.")],
		_(u"degree"):
			[(m,pi/180.0),u"\xb0",_(u"1/360 of a complete revolution.")],
		_(u"grad | grade | gon"):
			[(m,pi/200),_(u"g"),_(u"One-hundredth of a right angle.")],
		_(u"milliradian"):
			[(m,1/1000.0),_(u"mrad"),_(u"A unit of angular distance equal to one thousandth of a radian.")],
		_(u"minute"):
			[(m,pi/(180.0*60)),"'",_(u"The sixtieth part of a degree; sixty seconds (Marked thus ('); as, 10deg 20').")],
		_(u"second"):
			[(m,pi/(180.0*60*60)),'"',_(u"""One sixtieth of a minute.(Marked thus ("); as, 10deg 20' 30"). ''""")],
		_(u"mil"):
			[(m,(2*pi)/6400),'',_(u"Used in artillery; 1/6400 of a complete revolution.")],
		_(u"centesimal minute"):
			[(m,pi/20000),'',_(u"One hundredth of a grade, 0.01 grade")],
		_(u"centesimal second"):
			[(m,pi/2000000),'',_(u"One ten-thousandth of a grade, 0.0001 grade")],
		_(u"octant"):
			[(m,pi/4.0),'',_(u"The eighth part of a circle (an arc of 45 degrees).")],
		_(u"quadrant"):
			[(m,pi/2.0),'',_(u"The fourth part of a circle (an arc of 90 degrees).")],
		_(u"sextant"):
			[(m,pi/3.0),'',_(u"The sixth part of a circle (an arc of 60 degrees).")],
		_(u"point"):
			[(m,pi/16.0),'',_(u"1/32 of a circle. Points are used on the face of a compass (32 points). Each point is labelled clockwise starting from North as follows: North, North by East, North Northeast, Northeast by North, and Northeast, etc.")],
		_(u"sign"):
			[(m,pi/6.0),'',_(u"The twelfth part of a circle as in twelve signs of the zodiac (an arc of 30 degrees).")],
	},
	_(u"Angular Velocity / Frequency"):{".base_unit":_(u"radian per second"),
		_(u"kiloradian per second"):
			[(m,1000.0),"krad/s",''],
		_(u"revolution per second"):
			[(m,2*pi),"rev/s",''],
		_(u"hertz"):
			[(m,2*pi),"Hz",_(u"Named after the German physicist Heinrich Hertz (1857-1894) who was the first to produce electromagnetic waves artificially. Having a periodic interval of one second.")],
		_(u"radian per second"):
			[(m,1.0),"rad/s",''],
		_(u"milliradian per second"):
			[(m,1/1000.0),"mrad/s",''],
		_(u"revolution per minute"):
			[(m,(2*pi)/60.0),"rpm",''],
		_(u"revolution per hour"):
			[(m,(2*pi)/3600.0),"rph",''],
		_(u"revolution per day"):
			[(m,(2*pi)/(3600.0*24)),"rpd",''],
		_(u"gigahertz"):
			[(m,1e9*2*pi),"GHz",_(u"One billion hertz.")],
		_(u"terahertz"):
			[(m,1e12*2*pi),"THz",''],
		_(u"petahertz"):
			[(m,1e15*2*pi),"PHz",''],
		_(u"exahertz"):
			[(m,1e18*2*pi),"EHz",''],
		_(u"megahertz"):
			[(m,1e6*2*pi),"MHz",_(u"One million hertz.")],
		_(u"kilohertz"):
			[(m,1e3*2*pi),"kHz",_(u"One thousand hertz.")],
	},
	_(u"Area"):{".base_unit":_(u"square meter"),
		_(u"meter diameter circle"):
			[(f,('pi*(x/2.0)**2','2.0*(x/pi)**(0.5)')),"m dia.",_(u"Type the diameter of the circle in meters to find its area displayed in other fields.")],
		_(u"centimeter diameter circle"):
			[(f,('pi*(x/200.0)**2','200.0*(x/pi)**(0.5)')),"cm dia.",_(u"Type the diameter of the circle in centimeters to find its area displayed in other fields.")],
		_(u"inch diameter circle"):
			[(f,('pi*(((x*(25.4/1000))/2.0) )**2','1000/25.4 * 2.0*(x/pi)**(0.5)')),"in dia.",_(u"Type the diameter of the circle in inches to find its area displayed in other fields.")],
		_(u"foot diameter circle"):
			[(f,('pi*(((x*((12*25.4)/1000))/2.0) )**2','1000/(12*25.4) * 2.0*(x/pi)**(0.5)')),"ft dia.",_(u"Type the diameter of the circle in feet to find its area displayed in other fields.")],
		_(u"are"):
			[(m,100.0),'',_(u"The unit of superficial measure, being a square of which each side is ten meters in length; 100 square meters, or about 119.6 square yards.")],
		_(u"acre"):
			[(m,4046.8564224),'',_(u"A piece of land, containing 160 square rods, or 4,840 square yards, or 43,560 square feet. This is the English statute acre. That of the United States is the same. The Scotch acre was about 1.26 of the English, and the Irish 1.62 of the English. Note: The acre was limited to its present definite quantity by statutes of Edward I., Edward III., and Henry VIII.")],
		_(u"acre (Cheshire)"):
			[(m,8561.97632),'',''],
		_(u"acre (Irish)"):
			[(m,6555.26312),'',''],
		_(u"acre (Scottish)"):
			[(m,5142.20257),'',''],
		_(u"arpent (French)"):
			[(m,4088/1.196),'',_(u" 4,088 sq. yards, or nearly five sixths of an English acre.")],
		_(u"arpent (woodland)"):
			[(m,16*25.29285264*10+16*25.29285264*2.5+(16*25.29285264*10)/160),'',_(u"1 acre, 1 rood, 1 perch")],
		_(u"barn"):
			[(m,1.0/1e28),'',_('Used in Nuclear physics to describe the apparent cross-sectional size of atomic sized objects that are bombarded with smaller objects (like electrons). 10^-28 square meters. 100 square femtometers. Originated from the semi-humorous idiom big as a barn and used by physicists to describe the size of the scattering object (Ex: That was as big as 5 barns!).')],
		_(u"cho"):
			[(m,16*25.29285264*10*2.45),'',_(u"Japanese. 2.45 acre")],
		_(u"circular inch"):
			[(m,1000000.0/(1e6*1550*1.273)),'',''],
		_(u"circular mil"):
			[(m,1.0/(1e6*1550*1.273)),"cmil",''],
		_(u"desyatina | dessiatina"):
			[(m,16*25.29285264*10*2.6996),'',_(u"Russian. 2.6996 acre. 2400 square sadzhens")],
		_(u"flag"):
			[(m,25/10.7639104167097),'',_(u"square pace (a pace is 5 feet).")],
		_(u"hide | carucate"):
			[(m,40468.71618),'',_(u"An ancient English measure of the amount of land required to support family")],
		_(u"hectare"):
			[(m,10000.0),"ha",_(u"A measure of area, or superficies, containing a hundred ares, or 10,000 square meters, and equivalent to 2.471 acres.")],
		_(u"homestead | quarter section"):
			[(m,16*25.29285264*10*160),'',_(u"160 acres,1/4 square mile, or 1/4 section. Use by the governments of North America early settlers in the western states and provinces were allowed to take title to a homestead of 160 acres of land by registering a claim, settling on the land, and cultivating it.")],
		_(u"perch"):
			[(m,(16*25.29285264*10)/160),'',_(u"Used to measure land. A square rod; the 160th part of an acre.")],
		_(u"sabin"):
			[(m,1/10.7639104167097),'',_(u"A unit of acoustic absorption equivalent to the absorption by a square foot of a surface that absorbs all incident sound. 1ft\xb2.")],
		_(u"square"):
			[(m,100/10.7639104167097),'',_(u"Used in the construction for measuring roofing material, finished lumber, and other building materials. One square is equals 100 square feet.")],
		_(u"section"):
			[(m,2.59*1E6),'',_(u"Used in land measuring. One square mile. An area of about 640 acres")],
		_(u"square league (land)"):
			[(m,23309892.99),'',''],
		_(u"square mile"):
			[(m,2.59*1e6),u"mi\xb2",''],
		_(u"square kilometer"):
			[(m,1e6),u"km\xb2",''],
		_(u"rood"):
			[(m,16*25.29285264*2.5),'',_(u"The fourth part of an acre, or forty square rods.")],
		_(u"shaku"):
			[(m,330.6/10000),'',_(u"A Japanese unit of area, the shaku equals 330.6 square centimeters (51.24 square inches). Note: shaku also means length and volume.")],
		_(u"square chain (surveyor)"):
			[(m,16*25.29285264),u"ch\xb2",_(u"A unit for land measure equal to four rods square, or one tenth of an acre.")],
		_(u"link"):
			[(m,4*25.29285264),'',_(u"4 rods square")],
		_(u"square rod"):
			[(m,25.29285264),u"rd\xb2",''],
		_(u"square meter"):
			[(m,1.0),u"m\xb2",_(u"Also know as a centare is (1/100th of an are).")],
		_(u"square yard"):
			[(m,1/1.19599004630108),u"yd\xb2",_(u"A unit of area equal to one yard by one yard square syn: sq yd")],
		_(u"square foot"):
			[(m,1/10.7639104167097),u"ft\xb2",_(u"An area equal to that of a square the sides of which are twelve inches; 144 square inches.")],
		_(u"square inch"):
			[(m,1/(10.7639104167097*144)),u"in\xb2",_(u"A unit of area equal to one inch by one inch square syn: sq in")],
		_(u"square centimeter"):
			[(m,1.0/10000),u"cm\xb2",''],
		_(u"square micrometer"):
			[(m,1.0/1e12),u"\xb5m\xb2",''],
		_(u"square millimeter"):
			[(m,1.0/1e6),u"mm\xb2",''],
		_(u"square mil"):
			[(m,1.0/(1e6*1550)),u"mil\xb2",''],
		_(u"township"):
			[(m,1e6*2.59*36),'',_(u"A division of territory six miles square (36miles\xb2), containing 36 sections.")],
		_(u"roll (wallpaper)"):
			[(m,30/10.7639104167097),'',''],
		_(u"square Scottish ell"):
			[(m,0.88323),'',''],
		_(u"fall (Scottish)"):
			[(m,31.79618),'',''],
		_(u"joch (German) | yoke"):
			[(m,5746.5577),'',_(u"joch (German) is 40 square klafters")],
		_(u"labor (Texas)"):
			[(m,716862.83837),'',_(u"An area of land that could be cultivated by one farmer")],
		_(u"barony"):
			[(m,16187486.47094),'',''],
		_(u"square pes (Roman)"):
			[(m,0.08741),'',''],
		_(u"square alen (Denmark)"):
			[(m,.38121),'',''],
		_(u"ferfet (Iceland)"):
			[(m,0.09848),'',''],
		_(u"square vara (Spanish)"):
			[(m,0.59418),'',''],
		_(u"donum (Yugoslavia)"):
			[(m,699.99992),'',''],
		_(u"sahme (Egyptian)"):
			[(m,7.29106),'',''],
		_(u"tavola (Italian)"):
			[(m,37.62587),'',''],
		_(u"cuadra (Paraguay)"):
			[(m,7486.71249),'',''],
		_(u"acaena (Greek)"):
			[(m,9.19744),'',''],
		_(u"plethron (Greek)"):
			[(m,951.01483),'',''],
	},

	_(u"Atomic Physics"):{".base_unit":_(u"radian per second"),
		_(u"kilogram"):
			[(m,2.997925e8**2*(1.0/1.054e-34)),"kg",''],
		_(u"joule"):
			[(m,1.0/1.054e-34),'',_(u"Named after the English physicist James Prescott Joule (1818-1889). A unit of work which is equal to 10^7 units of work in the C. G. S. system of units (ergs), and is practically equivalent to the energy expended in one second by an electric current of one ampere in a resistance of one ohm. One joule is approximately equal to 0.738 foot pounds.")],
		_(u"erg"):
			[(m,1.0/1.054e-27),'',_(u"The unit of work or energy in the C. G. S. system, being the amount of work done by a dyne working through a distance of one centimeter; the amount of energy expended in moving a body one centimeter against a force of one dyne. One foot pound is equal to 13,560,000 ergs.")],
		_(u"GeV Giga electronvolt"):
			[(m,2.41796e23*2*pi),"Gev",''],
		_(u"neutron mass unit"):
			[(m,1.00137*1836.11*3.75577e4*13.6058*2.41796e14*2*pi),'',''],
		_(u"proton mass unit"):
			[(m,1836.11*3.75577e4*13.6058*2.41796e14*2*pi),'',''],
		_(u"atomic mass unit"):
			[(m,1822.84*3.75577e4*13.6058*2.41796e14*2*pi),"amu",''],
		_(u"MeV Mega electronvolt"):
			[(m,2.41796e20*2*pi),"MeV",''],
		_(u"electron rest mass"):
			[(m,3.75577e4*13.6058*2.41796e14*2*pi),'',''],
		_(u"Rydberg constant"):
			[(m,13.6058*2.41796e14*2*pi),'',_(u"Named after the Swedish physicist Johannes Robert Rydberg (1854-1919). A wave number characteristic of the wave spectrum of each element")],
		_(u"electronvolt"):
			[(m,2.41796e14*2*pi),"eV",_(u"A unit of energy equal to the work done by an electron accelerated through a potential difference of 1 volt.")],
		_(u"kayser or cm^-1"):
			[(m,2.997925e10*2*pi),"K",_('Named after the German physicist Heinrich Gustav Johannes Kayser (1853-1940). Used to measure light and other electromagnetic waves. The "wave number" in kaysers equals the number of wavelengths per centimeter.')],
		_(u"kelvin"):
			[(m,2.997925e8*2*pi/1.4387752e-2),"K",_(u"The basic unit of thermodynamic temperature adopted under the System International d'Unites")],
		"m^-1":
			[(m,2.997925e8*2*pi),'',''],
		_(u"millikayser"):
			[(m,2.997925e7*2*pi),'',''],
		_(u"hertz"):
			[(m,2*pi),"Hz",''],
		_(u"radian per second"):
			[(m,1.0),"rad/s",''],
	},
	_(u"Computer Data"):{".base_unit":_(u"bit"),
		_(u"bit"):
			[(m,1.0),'',_(u"One bit of data. Binary representation On/Off.")],
		_(u"nibble | hexit | quadbit"):
			[(m,4.0),'',_(u"One half a byte")],
		_(u"byte"):
			[(m,8.0),'',_(u"Eight bits")],
		_(u"character"):
			[(m,8.0),'',_('Usually described by one byte (256 possible characters can be defined by one byte).')],
		_(u"kilobit"):
			[(m,2.0**10.0),"kilobit",_(u"2^10 bits")],
		_(u"megabit"):
			[(m,2.0**20.0),"megabit",_(u"2^20 bits")],
		_(u"kilobyte | kibi"):
			[(m,1024.0*8),"K | Ki",_(u"2^10, 1024 bytes. 1024 comes from 2^10 which is close enough to 1000. kibi is the IEEE proposal.")],
		_(u"megabyte | mebi"):
			[(m,1024.0**2*8),"M | Mi",_(u"2^20, 1024^2 bytes. 1024 kilobytes. 1024 comes from 2^10 which is close enough to 1000. mebi is the IEEE proposal.")],
		_(u"gigabyte | gibi"):
			[(m,1024.0**3*8),"G | Gi",_(u"2^30, 1024^3. 1024 megabytes. 1024 comes from 2^10 which is close enough to 1000. gibi is the IEEE proposal.")],
		_(u"terabyte | tebi"):
			[(m,1024.0**4*8),"T | Ti",_(u"2^40, 1024^4. 1024 gigabytes. 1024 comes from 2^10 which is close enough to 1000. tebi is the IEEE proposal.")],
		_(u"petabyte | pebi"):
			[(m,1024.0**5*8),"P | Pi",_(u"2^50, 1024^5. 1024 terabytes. 1024 comes from 2^10 which is close enough to 1000. tebi is the IEEE proposal.")],
		_(u"exabyte | exbi"):
			[(m,1024.0**6*8),"E | Ei",_(u"2^60, 1024^6, 1024 petabytes. 1024 comes from 2^10 which is close enough to 1000. tebi is the IEEE proposal.")],
		_(u"zebi | zettabyte"):
			[(m,1024.0**7*8),"Zi",_(u"1024^7. 1024 exbibytes. 1024 comes from 2^10 which is close enough to 1000. tebi is the IEEE proposal.")],
		_(u"yobi | yottabyte"):
			[(m,1024.0**8*8),"Yi",_(u"1024^8. 1024 yobibytes. 1024 comes from 2^10 which is close enough to 1000. tebi is the IEEE proposal.")],
	},
	_(u"Computer Data flow rate"):{".base_unit":_('bits per second'),
		_(u"baud:1"):
			[(m,1.0),"",_(u'Symbol rate for 1 bit per symbol. Named after the French telegraph engineer Jean-Maurice-\u00C9mile Baudot (1845 - 1903). Data transmission measured in symbols per second.')],
		_(u"baud:10"):
			[(m,10.0),"",_(u'Symbol rate for 10 bits per symbol. Named after the French telegraph engineer Jean-Maurice-\u00C9mile Baudot (1845 - 1903). Data transmission measured in symbols per second.')],
		_(u"baud:8"):
			[(m,8.0),"",_(u'Symbol rate for 8 bits per symbol. Named after the French telegraph engineer Jean-Maurice-\u00C9mile Baudot (1845 - 1903). Data transmission measured in symbols per second.')],
		_(u"baud:4"):
			[(m,4.0),"",_(u'Symbol rate for 4 bits per symbol. Named after the French telegraph engineer Jean-Maurice-\u00C9mile Baudot (1845 - 1903). Data transmission measured in symbols per second.')],
		_(u"bits per second"):
			[(m,1.0),"bps",_(u" ")],
		_(u"characters per second"):
			[(m,10.0),"cps",_('Rate to transmit one character. The character is usually described as one byte with one stop bit and one start bit (10 bits in total).')],
	},
	_(u"Computer Numbers"):{".base_unit":_(u"base 10 decimal"),
		_(u"base  2 binary"):
			[(b,2),"base  2",_('Base two numbering system using the digits 0-1')],
		_(u"base  3 ternary | trinary"):
			[(b,3),"base  3",_(u"Base three numbering system using the digits 0-2. Russian Nikolay Brusentsov built a trinary based computer system.")],
		_(u"base  4 quaternary | quadrary"):
			[(b,4),"base  4",_(u"Base four numbering system using the digits 0-3.")],
		_(u"base  5 quinary"):
			[(b,5),"base  5",_(u"Base five numbering system using the digits 0-4.")],
		_(u"base  6 senary | hexary"):
			[(b,6),"base  6",_(u"Base six numbering system using the digits 0-5.")],
		_(u"base  7 septenary | septary"):
			[(b,7),"base  7",_(u"Base seven numbering system using the digits 0-6.")],
		_(u"base  8 octonary | octal | octonal | octimal"):
			[(b,8),"base  8",_(u"Base eight numbering system using the digits 0-7. Commonly used in older computer systems.")],
		_(u"base  9 nonary"):
			[(b,9),"base  9",_(u"Base nine numbering system using the digits 0-8.")],
		_(u"base 10 decimal"):
			[(b,10),"base 10",_(u"Base ten numbering system using the digits 0-9.")],
		_(u"base 11 undenary"):
			[(b,11),"base 11",_(u"Base eleven numbering system using the digits 0-9,a.")],
		_(u"base 12 duodecimal"):
			[(b,12),"base 12",_(u"Base twelve numbering system using the digits 0-9,a-b.")],
		_(u"base 13 tridecimal"):
			[(b,13),"base 13",_('Base Thirteen numbering system using the digits 0-9,a-c.')],
		_(u"base 14 quattuordecimal"):
			[(b,14),"base 14",_(u"Base Fourteen numbering system using the digits 0-9,a-d.")],
		_(u"base 15 quindecimal"):
			[(b,15),"base 15",_(u"Base Fifteen numbering system using the digits 0-9,a-e.")],
		_(u"base 16 sexadecimal | hexadecimal | hex"):
			[(b,16),"base 16",_(u"Base Sixteen numbering system using the digits 0-1,a-f. Commonly used in computer systems.")],
		_(u"base 17 septendecimal"):
			[(b,17),"base 17",_(u"Base Sixteen numbering system using the digits 0-1,a-g.")],
		_(u"base 18 octodecimal"):
			[(b,18),"base 18",_(u"Base Sixteen numbering system using the digits 0-1,a-h.")],
		_(u"base 19 nonadecimal"):
			[(b,19),"base 19",_(u"Base Sixteen numbering system using the digits 0-1,a-i.")],
		_(u"base 20 vigesimal"):
			[(b,20),"base 20",_(u"Base Twenty numbering system using the digits 0-1,a-j.")],
		_(u"base 30 trigesimal"):
			[(b,30),"base 30",_(u"Base Thirty numbering system using the digits 0-1,a-r.")],
		_(u"base 36 hexatrigesimal"):
			[(b,36),"base 36",_(u"Base Thirty-six numbering system using the digits 0-9,a-z.")],
		_(u"base 40 quadragesimal"):
			[(b,40),"base 40",_(u"Base Forty digits numbering system using the digits 0-1,a-f,A-C.")],
		_(u"base 50 quinquagesimal"):
			[(b,50),"base 50",_(u"Base Fifty digits numbering system using the digits 0-1,a-f,A-M.")],
		_(u"base 60 sexagesimal"):
			[(b,60),"base 60",_(u"Base Sixty numbering system using the digits 0-9,a-z,A-V.")],
		_(u"base 62 duosexagesimal"):
			[(b,62),"base 62",_('Base Sixty-two numbering system using the digits 0-9,a-z,A-Z. This is the highest numbering system that can be represented with all decimal numbers and lower and upper case English alphabet characters. Other number systems include septagesimal (base 70), octagesimal (base 80), nonagesimal (base 90), centimal (base 100), bicentimal (base 200), tercentimal (base 300), quattrocentimal (base 400), quincentimal (base 500).')],
		_(u"roman numerals"):
			[(r,0),'',_('A symbol set in the old Roman notation; I,V,X,L,C,D,M. Range 1 to 3999 (higher values cannot be represented with standard ASCII characters).')],
	},
	_('Density'):{".base_unit":_(u"kilogram/cubic meter"),
		_('kilogram per cubic meter'):
			[(m,1.0),u"kg/m\xb3",''],
		_('kg per cubic cm'):
			[(m,1.0e6),u"kg/cm\xb3",_(u"kilograms per cubic centimeter.")],
		_(u"pound mass per gallon (UK)"):
			[(m,99.7763664739553),"lbm/gal",_(u"Pounds mass per US liquid gallon.")],
		_(u"pound mass per gallon (US)"):
			[(m,119.826427316897),"lbm/gal",_(u"Pounds mass per US liquid gallon.")],
		_(u"slug per cubic ft"):
			[(m,515.3788),u"slug/ft\xb3",''],
		_(u"gram per cubic cm "):
			[(m,1000.0),u"g/cm\xb3",''],
		_(u"gram per cubic meter "):
			[(m,.001),u"g/m\xb3",''],
		_(u"milligram/cubic meter "):
			[(m,1.0e-6),u"mg/m\xb3",''],
		_(u"kilogram per liter"):
			[(m,1000.0),"kg/l",''],
		_(u"metric ton per cubic meter"):
			[(m,1000.0),u"metric ton/m\xb3",''],
		_(u"pound per cubic foot"):
			[(m,0.45359237/0.028316846592),u"lbm/ft\xb3",_(u"Pounds mass per cubic foot.")],
		_(u"pound per cubic inch"):
			[(m,0.45359237/0.000016387064),u"lbm/in\xb3",_(u"Pounds mass per cubic inch.")],
		_(u"aluminum"):
			[(m,2643.0),"Al",_(u"Enter 1 here to find the density of aluminum.")],
		_(u"iron"):
			[(m,7658.0),"Fe",_(u"Enter 1 here to find the density of iron.")],
		_(u"copper"):
			[(m,8906.0),"Cu",_(u"Enter 1 here to find the density of copper.")],
		_(u"lead"):
			[(m,11370.0),"Pb",_(u"Enter 1 here to find the density of lead.")],
		_(u"gold"):
			[(m,19300.0),"Au",_(u"Enter 1 here to find the density of gold.")],
		_(u"silver"):
			[(m,10510.0),"Ag",_(u"Enter 1 here to find the density of silver.")],
		_(u"water at 4degC"):
			[(m,1000.0),u"H20 at 4\xb0C",_(u"Enter 1 here to find the density of water at 4\xb0C. Water weighs 1 gram per cm\xb3.")],
		_(u"ounces per gallon (UK)"):
			[(m,(6.23602290462221)),_(u"oz/gal"),''],
		_(u"ounces per gallon (US)"):
			[(m,(7.48915170730604)),_(u"oz/gal"),''],
		_(u"ton (UK | long) per cubic yard"):
			[(m,2240.0 * 0.45359237/0.764554857984),u"ton/yard\xb3",''],
		_(u"ton (UK | long) per cubic foot"):
			[(m,2240.0 * 0.45359237/0.764554857984*27.0),u"ton/ft\xb3",''],
		_(u"ton (US | short) per cubic yard"):
			[(m,2000.0 * 0.45359237/0.764554857984),u"ton/yard\xb3",''],
		_(u"ton (US | short) per cubic foot"):
			[(m,32040.0),u"ton/ft\xb3",''],
	},

	_(u"Electrical Current"):{".base_unit":_(u"ampere"),
		_(u"ampere"):
			[(m,1.0),"A",u"Named after the French physicist Andr\x82 Marie Amp\x82re (1775-1836). The unit of electric current; -- defined by the International Electrical Congress in 1893 and by U. S. Statute as, one tenth of the unit of current of the C. G. S. system of electro-magnetic units, or the practical equivalent of the unvarying current which, when passed through a standard solution of nitrate of silver in water, deposits silver at the rate of 0.001118 grams per second."],
		_(u"kiloampere"):
			[(m,1.0e3),"kA",''],
		_(u"milliampere"):
			[(m,1.0e-3),"mA",''],
		_(u"microampere"):
			[(m,1.0e-6),u"\xb5A",''],
		_(u"nanoampere"):
			[(m,1.0e-9),"nA",''],
		_(u"picoampere"):
			[(m,1.0e-12),"pA",''],
		_(u"abampere"):
			[(m,10.0),"abA",_(u"The CGS electromagnetic unit of current.")],
		_(u"coulomb per second"):
			[(m,1.0),'',''],
		_(u"statampere"):
			[(m,1.e-9/3),'',_(u"The CGS electrostatic unit of current.")],
	},
	_(u"Electrical Charge"):{".base_unit":_(u"coulomb"),
		_(u"faraday"):
			[(m,96.5e3),'',_(u"Named after Michael Faraday the The English physicist and chemist who discovered electromagnetic induction (1791-1867). The amount of electric charge that liberates one gram equivalent of any ion from an electrolytic solution. ")],
		_(u"kilocoulomb"):
			[(m,1.0e3),"kC",''],
		_(u"ampere-hour"):
			[(m,3.6e3),u"A\xb7h",_(u"Commonly used to describe the capacity of a battery.")],
		_(u"abcoulomb"):
			[(m,10.0),"abC",_(u"The CGS electromagnetic unit of charge.")],
		_(u"coulomb (weber)"):
			[(m,1.0),"C",_(u"Named after the French physicist and electrican Coulomb. (Physics) The standard unit of quantity in electrical measurements. It is the quantity of electricity conveyed in one second by the current produced by an electro-motive force of one volt acting in a circuit having a resistance of one ohm, or the quantity transferred by one amp`ere in one second. Formerly called weber.")],
		_(u"microcoulomb"):
			[(m,1.0e-6),u"\xb5C",''],
		_(u"nanocoulomb"):
			[(m,1.0e-9),"nC",''],
		_(u"statcoulomb"):
			[(m,1.0e-9/3),"sC",_(u"The CGS electrostatic unit of charge.")],
		_(u"electron charge"):
			[(m,1.0/(6.2414503832469e18)),'',''],
	},
	_(u"Electrical Voltage"):{".base_unit":_(u"volt"),
		_(u"abvolt"):
			[(m,1.0e-8),"abV",_(u"A unit of potential equal to one-hundred-millionth of a volt.")],
		_(u"volt"):
			[(m,1.0),"V",_(u"""Named after the Italian electrician Alessandro Volta. The unit of electro-motive force; -- defined by the International Electrical Congress in 1893 and by United States Statute as, that electro-motive force which steadily applied to a conductor whose resistance is one ohm will produce a current of one ampere. It is practically equivalent to 1000/1434 the electro-motive force of a standard Clark's cell at a temperature of 15deg C.""")],
		_(u"gigavolt"):
			[(m,1.0e9),"GV",_(u"One billion volts.")],
		_(u"megavolt"):
			[(m,1.0e6),"MV",_(u"One million volts.")],
		_(u"kilovolt"):
			[(m,1.0e3),"kV",_(u"One thousand volts.")],
		_(u"millivolt"):
			[(m,1.0e-3),"mV",_(u"One thousandth of an volt.")],
		_(u"microvolt"):
			[(m,1.0e-6),u"\xb5V",_(u"One millionth of an volt.")],
		_(u"nanovolt"):
			[(m,1.0e-9),"nV",_(u"One billionth of an volt.")],
		_(u"statvolt"):
			[(m,300.0),'',_(u"300 volts.")],
	},
	_(u"Electrical Resistance & Conductance"):{".base_unit":_(u"ohm"),
		_(u"ohm"):
			[(m,1.0),"ohm",_(u"Named after the German physicist Georg Simon Ohm (1787-1854). The standard unit in the measure of electrical resistance, being the resistance of a circuit in which a potential difference of one volt produces a current of one ampere. As defined by the International Electrical Congress in 1893, and by United States Statute, it is a resistance substantially equal to 10^9 units of resistance of the C.G.S. system of electro-magnetic units, and is represented by the resistance offered to an unvarying electric current by a column of mercury at the temperature of melting ice 14.4521 grams in mass, of a constant cross-sectional area, and of the length of 106.3 centimeters. As thus defined it is called the international ohm")],
		_(u"siemens | mho"):
			[(inv,1.0),"S",_(u"Named after Ernst Werner von Siemens (1816-1892). A unit describing how well materials conduct equal to the reciprocal of an ohm syn: mho, S")],
		_(u"abmho"):
			[(inv,1.0e-9),"abmho",''],
		_(u"millisiemens | millimho"):
			[(inv,1.0e3),"mS",''],
		_(u"microsiemens | micromho"):
			[(inv,1.0e6),u"\xb5S",''],
		_(u"statmho"):
			[(inv,8.99e11),'',''],
		_(u"gigaohm"):
			[(m,1.0e9),_(u"G ohm"),_(u"One billion ohms.")],
		_(u"megaohm"):
			[(m,1.0e6),_(u"M ohm"),_(u"One million ohms.")],
		_(u"kilohm"):
			[(m,1.0e3),_(u"k ohm"),_(u"One thousand ohms.")],
		_(u"milliohm"):
			[(m,1.0e-3),_(u"m ohm"),_(u"One thousandth of an ohm.")],
		_(u"microhm"):
			[(m,1.0e-6),u"\xb5 ohm",_(u"One millionth of an ohm.")],
		_(u"nanohm"):
			[(m,1.0e-9),"n ohm",_(u"One billionth of an ohm.")],
		_(u"abohm"):
			[(m,1.0e-9),"ab ohm",''],
		_(u"statohm"):
			[(m,8.99e5*1e6),'',''],
	},
	_(u"Electrical Inductance"):{".base_unit":_(u"henry"),
		_(u"henry"):
			[(m,1.0),"H",_(u"Named after the American physicist Joseph Henry (1797-1878). The unit of electric induction; the induction in a circuit when the electro-motive force induced in this circuit is one volt, while the inducing current varies at the rate of one ampere a second.")],
		_(u"stathenry"):
			[(m,8.99e11),'',''],
		_(u"ohm-second"):
			[(m,1.0),u"ohm\xb7sec",''],
		_(u"millihenry"):
			[(m,1.0e-3),"mH",''],
		_(u"microhenry"):
			[(m,1.0e-6),u"\xb5H",''],
		_(u"nanohenry"):
			[(m,1.0e-9),"nH",''],
		_(u"abhenry"):
			[(m,1.0e-9),"abH",''],
	},
	_(u"Electrical Capacitance"):{".base_unit":_(u"farad"),
		_(u"farad"):
			[(m,1.0),"F",_(u"Named after the English electrician Michael Faraday. The standard unit of electrical capacity; the capacity of a condenser whose charge, having an electro-motive force of one volt, is equal to the amount of electricity which, with the same electromotive force, passes through one ohm in one second; the capacity, which, charged with one coulomb, gives an electro-motive force of one volt.")],
		_(u"abfarad"):
			[(m,1e9),"abF",_(u"A capacitance unit equal to one billion farads")],
		_(u"second/ohm"):
			[(m,1.0),'',''],
		_(u"microfarad"):
			[(m,1e-6),u"\xb5F",''],
		_(u"statfarad"):
			[(m,1.0e-6/8.99e5),'',''],
		_(u"nanofarad"):
			[(m,1e-9),"nF",''],
		_(u"picofarad"):
			[(m,1e-12),"pF",''],
	},
	_(u"Electromagnetic Radiation"):{".base_unit":_(u"hertz"),
		_(u"hertz"):
			[(m,1.0),'Hz',_(u"""Named after the German physicist Heinrich Hertz (1857-1894) who was the first to produce electromagnetic waves artificially. Having a periodic interval of one second.""")],
		_(u"meter"):
			[(inv,299792458.0),"m",_(u"Equal to 39.37 English inches, the standard of linear measure in the metric system of weights and measures. It was intended to be, and is very nearly, the ten millionth part of the distance from the equator to the north pole, as ascertained by actual measurement of an arc of a meridian.")],
		_(u"centimeter"):
			[(inv,29979245800.0),"cm",''],
		_(u"millimeter"):
			[(inv,299792458000.0),"mm",''],
		_(u"micrometer | micron"):
			[(inv,299792458000000.0),u"\xb5m",_(u"A metric unit of length equal to one millionth of a meter. The thousandth part of one millimeter.")],
		_(u"nanometer"):
			[(inv,299792458000000000.0),"nm",_(u"A metric unit of length equal to one billionth of a meter.")],
		_(u"angstrom"):
			[(inv,2997924580000000000.0),u"\xc5",_(u"Equal to one ten billionth of a meter (or 0.0001 micron); used to specify wavelengths of electromagnetic radiation")],
		_(u"kilohertz"):
			[(m,1.0e3),"KHz",''],
		_(u"megahertz"):
			[(m,1.0e6),"MHz",''],
		_(u"gigahertz"):
			[(m,1.0e9),"GHz",''],
		_(u"terahertz"):
			[(m,1.0e12),"THz",''],
		_(u"petahertz"):
			[(m,1.0e15),"PHz",''],
		_(u"exahertz"):
			[(m,1.0e18),"EHz",''],
		_(u"electron Volt"):
			[(m,1/4.13566e-15),"eV",_(u"Energy. e=h\xf6f where h = Planks constant (4.13566 x 10^-15 electron volts/second). f = frequency in Hertz.")],
	},
	_(u"Energy | Work"):{".base_unit":_(u"joule | wattsecond | newton-meter"),
		_(u"kiloton"):
			[(m,4200.0e9),'',_(u"A measure of explosive power (of an atomic weapon) equal to that of 1000 tons of TNT")],
		_(u"gigawatt-hour"):
			[(m,3.6e12),"GWh",''],
		_(u"megawatt-hour"):
			[(m,3.6e9),"MWh",''],
		_(u"kilowatt-hour"):
			[(m,3.6e6),"kWh",''],
		_(u"horsepower-hour"):
			[(m,2.686e6),u"hp\xb7h",''],
		_(u"gigajoule"):
			[(m,1.0e9),"GJ",''],
		_(u"megajoule"):
			[(m,1.0e6),"MJ",''],
		_(u"kg force meters"):
			[(m,9.80665),u"kgf\xb7m",_(u"Work done by one kilogram of force acting through a distance of one meter.")],
		_(u"kilojoule"):
			[(m,1.0e3),"kJ",''],
		_(u"watt-hour"):
			[(m,3.6e3),"Wh",''],
		_(u"British thermal unit"):
			[(m,1.055e3),"Btu",''],
		_(u"joule | wattsecond | newton-meter"):
			[(m,1.0),"J",_(u"Named after the English physicist James Prescott Joule(1818-1889). A unit of work which is equal to 10^7 units of work in the C. G. S. system of units (ergs), and is practically equivalent to the energy expended in one second by an electric current of one ampere in a resistance of one ohm. One joule is approximately equal to 0.738 foot pounds.")],
		_(u"kilocalorie"):
			[(m,4.184e3),"kcal",''],
		_(u"calorie"):
			[(m,4.184),"cal",_(u"The unit of heat according to the French standard; the amount of heat required to raise the temperature of one kilogram (sometimes, one gram) of water one degree centigrade, or from 0deg to 1deg.")],
		_(u"foot-poundals"):
			[(m,0.04214),'',''],
		_(u"foot-pound force"):
			[(m,1.356),u"ft\xb7lbf",_(u"A unit of work equal to a force of one pound moving through a distance of one foot")],
		_(u"millijoule"):
			[(m,1.0e-3),"mJ",''],
		_(u"microjoule"):
			[(m,1.0e-6),u"\xb5J",''],
		_(u"attojoule"):
			[(m,1.0e-18),"aJ",''],
		_(u"erg | dyne-centimeter"):
			[(m,1.0e-7),'',_(u"The unit of work or energy in the C. G. S. system, being the amount of work done by a dyne working through a distance of one centimeter; the amount of energy expended in moving a body one centimeter against a force of one dyne. One foot pound is equal to 13,560,000 ergs.")],
		_(u"GeV"):
			[(m,1.0e-9/6.24),'',_(u"A billion electronvolts")],
		_(u"MeV"):
			[(m,1.0e-12/6.24),'',_(u"a million electronvolts")],
		_(u"electron volt"):
			[(m,1.0e-18/6.24),"eV",_(u"A unit of energy equal to the work done by an electron accelerated through a potential difference of 1 volt")],
#1 cubic foot of natural gas ... 1,008 to 1,034 Btu 
		
		_(u"therm of natural gas"):
			[(m,1.055e8),"",'1 therm of natural gas = 100,000 Btu'],

		_(u"gallon of liquefied petroleum gas"):
			[(m,1.055e3*95475),"LPG",'1 gallon of liquefied petroleum gas = 95,475 Btu'],
		_(u"gallon of crude oil"):
			[(m,1.055e3*138095),"",'1 gallon of crude oil = 138,095 Btu'],
		_(u"barrel of crude oil"):
			[(m,1.055e3*5800000),"",'1 barrel of crude oil = 5,800,000 Btu'],
		_(u"gallon of kerosene or light distillate oil"):
			[(m,1.055e3*135000),"",'1 gallon of kerosene or light distillate oil = 135,000 Btu '],
		_(u"gallon middle distillate or diesel fuel oil"):
			[(m,1.055e3*138690),"",'1 gallon middle distillate or diesel fuel oil = 138,690 Btu '],


		_(u"gallon residential fuel oil"):
			[(m,1.055e3*149690),"",'1 gallon residential fuel oil = 149,690 Btu'],
		_(u"gallon of gasoline"):
			[(m,1.055e3*125000),"",'1 gallon of gasoline = 125,000 Btu'],
		_(u"gallon of ethanol"):
			[(m,1.055e3*84400),"",'1 gallon of ethanol = 84,400 Btu'],
		_(u"gallon of methanol"):
			[(m,1.055e3*62800),"",'1 gallon of methanol = 62,800 Btu'],
		_(u"gallon gasohol (10% ethanol, 90% gasoline)"):
			[(m,1.055e3*120900),"",'1 gallon gasohol (10% ethanol, 90% gasoline) = 120,900 Btu'],
# 		_(u"pound of coal"):
# 			[(m,1.055e3),"",'pound of coal = 8,100-13,000 Btu'],
# 		_(u"ton of coal"):
# 			[(m,1.055e3),"",'1 ton of coal = 16,200,00-26,000,000 Btu'],
		_(u"ton of coke"):
			[(m,1.055e3*26000000),"",'1 ton of coke = 26,000,000 Btu'],
# 1 ton of wood = 9,000,00-17,000,000 Btu
# 		_(u""):
# 			[(m,1.055e3),"",''],
# 1 standard cord of wood = 18,000,000-24,000,000 Btu
# 		_(u""):
# 			[(m,1.055e3),"",''],
# 1 face cord of wood = 6,000,000-8,000,000 Btu
# 		_(u""):
# 			[(m,1.055e3),"",''],

# GJ to therm and MBTUs would be nice too.
		_(u"therm"):
			[(m,1.055e-3*10000),"",'10^5 BTUs'],


		_(u"Mega British thermal unit"):
			[(m,1.055e-3),"MBtu",'Million British thermal units'],

		_(u"pound of carbon (upper heating value)"):
			[(m,1.055e3*14550),"",'1 pound of carbon is 14,550 btu (upper heating value).'],

	},
	_(u"Flow (dry)"):{".base_unit":"litres per second",
		_(u"litres per second"):
			[(m,1.0),"lps",_(u"A cubic decimeter of material moving past a point every second.")],
		_(u"litres per minute"):
			[(m,1.0/60),"lpm",_(u"A cubic decimeter of material moving past a point every minute.")],
		_(u"cubic feet per minute"):
			[(m,1/(60*0.0353146667215)),"cfm",_(u"Commonly used to describe the flow rate produced by a large fan or blower.")],
		_(u"cubic feet per second"):
			[(m,1/0.0353146667215),"cfs",''],
		_(u"cubic inches per minute"):
			[(m,1/(60*61.0237440947)),u"in\xb3/m",''],
		_(u"cubic inches per second"):
			[(m,1/61.0237440947),u"in\xb3/s",''],
	},
	_(u"Flow (liquid)"):{".base_unit":"litres per second",
		_(u"litres per second"):
			[(m,1.0),"lps",_(u"A cubic decimeter of material moving past a point every second")],
		_(u"litres per minute"):
			[(m,1.0/60),"lpm",''],
		_(u"US gallons per minute"):
			[(m,1/(60*3.785411784)),"gpm (US)",''],
		_(u"US gallons per second"):
			[(m,1/3.785411784),"gps (US)",''],
		_(u"UK gallons per minute"):
			[(m,1/(60*4.54609028199)),"gpm (UK)",''],
		_(u"UK gallons per second"):
			[(m,1/4.54609028199),"gps (UK)",''],
	},
	_(u"Force"):{".base_unit":"newton",
		_(u"tonne of force"):
			[(m,9806.65),'',_(u"Metric ton of force, 1000 kilonewtons.")],
		_(u"ton of force"):
			[(m,2000*4.4482216152605),"tnf",_(u"2000 pounds of force.")],
		_(u"sthene"):
			[(m,1.0e3),'',_(u"Named from the Greek word sthenos, strength. One sthene is the force required to accelerate a mass of one tonne at a rate of 1 m/s2. ")],
		_(u"atomic weight"):
			[(m,1.6283353926E-26),'',_(u"Generally understood as the weight of the hydrogen atom.")],
		_(u"kip"):
			[(m,4.4482216152605e3),'',_(u"Kilopounds of force.")],
		_(u"kilonewton"):
			[(m,1.0e3),"kN",''],
		_(u"kilogram force | kilopond"):
			[(m,9.80665),"kgf",''],
		_(u"pound force"):
			[(m,4.4482216152605),"lbf",''],
		_(u"newton"):
			[(m,1.0),"N",_(u"Named after the English mathematician and physicist Sir Isaac Newton (1642-1727). A unit of force equal to the force that imparts an acceleration of 1 m/sec\xb2 to a mass of 1 kilogram; equal to 100,000 dynes")],
		_(u"ounce force"):
			[(m,4.4482216152605/16),"ozf",''],
		_(u"poundal"):
			[(m,0.138254954376),"pdl",_(u"A unit of force based upon the pound, foot, and second, being the force which, acting on a pound avoirdupois for one second, causes it to acquire by the of that time a velocity of one foot per second. It is about equal to the weight of half an ounce, and is 13,825 dynes.")],
		_(u"gram force"):
			[(m,9.80665/1e3),"gf",''],
		_(u"millinewton"):
			[(m,1.0e-3),"mN",''],
		_(u"dyne"):
			[(m,1.0e-5),"dyn",_(u"The unit of force, in the C. G. S. (Centimeter Gram Second) system of physical units; that is, the force which, acting on a gram for a second, generates a velocity of a centimeter per second.")],
		_(u"micronewton"):
			[(m,1.0e-6),u"\xb5N",''],
	},
	_(u"Length"):{".base_unit":"meter",
		_(u"klafter | faden (German)"):
			[(m,1.8965),'',_(u"Similar to the fathom.")],
		_(u"klafter | faden (Switzerland)"):
			[(m,1.8),'',_(u"Similar to the fathom.")],
		_(u"earth diamater"):
			[(m,12742630),'',_(u"Diameter for the Earth.")],
		_(u"actus (roman actus)"):
			[(m,35.47872),'',_(u"Land measurement, 120 Roman feet (pedes monetales). This was equivalent to 35.47872 meters.")],
		_(u"angstrom"):
			[(m,1.0e-10),u"\xc5",_(u"Equal to one ten billionth of a meter (or 0.0001 micron); used to specify wavelengths of electromagnetic radiation")],
		_(u"arshin | arshine | archin"):
			[(m,0.7112),'',_(u"Russian.  28 inches")],
		_(u"arpentcan"):
			[(m,44289.14688),'',_(u"arpentcan = 27.52 mile")],
		_(u"arpent (Canadian)"):
			[(m,58.471308),'',_(u"Canadian unit of land measurement. 191.835 ft")],
		_(u"arpentlin | French arpent"):
			[(m,30*6.395*12*(25.4/1000)),'',_(u"French unit of land measurement. 30 toises")],
		_(u"assbaa"):
			[(m,0.02),'',_(u"Arabian measure.")],
		_(u"astronomical unit"):
			[(m,149597871000.0),"AU",_(u"Used for distances within the solar system; equal to the mean distance between the Earth and the Sun (approximately 93 million miles or 150 million kilometers).")],
		_(u"barleycorn"):
			[(m,8.46666666666667E-03),'',_(u"Formerly, a measure of length, equal to the average length of a grain of barley; the third part of an inch.")],
		_(u"bohr radius"):
			[(m,52.9177/1e12),'',_(u"Named after the Danish physicist Niels Bohr (1885-1962), who explained the structure of atoms in 1913. The bohr radius represents the mean distance between the proton and the electron in an unexcited hydrogen atom. 52.9177 picometers. ")],
		_(u"bolt"):
			[(m,36.576),'',_(u"A compact package or roll of cloth, as of canvas or silk, often containing about forty yards.")],
		_(u"bottom measure"):
			[(m,(25.4/1000)/40),'',_(u"One fortieth of an inch.")],
		_(u"cable length"):
			[(m,219.456),'',_(u"A nautical unit of depth. 720 feet.")],
		_(u"caliber (gun barrel caliber)"):
			[(m,0.000254),'',_(u"The diameter of round or cylindrical body, as of a bullet or column.")],
		_(u"cane"):
			[(m,3.84049),'',_(u"Persian")],
		_(u"chain (surveyors | Gunters)"):
			[(m,20.1168),'',_(u"A surveyors instrument which consists of links and is used in measuring land.One commonly in use is Gunter's chain, which consists of one hundred links, each link being seven inches and ninety-two one hundredths in length; making up the total length of rods, or sixty-six, feet; hence, a measure of that length; hence, also, a unit for land measure equal to four rods.")],
		_(u"chain (engineers)"):
			[(m,100*(12*25.4/1000)),'',_(u"100 ft.")],
		_(u"charac"):
			[(m,0.2601),'',_(u"Persian")],
		_(u"chebel"):
			[(m,21.03124),'',_(u"Persian")],
		_(u"city block"):
			[(m,100*(36*25.4/1000)),'',_(u"An informal measurement, about 100 yards")],
		_(u"cubit (Biblical | Hebrew | English)"):
			[(m,18.00*(25.4/1000)),'',_(u"A measure of length, being the distance from the elbow to the extremity of the middle finger. Note: The cubit varies in length in different countries, the English,Hebrew and Biblical cubits are 18 inches.")],
		_(u"cubit (Indian) | hasta"):
			[(m,0.64161),'',''],
		_(u"cubit (Roman)"):
			[(m,17.47*(25.4/1000)),'',_(u"A measure of length, being the distance from the elbow to the extremity of the middle finger. Note: The cubit varies in length in different countries, the Roman cubit is 17.47 inches.")],
		_(u"cubit (Greek) | pechya"):
			[(m,18.20*(25.4/1000)),'',_(u"A measure of length, being the distance from the elbow to the extremity of the middle finger. Note: The cubit varies in length in different countries, the Greek cubit is 18.20 inches.")],
		_(u"cubit (Israeli)"):
			[(m,0.55372),'',_(u"A measure of length, being the distance from the elbow to the extremity of the middle finger. Note: The cubit varies in length in different countries, the Israeli cubit is 21.8 inches.")],
		_(u"cloth finger"):
			[(m,4.5*(25.4/1000)),'',_(u"Used in sewing")],
		_(u"cloth quarter"):
			[(m,9*(25.4/1000)),'',_(u"Used in sewing")],
		_(u"compton wavelength of the electron"):
			[(m,1836.11*1.00138*1.31962/1e15),'',_(u"Named after Arthur Holly Compton (1892-1962)")],
		_(u"compton wavelength of the proton"):
			[(m,1.00138*1.31962/1e15),'',_(u"Named after Arthur Holly Compton (1892-1962)")],
		_(u"compton wavelength of the neutron"):
			[(m,1.31962/1e15),'',_(u"Named after Arthur Holly Compton (1892-1962)")],
		_(u"classical electron radius"):
			[(m,2.13247*1.00138*1.31962/1e15),'',''],
		_(u"digit | digitus"):
			[(m,0.018542),'',_(u"A finger's breadth, commonly estimated to be three fourths of an inch.")],
		_(u"decimeter"):
			[(m,1.0e-1),"dm","""The tenth part of a meter; a measure of length equal to rather more than 3.937 of an inch."""],
		_(u"diamond (Typographical)"):
			[(m,4.5*0.35146e-3),'',_(u"4 1/2 pt in height.")],
		_(u"pearl (Typographical)"):
			[(m,5*0.35146e-3),'',_(u"5 pt in height.")],
		_(u"agate | ruby (Typographical)"):
			[(m,5.5*0.35146e-3),'',_(u"Used in typing. A kind of type, larger than pearl and smaller than nonpareil; in England called ruby. 5 1/2 pt in height.")],
		_(u"nonpareil (Typographical)"):
			[(m,6*0.35146e-3),'',_(u"6 pt in height.")],
		_(u"minion (Typographical)"):
			[(m,7*0.35146e-3),'',_(u"7 pt in height.")],
		_(u"brevier (Typographical)"):
			[(m,8*0.35146e-3),'',_(u"8 pt in height.")],
		_(u"bourgeois (Typographical)"):
			[(m,9*0.35146e-3),'',_(u"9 pt in height.")],
		_(u"elite | long primer (Typographical)"):
			[(m,10*0.35146e-3),'',_(u"10 pt in height.")],
		_(u"small pica (Typographical)"):
			[(m,11*0.35146e-3),'',_(u"11 pt in height.")],
		_(u"pica (Typographical)"):
			[(m,12*0.35146e-3),'',_(u"A size of type next larger than small pica, and smaller than English.12 pt in height")],
		_(u"english (Typographical)"):
			[(m,14*0.35146e-3),'',_(u"14 pt in height.")],
		_(u"columbian (Typographical)"):
			[(m,16*0.35146e-3),'',_(u"16 pt in height.")],
		_(u"great primer (Typographical)"):
			[(m,18*0.35146e-3),'',_(u"18 pt in height.")],
		_(u"point (pica) (Typographical)"):
			[(m,0.35146e-3),"pt",_(u"Typographical measurement. This system was developed in England and is used in Great-Britain and the US. 1 pica equals 12 pica points.")],
		_(u"point (didot) (Typographical)"):
			[(m,0.376065e-3),"pt",_(u"Typographical measurement. The didot system originated in France but was used in most of Europe")],
		_(u"cicero (Typographical)"):
			[(m,12*0.376065e-3),'',_(u"Typographical measurement. 1 cicero equals 12 didot points.")],
		_(u"point (PostScript) (Typographical)"):
			[(m,(25.4/1000)/72),"pt",_(u"Typographical measurement. Created by Adobe. There are exactly 72 PostScript points in 1 inch.")],

		_(u"ell (English)"):
			[(m,45*(25.4/1000)),'',_(u"A measure for cloth; -- now rarely used. It is of different lengths in different countries; the English ell being 45 inches, the Dutch or Flemish ell 27, the Scotch about 37.")],
		_(u"ell (Dutch | Flemish)"):
			[(m,27*(25.4/1000)),'',_(u"A measure for cloth; -- now rarely used. It is of different lengths in different countries; the English ell being 45 inches, the Dutch or Flemish ell 27, the Scotch about 37.")],
		_(u"ell (Scotch)"):
			[(m,37*(25.4/1000)),'',_(u"A measure for cloth; -- now rarely used. It is of different lengths in different countries; the English ell being 45 inches, the Dutch or Flemish ell 27, the Scotch about 37.")],
		_(u"em"):
			[(m,0.0003514598),'',_(u"Used in typography. A quadrat, the face or top of which is a perfect square; also, the size of such a square in any given size of type, used as the unit of measurement for that type: 500 m's of pica would be a piece of matter whose length and breadth in pica m's multiplied together produce that number.")],
		_(u"en"):
			[(m,0.0001757299),'',_(u"Used in typography. Half an em, that is, half of the unit of space in measuring printed matter.")],
		_(u"fathom"):
			[(m,6*(12*25.4/1000)),'',_(u"6 feet. Approximately the space to which a man can extend his arms.")],
		_(u"fathom (Greek)"):
			[(m,4*18.20*(25.4/1000)),'',_(u"4 Greek cubits.")],
		_(u"fermi"):
			[(m,1e-15),'',_(u"a metric unit of length equal to one quadrillionth of a meter ")],
		_(u"finger breadth"):
			[(m,0.875*(25.4/1000)),'',_(u"The breadth of a finger, or the fourth part of the hand; a measure of nearly an inch.")],
		_(u"finger length"):
			[(m,4.5*(25.4/1000)),'',_(u"The length of finger, a measure in domestic use in the United States, of about four and a half inches or one eighth of a yard.")],
		_(u"foot"):
			[(m,12*(25.4/1000)),"ft",_(u"Equivalent to twelve inches; one third of a yard. This measure is supposed to be taken from the length of a man's foot.")],
		_(u"foot (Assyrian)"):
			[(m,2.63042),'',''],
		_(u"foot (Arabian)"):
			[(m,0.31919),'',''],
		_(u"foot (Roman) | pes"):
			[(m,0.2959608),'',''],
		_(u"foot (geodetic | survey)"):
			[(m,1200.0/3937),'',_(u"A former U.S. definition of the foot as exactly 1200/3937 meter or about 30.48006096 centimeters. This was the official U.S. definition of the foot from 1866 to 1959; it makes the meter equal exactly 39.37 inches. In 1959 the survey foot was replaced by the international foot, equal to exactly 30.48 centimeters. However, the survey foot remains the basis for precise geodetic surveying in the U.S.")],
		_(u"furlong"):
			[(m,40*5.0292),'','The eighth part of a mile; forty rods; two hundred and twenty yards. From the Old English fuhrlang, meaning "the length of a furrow".'],
		_(u"ghalva"):
			[(m,230.42925),'',_(u"Arabian measure")],
		_(u"gradus (Roman)"):
			[(m,2.43*(12*25.4/1000)),'',''],
		_(u"hand"):
			[(m,0.1016),'',_(u"A measure equal to a hand's breadth, -- four inches; a palm. Chiefly used in measuring the height of horses.")],
		_(u"inch"):
			[(m,(25.4/1000)),"in",_(u"The twelfth part of a foot, commonly subdivided into halves, quarters, eights, sixteenths, etc., as among mechanics. It was also formerly divided into twelve parts, called lines, and originally into three parts, called barleycorns, its length supposed to have been determined from three grains of barley placed end to end lengthwise.")],
		_(u"ken"):
			[(m,2.11836),'',_(u"Japanese fathom. The ken is the length of a traditional tatami mat.")],
		_(u"league (land | statute)"):
			[(m,3*1609.344),'',_(u" Used as a land measure. 3 statute miles.")],
		_(u"league (nautical)"):
			[(m,3*1852),'',_(u" Used as a marine measure. 3 nautical miles.")],
		_(u"li"):
			[(m,644.652),'',_(u"A Chinese measure of distance, being a little more than one third of a mile.")],
		_(u"light second"):
			[(m,299792458),'',_(u"The distance over which light can travel in one second; -- used as a unit in expressing stellar distances.")],
		_(u"light year"):
			[(m,9.460528405106E+15),'',_(u"The distance over which light can travel in a year's time; -- used as a unit in expressing stellar distances. It is more than 63,000 times as great as the distance from the earth to the sun.")],
		_(u"line"):
			[(m,(25.4/1000)/12),'',_(u"A measure of length; one twelfth of an inch.")],
		_(u"link (Gunters | surveyors)"):
			[(m,0.201168),'',_(u"""Part of a surveyors instrument (chain) which consists of links and is used in measuring land. One commonly in use is Gunter's chain, which consists of one hundred links, each link being 7.92" in length.""")],
		_(u"link (US | engineers)"):
			[(m,12*(25.4/1000)),'',_(u"Used by surveyors. In the U.S., where 100-foot chains are more common, the link is the same as the foot. ")],
		_(u"marathon"):
			[(m,42194.988),'',_(u"a footrace of 26 miles 385 yards")],

		_(u"megameter"):
			[(m,1.0e6),'',_(u"In the metric system, one million meters, or one thousand kilometers.")],
		_(u"kilometer"):
			[(m,1.0e3),"km",_(u"Being a thousand meters. It is equal to 3,280.8 feet, or 62137 of a mile.")],
		_(u"meter"):
			[(m,1.0),"m",_(u"Equal to 39.37 English inches, the standard of linear measure in the metric system of weights and measures. It was intended to be, and is very nearly, the ten millionth part of the distance from the equator to the north pole, as ascertained by actual measurement of an arc of a meridian.")],
		_(u"centimeter"):
			[(m,1.0e-2),"cm",_(u"""The hundredth part of a meter; a measure of length equal to rather more than thirty-nine hundredths (0.3937) of an inch.""")],
		_(u"millimeter"):
			[(m,1.0e-3),"mm",_(u"A lineal measure in the metric system, containing the thousandth part of a meter; equal to .03937 of an inch.")],
		_(u"micrometer | micron"):
			[(m,1.0e-6),u"\xb5m",_(u"A metric unit of length equal to one millionth of a meter. The thousandth part of one millimeter.")],
		_(u"nanometer"):
			[(m,1.0e-9),"nm",_(u"A metric unit of length equal to one billionth of a meter.")],
		_(u"picometer"):
			[(m,1.0e-12),'',_(u"A metric unit of length equal to one trillionth of a meter.")],
		_(u"femtometer"):
			[(m,1.0e-15),'',_(u"A metric unit of length equal to one quadrillionth of a meter.")],

		_(u"mil"):
			[(m,(25.4/1e6)),"mil",_(u"Equal to one thousandth of an inch; used to specify thickness (e.g., of sheets or wire)")],
		_(u"mile (Roman)"):
			[(m,1479.804),'',_(u"5000 Roman feet.")],
		_(u"mile (statute)"):
			[(m,1609.344),"mi",_(u"Mile is from the Latin word for 1000 (mille). A mile conforming to statute, that is, in England and the United States, a mile of 5,280 feet, as distinguished from any other mile.")],
		_(u"mile (nautical | geographical)"):
			[(m,1852.0),"nmi",_(u"Geographical, or Nautical mile, one sixtieth of a degree of a great circle of the earth, or about 6080.27 feet.")],
		_(u"nail (cloth)"):
			[(m,0.05715),'',_(u"Used for measuring cloth. 1/20 ell. The length of the last two joints (including the fingernail) of the middle finger. The nail is equivalent to 1/16 yard, 1/4 span.")],
		_(u"naval shot"):
			[(m,15*6*(12*25.4/1000)),'',_(u"Equal to 15 fathoms")],
		_(u"pace"):
			[(m,2.5*(12*25.4/1000)),'',_(u"The length of a step in walking or marching, reckoned from the heel of one foot to the heel of the other. Note: Ordinarily the pace is estimated at two and one half linear feet.")],
		_(u"pace (Roman) | passus"):
			[(m,5*0.2959608),'',_(u" The Roman pace (passus) was from the heel of one foot to the heel of the same foot when it next touched the ground, five Roman feet.")],
		_(u"pace (quick-time marching)"):
			[(m,30*(25.4/1000)),'',_(u"The regulation marching pace in the English and United States armies is thirty inches for quick time.")],
		_(u"pace (double-time marching)"):
			[(m,36*(25.4/1000)),'',_(u"The regulation marching pace in the English and United States armies is thirty-six inches for double time. ")],
		_(u"palm (Greek)"):
			[(m,7.71313333333333e-02),'',_(u"A lineal measure equal either to the breadth of the hand or to its length from the wrist to the ends of the fingers; a hand; -- used in measuring a horse's height. In Greece, the palm was reckoned at three inches. At the present day, this measure varies in the most arbitrary manner, being different in each country, and occasionally varying in the same. One third of a Greek span,")],
		_(u"palm (Roman lesser)"):
			[(m,2.91*(25.4/1000)),'',_(u"A lineal measure equal either to the breadth of the hand or to its length from the wrist to the ends of the fingers; a hand; -- used in measuring a horse's height. One of two Roman measures of the palm, the lesser palm is 2.91 inches. At the present day, this measure varies in the most arbitrary manner, being different in each country, and occasionally varying in the same.")],
		_(u"palm (Roman greater)"):
			[(m,8.73*(25.4/1000)),'',_(u"A lineal measure equal either to the breadth of the hand or to its length from the wrist to the ends of the fingers; a hand; -- used in measuring a horse's height. One of two Roman measures of the palm, the greater palm is 8.73 inches. At the present day, this measure varies in the most arbitrary manner, being different in each country, and occasionally varying in the same.")],
		_(u"parasang"):
			[(m,3.5*1609.344),'',_(u"A Persian measure of length, which, according to Herodotus and Xenophon, was thirty stadia, or somewhat more than three and a half miles. The measure varied in different times and places, and, as now used, is estimated at three and a half English miles.")],
		_(u"parsec"):
			[(m,3.08567758767931e16),'',_(u"A unit of astronomical length based on the distance from  Earth at which stellar parallax is 1 second of arc; equivalent to 3.262 light years")],
		_(u"rod | pole | perch"):
			[(m,5.0292),'',_(u"Containing sixteen and a half feet; -- called also perch, and pole.")],
		_(u"ri"):
			[(m,3926.79936),'',_(u"Japanese league.")],
		_(u"rope"):
			[(m,20*12*(25.4/1000)),'',_(u"20 feet")],
		_(u"sadzhens | sagene | sazhen"):
			[(m,2.10312),'',_(u"Russian and East European. Used in previous centuries (until WWI or WWII). The distance between a grown man's spread of arms , from the finger- tips of one to hand to the finger-tips of the other hand. Equal to about 7 feet long (2.13 m).")],
		_(u"shaku"):
			[(m,0.303022),'',_(u" A Japanese foot. Note: shaku also means area and volume.")],
		_(u"skein"):
			[(m,120*3*12*(25.4/1000)),'',_(u"120 yards. A skein of cotton yarn is formed by eighty turns of the thread round a fifty-four inch reel.")],
		_(u"soccer field"):
			[(m,100*3*12*(25.4/1000)),'',_(u"100 yards")],
		_(u"solar diameter"):
			[(m,1391900000),'',_(u"Diameter of our sun.")],
		_(u"span (Greek)"):
			[(m,0.231394),'',_(u"To measure by the span of the hand with the fingers extended, or with the fingers encompassing the object; as, to span a space or distance; to span a cylinder. One half of a Greek cubit.")],
		_(u"span (cloth)"):
			[(m,9*(25.4/1000)),'',_(u"9 inches")],
		_(u"spindle (cotten yarn)"):
			[(m,15120*3*12*(25.4/1000)),'',_(u"A cotten yarn measure containing 15,120 yards.")],
		_(u"spindle (linen yarn)"):
			[(m,14400*3*12*(25.4/1000)),'',_(u"A linen yarn measure containing 14,400 yards.")],
		_(u"stadia (Greek) | stadion"):
			[(m,185.1152),'',_(u"A Greek measure of length, being the chief one used for itinerary distances, also adopted by the Romans for nautical and astronomical measurements. It was equal to 600 Greek or 625 Roman feet, or 125 Roman paces, or to 606 feet 9 inches English. This was also called the Olympic stadium, as being the exact length of the foot-race course at Olympia.")],
		_(u"stadium (Persian)"):
			[(m,214.57962),'',''],
		_(u"stadium (Roman)"):
			[(m,184.7088),'',_(u"A Greek measure of length, being the chief one used for itinerary distances, also adopted by the Romans for nautical and astronomical measurements. It was equal to 600 Greek or 625 Roman feet, or 125 Roman paces, or to 606 feet 9 inches English. This was also called the Olympic stadium, as being the exact length of the foot-race course at Olympia.")],
		_(u"sun (Japanese)"):
			[(m,0.0303022),'',_(u"Japanese measurement.")],
		_(u"toise (French)"):
			[(m,6.395*12*(25.4/1000)),'',_(u"French fathom.")],
		_(u"vara (Spanish)"):
			[(m,33.385*(25.4/1000)),'',_(u"A Spanish measure of length equal to about one yard. 33.385 inches. ")],
		_(u"vara (Mexican)"):
			[(m,0.837946),'',_(u"A Mexican measure of length equal to about one yard. 32.99 inches. ")],
		_(u"verst | werst"):
			[(m,3500*12*(25.4/1000)),'',_(u"A Russian measure of length containing 3,500 English feet.")],
		_(u"yard"):
			[(m,3*12*(25.4/1000)),"yd",_(u"Equaling three feet, or thirty-six inches, being the standard of English and American measure.")],
	},
	_(u"Luminance"):{".base_unit":"candela per square meter",
		_(u"magnitudes per square arcsecond"):
			[(f,('108000*(10**(-0.4*x))','log((x/108000),10)/-0.4')),"mags/arcsec2",_(u"Used by astronomers to define the darkness of the night sky. Stars are rated by brightness in magnitudes . A lower magnitude number is a brighter star. The star Vega has a magnitude of zero, and a measurement of 0 magnitudes per square arcsecond would be like having every square arcsecond in the sky will with the brightness of the star Vega.")],
		_(u"candela per square centimeter"):
			[(m,1.0e4),u"cd/cm\xb2",''],
		_(u"kilocandela per square meter"):
			[(m,1.0e3),u"kcd/m\xb2",''],
		_(u"stilb"):
			[(m,1.0e4),"sb",'From a Greek word stilbein meaning "to glitter". Equal to one candela per square centimeter or 104 nits.'],
		_(u"lambert"):
			[(m,3183.09886183791),"L",_(u"Named after the German physicist Johann Heinrich Lambert (1728-1777).Equal to the brightness of a perfectly diffusing surface that emits or reflects one lumen per square centimeter")],
		_(u"candela per square inch"):
			[(m,1550.0031000062),u"cd/in\xb2",''],
		_(u"candela per square foot"):
			[(m,10.7639104167097),u"cd/ft\xb2",''],
		_(u"foot lambert"):
			[(m,3.42625909963539),"fL",''],
		_(u"millilambert"):
			[(m,3.18309886183791),"mL",''],
		_(u"candela per square meter"):
			[(m,1.0),u"cd/m\xb2",''],
		_(u"lumen per steradian square meter"):
			[(m,1.0),'',''],
		_(u"nit"):
			[(m,1.0),'',_(u"Named from the Latin niteo, to shine.")],
		_(u"apostilb"):
			[(m,3.18309886183791/10),"asb",'Named from the Greek stilbein, to "glitter" or "shine," with the prefix apo-, "away from." '],
	},
	_(u"Illumination"):{".base_unit":"lux",
		_(u"phot"):
			[(m,1.0e4),"ph",_(u"a unit of illumination equal to 1 lumen per square centimeter; 10,000 phots equal 1 lux")],
		_(u"lumen per square centimeter"):
			[(m,1.0e4),u"lm/cm\xb2",''],
		_(u"foot candle"):
			[(m,10.7639104167097),"fc",''],
		_(u"lumen per square foot"):
			[(m,10.7639104167097),u"lm/ft\xb2",''],
		_(u"lux"):
			[(m,1.0),"lx",_(u"Equal to the illumination produced by luminous flux of one lumen falling perpendicularly on a surface one meter square. Also called meter-candle.")],
		_(u"metre-candle"):
			[(m,1.0),"m-cd",_(u"Equal to the illumination produced by luminous flux of one lumen falling perpendicularly on a surface one meter square. Also called lux.")],
		_(u"lumen per square meter"):
			[(m,1.0),u"lm/m\xb2",''],
		_(u"candela steradian per square meter"):
			[(m,1.0),'',''],
	},
	_(u"Luminous Intensity (point sources)"):{".base_unit":"candela",
		_(u"candela"):
			[(m,1.0),"cd",_(u"The basic unit of luminous intensity adopted under the System International d'Unites; equal to 1/60 of the luminous intensity per square centimeter of a blackbody radiating at the temperature of 2,046 degrees Kelvin syn: candle, cd, standard candle.")],
		_(u"lumen per steradian"):
			[(m,1.0),"lm/sr",''],
		_(u"hefner candle"):
			[(m,0.92),"HC",_(u"Named after F. von Hefner-Altenack (1845-1904)")],
	},
	_(u"Luminous Flux"):{".base_unit":"lumen",
		_(u"lumen"):
			[(m,1.0),"lm",_(u"Equal to the luminous flux emitted in a unit solid angle by a point source of one candle intensity")],
		_(u"candela steradian"):
			[(m,1.0),u"cd\xb7sr",''],
	},
	_(u"Magnetomotive force"):{".base_unit":"ampere",
		_(u"ampere"):
			[(m,1.0),"A",''],
		_(u"ampere-turn"):
			[(m,1.0),"At",_(u"A unit of magnetomotive force equal to the magnetomotive force produced by the passage of 1 ampere through 1 complete turn of a coil.")],
		_(u"gilbert"):
			[(m,0.795775),"Gb",_(u"Named after the English scientist William Gilbert (1544-1603)")],
		_(u"kiloampere"):
			[(m,1e3),"kA",''],
		_(u"oersted-centimeter"):
			[(m,0.795775),'',_(u"The same value as the gilbert.")],
	},
	_(u"Magnetic Flux"):{".base_unit":"weber",
		_(u"weber"):
			[(m,1.0),"Wb",_(u"From the name of Professor Weber, a German electrician. One volt second.")],
		_(u"milliweber"):
			[(m,1.0e-3),"mWb",''],
		_(u"microweber"):
			[(m,1.0e-6),u"\xb5Wb",''],
		_(u"unit pole (electro magnetic unit)"):
			[(m,4e-8*pi),'',''],
		_(u"maxwell"):
			[(m,1.0e-8),"Mx",_(u"Named after the Scottish physicist James Clerk Maxwell (1831-1879). A cgs unit of magnetic flux equal to the flux perpendicular to an area of 1 square centimeter in a magnetic field of 1 gauss.")],
		_(u"line of force"):
			[(m,1.0e-8),'',_(u"Same as Maxwell")],
	},
	_(u"Magnetic Field strength"):{".base_unit":"ampere per meter",
		_(u"oersted"):
			[(m,1.0e3/(4*pi)),"Oe",_(u"Named after the Danish physicist and chemist Hans Christian Oersted (1777-1851). The C.G.S. unit of magnetic reluctance or resistance, equal to the reluctance of a centimeter cube of air (or vacuum) between parallel faces. Also, a reluctance in which unit magnetomotive force sets up unit flux.")],
		_(u"ampere per meter"):
			[(m,1.0),"A/m",''],
		_(u"ampere-turn per meter"):
			[(m,1.0),"A/m",''],
		_(u"kiloampere per meter"):
			[(m,1.0e3),"kA/m",''],
		_(u"ampere-turn per inch"):
			[(m,39.3700787401575),"At/in",''],
		_(u"newton per weber"):
			[(m,1.0),"N/Wb",_(u"Same as ampere per meter")],
	},
	_(u"Magnetic Flux Density"):{".base_unit":"tesla",
		_(u"tesla"):
			[(m,1.0),"T",_(u"Named after the Croatian born inventer Nikola Tesla (1856-1943). A unit of magnetic flux density equal to one weber per square meter.")],
		_(u"millitesla"):
			[(m,1.0e-3),"mT",''],
		_(u"microtesla"):
			[(m,1.0e-6),u"\xb5T",''],
		_(u"nanotesla"):
			[(m,1.0e-9),"nT",''],
		_(u"weber per square meter"):
			[(m,1.0),u"Wb/m\xb2",''],
		_(u"kilogauss"):
			[(m,1.0e-1),"kG",''],
		_(u"gauss"):
			[(m,1.0e-4),"G",_(u"Named after German mathematician and astronomer Karl Friedrich Gauss (1777-1855). The C.G.S. unit of density of magnetic field, equal to a field of one line of force per square centimeter, being thus adopted as an international unit at Paris in 1900; sometimes used as a unit of intensity of magnetic field. It was previously suggested as a unit of magnetomotive force.")],
		_(u"maxwell per square centimeter"):
			[(m,1.0e-4),u"Mx/cm\xb2",''],
		_(u"maxwell per square inch"):
			[(m,1.5500031000062E-05),u"Mx/in\xb2",''],
		_(u"line per square inch"):
			[(m,1.5500031000062E-05),'',_(u"Same as Maxwell per square inch.")],
		_(u"gamma"):
			[(m,1.0e-9),'',_(u"one nanotesla.")],
	},
	_(u"Mass"):{".base_unit":"kilogram",
		_(u"talanton"):
			[(m,149.9985),'',_(u"Greek measure.")],
		_(u"oka (Egyptian)"):
			[(m,1.248),'',''],
		_(u"oka (Greek)"):
			[(m,1.2799),'',''],
		_(u"okia"):
			[(m,0.03744027),'',_(u"Egyptian measure.")],
		_(u"kat"):
			[(m,0.009331),'',_(u"Egyptian measure.")],
		_(u"kerat"):
			[(m,0.00019504),'',_(u"Egyptian measure.")],
		_(u"pala"):
			[(m,0.047173),'',_(u"Indian measure.")],
		_(u"kona"):
			[(m,0.00699828),'',_(u"Indian measure.")],
		_(u"mast"):
			[(m,.9331),'',_(u"British")],
		_(u"kilogram"):
			[(m,1.0),"kg",_(u"A measure of weight, being a thousand grams, equal to 2.2046 pounds avoirdupois (15,432.34 grains). It is equal to the weight of a cubic decimeter of distilled water at the temperature of maximum density, or 39deg Fahrenheit.")],
		_(u"megagram"):
			[(m,1.0e3),"Mg",''],
		_(u"gram"):
			[(m,1.0e-3),"g",_(u"The unit of weight in the metric system. It was intended to be exactly, and is very nearly, equivalent to the weight in a vacuum of one cubic centimeter of pure water at its maximum density. It is equal to 15.432 grains.")],
		_(u"milligram"):
			[(m,1.0e-6),"mg",_(u"A measure of weight, in the metric system, being the thousandth part of a gram, equal to the weight of a cubic millimeter of water, or .01543 of a grain avoirdupois.")],
		_(u"microgram"):
			[(m,1.0e-9),u"\xb5g",_(u"A measure of weight, in the metric system, being the millionth part of a gram.")],
		_(u"ton (UK | long | gross | deadweight)"):
			[(m,2240 * 0.45359237),'',_(u"A British unit of weight equivalent to 2240 pounds")],
		_(u"ton (US | short)"):
			[(m,2000 * 0.45359237),"tn",_(u"A US unit of weight equivalent to 2000 pounds")],
		_(u"tonne | metric ton"):
			[(m,1.0e3),"t",_(u"A metric ton, One Megagram. 1000 kg")],
		_(u"pound (avoirdupois)"):
			[(m,0.45359237),"lb",_(u"The pound in general use in the United States and in England is the pound avoirdupois, which is divided into sixteen ounces, and contains 7,000 grains. The pound troy is divided into twelve ounces, and contains 5,760 grains. 144 pounds avoirdupois are equal to 175 pounds troy weight")],
		_(u"pound (troy)"):
			[(m,0.3732417216),'',''],
		_(u"hundredweight (short | net | US)"):
			[(m,100*0.45359237),"cwt",_(u"A denomination of weight of 100 pounds. In most of the United States, both in practice and by law, it is 100 pounds avoirdupois.")],
		_(u"hundredweight (long | English)"):
			[(m,112*0.45359237),"cwt",_(u"A denomination of weight of 112 pounds")],
		_(u"slug"):
			[(m,14.5939029372064),'',_(u"One slug is the mass accelerated at 1 foot per second per second by a force of 1 pound.")],
		_(u"ounce (troy)"):
			[(m,0.0311034768),"ozt",_(u"A unit of apothecary weight equal to 480 grains.")],
		_(u"ounce (avoirdupois)"):
			[(m,0.45359237/16),"oz",_(u"A weight, the sixteenth part of a pound avoirdupois")],
		_(u"dram (avoirdupois)"):
			[(m,(0.45359237/16)/16),'',_(u"A weight; in Avoirdupois weight, one sixteenth part of an ounce.")],
		_(u"dram (troy | apothecary)"):
			[(m,(0.0311034768)/8),'',_(u"""A weight; in Apothecaries' weight, one eighth part of an ounce, or sixty grains.""")],
		_(u"scruple (troy)"):
			[(m,20*(0.45359237/5760)),'',_(u"A weight of twenty grains; the third part of a troy dram.")],
		_(u"carat"):
			[(m,0.0002),'',_(u"The weight by which precious stones and pearls are weighed.")],
		_(u"grain"):
			[(m,0.00006479891),"gr",_(u"The unit of the English system of weights; -- so called because considered equal to the average of grains taken from the middle of the ears of wheat. 7,000 grains constitute the pound avoirdupois and 5,760 grains constitute the pound troy.")],
		_(u"amu (atomic mass unit) | dalton"):
			[(m,1.66044E-27),"amu",_(u"Unit of mass for expressing masses of atoms or molecules.")],
		_(u"catty | caddy | chin"):
			[(m,(4.0/3)*0.45359237),'',_(u"An Chinese or East Indian Weight of 1 1/3 pounds.")],
		_(u"cental"):
			[(m,100*0.45359237),'',_(u"British for 100 pounds. Also called hundredweight in the US.")],
		_(u"cotton bale (US)"):
			[(m,500*0.45359237),'',_(u"US measurement. 500 pounds")],
		_(u"cotton bale (Egypt)"):
			[(m,750*0.45359237),'',_(u"Egyptian measurement. 750 pounds")],
		_(u"crith"):
			[(m,0.0000906),'',_(u"From the Greek word for barleycorn. The weight of a liter of hydrogen at 0.01\xb0 centigrade and with a and pressure of 1 atmosphere.")],
		_(u"denarius"):
			[(m,60*(0.45359237/5760)),'',_(u"Roman weight measuring 60 troy grains")],
		_(u"dinar"):
			[(m,4.2e-3),'',_(u"Arabian weight measuring 4.2 gram")],
		_(u"doppelzentner"):
			[(m,100.0),'',_(u"Metric hundredweight = 100 kg")],
		_(u"drachma (Greek)"):
			[(m,0.0042923),'',_(u"The weight of an old Greek drachma coin")],
		_(u"drachma (Dutch)"):
			[(m,3.906e-3),'',_(u"The weight of an old Dutch drachma coin")],
		_(u"earth mass"):
			[(m,5.983E+24),'',_(u"Mass of the Earth.")],
		_(u"electron rest mass"):
			[(m,9.109558E-31),'',_(u"The mass of an electron as measured when the it is at rest relative to an observer, an inherent property of the body.")],
		_(u"funt"):
			[(m,0.408233133),'',_(u"Russian, 0.9 pounds")],
		_(u"obolos (Ancient Greece)"):
			[(m,0.0042923/6),'',_(u"Ancient Greek weight of an obol coin, 1/6 drachma")],
		_(u"obolos (Modern Greece)"):
			[(m,1.0e-4),'',_(u"Modern Greek name for decigram.")],
		_(u"hyl"):
			[(m,0.00980665),'',_(u"From an ancient Greek word for matter. One hyl is the mass that is accelerated at one meter per second per second by one kilogram of force. 0.00980665 kg.")],

		_(u"pennyweight (troy)"):
			[(m,24*0.00006479891),'',_(u"A troy weight containing twenty-four grains, or the twentieth part of a troy ounce; as, a pennyweight of gold or of arsenic. It was anciently the weight of a silver penny.")],
		_(u"bekah (Biblical)"):
			[(m,5*24*0.00006479891),'',_(u"1/2 shekel, 5 pennyweight.")],
		_(u"shekel (Israeli)"):
			[(m,10*24*0.00006479891),'',_(u"The sixtieth part of a mina. Ten pennyweight. An ancient weight and coin used by the Jews and by other nations of the same stock.")],
		_(u"mina (Greek) | minah (Biblical)"):
			[(m,60*10*24*0.00006479891),'',_(u"The weight of the ancient Greek mina coin. 60 shekels")],
		_(u"talent (Roman)"):
			[(m,125*0.3265865064),'',_(u"125 Roman libra.")],
		_(u"talent (silver)"):
			[(m,3000*10*24*0.00006479891),'',_(u"3,000 shekels or 125 lbs.")],
		_(u"talent (gold)"):
			[(m,6000*10*24*0.00006479891),'',_(u"2 silver talents, 250 lbs.")],
		_(u"talent (Hebrew)"):
			[(m,26.332),'',''],

		_(u"kin"):
			[(m,0.60010270551),'',_(u"Japanese kin,  1.323 pound.")],
		_(u"kwan"):
			[(m,3.7512088999),'',_(u"Japanese kwan. 8.27 pound")],
		_(u"liang | tael"):
			[(m,((4.0/3)*0.45359237)/16),'',_(u"Chinese. 1/16 catty")],
		_(u"libra | librae | as | pondus"):
			[(m,0.3265865064),'',_(u"Roman originator of the English pound (lb). 12 uncia")],
		_(u"libra (Mexican)"):
			[(m,0.46039625555),'',''],
		_(u"libra (Spanish)"):
			[(m,0.45994266318),'',''],
		_(u"livre (French)"):
			[(m,0.49),'',''],
		_(u"quarter (long)"):
			[(m,(112*0.45359237)/4),'',_(u"The fourth part of a long hundredweight. 28 pounds")],
		_(u"quarter (short)"):
			[(m,(100*0.45359237)/4),'',_(u"The fourth part of a short hundredweight. 25 pounds")],
		_(u"mite (English)"):
			[(m,0.0000032399455),'',_(u"A small weight; one twentieth of a grain.")],
		_(u"neutron rest mass"):
			[(m,1.67492E-27),'',_(u"The mass of a neutron as measured when the it is at rest relative to an observer, an inherent property of the body.")],
		_(u"proton rest mass"):
			[(m,1.672614E-27),'',_(u"The mass of a proton as measured when the it is at rest relative to an observer, an inherent property of the body.")],
		_(u"pfund (German)"):
			[(m,0.5),'',_(u"German pound. 500 grams. 16 unze.")],
		_(u"unze (German)"):
			[(m,0.5/16),'',_(u"German ounce. 1/16 pfund.")],
		_(u"lot (German)"):
			[(m,0.5/32),'',_(u"One half unze.")],
		_(u"picul | tan | pecul | pecal (Chinese | Summatra))"):
			[(m,133.5*0.45359237),'',_(u"100 catty. 133 1/2 pounds")],
		_(u"picul (Japan)"):
			[(m,(400.0/3)*0.45359237),'',_(u"133 1/3 pounds")],
		_(u"picul (Borneo)"):
			[(m,(1085.0/8)*0.45359237),'',_(u"135 5/8 pounds")],
		_(u"pood (Russian)"):
			[(m,16.3792204807),'',_(u"A Russian weight, equal to forty Russian pounds or about thirty-six English pounds avoirdupois.")],
		_(u"quintal"):
			[(m,100.0),'',_(u"A metric measure of weight, being 100,000 grams, or 100 kilograms")],
		_(u"quintal (short UK)"):
			[(m,100*0.45359237),'',_(u"100 pounds")],
		_(u"quintal (long UK)"):
			[(m,112*0.45359237),'',_(u"112 pounds")],
		_(u"quintal (Spanish)"):
			[(m,45.994266318),'',_(u"Spanish hundredweight")],
		_(u"scrupulum (Roman)"):
			[(m,0.0011359248923),'',''],
		_(u"stone (legal)"):
			[(m,14*0.45359237),'',_(u"14 pounds")],
		_(u"stone (butchers)"):
			[(m,8*0.45359237),'',_(u"Meat or fish. 8 pounds")],
		_(u"stone (cheese)"):
			[(m,16*0.45359237),'',_(u"16 pounds.")],
		_(u"stone (hemp)"):
			[(m,32*0.45359237),'',_(u"32 pounds")],
		_(u"stone (glass)"):
			[(m,5*0.45359237),'',_(u"5 pounds")],
		_(u"uncia"):
			[(m,0.3265865064/12),'',_('Ancient Roman. A twelfth part, as of the Roman "as" or "libra"; an ounce. 420 grains')],
	},
	_(u"Musical notes"):{".base_unit":"breve",
		_(u"whole note | semibreve"):
			[(m,0.5),'',_(u"A note of half the time or duration of the breve; -- now usually called a whole note.")],
		_(u"breve"):
			[(m,1.0),'',_(u"A note or character of time, equivalent to two semibreves or four minims. When dotted, it is equal to three semibreves.")],
		_(u"minim"):
			[(m,0.25),'',_(u"A time note, a half note, equal to half a semibreve, or two quarter notes or crotchets.")],
		_(u"crotchet"):
			[(m,0.125),'',_(u"A time note, with a stem, having one fourth the value of a semibreve, one half that of a minim, and twice that of a quaver; a quarter note.")],
		_(u"quaver"):
			[(m,0.0625),'',_(u"An eighth note.")],
	},
	_(u"Power"):{".base_unit":"watt",
		_(u"megawatt"):
			[(m,1.0e6),"MW",''],
		_(u"kilowatt"):
			[(m,1.0e3),"kW",''],
		_(u"watt"):
			[(m,1.0),"W",_(u"Named after the Scottish engineer and inventor James Watt (1736-1819). A unit of power or activity equal to 10^7 C.G.S. units of power, or to work done at the rate of one joule a second.")],
		_(u"milliwatt"):
			[(m,1.0e-3),"mW",''],
		_(u"microwatt"):
			[(m,1.0e-6),"uW",''],

		_(u"horsepower (boiler)"):
			[(m,9.81e3),'',_(u"A unit of power representing the power exerted by a horse in pulling.")],
		_(u"horsepower"):
			[(m,746.0),"hp",''],
		_(u"ton of refrigeration"):
			[(m,10.0/3*1055.05585262),"TR",''],
		_(u"btu per second"):
			[(m,1055.05585262),"Btu/s",''],
		_(u"calorie per second"):
			[(m,4.1868),"cal/s",''],
		_(u"kilcalorie per hour"):
			[(m,4186.8/3600),"kcal/h",_(u"Useful for calculating heating facilities and kitchens.")],
		_(u"frig per hour"):
			[(m,4186.8/3600),"frig/h",_(u"The same as kcal/h, but used for air conditioning and refrigerating.")],
		_(u"foot pound force per second"):
			[(m,1.356),"lbf/s",''],
		_(u"joule per second"):
			[(m,1.0),"J/s",''],
		_(u"newton meter per second"):
			[(m,1.0),u"N\xb7m/s",''],
		_(u"btu per hour"):
			[(m,0.293071070172222),"Btu/h",''],
		_(u"foot pound force per minute"):
			[(m,0.0226),u"ft\xb7lbf/min",''],
		_(u"erg per second"):
			[(m,1.0e-7),"erg/s",''],
		_(u"dyne centimeter per second"):
			[(m,1.0e-7),'',''],
		_(u"lusec"):
			[(m,0.000133322368421),'',_(u"Used to measure the leakage of vacuum pumps. A flow of one liter per second at a pressure of one micrometer of mercury.")],
	},
	_(u"Pressure and Stress"):{".base_unit":"pascal",
		_(u"pascal"):
			[(m,1.0),"Pa",_(u"Named after the French philosopher and mathematician Blaise Pascal (1623 - 1662). Equal to one newton per square meter.")],
		_(u"hectopascal"):
			[(m,100),"hPa",''],
		_(u"kilopascal"):
			[(m,1.0e3),"kPa",''],
		_(u"megapascal"):
			[(m,1.0e6),"MPa",''],
		_(u"atmosphere (absolute,standard)"):
			[(m,101325),"atm",_(u"The average pressure of the Earth's atmosphere at sea level.")],
		_(u"atmosphere (technical)"):
			[(m,98066.5),"atm",_(u"A metric unit equal to one kilogram of force per square centimeter.")],
		_(u"bar"):
			[(m,1.0e5),"bar",_(u"From the Greek word baros.")],
		_(u"pound force per square inch"):
			[(m,6894.75729316836),"psi",''],
		_(u"ounces per square inch"):
			[(m,6894.75729316836/16),u"oz/in\xb2",''],
		_(u"feet of water (60F,15.5C)"):
			[(m,12*133.322*1.866),"ftH20",''],
		_(u"inches of water (60F,15.5C)"):
			[(m,133.322*1.866),"inH20",''],
		_(u"meter of water (60F,15.5C)"):
			[(m,133.322*1.866/.0254),"mH20",''],
		_(u"centimeter of water (60F,15.5C)"):
			[(m,133.322*1.866/2.54),"cmH20",''],
		_(u"millimeter of water (60F,15.5C)"):
			[(m,133.322*1.866/25.4),"mmH20",''],

		_(u"feet of water (39.2F,4C)"):
			[(m,2988.9921933),"ftH20",''],
		_(u"inches of water (39.2F,4C)"):
			[(m,249.0826828),"inH20",''],
		_(u"meter of water (39.2F,4C)"):
			[(m,9806.4048337),"mH20",''],
		_(u"centimeter of water (39.2F,4C)"):
			[(m,98.0640483),"cmH20",''],
		_(u"millimeter of water (39.2F,4C)"):
			[(m,9.80640483),"mmH20",''],

		_(u"inches of mercury (60F,15.5C)"):
			[(m,3337.0),"inHg",''],
		_(u"millimeter of mercury (0C)"):
			[(m,133.322368421),"mmHg",''],
		_(u"inches of mercury (0C)"):
			[(m,133.322368421*25.4),"inHg",''],
		_(u"micrometer of mercury (0C)"):
			[(m,0.133322368421),u"\xb5mHg",''],
		_(u"centimeter of mercury (0C)"):
			[(m,1333.22368421),"cmHg",''],
		_(u"foot of mercury (0C)"):
			[(m,1333.22368421*25.4),"ftHg",''],
		_(u"torricelli"):
			[(m,133.322368421),"torr",_(u"Named after Italian physicist and mathematician Evangelista Torricelli, (1608-1647). A unit of pressure equal to 0.001316 atmosphere.")],
		_(u"micron"):
			[(m,133.322368421/1000),u"\xb5",_(u"Used in vacuum technology. Equal to 1 millitorr.")],
		_(u"millibar"):
			[(m,1.0e2),"mbar",''],
		_(u"pound force per square foot"):
			[(m,47.8802589803358),u"lbf/ft\xb2",''],
		_(u"tons (UK) per square foot"):
			[(m,47.8802589803358*2240),u"tons(UK)/ft\xb2",''],
		_(u"tons (US) per square foot"):
			[(m,47.8802589803358*2000),u"tons(US)/ft\xb2",''],
		_(u"kilogram force per square meter"):
			[(m,9.80665),u"kgf/m\xb2",''],
		_(u"kilogram force per square centimeter"):
			[(m,9.80665e4),u"kgf/cm\xb2",_(u"Used for ground pressure and steel stress.")],
		_(u"newton per square meter"):
			[(m,1.0),u"N/m\xb2",''],
		_(u"newton per square centimeter"):
			[(m,1.0e4),u"N/cm\xb2",''],
		_(u"newton per square millimeter"):
			[(m,1.0e6),u"N/mm\xb2",_(u"Used for concrete stress.")],
		_(u"kiloNewton per square meter"):
			[(m,1.0e3),u"kN/m\xb2",_(u"Used for ground pressure.")],
		_(u"kiloNewton per square centimeter"):
			[(m,1.0e7),u"kN/cm\xb2",_(u"Used for loads and concrete stress.")],
		_(u"microbar"):
			[(m,1.0e-1),u"\xb5bar",''],
		_(u"dyne per square centimeter"):
			[(m,1.0e-1),u"dyn/cm\xb2",''],
		_(u"barie | barye"):
			[(m,0.1),'',''],
		_(u"pieze"):
			[(m,1.0e3),'',_(u"From the Greek word piezein (to press). The pieze is a pressure of one sthene per square meter. 1000 newtons per square meter.")],
	},
	_(u"Prefixes and Suffixes"):{".base_unit":"one | mono",
		_(u"centillion (US)"):
			[(m,1.0e303),'',_(u"10^303. Note: British word centillion means 10^600 (too big for this program to represent as floating point).")],
		_(u"novemtrigintillion (US) | vigintillion (UK)"):
			[(m,1.0e120),'',_(u"10^120. ")],
		_(u"octotrigintillion (US)"):
			[(m,1.0e117),'',_(u"10^117. ")],
		_(u"septentrigintillion (US) | novemdecillion (UK)"):
			[(m,1.0e114),'',_(u"10^114. ")],
		_(u"sextrigintillion (US)"):
			[(m,1.0e111),'',_(u"10^111. ")],
		_(u"quintrigintillion (US) | octodecillion (UK)"):
			[(m,1.0e108),'',_(u"10^108. ")],
		_(u"quattuortrigintillion (US)"):
			[(m,1.0e105),'',_(u"10^105. ")],
		_(u"tretrigintillion (US) | septendecillion (UK)"):
			[(m,1.0e102),'',_(u"10^102. ")],
		_(u"googol"):
			[(m,1.0e100),'',_(u"10^100 Ten dotrigintillion (US). Note: a googolplex is 10^10^10^2.")],
		_(u"dotrigintillion (US)"):
			[(m,1.0e99),'',_(u"10^99. ")],
		_(u"untrigintillion (US) | sexdecillion (UK)"):
			[(m,1.0e96),'',_(u"10^96. ")],
		_(u"trigintillion (US)"):
			[(m,1.0e93),'',_(u"10^93. ")],
		_(u"novemvigintillion (US) | quindecillion (UK)"):
			[(m,1.0e90),'',_(u"10^90. ")],
		_(u"octovigintillion (US)"):
			[(m,1.0e87),'',_(u"10^87. ")],
		_(u"septenvigintillion (US) | quattuordecillion (UK)"):
			[(m,1.0e84),'',_(u"10^84. ")],
		_(u"sexvigintillion (US)"):
			[(m,1.0e81),'',_(u"10^81. ")],
		_(u"quinvigintillion (US) | tredecillion (UK)"):
			[(m,1.0e78),'',_(u"10^78. ")],
		_(u"quattuorvigintillion (US)"):
			[(m,1.0e75),'',_(u"10^75. ")],
		_(u"trevigintillion (US) | duodecillion (UK)"):
			[(m,1.0e72),'',_(u"10^72. ")],
		_(u"dovigintillion (US)"):
			[(m,1.0e69),'',_(u"10^69. ")],
		_(u"unvigintillion (US) | undecillion (UK"):
			[(m,1.0e66),'',_(u"10^66. ")],
		_(u"vigintillion (US)"):
			[(m,1.0e63),'',_(u"10^63. ")],
		_(u"novemdecillion (US) | decillion (UK)"):
			[(m,1.0e60),'',_(u"10^60. ")],
		_(u"octodecillion (US)"):
			[(m,1.0e57),'',_(u"10^57. ")],
		_(u"septendecillion (US) | nonillion (UK)"):
			[(m,1.0e54),'',_(u"10^54. ")],
		_(u"sexdecillion (US)"):
			[(m,1.0e51),'',_(u"10^51. ")],
		_(u"quindecillion (US) | octillion (UK)"):
			[(m,1.0e48),'',_(u"10^48. ")],
		_(u"quattuordecillion (US)"):
			[(m,1.0e45),'',_(u"10^45. ")],
		_(u"tredecillion (US) | septillion (UK)"):
			[(m,1.0e42),'',_(u"10^42. ")],
		_(u"duodecillion (US) | chici"):
			[(m,1.0e39),"Ch",_(u"10^39. chici coined by Morgan Burke after Marx brother Chico Marx.")],
		_(u"undecillion (US) | sextillion (UK) | gummi"):
			[(m,1.0e36),"Gm",_(u"10^36. gummi coined by Morgan Burke after Marx brother Gummo Marx.")],
		_(u"una | decillion (US) | zeppi"):
			[(m,1.0e33),"Zp",_(u"10^33. zeppi coined by Morgan Burke after Marx brother Zeppo Marx.")],
		_(u"dea | nonillion (US) | quintillion (UK) | grouchi"):
			[(m,1.0e30),"Gc",_(u"10^30. grouchi coined by Morgan Burke after Marx brother Groucho Marx.")],
		_(u"nea | octillion (US) | quadrilliard (UK) | harpi"):
			[(m,1.0e27),"Hr",_(u"10^27. harpi coined by Morgan Burke after Marx brother Harpo Marx.")],
		_(u"yotta | septillion (US) | quadrillion (UK)"):
			[(m,1.0e24),"Y",'10^24. Origin Latin penultimate letter y "iota".'],
		_(u"zetta | sextillion (US) | trilliard (UK)"):
			[(m,1.0e21),"Z",'10^21. Origin Latin ultimate letter z "zeta".'],
		_(u"exa | quintillion (US) | trillion (UK)"):
			[(m,1.0e18),"E",'10^18. Origin Greek for outside "exo" / Greek six hexa" as in 1000^6.'],
		_(u"peta | quadrillion (US) | billiard (UK)"):
			[(m,1.0e15),"P",'10^15. Origin Greek for spread "petalos" / Greek five "penta" as in 1000^5. Note: British use the words "1000 billion".'],
		_(u"tera | trillion (US) | billion (UK)"):
			[(m,1.0e12),"T",'10^12. Origin Greek for monster "teras" / Greek four "tetra" as in 1000^4. Note: British use the word billion.'],
		_(u"giga"):
			[(m,1.0e9),"G",'10^9. Origin Greek for giant "gigas".'],
		_(u"billion (US) | milliard (UK)"):
			[(m,1.0e9),'','10^9.'],
		_(u"mega | million"):
			[(m,1.0e6),"M",'10^6. One million times. Origin Greek for large, great "megas".'],
		_(u"hectokilo"):
			[(m,1.0e5),"hk",_(u"10^5. 100 thousand times")],
		_(u"myra | myria"):
			[(m,1.0e4),"ma",_(u"Ten thousand times, 10^4")],
		_(u"kilo | thousand"):
			[(m,1.0e3),"k",'One thousand times, 10^3.Origin Greek for thousand "chylioi".'],
		_(u"gross"):
			[(m,144.0),'',_(u"Twelve dozen.")],
		_(u"hecto | hundred"):
			[(m,1.0e2),'','One hundred times, 10^2.Origin Greek for hundred "hekaton".'],
		_(u"vic"):
			[(m,20.0),'',_(u"Twenty times.")],
		_(u"duodec"):
			[(m,12.0),'',_(u"Twelve times.")],
		_(u"dozen (bakers | long)"):
			[(m,13.0),'',_(u"Thirteen items. The cardinal number that is the sum of twelve and one syn:  thirteen, 13, XIII, long dozen.")],
		_(u"dozen"):
			[(m,12.0),'',_(u"Twelve items. Usually used to measure the quantity of eggs in a carton.")],
		_(u"undec"):
			[(m,11.0),'',_(u"Eleven times.")],
		_(u"deca | deka | ten"):
			[(m,1.0e1),'','10^1. Ten times. Origin Greek for ten "deka".'],
		_(u"sex | hexad"):
			[(m,6.0),'',_(u"Six times.")],
		_(u"quin"):
			[(m,5.0),'',_(u"Five times.")],
		_(u"quadr | quadri | quadruple"):
			[(m,4.0),'',_(u"Four times.")],
		_(u"thrice | tri | triple"):
			[(m,3.0),'',_(u"Three times.")],
		_(u"bi | double"):
			[(m,2.0),'',_(u"Two times.")],
		_(u"sesqui | sesqu"):
			[(m,1.5),'',_(u"One and one half times.")],
		_(u"one | mono"):
			[(m,1.0),'',_(u"Single unit value.")],
		_(u"quarter"):
			[(m,0.25),'',_(u"One fourth.")],
		_(u"demi | semi | half"):
			[(m,0.5),'',_(u"One half.")],
		_(u"eigth"):
			[(m,0.125),'',_(u"One eigth.")],
		_(u"deci"):
			[(m,1.0e-1),"d",'10^-1. Origin Latin tenth "decimus".'],
		_(u"centi"):
			[(m,1.0e-2),"c",'10^-2. Origin Latin hundred, hundredth "centum".'],
		_(u"percent"):
			[(m,1.0e-2),"%",_(u"10^-2. A proportion multiplied by 100")],
		_(u"milli"):
			[(m,1.0e-3),"m",'10^-3. A prefix denoting a thousandth part of; as, millimeter, milligram, milliampere.Origin Latin thousand "mille".'],
		_(u"decimilli"):
			[(m,1.0e-4),"dm",_(u"10^-4")],
		_(u"centimilli"):
			[(m,1.0e-5),"cm",_(u"10^-5. ")],
		_(u"micro"):
			[(m,1.0e-6),u"\xb5",'10^-6. A millionth part of; as, microfarad, microohm, micrometer.Origin Latin small "mikros".'],
		_(u"parts per million | ppm"):
			[(m,1.0e-6),"ppm",_(u"10^-6. Parts per million usually used in measuring chemical concentrations.")],
		_(u"nano"):
			[(m,1.0e-9),"n",'10^-9. Origin Greek dwarf "nanos".'],
		_(u"pico"):
			[(m,1.0e-12),"p",'10^-12. Origin Italian tiny "piccolo".'],
		_(u"femto"):
			[(m,1.0e-15),"f",'10^-15. Origin Old Norse fifteen "femten" as in 10^-15.'],
		_(u"atto"):
			[(m,1.0e-18),"a",'10^-18. Origin Old Norse eighteen "atten" as in 10^-18.'],
		_(u"zepto | ento"):
			[(m,1.0e-21),"z",'10^-21. zepto origin Latin ultimate letter z "zeta".'],
		_(u"yocto | fito"):
			[(m,1.0e-24),"y",'10^-24. yocto origin Latin penultimate letter y "iota".'],
		_(u"syto | harpo"):
			[(m,1.0e-27),"hr",_(u"10^-27. harpo coined by Morgan Burke after Marx brother Harpo Marx.")],
		_(u"tredo | groucho"):
			[(m,1.0e-30),"gc",_(u"10^-30. groucho coined by Morgan Burke after Marx brother Groucho Marx.")],
		_(u"revo | zeppo"):
			[(m,1.0e-33),"zp",_(u"10^-33. zeppo coined by Morgan Burke after Marx brother Zeppo Marx.")],
		_(u"gummo"):
			[(m,1.0e-36),"gm",_(u"10^-36. Coined by Morgan Burke after Marx brother Gummo Marx.")],
		_(u"chico"):
			[(m,1.0e-39),"ch",_(u"10^-39. Coined by Morgan Burke after Marx brother Chico Marx.")],
	},
	#There does not seem to be a "standard" for shoe sizes so some are left out for now until a decent reference can be found.
	_(u"Shoe Size"):{".base_unit":"centimeter",
		_(u"centimeter"):
			[(m,1.0),"cm",_(u"The hundredth part of a meter; a measure of length equal to rather more than thirty-nine hundredths (0.3937) of an inch.")],
		_(u"inch"):
			[(m,(2.54)),"in",_(u"The twelfth part of a foot, commonly subdivided into halves, quarters, eights, sixteenths, etc., as among mechanics. It was also formerly divided into twelve parts, called lines, and originally into three parts, called barleycorns, its length supposed to have been determined from three grains of barley placed end to end lengthwise.")],
		#"European"):
		#	[(slo,((35,47),(22.5,30.5))),'',_(u"Used by Birkenstock")],
		_(u"Mens (US)"):
			[(slo,((6.0,13.0),((2.54*(9+1.0/3)),(2.54*(11+2.0/3))))),'','Starting at 9 1/3" for size 6 and moving up by 1/6" for each half size to 11 2/3" for size 13. Beware that some manufacturers use different measurement techniques.'],
		_(u"Womens (US)"):
			[(gof,(2.54*((2.0+2.0/6)/7.0),2.54*(8.5-(5.0*((2.0+2.0/6)/7.0))))),'','Starting at 8 1/2" for size 5 and moving up by 1/6" for each half size to 10 5/6" for size 12. Beware that some manufacturers use different measurement techniques.'],
		_(u"Childrens (US)"):
			[(dso,((5.5,13.5),((2.54*(4.0+5.0/6)),(2.54*7.5)),(1.0,5.0),(2.54*(7.0+2.0/3),2.54*9.0))),'','Starting at 4 5/6" for size 5 1/2 up to 7 1/3" for size 13 then 7 2/3" for size 1 and going up to 9" for size 5.'],
		_(u"Mens (UK)"):
			[(slo,((5.0,12.0),((2.54*(9+1.0/3)),(2.54*(11+2.0/3))))),'','Starting at 9 1/3" for size 5 and moving up by 1/6" for each half size to 11 2/3" for size 12. Beware that some manufacturers use different measurement techniques.'],
		_(u"Womens (UK)"):
			[(gof,(2.54*((2.0+2.0/6)/7.0),2.54*(8.5-(3.0*((2.0+2.0/6)/7.0))))),'','Starting at 8 1/2" for size 3 and moving up by 1/6" for each half size to 10 5/6" for size 10. Beware that some manufacturers use different measurement techniques.'],
		#"Asian"):
		#	[(slo,((23.5,31.5),(25.0,30.5))),'',''],
	},
	_(u"Speed | Velocity"):{".base_unit":"meter per second",
		_(u"meter per second"):
			[(m,1.0),"m/s",''],
		_(u"speed of light | warp"):
			[(m,299792458.0),"c",_(u"The speed at which light travels in a vacuum; about 300,000 km per second; a universal constant.")],
		_(u"miles per second"):
			[(m,1609.344),"mi/s",''],
		_(u"kilometer per second"):
			[(m,1.0e3),"km/s",''],
		_(u"millimeter per second"):
			[(m,1.0e-3),"mm/s",''],
		_(u"knot"):
			[(m,0.514444444444444),'',_(u"Nautical measurement for speed as one nautical mile per hour. The number of knots which run off from the reel in half a minute, therefore, shows the number of miles the vessel sails in an hour.")],
		_(u"miles per hour"):
			[(m,0.44704),"mi/h",''],
		_(u"foot per second"):
			[(m,0.3048),"ft/s",''],
		_(u"foot per minute"):
			[(m,0.00508),"ft/min",''],
		_(u"kilometer per hour"):
			[(m,0.277777777777778),"km/h",''],
		_(u"mile per day"):
			[(m,1.86266666666667E-02),"mi/day",''],
		_(u"centimeter per second"):
			[(m,1.0e-2),"cm/s",''],
		_(u"knot (admiralty)"):
			[(m,0.514773333333333),'',''],
		_(u"mach (sea level & 32 degF)"):
			[(m,331.46),'',''],
	},
	_(u"Temperature"):{".base_unit":_(u"kelvin"),
		_(u"kelvin"):
			[(m,1.0),"K",_(u"Named after the English mathematician and physicist William Thomson Kelvin (1824-1907). The basic unit of thermodynamic temperature adopted under the System International d'Unites.")],
		_(u"celsius (absolute)"):
			[(m,1.0),u"\xb0C absolute",''],
		_(u"celsius (formerly centigrade)"):
			[(ofg,(273.15,1.0)),u"\xb0C",_(u"Named after the Swedish astronomer and physicist Anders Celsius (1701-1744). The Celsius thermometer or scale. It is the same as the centigrade thermometer or scale. 0\xb0 marks the freezing point of water and 100\xb0 marks the boiling point of water.  ")],
		_(u"fahrenheit"):
			[(f,('((x-32.0)/1.8)+273.15','((x-273.15)*1.8)+32.0')),u"\xb0F",_(u"Named after the German physicist Gabriel Daniel Fahrenheit (1686-1736). The Fahrenheit thermometer is so graduated that the freezing point of water is at 32\xb0 above the zero of its scale, and the boiling point at 212\xb0 above. It is commonly used in the United States and in England.")],

		_(u"reaumur"):
			[(gof,(1.25,273.15)),u"\xb0Re",_(u"Named after the French scientist Ren\u00E9-Antoine Ferchault de R\u00E9aumur (1683-1757). Conformed to the scale adopted by R\u00E9aumur in graduating the thermometer he invented. The R\u00E9aumur thermometer is so graduated that 0\xb0 marks the freezing point and 80\xb0 the boiling point of water.")],
		_(u"fahrenheit (absolute)"):
			[(m,1/1.8),u"\xb0F absolute",''],
		_(u"rankine"):
			[(m,1/1.8),u"\xb0R",_(u"Named after the British physicist and engineer William Rankine (1820-1872). An absolute temperature scale in Fahrenheit degrees.")],
	},

	_(u"Temperature Difference"):{".base_unit":"temp. diff. in kelvin",
		_(u"temp. diff. in kelvin"):
			[(m,1.0),"K",''],
		_(u"temp. diff. in degrees Celsius"):
			[(m,1.0),u"\xb0C",''],
		_(u"temp. diff. in degrees Reaumur"):
			[(m,1.25),u"\xb0Re",''],
		_(u"temp. diff. in degrees Rankine"):
			[(m,5.0/9),u"\xb0R",''],
		_(u"temp. diff. in degrees Fahrenheit"):
			[(m,5.0/9),u"\xb0F",''],
	},
	_(u"Time"):{".base_unit":"second",
		_(u"year"):
			[(m,365*86400.0),"a",_(u"The time of the apparent revolution of the sun trough the ecliptic; the period occupied by the earth in making its revolution around the sun, called the astronomical year; also, a period more or less nearly agreeing with this, adopted by various nations as a measure of time, and called the civil year; as, the common lunar year of 354 days, still in use among the Mohammedans; the year of 360 days, etc. In common usage, the year consists of 365 days, and every fourth year (called bissextile, or leap year) of 366 days, a day being added to February on that year, on account of the excess above 365 days")],
		_(u"year (anomalistic)"):
			[(m,365*86400.0+22428.0),'',_(u"The time of the earth's revolution from perihelion to perihelion again, which is 365 days, 6 hours, 13 minutes, and 48 seconds.")],
		_(u"year (common lunar)"):
			[(m,354*86400.0),'',_(u"The period of 12 lunar months, or 354 days.")],
		_(u"year (embolismic | Intercalary lunar)"):
			[(m,384*86400.0),'',_(u"The period of 13 lunar months, or 384 days.")],
		_(u"year (leap | bissextile)"):
			[(m,366*86400.0),'',_(u"Bissextile; a year containing 366 days; every fourth year which leaps over a day more than a common year, giving to February twenty-nine days. Note: Every year whose number is divisible by four without a remainder is a leap year, excepting the full centuries, which, to be leap years, must be divisible by 400 without a remainder. If not so divisible they are common years. 1900, therefore, is not a leap year.")],
		_(u"year (sabbatical)"):
			[(m,7*365*86400.0),'',_(u"Every seventh year, in which the Israelites were commanded to suffer their fields and vineyards to rest, or lie without tillage.")],
		_(u"year (lunar astronomical)"):
			[(m,354*86400.0+31716.0),'',_(u"The period of 12 lunar synodical months, or 354 days, 8 hours, 48 minutes, 36 seconds.")],
		_(u"year (lunisolar)"):
			[(m,532*365*86400.0),'',_(u"A period of time, at the end of which, in the Julian calendar, the new and full moons and the eclipses recur on the same days of the week and month and year as in the previous period. It consists of 532 common years, being the least common multiple of the numbers of years in the cycle of the sun and the cycle of the moon.")],
		_(u"year (sidereal)"):
			[(m,365*86400.0+22149.3),'',_(u"The time in which the sun, departing from any fixed star, returns to the same. This is 365 days, 6 hours, 9 minutes, and 9.3 seconds.")],
		_(u"year (sothic)"):
			[(m,365*86400.0+6*3600.0),'',_(u"The Egyptian year of 365 days and 6 hours, as distinguished from the Egyptian vague year, which contained 365 days. The Sothic period consists of 1,460 Sothic years, being equal to 1,461 vague years. One of these periods ended in July, a.d. 139.")],
		_(u"year (tropic)"):
			[(m,365*86400.0+20926.0),'',_(u"The solar year; the period occupied by the sun in passing from one tropic or one equinox to the same again, having a mean length of 365 days, 5 hours, 48 minutes, 46.0 seconds, which is 20 minutes, 23.3 seconds shorter than the sidereal year, on account of the precession of the equinoxes.")],
		_(u"month"):
			[(m,365*86400.0/12),'',_(u"One of the twelve portions into which the year is divided; the twelfth part of a year, corresponding nearly to the length of a synodic revolution of the moon, -- whence the name. In popular use, a period of four weeks is often called a month.")],
		_(u"month (sidereal)"):
			[(m,27.322*86400.0),'',_(u"Period between successive conjunctions with a star, 27.322 days")],
		_(u"month (synodic | lunar month | lunation)"):
			[(m,29.53059*86400.0),'',_(u"The period between successive new moons (29.53059 days) syn: lunar month, moon, lunation")],
		_(u"day"):
			[(m,86400.0),"d",_(u"The period of the earth's revolution on its axis. -- ordinarily divided into twenty-four hours. It is measured by the interval between two successive transits of a celestial body over the same meridian, and takes a specific name from that of the body. Thus, if this is the sun, the day (the interval between two successive transits of the sun's center over the same meridian) is called a solar day; if it is a star, a sidereal day; if it is the moon, a lunar day.")],
		_(u"day (sidereal)"):
			[(m,86164.09),'',_(u"The interval between two successive transits of the first point of Aries over the same meridian. The Sidereal day is 23 h. 56 m. 4.09 s. of mean solar time.")],
		_(u"day (lunar | tidal)"):
			[(m,86400.0+50*60.0),'',_(u"24 hours 50 minutes used in tidal predictions. ")],
		_(u"hour"):
			[(m,3600.0),"h",_(u"The twenty-fourth part of a day; sixty minutes.")],
		_(u"minute"):
			[(m,60.0),"min",_(u"The sixtieth part of an hour; sixty seconds.")],
		_(u"second"):
			[(m,1.0),"s",_(u"The sixtieth part of a minute of time.")],
		_(u"millisecond"):
			[(m,1.0e-3),"ms",_(u"One thousandth of a second.")],
		_(u"microsecond"):
			[(m,1.0e-6),u"\xb5s",_(u"One millionth of a second.")],
		_(u"nanosecond"):
			[(m,1.0e-9),"ns",''],
		_(u"picosecond"):
			[(m,1.0e-12),"ps",''],
		_(u"millennium"):
			[(m,1000*365*86400.0),'',_(u"A thousand years; especially, the thousand years mentioned in the twentieth chapter in the twentieth chapter of Revelation, during which holiness is to be triumphant throughout the world. Some believe that, during this period, Christ will reign on earth in person with his saints.")],
		_(u"century"):
			[(m,100*365*86400.0),'',_(u"A period of a hundred years; as, this event took place over two centuries ago. Note: Century, in the reckoning of time, although often used in a general way of any series of hundred consecutive years (as, a century of temperance work), usually signifies a division of the Christian era, consisting of a period of one hundred years ending with the hundredth year from which it is named; as, the first century (a. d. 1-100 inclusive); the seventh century (a.d. 601-700); the eighteenth century (a.d. 1701-1800). With words or phrases connecting it with some other system of chronology it is used of similar division of those eras; as, the first century of Rome (A.U.C. 1-100).")],
		_(u"decade"):
			[(m,10*365*86400.0),'',_(u"A group or division of ten; esp., a period of ten years; a decennium; as, a decade of years or days; a decade of soldiers; the second decade of Livy.")],
		_(u"week"):
			[(m,7*86400.0),'',_(u"A period of seven days, usually that reckoned from one Sabbath or Sunday to the next. Also seven nights, known as sennight.")],
		_(u"fortnight"):
			[(m,14*86400.0),'',_(u"Fourteen nights, our ancestors reckoning time by nights and winters.  The space of fourteen days; two weeks.")],
		_(u"novennial"):
			[(m,9*365*86400.0),'',_(u"Done or recurring every ninth year.")],
		_(u"octennial"):
			[(m,8*365*86400.0),'',_(u"Happening every eighth year; also, lasting a period of eight years.")],
		_(u"olympiad"):
			[(m,4*365*86400.0),'',_(u"A period of four years, by which the ancient Greeks reckoned time, being the interval from one celebration of the Olympic games to another, beginning with the victory of Coroebus in the foot race, which took place in the year 776 b.c.; as, the era of the olympiads.")],
		_(u"pregnancy"):
			[(m,9*365*86400.0/12),'',_(u"The condition of being pregnant; the state of being with young. A period of approximately 9 months for humans")],
		_(u"quindecennial"):
			[(m,15*365*86400.0),'',_(u"A period of 15 years.")],
		_(u"quinquennial"):
			[(m,5*365*86400.0),'',_(u"Occurring once in five years, or at the end of every five years; also, lasting five years. A quinquennial event.")],
		_(u"septennial"):
			[(m,7*365*86400.0),'',_(u"Lasting or continuing seven years; as, septennial parliaments.")],
		_(u"cesium vibrations"):
			[(m,1.0/9192631770.0),"vibrations",_(u"It takes one second for hot cesium atoms to vibrate 9,192,631,770 times (microwaves). This standard was adopted by the International System in 1967.")],
	},
	_(u"Viscosity (Dynamic)"):{".base_unit":"pascal-second",
		_(u"pascal-second"):
			[(m,1.0),u"Pa\xb7s",''],
		_(u"reyn"):
			[(m,6894.75729316836),'',''],
		_(u"poise"):
			[(m,0.1),"P",''],
		_(u"microreyn"):
			[(m,6894.75729316836e-6),'',''],
		_(u"millipascal-second"):
			[(m,1.0e-3),u"mPa\xb7s",''],
		_(u"centipoise"):
			[(m,1.0e-3),"cP",''],
		_(u"micropascal-second"):
			[(m,1.0e-6),u"\xb5Pa\xb7s",''],
	},
	_(u"Viscosity (Kinematic)"):{".base_unit":"square meter per second",
		_(u"square meter per second"):
			[(m,1.0),u"m\xb2/s",''],
		_(u"square millimeter per second"):
			[(m,1.0e-6),u"mm\xb2/s",''],
		_(u"square foot per second"):
			[(m,0.09290304),u"ft\xb2/s",''],
		_(u"square centimetre per second"):
			[(m,1.0e-4),u"cm\xb2/s",''],
		_(u"stokes"):
			[(m,1.0e-4),"St",''],
		_(u"centistokes"):
			[(m,1.0e-6),"cSt",''],
	},
	_(u"Volume and Liquid Capacity"):{".base_unit":"millilitre",
		_(u"can #10 can"):
			[(m,4*2*2*8*2*3*4.92892159375/128*109.43),'',_(u"Taken from the Can Manufacturers Institute (CMI).  http://www.cancentral.com/standard.cfm#foodcan")],
		_(u"can #2 can"):
			[(m,4*2*2*8*2*3*4.92892159375/128*20.55),'',_(u"Taken from the Can Manufacturers Institute (CMI).  http://www.cancentral.com/standard.cfm#foodcan")],
		_(u"can #2.5 can"):
			[(m,4*2*2*8*2*3*4.92892159375/128*29.79),'',_(u"Taken from the Can Manufacturers Institute (CMI).  http://www.cancentral.com/standard.cfm#foodcan")],
		_(u"can #5 can"):
			[(m,4*2*2*8*2*3*4.92892159375/128*59.1),'',_(u"Taken from the Can Manufacturers Institute (CMI).  http://www.cancentral.com/standard.cfm#foodcan")],
		_(u"can #1 can (Picnic)"):
			[(m,4*2*2*8*2*3*4.92892159375/128*10.94),'',_(u"Taken from the Can Manufacturers Institute (CMI).  http://www.cancentral.com/standard.cfm#foodcan")],
		_(u"can #1 can (Tall)"):
			[(m,4*2*2*8*2*3*4.92892159375/128* 16.70),'',_(u"Taken from the Can Manufacturers Institute (CMI).  http://www.cancentral.com/standard.cfm#foodcan")],
		_(u"can #303 can"):
			[(m,4*2*2*8*2*3*4.92892159375/128* 16.88),'',_(u"Taken from the Can Manufacturers Institute (CMI) http://www.cancentral.com/standard.cfm#foodcan .")],
		_(u"barrel (wine UK)"):
			[(m,31.5*4*2*2.5*8*2*3*4.73551071041125),'',_(u"31.5 UK Gallons")],
		_(u"barrel (UK)"):
			[(m,36*4*2*2.5*8*2*3*4.73551071041125),'',_(u"36 UK Gallons")],
		_(u"barrel of oil (US)"):
			[(m,42*4*2*2*8*2*3*4.92892159375),"",_(u"Barrel of petroleum (oil), 42 US Gallons")],
		_(u"barrel (US federal)"):
			[(m,31*4*2*2*8*2*3*4.92892159375),"",_(u"31 US Gallons")],
		_(u"barrel (US)"):
			[(m,31.5*4*2*2*8*2*3*4.92892159375),"",_(u"31.5 US Gallons")],
		_(u"caphite"):
			[(m,1374.1046),'',_(u"Ancient Arabian")],
		_(u"cantaro"):
			[(m,13521.1108),'',_(u"Spanish")],
		_(u"oxybaphon"):
			[(m,66.245),'',_(u"Greek")],
		_(u"cotula | hemina | kotyle"):
			[(m,308.3505),'',_(u"Greek")],
		_(u"cyathos"):
			[(m,451.5132),'',_(u"Greek")],
		_(u"cados"):
			[(m,38043.3566),'',_(u"Greek")],
		_(u"metertes | amphura"):
			[(m,39001.092),'',_(u"Greek")],
		_(u"mushti"):
			[(m,60.9653),'',_(u"Indian")],
		_(u"cab"):
			[(m,2202.5036),'',_(u"Israeli")],
		_(u"hekat"):
			[(m,4768.6752),'',_(u"Israeli")],
		_(u"bath | bu"):
			[(m,36871.2),'',_(u"Israeli")],
		_(u"acetabulum"):
			[(m,66.0752),'',_('Roman')],

		_(u"dash (UK)"):
			[(m,4.73551071041125/16),'',_(u"one half of a pinch")],
		_(u"pinch (UK)"):
			[(m,4.73551071041125/8),'',_(u"One eigth of a teaspoon")],
		_(u"gallon (UK)"):
			[(m,4*2*2.5*8*2*3*4.73551071041125),'',_(u"A measure of capacity, containing four quarts; -- used, for the most part, in liquid measure, but sometimes in dry measure. The English imperial gallon contains 10 pounds avoirdupois of distilled water at 62\xb0F, and barometer at 30 inches, equal to 277.274 cubic inches.")],
		_(u"quart (UK)"):
			[(m,2*2.5*8*2*3*4.73551071041125),'',_(u"The fourth part of a gallon; the eighth part of a peck; two pints. Note: In imperial measure, a quart is forty English fluid ounces; in wine measure, it is thirty-two American fluid ounces. The United States dry quart contains 67.20 cubic inches, the fluid quart 57.75. The English quart contains 69.32 cubic inches.")],
		_(u"pint (UK)"):
			[(m,2.5*8*2*3*4.73551071041125),'',''],
		_(u"cup (UK)"):
			[(m,8*2*3*4.73551071041125),'',''],
		_(u"ounce - fluid ounce (UK)"):
			[(m,2*3*4.73551071041125),'',_(u"Contains 1 ounce mass of distilled water at 62\xb0F, and barometer at 30 inches")],
		_(u"tablespoon (UK)"):
			[(m,3*4.73551071041125),'',_(u"One sixteenth of a cup. A spoon of the largest size commonly used at the table; -- distinguished from teaspoon, dessert spoon, etc.")],
		_(u"teaspoon (UK)"):
			[(m,4.73551071041125),'',_(u"One third of a tablespoon. A small spoon used in stirring and sipping tea, coffee, etc., and for other purposes.")],

		_(u"dash (US)"):
			[(m,4.92892159375/16),'',_(u"one half of a pinch")],
		_(u"pinch (US)"):
			[(m,4.92892159375/8),'',_(u"One eigth of a teaspoon")],
		_(u"keg (beer US)"):
			[(m,15.5*768*4.92892159375),"","""US standard size beer keg = 1/2 barrel = 15.5 US gallons; weighs approx. 29.7 pounds empty, 160.5 pounds full."""],
		_(u"keg (wine US)"):
			[(m,12*768*4.92892159375),"","""12 US gallons."""],
		_(u"ponykeg (US)"):
			[(m,7.75*768*4.92892159375),"","""1/2 US beerkeg, 7.75 US gallons."""],
		_(u"barrel (beer US)"):
			[(m,31*768*4.92892159375),"","""Two US beerkegs, 31 US gallons."""],
		_(u"barrel (wine US)"):
			[(m,31.5*768*4.92892159375),"","""31.5 US gallons."""],
		_(u"hogshead (US)"):
			[(m,63*768*4.92892159375),"","""Equal to 2 barrels or 63 US gallons."""],	
		_(u"fifth (US)"):
			[(m,.2*768*4.92892159375),"","""One fifth of a gallon."""],
		_(u"jigger"):
			[(m,9*4.92892159375),"","""1.5 fluid ounces (US)"""],
		_(u"shot"):
			[(m,9*4.92892159375),"","""1.5 fluid ounces (US)"""],
		_(u"winebottle"):
			[(m,750*1.0),"","""750 milliliters"""],
		_(u"wineglass (US)"):
			[(m,24*4.92892159375),"","""Equal to 4 fluid ounces (US)."""],
		_(u"winesplit"):
			[(m,750.0/4),"","""1/4 winebottle"""],
		_(u"magnum"):
			[(m,1500),"","""1.5 liters"""],
		_(u"gallon (US)"):
			[(m,4*2*2*8*2*3*4.92892159375),'',_(u"A measure of capacity, containing four quarts; -- used, for the most part, in liquid measure, but sometimes in dry measure. Note: The standard gallon of the Unites States contains 231 cubic inches, or 8.3389 pounds avoirdupois of distilled water at its maximum density, and with the barometer at 30 inches. This is almost exactly equivalent to a cylinder of seven inches in diameter and six inches in height, and is the same as the old English wine gallon. The beer gallon, now little used in the United States, contains 282 cubic inches.")],
		_(u"quart (US)"):
			[(m,2*2*8*2*3*4.92892159375),'',_(u"The fourth part of a gallon; the eighth part of a peck; two pints. Note: In imperial measure, a quart is forty English fluid ounces; in wine measure, it is thirty-two American fluid ounces. The United States dry quart contains 67.20 cubic inches, the fluid quart 57.75. The English quart contains 69.32 cubic inches.")],
		_(u"pint (US)"):
			[(m,2*8*2*3*4.92892159375),'',''],
		_(u"cup (US)"):
			[(m,8*2*3*4.92892159375),'',''],
		_(u"ounce - fluid ounce (US)"):
			[(m,2*3*4.92892159375),'',''],
		_(u"beerbottle (US 12 ounce)"):
			[(m,12*2*3*4.92892159375),'',''],
		_(u"tablespoon (US)"):
			[(m,3*4.92892159375),'',_(u"One sixteenth of a cup. A spoon of the largest size commonly used at the table; -- distinguished from teaspoon, dessert spoon, etc.")],
		_(u"teaspoon (US)"):
			[(m,4.92892159375),'',_(u"One third of a tablespoon. A small spoon used in stirring and sipping tea, coffee, etc., and for other purposes.")],

		_(u"shaku"):
			[(m,18.04),'',_(u"A Japanese unit of volume, the shaku equals about 18.04 milliliters (0.61 U.S. fluid ounce). Note: shaku also means area and length.")],

		_(u"cubic yard"):
			[(m,27*1728*16.387064),u"yd\xb3",''],
		_(u"acre foot"):
			[(m,1728*16.387064*43560),'',''],
		_(u"cubic foot"):
			[(m,1728*16.387064),u"ft\xb3",''],
		_(u"cubic inch"):
			[(m,16.387064),u"in\xb3",''],

		_(u"cubic meter"):
			[(m,1.0e6),u"m\xb3",''],
		_(u"cubic decimeter"):
			[(m,1.0e3),u"dm\xb3",''],
		_(u"litre"):
			[(m,1.0e3),"l",_(u"A measure of capacity in the metric system, being a cubic decimeter.")],
		_(u"cubic centimeter"):
			[(m,1.0),u"cm\xb3",''],
		_(u"millilitre"):
			[(m,1.0),"ml",''],
		_(u"centilitre"):
			[(m,10*1.0),"cl",''],
		_(u"decilitre"):
			[(m,10*10*1.0),"dl",''],
		_(u"mil"):
			[(m,1.0),'',_(u"Equal to one thousandth of a liter syn: milliliter, millilitre, ml, cubic centimeter, cubic centimeter, cc")],
		_(u"minim"):
			[(m,2*3*4.92892159375/480),'',_(u"Used in Pharmaceutical to represent one drop. 1/60 fluid dram or 1/480 fluid ounce. A U.S. minim is about 0.003760 in\xb3 or 61.610 \xb5l. The British minim is about 0.003612 in\xb3 or 59.194 \xb5l. Origin of the word is from the Latin minimus, or small.")],
	},
	_(u"Volume and Dry Capacity"):{".base_unit":"cubic meter",
		_(u"cubic meter"):
			[(m,1.0),u"m\xb3",''],
		_(u"cubic decimeter"):
			[(m,1.0e-3),u"dm\xb3",''],
		_(u"cubic millimeter"):
			[(m,1.0e-9),u"mm\xb3",""""""],
		_(u"cubic centimeter"):
			[(m,1.0e-6),u"cm\xb3",""""""],
		_(u"cord"):
			[(m,3.624556363776),'',_(u"A pile of wood 8ft x 4ft x 4ft.")],
		_(u"cubic yard"):
			[(m,0.764554857984),u"yd\xb3",''],
		_(u"bushel (US)"):
			[(m,4*2*0.00440488377086),"bu",_(u"A dry measure, containing four pecks, eight gallons, or thirty-two quarts. Note: The Winchester bushel, formerly used in England, contained 2150.42 cubic inches, being the volume of a cylinder 181/2 inches in internal diameter and eight inches in depth. The standard bushel measures, prepared by the United States Government and distributed to the States, hold each 77.6274 pounds of distilled water, at 39.8deg Fahr. and 30 inches atmospheric pressure, being the equivalent of the Winchester bushel. The imperial bushel now in use in England is larger than the Winchester bushel, containing 2218.2 cubic inches, or 80 pounds of water at 62deg Fahr.")],
		_(u"bushel (UK | CAN)"):
			[(m,4*2*4*1.1365225e-3),"bu",_(u"A dry measure, containing four pecks, eight gallons, or thirty-two quarts. Note: The Winchester bushel, formerly used in England, contained 2150.42 cubic inches, being the volume of a cylinder 181/2 inches in internal diameter and eight inches in depth. The standard bushel measures, prepared by the United States Government and distributed to the States, hold each 77.6274 pounds of distilled water, at 39.8deg Fahr. and 30 inches atmospheric pressure, being the equivalent of the Winchester bushel. The imperial bushel now in use in England is larger than the Winchester bushel, containing 2218.2 cubic inches, or 80 pounds of water at 62deg Fahr.")],
		_(u"peck (US)"):
			[(m,2*0.00440488377086),'',''],
		_(u"peck (UK | CAN)"):
			[(m,2*4*1.1365225e-3),'',''],
		_(u"gallon (US dry)"):
			[(m,0.00440488377086),"gal",''],
		_(u"gallon (CAN)"):
			[(m,4*1.1365225e-3),"gal",''],
		_(u"quart (US dry)"):
			[(m,1.101220942715e-3),"qt",''],
		_(u"quart (CAN)"):
			[(m,1.1365225e-3),"qt",''],
		_(u"cubic foot"):
			[(m,0.028316846592),u"ft\xb3",''],
		_(u"board foot"):
			[(m,0.028316846592/12),'',_(u"lumber 1ft\xb2 and 1 in thick")],
		_(u"litre"):
			[(m,1.0e-3),"l",_(u"A measure of capacity in the metric system, being a cubic decimeter.")],
		_(u"pint (US dry)"):
			[(m,5.506104713575E-04),"pt",''],
		_(u"cubic inch"):
			[(m,0.000016387064),u"in\xb3",''],
		_(u"coomb"):
			[(m,4*4*2*4*1.1365225e-3),'',_(u"British. 4 bushels")],
		_(u"peck"):
			[(m,37.23670995671),'',_(u"The fourth part of a bushel; a dry measure of eight quarts")],
		_(u"quart (dry)"):
			[(m,4.65458874458874),'',_(u"The fourth part of a gallon; the eighth part of a peck; two pints. Note: In imperial measure, a quart is forty English fluid ounces; in wine measure, it is thirty-two American fluid ounces. The United States dry quart contains 67.20 cubic inches, the fluid quart 57.75. The English quart contains 69.32 cubic inches.")],
	},
	_(u"Thermal conductance (Area)"):{".base_unit":"Watts per square meter Kelvin",
		_(u"watts per square meter Kelvin"):
			[(m,1.0),u"W/m\xb2\xb7K",''],
		_(u"watts per square meter deg C"):
			[(m,1.0),u"W/h.m\xb2\xb7\xb0C",''],
		_(u"kilocalories per hour square meter deg C"):
			[(m,1.163),u"kcal/h\xb7m\xb7\xb0C",''],
		_(u"british thermal units per second square foot deg F"):
			[(m,2.0428),u"Btu/sec\xb7ft\xb2\xb7\xb0F",''],
		_(u"british thermal units per hour square foot deg F"):
			[(m,5.6782),u"Btu/h\xb7ft\xb2\xb7\xb0F",''],
	},
	_(u"Thermal conductance (Linear)"):{".base_unit":"cubic meter",
		_(u"watts per meter Kelvin"):
			[(m,1.0),u"W/m\xb7K",''],
		_(u"watts per meter deg C"):
			[(m,1.0),u"W/m\xb7\xb0C",''],
		_(u"kilocalories per hour meter deg C"):
			[(m,1.163),u"kcal/h\xb7m\xb7\xb0C",''],
		_(u"british thermal units per second foot deg F"):
			[(m,1.703),u"Btu/sec\xb7ft\xb7\xb0F",''],
	},
	_(u"Thermal resistance"):{".base_unit":_(u"square meter kelvin per watt"),
		_(u"square meter kelvin per watt"):
			[(m,1.0),u"m\xb2\xb7K/W",''],
		_(u"square meter deg C per watt"):
			[(m,1.0),u"m\xb2\xb7\xb0C/W",''],
		_(u"clo"):
			[(m,1.50e-1),u"clo",_(u"Clo is the unit for effective clothing insulation. It is used to evaluate the expected comfort of users in certain humidity, temperature and workload conditions (and estimate air conditioning or heating loads, for instance.).")],
		_(u"hour square foot deg F per BTU"):
			[(m,1.761e-1),u"h\xb7ft\xb2\xb7\xb0F/Btu",''],
		_(u"hour square meter deg C per kilocalorie"):
			[(m,8.62e-1),u"h\xb7m\xb2\xb7\xb0C/kcal",''],
	},
	_(u"Specific Heat"):{".base_unit":"joule per kilogram kelvin",
		_(u"joule per kilogram kelvin"):
			[(m,1.0),u"J/kg\xb7K",''],
		_(u"joule per kilogram deg C"):
			[(m,1.0),u"J/kg\xb7\xb0C",''],
		_(u"kilocalories per kilogram deg C"):
			[(m,4.18855e3),u"kcal/kg\xb7\xb0C",''],
		_(u"btu per pound deg F"):
			[(m,4.1868e3),u"BTU/lb\xb7\xb0F",''],
	},
	_(u"Fuel consumption"):{".base_unit":"miles per gallon (US)",
		_(u"miles per gallon (US)"):
			[(m,1.0),u"mpg (US)",''],
		_(u"gallons  (US) per 100 miles"):
			[(inv,100.0),u'',''],
		_(u"miles per gallon (Imperial)"):
			[(m,1.0/1.20095),u"mpg (Imperial)",''],
		_(u"gallons (Imperial) per 100 miles"):
			[(inv,100.0/1.20095),u'',''],
		_(u"liters per 100 kilometer"):
			[(inv,62.1371192237/0.264172052358),u'',''],
		_(u"kilometers per liter"):
			[(m,.621371192237/0.264172052358),u'',''],
	},
	_(u"Torque"):{".base_unit":"newton meter",
		_(u"newton meter"):
			[(m,1.0),u"N\xb7m",_(u"The SI unit of force that causes rotation.")],
		_(u"joules"):
			[(m,1.0),u"j",''],
		_(u"kilo newton meter"):
			[(m,1000.0),u"kN\xb7m",''],
		_(u"mega newton meter"):
			[(m,1000000.0),u"MN\xb7m",''],
		_(u"milli newton meter"):
			[(m,1.0e-3),u"mN\xb7m",''],
		_(u"micro newton meter"):
			[(m,1.0e-6),u"\xb5N\xb7m",''],
		_(u"dyne centimeter"):
			[(m,1.0e-7),u"dyne\xb7cm",''],
		_(u"kilogram meter"):
			[(m,9.80665),u"kg\xb7m",''],
		_(u"centimeter gram"):
			[(m,9.80665/100000.0),u"cm\xb7g",''],
		_(u"kip"):
			[(m,113.0),u"kip",_(u"One thousand inch pounds.")],
		_(u"foot pounds"):
			[(m,1356.0/1000.0),u"lbf\xb7ft",''],
		_(u"foot ounce"):
			[(m,1356.0/1000.0/16.0),u"oz\xb7ft",''],
		_(u"meter kilopond"):
			[(m,9.80665),u"mkp",''],
		_(u"newton centimeter"):
			[(m,.01),u"N\xb7cm",''],
		_(u"inch ounces"):
			[(m,113.0/16.0*.001),u"in\xb7oz",''],
		_(u"inch pounds"):
			[(m,113.0*.001),u"in\xb7lb",''],
		_(u"foot poundal"):
			[(m,1.0/23.7303605),u'',''],
	},
	_(u"Current Loop"):{".base_unit":"6400 to 32000",
		_(u"6400 to 32000"):
			[(m,1.0),u"counts",_(u"Many PLCs must scale the 4 to 20mA signal to an integer, this is commonly a value from 6400 to 32000,")],
		_(u"4 to 20mA"):
			[(m,1600.0),u"mA",_(u"This range of current is commonly used in instrumentation. 0mA is an indication of a broken transmitter loop.")],
		_(u"V across 250 ohm"):
			[(m,6400.0),u"V",_(u"A common resistance for current loop instrumentation is 250 ohms. A voltage will be developed across this resistor, that voltage can be used to test the current loop.")],
		_(u"percent"):
			[(gof,(((32000.0-6400.0)/100.0),6400.0)),u"%",_(u"This is a percentage of the 4 to 20mA signal.")],
	},

	_(u"Currency (UK)"):{".base_unit":"pound",
		_(u"pound | quid | soverign"):
			[(m,1.0),"","""The base monetary unit in UK."""],
		_(u"soverign"):
			[(m,1.0),"","""One pound."""],
		_(u"quid"):
			[(m,1.0),"","""One pound."""],
		_(u"fiver"):
			[(m,5*1.0),"","""Equal to five pounds."""],
		_(u"tenner"):
			[(m,10*1.0),"","""Equal to Ten pounds."""],
		_(u"crown"):
			[(m,5*1.0/20),"","""Equal to five shillings."""],
		_(u"shilling"):
			[(m,1.0/20),"","""Equal to one twentieth of a pound."""],
		_(u"bob | shilling"):
			[(m,1.0/20),"","""Equal to one twentieth of a pound."""],
		_(u"penny | pence"):
			[(m,1.0/100),"","""Equal to 1/100 of a pound."""],
		_(u"penny | pence (old)"):
			[(m,1.0/240),"","""Equal to 1/240 of a pound.  February 15, 1971 the English coinage system was changed to a decimal system and the old penny ceased to be legal tender August 31, 1971."""],
		_(u"tuppence(old)"):
			[(m,2*1.0/240),"","""Equal to two old pennies. February 15, 1971 the English coinage system was changed to a decimal system."""],
		_(u"threepence (old)"):
			[(m,3*1.0/240),"","""Equal to three old pence.  The threepence was demonitized August 31, 1971."""],
		_(u"halfpenny | hapenny (old)"):
			[(m,1.0/240/2),"","""The old halfpenny was demonetized on August 31, 1969."""],
		_(u"guinea"):
			[(m,21*1.0/20),"","""While the term is still used, the coins are no longer in use.  Webster's Revised Unabridged Dictionary (1913) - A gold coin of England current for twenty-one shillings sterling, ... but not coined since the issue of sovereigns in 1817."""],
		_(u"farthing"):
			[(m,1.0/240/4),"",""""""],
		_(u"florin (or two bob bit)"):
			[(m,2*1.0/20),"",""""""],
		_(u"half crown (old)"):
			[(m,(2*1.0/20)+(6*1.0/240)),"",""" The half-crown was demonetized on 1st January 1970."""],
		_(u"sixpence"):
			[(m,6*1.0/240),"","""Equal to six old pence.  February 15, 1971 the English coinage system was changed to a decimal system ."""],
		_(u"tanner | sixpence"):
			[(m,6*1.0/240),"","""Equal to six old pence.  February 15, 1971 the English coinage system was changed to a decimal system ."""],
		_(u"mark (old British mark)"):
			[(m,160*1.0/240),"",""""""],
		_(u"groat"):
			[(m,4*1.0/240),"","""Equal to four old pence"""],
		_(u"pony"):
			[(m,25.0),"","""Equal to twenty five pounds sterling"""],

	},

	}

future_dic = {



	_(u"Wire Gauge"):{".base_unit":"circular mils",
		_(u"circular mil"):
			[(m,1.0),u"CM",''],
		_(u"square mil"):
			[(m,1.0),u'',''],
		_(u"square milimetres"):
			[(m,1.0),u"mm\xb2",''],
		_(u"AWG"):
			[(m,1.0),"AWG",_(u"American Wire Gauge")],
		_(u"Diameter mils"):
			[(m,1.0),"mil",''],
		_(u"Diameter inches"):
			[(m,1.0),"in",''],
		_(u"Diameter mm"):
			[(m,1.0),"mm",''],
		_(u"Diameter m"):
			[(m,1.0),"m",''],
		_(u"Ampacity Cu"):
			[(m,1.0),"A",_(u"Copper wire ampacity")],
		_(u"Ampacity Al"):
			[(m,1.0),"A",_(u"Aluminum wire ampacity")],
		_(u"Resistance of Cu wire at xxdegC"):
			[(m,1.0),"ohms/kft",_(u"Copper wire resistance.")],
		_(u"Resistance of Cu wire at xxdegC"):
			[(m,1.0),"ohms/ft",_(u"Copper wire resistance.")],
		_(u"Resistance of Cu wire at xxdegC"):
			[(m,1.0),"ohms/m",_(u"Copper wire resistance.")],
		_(u"Resistance of Cu wire at xxdegC"):
			[(m,1.0),"ohms/km",_(u"Copper wire resistance.")],
		_(u"Resistance of Al wire at xxdegC"):
			[(m,1.0),"ohms/kft",_(u"Copper wire resistance.")],
		_(u"Resistance of Al wire at xxdegC"):
			[(m,1.0),"ohms/ft",_(u"Copper wire resistance.")],
		_(u"Resistance of Al wire at xxdegC"):
			[(m,1.0),"ohms/m",_(u"Copper wire resistance.")],
		_(u"Resistance of Al wire at xxdegC"):
			[(m,1.0),"ohms/km",_(u"Copper wire resistance.")],
		_(u"Length per Weight Cu Wire"):
			[(m,1.0),"ft/lb (Cu)",_(u"Length per weight Copper Wire.")],
		_(u"Length per Weight Al Wire"):
			[(m,1.0),"ft/lb (Al)",_(u"Length per weight Aluminum Wire.")],
		_(u"Length per resistance Cu Wire"):
			[(m,1.0),"ft/ohm (Cu)",_(u"Length per resistance Copper Wire.")],
		_(u"Length per resistance Al Wire"):
			[(m,1.0),"ft/ohm (Al)",_(u"Length per resistance Aluminum Wire.")],
		_(u"Weight Cu wire"):
			[(m,1.0),"kg/km (Cu)",_(u"Copper wire weight.")],
		_(u"Weight Al wire"):
			[(m,1.0),"kg/km (Al)",_(u"Aluminum wire weight.")],
		_(u"Weight Cu wire"):
			[(m,1.0),"lb/kft (Cu)",_(u"Copper wire weight in pounds per 1000 feet.")],
		_(u"Weight Al wire"):
			[(m,1.0),"lb/kft (Al)",_(u"Aluminum wire weight in pounds per 1000 feet.")],
		_(u"Tensile strength"):
			[(m,1.0),"kgf",_(u"Aluminum wire weight.")],
		_(u"Turns per inch"):
			[(m,1.0),"TPI",_(u"Turns per inch of bare wire, useful for winding coils. This value is approximate and will be reduced with insulated wire")],
	},}


list_items = []

keys=list_dic.keys()
keys.sort()

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
for key in keys:
  iter = cat_model.append()
  cat_model.set(iter,0,key)

if os.path.exists(home+'/.gonvert/bookmarks.dat'):
	bookmarks=pickle.load(open(home+'/.gonvert/bookmarks.dat'))
	print bookmarks

ToolTips=gtk.Tooltips()
find_button  = widgets.get_widget('find_button')
ToolTips.set_tip(find_button,_(u'Find unit (F6)'))

#Restore selections from previously saved settings if it exists and is valid.
historical_catergory_found=False
if os.path.exists(home+'/.gonvert/selections.dat'):
  #Retrieving previous selections from ~/.gonvert/selections.dat
  selections=pickle.load(open(home+'/.gonvert/selections.dat','r'))
  #Restoring previous selections.
  #
  #Make a list of categories to determine which one to select
  categories=list_dic.keys()
  categories.sort()
  #
  #If the 'selected_unts' has been stored, then extract selected_units from selections.
  if selections.has_key('selected_units'):
    selected_units=selections['selected_units']
  #Make sure that the 'selected_category' has been stored.
  if selections.has_key('selected_category'):
    #Match an available category to the previously selected category.
    for counter in range(len(categories)):
      if selections['selected_category']==categories[counter]:
        # Restore the previously selected category.
        cat_clist.set_cursor(counter, col, False )
        cat_clist.grab_focus()
	historical_catergory_found=True

if not historical_catergory_found:
  print "Couldn't find saved category, using default."
  #If historical records were not kept then default to 
  # put the focus on the first category
  cat_clist.set_cursor(0, col, False )
  cat_clist.grab_focus()

restore_units()


gtk.main()

