PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin
# check_package.py checks this checkout, so it runs only from here.
SCRIPTS := $(filter-out scripts/check_package.py,$(wildcard scripts/*))

.PHONY: install
install:
	mkdir -p "$(DESTDIR)$(BINDIR)"
	install -m 755 $(SCRIPTS) "$(DESTDIR)$(BINDIR)"
