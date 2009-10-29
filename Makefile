NAME=gonvert

#Get version number from source file
VERSION=$(shell head -3 $(NAME) | grep version | cut -d\" -f2)

#DESTDIR can be defined when calling make ie. make install DESTDIR=$RPM_BUILD_ROOT
prefix  = /usr/local
bindir  = $(prefix)/bin
datadir = $(prefix)/share
docdir  = $(datadir)/doc

DESTDIR =

all:

install:
	install -D -m0755 gonvert $(DESTDIR)$(bindir)/gonvert
	install -D -m0644 gonvert.glade $(DESTDIR)$(datadir)/gonvert/gonvert.glade
	install -d -m0755 $(DESTDIR)$(datadir)/pixmaps/
	install -m0644 pixmaps/*.png $(DESTDIR)$(datadir)/pixmaps/
	install -D -m0644 gonvert.desktop $(DESTDIR)$(datadir)/gnome/apps/Utilities/gonvert.desktop
	install -d -m0755 $(DESTDIR)$(docdir)/gonvert/
	install -m0644 doc/* $(DESTDIR)$(docdir)/gonvert/

install_pl:
	install -D -m0755 gonvert $(DESTDIR)$(bindir)/gonvert
	install -D -m0644 gonvert.glade $(DESTDIR)$(datadir)/gonvert/gonvert.glade
	install -d -m0755 $(DESTDIR)$(datadir)/pixmaps/
	install -m0644 pixmaps/*.png $(DESTDIR)$(datadir)/pixmaps/
	install -D -m0644 gonvert.desktop $(DESTDIR)$(datadir)/gnome/apps/Utilities/gonvert.desktop
	install -d -m0755 $(DESTDIR)$(docdir)/gonvert/
	install -m0644 doc/* $(DESTDIR)$(docdir)/gonvert/
	install -m0644 i18n/pl_messages.gmo /usr/share/locale/pl/LC_MESSAGES/gonvert.mo

uninstall:
	#specify project name manually to prevent removal of all directories
	rm -f  $(bindir)/gonvert
	rm -rf $(datadir)/gonvert*
	rm -rf $(docdir)/gonvert*
	rm -f /usr/share/gnome/apps/Utilities/$(NAME).desktop
	rm -f /usr/share/pixmaps/$(NAME).png

uninstall_pl:
	#specify project name manually to prevent removal of all directories
	rm -f  $(bindir)/gonvert
	rm -rf $(datadir)/gonvert*
	rm -rf $(docdir)/gonvert*
	rm -f /usr/share/gnome/apps/Utilities/$(NAME).desktop
	rm -f /usr/share/pixmaps/$(NAME).png
	rm -f /usr/share/locale/pl/LC_MESSAGES/gonvert.mo

dist:
	if test -d "$(NAME)-$(VERSION)"; then rm -rf $(NAME)-$(VERSION); fi
	if test -f "$(NAME)-$(VERSION).tar.gz"; then rm -f $(NAME)-$(VERSION).tar.gz; fi
	mkdir $(NAME)-$(VERSION)
	cp Makefile $(NAME)-$(VERSION)
	cp messages.pot $(NAME)-$(VERSION)
	cp -R i18n $(NAME)-$(VERSION)
	cp -R doc $(NAME)-$(VERSION)
	cp $(NAME) $(NAME)-$(VERSION)
	cp $(NAME).glade $(NAME)-$(VERSION)
	cp $(NAME).spec $(NAME)-$(VERSION)
	cp $(NAME).desktop $(NAME)-$(VERSION)
	cp -R pixmaps $(NAME)-$(VERSION)
	tar cvzf $(NAME)-$(VERSION).tar.gz $(NAME)-$(VERSION)
	rm -rf $(NAME)-$(VERSION)

rpm:
	#You will most likely have to be root for this to work
	sed '/Version/s/replaceme/$(VERSION)/' gonvert.spec.skel > gonvert.spec
	cp $(NAME).spec /usr/src/redhat/SPECS/$(NAME).spec
	cp $(NAME)-$(VERSION).tar.gz /usr/src/redhat/SOURCES
	rpmbuild -ba /usr/src/redhat/SPECS/gonvert.spec
	cp /usr/src/redhat/RPMS/noarch/gonvert-$(VERSION)*.rpm ~anthony/web/unihedron/projects/gonvert/downloads

pub:
	#For authors use only
	if test -f "$(NAME)"; then cp $(NAME)  ~/web/unihedron/projects/gonvert/downloads/$(NAME).pyw; fi
	if test -f "$(NAME).glade"; then cp $(NAME).glade  ~/web/unihedron/projects/gonvert/downloads; fi
	if test -f "$(NAME)-$(VERSION).tar.gz"; then mv -f $(NAME)-$(VERSION).tar.gz  ~/web/unihedron/projects/gonvert/downloads; fi
	if test -f "doc/CHANGELOG"; then cp -f doc/CHANGELOG  ~/web/unihedron/projects/gonvert/CHANGELOG; fi
