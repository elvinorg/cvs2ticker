#

VERSION:=1.1a

INSTALL_ROOT=/usr/local/stow/cvs2ticker-$(VERSION)
CGI_ROOT=/projects/www/internal/cgi-bin

all:
	@echo "this is pretty broken, try install"

install:
	mkdir -p $(INSTALL_ROOT)/bin
	cp cvs2ticker.py $(INSTALL_ROOT)/bin
	chmod 775 $(INSTALL_ROOT)/bin/cvs2ticker.py
	chgrp local $(INSTALL_ROOT)/bin/cvs2ticker.py

	mkdir -p $(INSTALL_ROOT)/man/man1
	cp cvs2ticker.1 $(INSTALL_ROOT)/man/man1
	chmod 664 $(INSTALL_ROOT)/man/man1/cvs2ticker.1
	chgrp local $(INSTALL_ROOT)/man/man1/cvs2ticker.1

	cp cvs2web.py $(CGI_ROOT)
	chmod 775 $(CGI_ROOT)/cvs2web.py
	chgrp www $(CGI_ROOT)/cvs2web.py


stow:
	(cd /usr/local/stow; \
	stow -c cvs2ticker-$(VERSION) && stow -v cvs2ticker-$(VERSION))

dist:
	(cd ..; tar zcvf cvs2ticker/cvs2ticker.tar.gz cvs2ticker/cvs2ticker.1 cvs2ticker/cvs2ticker.py cvs2ticker/cvs2web.py cvs2ticker/Makefile)
