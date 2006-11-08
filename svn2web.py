#! /usr/bin/env python
########################################################################
# COPYRIGHT_BEGIN
#
#              Tickertape
#              Subversion web commit viewing interface
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/Attic/svn2web.py,v $
# Version:     $Id: svn2web.py,v 1.1 2006/11/08 00:50:11 ilister Exp $
#
# Copyright    (C) 2006 Ian Lister
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above
#   copyright notice, this list of conditions and the following
#   disclaimer.
#
# * Redistributions in binary form must reproduce the above
#   copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials
#   provided with the distribution.
#
# * Neither the name of Mantara Software nor the names
#   of its contributors may be used to endorse or promote
#   products derived from this software without specific prior
#   written permission. 
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# COPYRIGHT_END
########################################################################
"""

svn2web - presents Subversion change information on a web page.

"""
__author__  = "ticker-user@tickertape.org"
__version__ = "$Revision: 1.1 $"[11:-2]

#############################################################################

import cgi
import cgitb; cgitb.enable()

import urllib
import sys
import time

import svn.repos
import svn.fs

########################################################################

CONFIG_MAIL_DOMAIN      = "mail_domain"

########################################################################

class Page:
    """ A generic class for CGI scripts to represent themselves with
    structure to assist in output."""

    def __init__(self, form=None):
        self._form = form
        self._stream = sys.stdout
        self._indent = 0
        self._title = None
        self._outputStarted = False


    """ Accessors """

    def title(self):
        """ Returns the page title. """
        return self._title


    """ Page output utilities. """
    
    def indent(self):
        """ Increases the current page indent level. """
        self._indent += 1

    def outdent(self):
        """ Decreases the current page indent level. """
        assert(self._indent > 0)
        self._indent -= 1

    def write(self, text):
        """ Writes the specified text to the page. """
        self._outputStarted = True
        self._stream.write(text)

    def writeln(self, text=""):
        """ Writes the specified line of text to the page,
        appropriately indented and terminated."""
        self._stream.write("  " * self._indent + text + "\n")

    def die(self, message=None):
        """ Displays a fatal error. """
        # Print HTTP headers iff we haven't already
        if not self._outputStarted:
            self.writeln("Content-Type: text/plain")
            self.writeln()
        
        self.writeln("svn2web.py error")
        if message:
            self.writeln(message)
        
        sys.exit(1)


    """ Page output control. """
    
    def run(self):
        self.input()
        self.http_page()

    def input(self):
        """ Reads CGI input. """
        if self._form == None:
            self._form = cgi.FieldStorage()
    

    def http_page(self):
        self.http_header()
        print
        self.html_page()

    def http_header(self, content_type="text/html"):
        self.writeln("Content-Type: " + content_type)

    def html_page(self):
        self.writeln("<html>")
        self.indent()
        
        self.html_head()
        self.html_body()

        self.outdent()
        self.writeln("</html>")

    def html_head(self):
        self.writeln("<head>")
        self.indent()

        if self.title():
            self.writeln("<title>%s</title>" % self.title())
        
        self.outdent()
        self.writeln("</head>")
        
    def html_body(self):
        self.writeln("<body bgcolor=\"white\">")
        self.indent()

        self.html_header()
        self.html_content()
        self.html_footer()
        
        self.outdent()
        self.writeln("</body>")

    def html_header(self):
        if self.title():
            self.writeln("<h1>%s</h1>" % self.title())
            self.writeln()

    def html_footer(self):
        self.writeln()
        self.writeln("<hr />")
        self.writeln("<p><font size=\"-1\">Generated %s.</font></p>" % time.asctime())

    def html_content(self):
        """ Outputs content specific to the page subclass. """
        pass
        

########################################################################

class SubversionPage(Page):

    """ A slight specialisation of the Page class, for displaying
    information about Subversion repositories. """

    def __init__(self, config, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)
        self._config = config
        self._repository = None
        self._revision = None

    @staticmethod
    def get_page(config):
        form = cgi.FieldStorage()
        action = form.getfirst("action", "commit")
        if action == "commit":
            page = CommitPage(config, form)
        else:
            raise ValueError("unknown action: " + action)
        return page

    def title(self):
        return "Subversion (rev %d)" % self._revision

    def input(self):
        Page.input(self)

        self._repository = self._form.getfirst("rep", None)
        self._revision = int(self._form.getfirst("rev", None))

        # Verify input
        if not self._repository:
            self.die("missing required repository")
        if not self._revision:
            self.die("missing required revision")

    def html_header(self):
        pass


########################################################################

class CommitPage(SubversionPage):

    """ Displays information about a particular commit (revision) to a
    CVS repository."""

    def html_content(self):
        """ Displays a web page containing information about a
        particular commit (revision) in a repository."""
        # Get access to the repository
        repos = svn.repos.open(self._repository)
        fs = svn.repos.fs(repos)
        root = svn.fs.revision_root(fs, self._revision)

        # Look up some information about this revision
        author = svn.fs.revision_prop(fs, self._revision,
                                      svn.core.SVN_PROP_REVISION_AUTHOR)
        revision_date = svn.fs.revision_prop(fs, self._revision,
                                             svn.core.SVN_PROP_REVISION_DATE)
        log_message = svn.fs.revision_prop(fs, self._revision,
                                           svn.core.SVN_PROP_REVISION_LOG)

        # Display general information
        self.writeln("<table>")
        self.indent()
        self.writeln("<tr><td>Repository</td><td><tt>%s</tt></td></tr>" %
                     self._repository)
        self.writeln("<tr><td>Revision</td><td>%d <font size=\"-1\">(%s)</font></td></tr>" %
                     (self._revision, revision_date))
        if config.get(CONFIG_MAIL_DOMAIN):
            author_text = "<a href=\"mailto:%s@%s\"><tt>%s</tt></a>" % \
                          (author, CONFIG_MAIL_DOMAIN, author)
        else:
            author_text = "<tt>%s</tt>" % author
        self.writeln("<tr><td>Author</td><td>%s</td></tr>" % author_text)
        self.outdent()
        self.writeln("</table>")
        self.writeln()

        # Display the commit message
        self.writeln("<div style=\"background-color:#c0c0c0;\"><pre>")
        self.indent()
        self.write(log_message + "\n")
        self.outdent()
        self.writeln("</pre></div>")
        self.writeln()

        # Collect all the changes made in the revision
        editor = svn.repos.ChangeCollector(fs, root)
        ptr, baton = svn.delta.make_editor(editor)
        svn.repos.replay(root, ptr, baton)
        changes = editor.get_changes()
        changelist = changes.items()
        changelist.sort()

        # Traverse the changes, gathering information
        assert len(changelist) > 0
        self.writeln("<table border=\"0\">")
        self.indent()
        for path, change in changelist:
            path = change.path
            extra = ""
            if change.added:
                op = "Added"
            elif not path:
                op = "Removed"
                path = change.base_path
            else:
                op = "Modified"
            if change.path != change.base_path and change.path:
                extra = "based on <tt>%s</tt>" % change.base_path
            self.writeln("<tr><td>%s</td><td><tt>%s</tt></td><td>%s</td></tr>"
                         % (op, path, extra))
        self.outdent()
        self.writeln("</table>")


########################################################################

def read_config(path):
    """Parse configuration file, compatible with cvs2ticker's."""

    # Open the file
    try:
        config_file = open(path)
    except IOError, e:
        sys.stderr.write(e.filename + ": " + e.strerror + "\n")
        sys.exit(1)

    # Process the contents
    config = {}
    try:
        for line in config_file:
            # Strip the line down to what we're interested in
            comment = line.find("#")
            if comment != -1:
                line = line[:comment]
            line = line.strip()
            if not line:
                continue

            # Parse the line
            try:
                key, value = line.split("=", 1)
            except ValueError:
                sys.stderr.write(path + ": unable to parse: " + line + "\n")
                sys.exit(1)

            config[key.strip()] = value.strip()
    finally:
        config_file.close()

    return config


########################################################################

if __name__ == "__main__":
    config = read_config("svn2ticker.conf")
    SubversionPage.get_page(config).run()


########################################################################
# end of svn2web.py
