#

VERSION:=1.1


all:
	@echo "this is pretty broken, try install"

install-shared:
	mkdir -p /opt/share/stow/cvs2ticker-$(VERSION)/bin

	cp cvs2ticker /opt/share/stow/cvs2ticker-$(VERSION)/bin
	chmod 775 /opt/share/stow/cvs2ticker-$(VERSION)/bin/cvs2ticker
	chgrp local /opt/share/stow/cvs2ticker-$(VERSION)/bin/cvs2ticker

	cp cvs2ticker.py /opt/share/stow/cvs2ticker-$(VERSION)/bin
	chmod 664 /opt/share/stow/cvs2ticker-$(VERSION)/bin/cvs2ticker.py
	chgrp local /opt/share/stow/cvs2ticker-$(VERSION)/bin/cvs2ticker.py

	cp cvs2web.py  /projects/www/internal/cgi-bin
	chmod 775 /projects/www/internal/cgi-bin/cvs2web.py
	chgrp www /projects/www/internal/cgi-bin/cvs2web.py


install-exec:
	mkdir -p /opt/local/stow/cvs2ticker-$(VERSION)/bin
	(cd /opt/local/stow/cvs2ticker-$(VERSION)/bin; \
	ln -s /opt/share/stow/cvs2ticker-$(VERSION)/bin/* .)

install: install-shared install-exec

stow:
	(cd /opt/local/stow; \
	stow -c cvs2ticker-$(VERSION) && stow -v cvs2ticker-$(VERSION))

