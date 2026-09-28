PREFIX ?= $(HOME)/.local
BINDIR ?= $(PREFIX)/bin

.PHONY: install
install:
	mkdir -p "$(DESTDIR)$(BINDIR)"
	install -m 755 scripts/* "$(DESTDIR)$(BINDIR)"
