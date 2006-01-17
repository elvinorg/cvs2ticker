#

VERSION:=1.4.2

prefix=/usr/local
CGI_ROOT=$(prefix)/cgi-bin
DESTDIR=

all:
	@echo "try make install"

install:
	mkdir -p $(DESTDIR)$(prefix)/bin
	cp cvs2ticker.py $(DESTDIR)$(prefix)/bin

	mkdir -p $(DESTDIR)$(prefix)/man/man1
	cp cvs2ticker.1 $(DESTDIR)$(prefix)/man/man1

	cp cvs2web.py $(DESTDIR)$(CGI_ROOT)

dist:
	(cd ..; tar zcvf cvs2ticker-$(VERSION).tar.gz \
		cvs2ticker/cvs2ticker.1 \
		cvs2ticker/cvs2ticker.py \
		cvs2ticker/cvs2web.py \
		cvs2ticker/setup.py \
		cvs2ticker/Makefile \
		cvs2ticker/COPYING \
		cvs2ticker/INSTALL \
		cvs2ticker/NEWS \
		cvs2ticker/README)
