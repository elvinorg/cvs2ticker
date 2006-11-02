#! /usr/bin/env python
########################################################################
# COPYRIGHT_BEGIN
#
#              Tickertape
#              cvs loginfo producer
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/cvs2web.py,v $
# Version:     $Id: cvs2web.py,v 1.26 2006/11/02 01:14:49 ilister Exp $
#
# Copyright    (C) 1999-2006 Mantara Software
# Copyright    (C) 2006 David Arnold
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

cvs2web - takes CVS commit information encoded by cvs2ticker and presents
it on the web. Allows viewing the file, diff, log or linking to cvsweb or
ViewVC.


"""
__author__  = "ticker-user@tickertape.org"
__version__ = "$Revision: 1.26 $"[11:-2]

#############################################################################
#############################################################################
#
#  CONFIGURATION SECTION
#

CGI_URL       = "/cgi-bin"
CVS2WEB_URL   = CGI_URL + "/cvs2web.py"

# Set BUGZILLA_URL to the empty string if you don't use Bugzilla
BUGZILLA_URL = "http://www.tickertape.org/bugzilla/show_bug.cgi?id=%s"
# BUGZILLA_URL = ""

# Set VIEWVC_URL to the empty string if you don't use CVSWeb, ViewCVS or ViewVC
VIEWVC_URL    = CGI_URL + "/cvsweb.cgi"
# VIEWVC_URL    = ""

# Set TICKER_URL to the empty string if you don't use CGITicker
TICKER_URL    = CGI_URL + "/ticker.py"
# TICKER_URL    = ""

# Set MAILDOMAIN to the empty string if all users don't share a domain
# for mailto links
MAIL_DOMAIN   = "tickertape.org"
# MAIL_DOMAIN   = ""

# Set RCSPATH to the location of the installed RCS tools (with a
# trailing slash), or empty to use the default PATH
RCSPATH = ""
# RCSPATH = "/usr/local/bin/"

#  end of configuration
#############################################################################
#############################################################################

import base64, cgi, exceptions, os, pickle, popen2, regsub, string, sys, time, traceback, urllib


#############################################################################

def send(txt, indent=0):
    """Write text to output."""
    
    # Create indent string
    str_indent = " " * indent

    # Insert indent after carriage returns
    txt = regsub.gsub("\n\(.\)", "\n%s\\1" % str_indent, txt)

    # Write
    sys.stdout.write("%s%s" % (str_indent, txt))
    
    return


def wrap(s, width=60):
    """Return the string with long strings wrapped."""

    res = ""
    
    # Separate into paragraphs
    lst_para = string.split(s, "\n")
    for para in lst_para:
        if len(para) <= width:
            res = res + para + "\n"

        else:
            lst_word = string.split(para)
            line = ""
            for word in lst_word:
                if not line:
                    line = word
                    
                elif len(line) + len(word) + 1 <= width:
                    line = line + " " + word
                    
                else:
                    res = res + line + "\n"
                    line = word
                    
            res = res + line + "\n"

    return res


def common_tail(str1, str2):
    """ """
    return ""

            
#############################################################################

def header():
    send("Content-type: text/html\n\n")
    send("<html>\n")
    send("<head>\n", 2)
    send("<title>cvs2ticker</title>\n", 4)
    send("</head>\n", 2)

    send('<body bgcolor="white">\n', 2)
    send('<h1><tt>cvs2web, v%s</tt><hr></h1>\n' % __version__, 4)
    
    return


def end_body():
    send("<hr>\n", 4)
    str_time = time.asctime(time.localtime(time.time()))
    
    send("<address>%s</address>\n" % str_time, 4)
    send("</body>\n", 2)
    send("</html>\n\n")
    return


#############################################################################

def user_info(user, d_cvs):
    """Show the name of the user who performed the commit"""

    # Get the name of the person?
    logname = "cvs%20user"

    # Find the module name(s)
    str_dir = d_cvs["Repository-Directory"]
    str_rep = d_cvs["Repository-Root"]
    str_rep_name = d_cvs["Repository"]
    rep_rel_path = str_dir[len(str_rep)+1:]
    mod_rel_path = string.join(string.split(rep_rel_path, "/")[1:], "/")
    module = string.split(rep_rel_path, "/")[0]

    send('<dl>\n', 4)
    send('<dt><b>cvs commit</b></tt><p>\n', 6)
    send('<dd>\n  <table>\n', 6)
    send('<tr><td>Repository</td> <td><b>%s</b></td> <td>&nbsp;</td></tr>\n' % str_rep_name,10)
    send('<tr><td>Module</td> <td><b>%s</b></td> <td>&nbsp;</td></tr>\n' % module, 10)
    send('<tr><td>User</td> <td><b>%s</b></td>\n' % user, 10)
    send('<td>\n', 14)
    if MAIL_DOMAIN:
        send('[<a href="mailto:%s@%s">mail</a>]\n' % (user, MAIL_DOMAIN), 18)
    if TICKER_URL:
        send('[<a href="%s?%s+10+%s+%s+%s">ticker</a>]\n' % \
         (TICKER_URL, logname, user, module, str_rep_name), 18)
    send('</td>\n', 14)
    send('</tr>\n', 10)
    send('</table>\n', 8)
    send('</dl>\n', 4)
    send('<p>\n', 4)
    return


def log_msg(d_cvs):
    if not d_cvs.has_key("Log-Message"):
        return

    send('<table align="center" width="90%">\n', 4)
    send('<tr>\n', 6)
    send('<td bgcolor="#c0c0c0">\n', 8)
    send("<pre>\n\n", 10)

    if BUGZILLA_URL:
        bugzilla_url = BUGZILLA_URL % ('\\2')
        replacement = '<a href="%s">\\1</a>' % (bugzilla_url)
        send(regsub.gsub('\([Bb]ug #?\([0-9]+\)\)', replacement, wrap(d_cvs["Log-Message"])))  
        
    else:
	send(wrap(d_cvs["Log-Message"]))

    send("\n</pre>\n", 10)
    send("    </td>\n  </tr>\n</table>\n", 4)
    return


def add_info(d_cvs):

    if not d_cvs.has_key("Added-Files"):
        return

    if not d_cvs["Added-Files"]:
        return
    
    # Find the module name(s)
    str_dir = d_cvs["Repository-Directory"]
    str_rep = d_cvs["Repository-Root"]
    str_rep_name = d_cvs["Repository"]
    rep_rel_path = str_dir[len(str_rep)+1:]
    mod_rel_path = string.join(string.split(rep_rel_path, "/")[1:], "/")
    
    send("<dl>\n  <dt>Added files:\n", 4)

    for file in string.split(d_cvs["Added-Files"]):
        full_path = os.path.join(str_dir, file)
        
        send("<dd>%s/%s\n" % (mod_rel_path, file), 6)
        cooked_url = "%s?file+%s" % (CVS2WEB_URL, urllib.quote(full_path))
        send('[<a href="%s">file</a>]\n' % cooked_url, 10)
        if VIEWVC_URL:
            cooked_url = "%s/%s/%s?%s" % \
                         (VIEWVC_URL,
                          urllib.quote(rep_rel_path),
                          urllib.quote(file),
                          urllib.quote("cvsroot="+str_rep_name))
            send('[<a href="%s">cvsweb</a>]\n' % cooked_url, 10)
        
    send("</dl>", 4)
    send("<p>", 4)
    
    return


def modify_info(d_cvs):
    """Print info on modified files."""

    if not d_cvs.has_key("Modified-Files"):
        return

    if not d_cvs["Modified-Files"]:
        return
    
    send("<dl>\n  <dt>Modified files:\n", 4)

    # Find the module name(s)
    str_dir = d_cvs["Repository-Directory"]
    str_rep = d_cvs["Repository-Root"]
    str_rep_name = d_cvs["Repository"]
    rep_rel_path = str_dir[len(str_rep)+1:]
    mod_rel_path = string.join(string.split(rep_rel_path, "/")[1:], "/")
    
    for file in string.split(d_cvs["Modified-Files"]):
        full_path = os.path.join(str_dir, file)
        
        send('<dd>%s/%s\n' % (mod_rel_path, file), 6)
        cooked_url = "%s?file+%s" % (CVS2WEB_URL, urllib.quote(full_path))
        send('[<a href="%s">file</a>]\n' % cooked_url, 10)
        cooked_url = "%s?diff+%s" % (CVS2WEB_URL, urllib.quote(full_path))
        send('[<a href="%s">diff</a>]\n' % cooked_url, 10)
        cooked_url = "%s?log+%s" % (CVS2WEB_URL, urllib.quote(full_path))
        send('[<a href="%s">log</a>]\n' % cooked_url, 10)
        if VIEWVC_URL:
            cooked_url = "%s/%s/%s?%s" % \
                         (VIEWVC_URL,
                          urllib.quote(rep_rel_path),
                          urllib.quote(file),
                          urllib.quote("cvsroot="+str_rep_name))
            send('[<a href="%s">cvsweb</a>]\n' % cooked_url, 10)
        
    send("</dl>\n", 4)
    send("<p>\n", 4)
    
    return


def import_info(d_cvs):
    if not d_cvs.has_key("Imported-Files"):
        return

    if not d_cvs["Imported-Files"]:
        return

    # Find the repository details
    str_rep = d_cvs["Repository-Root"]
    str_rep_name = d_cvs["Repository"]
    
    send("<dl>\n  <dt>Imported files:\n", 4)

    for file in string.split(d_cvs["Imported-Files"]):
        full_path = os.path.join(str_rep, file)

        send('<dd>%s\n' % file, 6)
        cooked_url = "%s?file+%s" % (CVS2WEB_URL, urllib.quote(full_path))
        send('[<a href="%s">file</a>]\n' % cooked_url, 10)
        cooked_url = "%s?log+%s" % (CVS2WEB_URL, urllib.quote(full_path))
        send('[<a href="%s?log+%s">log</a>]\n' % cooked_url, 10)
        if VIEWVC_URL:
            cooked_url = "%s/%s?%s" % \
                         (VIEWVC_URL,
                          urllib.quote(file),
                          urllib.quote("cvsroot="+str_rep_name))
            send('[<a href="%s">cvsweb</a>]\n' % cooked_url, 10)

    send("</dl>\n", 4)
    send("<p>\n", 4)
    
    return


def remove_info(d_cvs):
    if not d_cvs.has_key("Removed-Files"):
        return

    if not d_cvs["Removed-Files"]:
        return
    
    send("<dl>\n  <dt>Removed files:\n", 4)

    for file in string.split(d_cvs["Removed-Files"]):
        send("<dd>%s\n" % file, 6)
        
    send("</dl>", 4)
    send("<p>", 4)
    
    return


#############################################################################

def file(str_file):
    """Return the full source of the named file."""

    send('Content-type: text/plain\n\n')

    try:
        os.system("cd /tmp; " + RCSPATH + "co %s,v" % str_file)
    
        f = open("/tmp/%s" % os.path.basename(str_file))
        s = f.read()
        f.close()

        if s:
            send(s)

        else:
            send("< zero length file >")
            
    finally:
        os.unlink("/tmp/%s" % os.path.basename(str_file))
        
    return


#############################################################################

def diff(str_file):
    """Return the diff between the current and last versions."""

    send('Content-type: text/plain\n\n')

    try:
        # Check out working file in /tmp
        os.system("cd /tmp; " + RCSPATH + "co %s,v" % str_file)

        # Run rlog to get latest version number
        p = os.popen(RCSPATH + "rlog %s" % str_file, "r")
        l = p.readlines()
        p.close()

        rev = l[3][6:-1]
        major, minor = string.split(rev, ".")
        prev = "%s.%s" % (major, str(string.atoi(minor) - 1))

        # Run rcsdiff
        pout, pin, perr = popen2.popen3("cd /tmp; " + RCSPATH + "rcsdiff -r%s -u %s,v 2>&1" % (prev, str_file))
        s = pout.read()
        pout.close()
        pin.close()
        perr.close()
        
        # Return output
        send(s)

    finally:
        # Remove checked out working file
        os.unlink("/tmp/%s" % os.path.basename(str_file))

    return


#############################################################################

def log(str_file):
    """Return the log for the file."""

    send('Content-type: text/plain\n\n')
    try:
        p = os.popen(RCSPATH + "rlog %s" % str_file, "r")
        s = p.read()
        p.close()

        send(s)

    finally:
        sys.exit(0)
        
    return


#############################################################################

def error(msg, e=None):
    """Print a HTML usage message."""
    
    send('Content-type: text/plain\n\n')
    send('cvs2web, v%s\n' % __version__)
    send('%s\n\n' % msg)

    send('Required arguments are ...\n')
    send('user  -- string user name\n')
    send('dict  -- pickled dictionary of parsed CVS log message\n\n')

    send('Traceback\n')
    if e:
        for s in traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback):
            send(s)

    return

        
#############################################################################

if __name__ == "__main__":

    # Check parameters
    if len(sys.argv) != 3:
        error("Not enough arguments: %d, %s" % (len(sys.argv), str(sys.argv)))
        sys.exit(0)

    # Process arguments
    user = sys.argv[1]

    if user == "log":
        log(sys.argv[2])
        sys.exit(0)

    elif user == "diff":
        diff(sys.argv[2])
        sys.exit(0)

    elif user == "file":
        file(sys.argv[2])
        sys.exit(0)

    elif user == "commit":
        pass

    else:
        try:
            raw_str = sys.argv[2]

            if raw_str[0] == "\\" or raw_str[0] == "%":
                # New-style escaping
                raw_str = urllib.unquote(raw_str)
                str_pkl = string.replace(raw_str, "\\", "")

            else:
                # Backward compatibility.  \x escapes are no-longer generated
                raw_str = string.replace(raw_str, r'\x0a', '\012')
                raw_str = string.replace(raw_str, r'\x3d', '=')
                raw_str = string.replace(raw_str, r'\x2b', '+')

                str_pkl = base64.decodestring(raw_str)

            # Unpack
            d_cvs = pickle.loads(str_pkl)

        except exceptions.Exception, e:
            error("URL decoding error", e)
            send('Pickle arg\n')
            send(sys.argv[2])
            sys.exit(0)

        # Start HTML output
        header()

        user_info(user, d_cvs)

        log_msg(d_cvs)

        import_info(d_cvs)
        add_info(d_cvs)
        remove_info(d_cvs)
        modify_info(d_cvs)
        
        end_body()
        sys.exit(0)

    
#############################################################################

