#!/usr/bin/python2.5

import os
import sys

import py2deb

import constants


__appname__ = constants.__app_name__
__description__ = """Unit Conversions
A conversion utility that allows conversion between many units like CGS, Ancient, Imperial with many categories like length, mass, numbers, etc. All units converted values shown at once as you type
.
Homepage: http://www.unihedron.com/projects/gonvert/index.php
"""
__author__ = "Anthony Tekatch"
__email__ = "anthony@unihedron.com"
__version__ = constants.__version__
__build__ = constants.__build__
__changelog__ = """
0.9.2
* Added search toggle to the menu
* Maemo 5: Added sorting to the app menu

0.9.1
* Added support for creating generic .deb files
* Added an apothecary unit
* Bug fix: Can directly enter numbers after selecting category
* Bug fix: font of the category button was inconsistent
* Bug fix: Improved up/down arrow keys

0.9.0
* Added Radioactivity and Radiation dose categories.
* Aligning the numbers by their decimal place
* Added shortcuts for fullscreen
* Switched to Find being brought up by CTRL+F
* Added Find Previous and Find Next shortcuts (CTRL+P, CTRL+N)
* Adjusted the sizing on various widgets
* Removed unused UI features for polish
* Bug fix: improved behavior when corner case values are inputted (like floats for base conversions)
* Debugging: Added logging support
* Marketting: Huge version bump to express a basic level of feature complete
* Internal: Massive cleanup of code

0.2.23  - Added UK currency category and other UK measurements thanks to Dale Hair
0.2.22  - Restore previously used window size
0.2.21  - Category column widened. Maximize on start.
0.2.20  - correction in micron pressure conversion
0.2.19  - viscosity cP conversion correction
0.2.18	- addition of magnitudes per square arcsecond to Luminance category
0.2.17	- updated baud definitions
	- fixed homepath location because new debian version changed
0.2.16	- fixed icon locating for display in about
	- added alternate icon gonvert-icon_alernative.png (copy over gonvert.png)
0.2.15	- updated mainloop to main as discovered by Alexander Skwar
0.2.14	- added Calgary energy and volume suggestions per Kim Lux
0.2.13	- new more easily understandable icon
	- nanotesla definition (nT).
	- added shortlist feature.
0.2.12	- removed inoperable books feature.
	- fixed up acre accuracy.
0.2.11	- miodified descriprion for silver, newton, sadzhens.
0.2.10	- \x90 changed to \u00C9 for Emile and similar for Reaumur utf-8 text.
	- Added translation for "All" book text.
	- The write units text is translatable.
	- The pl_messages.po file has been updated
0.2.09	- Added utf-8 coding to all text strings in preparation for complete language translation.
0.2.08	- Added language translation for menus and labels.
0.2.07	- Added language translation changes and messages.pot.
0.2.06	- Fixed category list size to show preselected categorys on startup,
	  scroll window H&Vpolicy set to always.
0.2.05	- Spelling of Luminance category fixed.
0.2.04	- Modified unit clicking to force focus on value entry.
	  Modified Makefile to remove /share/share bug for desktop entry.
0.2.03	- Modified Makefile to allow better integration on other platforms.
0.2.01	- Added saved selections feature, creates ~/.gonvert/ and file. 
0.1.11	- fixed packaging for RPM
0.1.10	- added Current Loop category for PLCs and 4-20mA instrumentation.
0.1.9	- added kilobit, and more density units.
0.1.8	- Added Torque units
0.1.7	- Added many more pressure units
	- Added thermal categories
	- Added fuel consumption category
	- Program extension to .pyw so that Windows startup without console
0.1.6	- add more frequency units
	- fixed computer number bases nums was bad near "h" and "v"
	- fixed error:
	  "GtkTextBuffer.insert_at_cursor() takes exactly 1 argument (2 given)"
	  thanks to Riccardo Galli
0.1.5	- put packages into /usr instead of /usr/local
	- add gnome menu item back in
0.1.4	- remove dependency on gnome-config from Makefile, RPM, binary.
0.1.3	- touched up computer numbers units for better sorting
	- limited up resizing of windows to prevent dissapearing areas
	- fixed find bug that some users might notice (TreeViewColumn/None)
0.1.2	- Added description box when writing units
0.1.1	- Added help/about box
	- fixed bug that sets focus on line 2480
	- fixed temperature difference units labels
	- all scroll bars only show when needed
	- Added RPM distribution
0.1.0   - Major modifications for GTK2 (RedHat 8.0)
	- addition of units column in display
	- sorting for all units columns with sort pointer
0.0.15	- added Electromagnetic Radiation category
0.0.14	- fixed window close bug, attempt to fix libglade XML startup bug for
          some machines
0.0.13	- changes for python2.2, had to remove gnome dependencies
0.0.12	- change contact information address
0.0.11	- addition of ppm to "find" utility
0.0.10	- addition of petabyte to computer data
0.0.9	- addition of cesium atom vibrations to Time category
0.0.8	- more accurate calculation of degrees F
0.0.7	- added 'Find unit' feature
	- changed Category list to clist for ease of moveto (focus) after find
0.0.6	- added description for Amperes
	- added DENSITY category
	- added 4 new categories 101 new units
	- added shoe size converter
	- add a function to convert custom formulas (like area from diameter)
	  example: area = pi * (D/2)^2
  	  base value = pi* (x/2)^2  #metres in diameter metres, cm, inch, foot.
0.0.5	- Tool for listing all categories and units to STDOUT.
	- re-organization of project files.
	- addition of suffixes between duodecillion and centillion.
	- addition of Makefile to install onto Gnome based systems.
	- sort Units or Value columns (ascending or descending)
	  by clicking on column.
0.0.4	- Prefixes and Suffixes addition of;
	  ppm, %, Marx brothers, various descriptions.
	- addition of microgram to mass category.
	- replaced base 63 with 62 from computer numbers since
	  only 62 characters can be represented.
	- fixed error if second line has nothing it wouldn't get
	  updated.
0.0.3	- fix bug in labelling of base 36 (was base 37)
	  all numbering systems past 23 were at fault due
	  to improper nums string (fixed).
0.0.2	- Completion of second row data entry so that changes
	  to text are not cyclicly causing changes to all
	  values.
0.0.1	- Initial release.
"""


__postinstall__ = """#!/bin/sh -e

gtk-update-icon-cache -f /usr/share/icons/hicolor
rm -f ~/.gonvert/gonvert.log ~/.gonvert/selections.dat ~/.gonvert/window.dat
"""

__preremove__ = """#!/bin/sh -e
"""


def find_files(prefix, path):
	for root, dirs, files in os.walk(path):
		for file in files:
			if file.startswith(prefix+"-"):
				fileParts = file.split("-")
				unused, relPathParts, newName = fileParts[0], fileParts[1:-1], fileParts[-1]
				assert unused == prefix
				relPath = os.sep.join(relPathParts)
				yield relPath, file, newName


def unflatten_files(files):
	d = {}
	for relPath, oldName, newName in files:
		if relPath not in d:
			d[relPath] = []
		d[relPath].append((oldName, newName))
	return d


def build_package(distribution):
	try:
		os.chdir(os.path.dirname(sys.argv[0]))
	except:
		pass

	py2deb.Py2deb.SECTIONS = py2deb.SECTIONS_BY_POLICY[distribution]
	p = py2deb.Py2deb(__appname__)
	p.prettyName = constants.__pretty_app_name__
	p.description = __description__
	p.bugTracker = "https://bugs.maemo.org/enter_bug.cgi?product=Gonvert"
	p.upgradeDescription = __changelog__.split("\n\n", 1)[0]
	p.author = __author__
	p.mail = __email__
	p.license = "gpl"
	p.depends = ", ".join([
		"python2.6 | python2.5",
		"python-gtk2 | python2.5-gtk2",
		"python-xml | python2.5-xml",
		"python-dbus | python2.5-dbus",
	])
	maemoSpecificDepends = ", python-osso | python2.5-osso, python-hildon | python2.5-hildon"
	p.depends += {
		"debian": ", python-glade2",
		"diablo": maemoSpecificDepends,
		"fremantle": maemoSpecificDepends + ", python-glade2",
	}[distribution]
	p.recommends = ", ".join([
	])
	p.section = {
		"debian": "science",
		"diablo": "user/science",
		"fremantle": "user/science",
	}[distribution]
	p.arch = "all"
	p.urgency = "low"
	p.distribution = "diablo fremantle debian"
	p.repository = "extras"
	p.changelog = __changelog__
	p.postinstall = __postinstall__
	p.preremove = __preremove__
	p.icon = {
		"debian": "data-pixmaps-gonvert.png",
		"diablo": "data-pixmaps-gonvert.png",
		"fremantle": "data-pixmaps-gonvert.png", # Fremantle natively uses 48x48
	}[distribution]
	p["/usr/bin"] = [ "gonvert.py" ]
	for relPath, files in unflatten_files(find_files("src", ".")).iteritems():
		fullPath = "/usr/lib/gonvert"
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	for relPath, files in unflatten_files(find_files("data", ".")).iteritems():
		fullPath = "/usr/share/gonvert"
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	p["/usr/share/applications/hildon"] = ["gonvert.desktop"]
	p["/usr/share/icons/hicolor/26x26/hildon"] = ["data-pixmaps-gonvert.png|gonvert.png"]
	p["/usr/share/icons/hicolor/64x64/hildon"] = ["data-pixmaps-gonvert.png|gonvert.png"]
	p["/usr/share/icons/hicolor/scalable/hildon"] = ["data-pixmaps-gonvert.png|gonvert.png"]

	if distribution == "debian":
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=True,
			tar=False,
			changes=False,
			dsc=False,
		)
		print "Building for %s finished" % distribution
	else:
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=False,
			tar=True,
			changes=True,
			dsc=True,
		)
		print "Building for %s finished" % distribution


if __name__ == "__main__":
	if len(sys.argv) > 1:
		try:
			import optparse
		except ImportError:
			optparse = None

		if optparse is not None:
			parser = optparse.OptionParser()
			(commandOptions, commandArgs) = parser.parse_args()
	else:
		commandArgs = None
		commandArgs = ["diablo"]
	build_package(commandArgs[0])
