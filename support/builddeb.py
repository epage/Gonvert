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
1.0.0
* Switched from GTK to QT in preparation for Meego, all previous features still present
* Except removed the current form of search
* Added a "Recent" window
* Added a "Quick Jump" window (to replace old form of search)
* Added favorites to limit the number of categories and units shown
* Should be auto-rotatable (might not be working for some reason)
* Should auto-enable Fn on Maemo 5
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
		"python-pyqt4 | python2.5-pyqt4",
	])
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
