PREFIX  ?= $(HOME)/.local
DESTDIR ?=
APP_ID   = io.github.nikjft.DeskCutGTK
SHARE    = $(PREFIX)/share
ROOT     = $(DESTDIR)$(PREFIX)
ROOTSHARE = $(DESTDIR)$(SHARE)

.PHONY: install uninstall test

install:
	install -d $(ROOTSHARE)/deskcut-gtk $(ROOT)/bin
	cp -r deskcut_gtk $(ROOTSHARE)/deskcut-gtk/
	find $(ROOTSHARE)/deskcut-gtk -name __pycache__ -prune -exec rm -rf {} +
	printf '#!/bin/sh\nexec python3 -c "import sys; sys.path.insert(0, \\"$(SHARE)/deskcut-gtk\\"); from deskcut_gtk.app import main; sys.exit(main())" "$$@"\n' > $(ROOT)/bin/deskcut-gtk
	chmod +x $(ROOT)/bin/deskcut-gtk
	install -Dm644 data/$(APP_ID).desktop $(ROOTSHARE)/applications/$(APP_ID).desktop
	for size in 16 32 48 64 128 256; do \
	  install -Dm644 data/icons/hicolor/$${size}x$${size}/apps/$(APP_ID).png \
	    $(ROOTSHARE)/icons/hicolor/$${size}x$${size}/apps/$(APP_ID).png; \
	done
ifeq ($(DESTDIR),)
	-gtk-update-icon-cache -q -t $(SHARE)/icons/hicolor
	-update-desktop-database -q $(SHARE)/applications
endif

uninstall:
	rm -rf $(ROOTSHARE)/deskcut-gtk $(ROOT)/bin/deskcut-gtk $(ROOTSHARE)/applications/$(APP_ID).desktop
	rm -f $(ROOTSHARE)/icons/hicolor/*/apps/$(APP_ID).png

test:
	python3 -m unittest discover -s tests -v
