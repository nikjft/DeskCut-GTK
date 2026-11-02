PREFIX ?= $(HOME)/.local
APP_ID  = io.github.nikjft.DeskCutGTK
SHARE   = $(PREFIX)/share

.PHONY: install uninstall test

install:
	install -d $(SHARE)/deskcut-gtk $(PREFIX)/bin
	cp -r deskcut_gtk $(SHARE)/deskcut-gtk/
	find $(SHARE)/deskcut-gtk -name __pycache__ -prune -exec rm -rf {} +
	printf '#!/bin/sh\nexec python3 -c "import sys; sys.path.insert(0, \\"$(SHARE)/deskcut-gtk\\"); from deskcut_gtk.app import main; sys.exit(main())" "$$@"\n' > $(PREFIX)/bin/deskcut-gtk
	chmod +x $(PREFIX)/bin/deskcut-gtk
	install -Dm644 data/$(APP_ID).desktop $(SHARE)/applications/$(APP_ID).desktop
	for size in 16 32 48 64 128 256; do \
	  install -Dm644 data/icons/hicolor/$${size}x$${size}/apps/$(APP_ID).png \
	    $(SHARE)/icons/hicolor/$${size}x$${size}/apps/$(APP_ID).png; \
	done
	-gtk-update-icon-cache -q -t $(SHARE)/icons/hicolor
	-update-desktop-database -q $(SHARE)/applications

uninstall:
	rm -rf $(SHARE)/deskcut-gtk $(PREFIX)/bin/deskcut-gtk $(SHARE)/applications/$(APP_ID).desktop
	rm -f $(SHARE)/icons/hicolor/*/apps/$(APP_ID).png

test:
	python3 -m unittest discover -s tests -v
