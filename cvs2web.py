#! /usr/local/dstc/alpha-dec-osfV4.0/bin/python
#############################################################################
#
#              Tickertape
#              CGI script for cvs2ticker URLs
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/cvs2web.py,v $
# Version:     $RCSfile: cvs2web.py,v $ $Revision: 1.4 $
# Copyright:   (C) 1999, David Arnold.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
########################################################################
"""

this file is a CGI script which produces a download request page for a
package.  it is generic, in that it takes a number of parameters
supplying the package name, available formats, etc etc

"""
__author__  = "David Arnold <davida@pobox.com>"
__version__ = "$Revision: 1.4 $"[11:-2]


#############################################################################

import base64, cgi, os, pickle, popen2, regsub, string, sys, time


#############################################################################

def send(txt, indent=0):
    """Write text to output."""
    
    #-- create indent string
    str_indent = " " * indent

    #-- insert indent after carriage returns
    txt = regsub.gsub("\n\(.\)", "\n%s\\1" % str_indent, txt)

    #-- write
    sys.stdout.write("%s%s" % (str_indent, txt))
    
    return


def wrap(s, width=60):
    """Return the string with long strings wrapped."""

    res = ""
    
    #-- separate into paragraphs
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

    #-- get the name of the person?
    logname = "cvs%20user"

    #-- determine module name (from working & repository paths)
    module = "elvin"
    
    send('<tt><b>cvs commit</b></tt> by %s' % user, 4)
    send(' [<a href="mailto:%s@dstc.edu.au">mail</a>]' % user, 4)
    send(' [<a href="/cgi-bin/ticker.py?%s+10+%s+%s+CVS">ticker</a>]<p>\n' % \
         (logname, user, module), 4)
    
    return


def log_msg(d_cvs):
    if not d_cvs.has_key("Log-Message"):
        return

    send('<table align="center" width="90%">\n', 4)
    send('<tr>\n', 6)
    send('<td bgcolor="#c0c0c0">\n', 8)
    send("<pre>\n\n", 10)
    send(wrap(d_cvs["Log-Message"]))
    send("\n  </pre>\n", 10)
    send("    </td>\n  </tr>\n</table>", 4)
    return


def add_info(d_cvs):

    if not d_cvs.has_key("Added-Files"):
        return

    if not d_cvs["Added-Files"]:
        return
    
    send("<dl>\n  <dt>Added files:\n", 4)

    str_dir = d_cvs["Repository-Directory"]
    str_module = os.path.basename(str_dir)
    
    for file in string.split(d_cvs["Added-Files"]):
        full_path = os.path.join(str_dir, file)
        
        send("<dd>%s" % file)
        send(' [<a href="/cgi-bin/cvs2web.py?file+%s">file</a>]' % full_path, 6)
        send(' [<a href="/cgi-bin/cvsweb.cgi/%s/%s">cvsweb</a>]' % (str_module, file), 6)
        
    send("</dl>", 4)
    send("<p>", 4)
    
    return


def modify_info(d_cvs):
    if not d_cvs.has_key("Modified-Files"):
        return

    if not d_cvs["Modified-Files"]:
        return
    
    send("<dl>\n  <dt>Modified files:\n", 4)

    str_dir = d_cvs["Repository-Directory"]
    str_module = os.path.basename(str_dir)
    
    for file in string.split(d_cvs["Modified-Files"]):
        full_path = os.path.join(str_dir, file)
        
        send('<dd>%s' % file, 6)
        send(' [<a href="/cgi-bin/cvs2web.py?file+%s">file</a>]' % full_path, 6)
        send(' [<a href="/cgi-bin/cvs2web.py?diff+%s">diff</a>]' % full_path, 6)
        send(' [<a href="/cgi-bin/cvs2web.py?log+%s">log</a>]' % full_path, 6)
        send(' [<a href="/cgi-bin/cvsweb.cgi/%s/%s">cvsweb</a>]' % (str_module, file), 6)
        
    send("\n</dl>\n", 4)
    send("<p>\n", 4)
    
    return


def import_info(d_cvs):
    if not d_cvs.has_key("Imported-Files"):
        return

    if not d_cvs["Imported-Files"]:
        return

    str_dir = os.path.dirname(d_cvs["Repository-Directory"])
    send("<dl>\n  <dt>Imported files:\n", 4)

    for file in string.split(d_cvs["Imported-Files"]):
        full_path = os.path.join(str_dir, file)

        send('<dd>%s' % file, 6)
        send(' [<a href="/cgi-bin/cvs2web.py?file+%s">file</a>]' %full_path, 6)
        send(' [<a href="/cgi-bin/cvs2web.py?log+%s">log</a>]' %full_path, 6)
        send(' [<a href="/cgi-bin/cvsweb.cgi/%s">cvsweb</a>]' %file, 6)

    send("\n</dl>\n", 4)
    send("<p>\n", 4)
    
    return


def remove_info(d_cvs):
    if not d_cvs.has_key("Removed-Files"):
        return

    if not d_cvs["Removed-Files"]:
        return
    
    send("<dl>\n  <dt>Removed files:\n", 4)

    for file in string.split(d_cvs["Removed-Files"]):
        send("<dd>%s\n" % file)
        
    send("</dl>", 4)
    send("<p>", 4)
    
    return


#############################################################################

def file(str_file):
    """Return the full source of the named file."""

    send('Content-type: text/plain\n\n')

    try:
        os.system("cd /tmp; /usr/local/bin/co %s,v" % str_file)
    
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
        #-- check out working file in /tmp
        os.system("cd /tmp; /usr/local/bin/co %s,v" % str_file)

        #-- run rlog to get latest version number
        p = os.popen("/usr/local/bin/rlog %s" % str_file, "r")
        l = p.readlines()
        p.close()

        rev = l[3][6:-1]
        major, minor = string.split(rev, ".")
        prev = "%s.%s" % (major, str(string.atoi(minor) - 1))

        #-- run rcsdiff
        pout, pin, perr = popen2.popen3("cd /tmp; /usr/local/bin/rcsdiff -u -r%s %s,v 2>&1" % (prev, str_file))
        s = pout.read()
        pout.close()
        pin.close()
        perr.close()
        
        #-- return output
        send(s)

    finally:
        #-- remove checked out working file
        os.unlink("/tmp/%s" % os.path.basename(str_file))

    return


#############################################################################

def log(str_file):
    """Return the log for the file."""

    send('Content-type: text/plain\n\n')
    try:
        p = os.popen("/usr/local/bin/rlog %s" % str_file, "r")
        s = p.read()
        p.close()

        send(s)

    finally:
        sys.exit(0)
        
    return


#############################################################################

def error(msg):
    """Print a HTML usage message."""
    
    send('Content-type: text/plain\n\n')
    send('cvs2web, v%s\n' % __version__)
    send('%s\n\n' % msg)

    send('Required arguments are ...\n')
    send('user  -- string user name\n')
    send('dict  -- pickled dictionary of parsed CVS log message\n\n')

    return

        
#############################################################################

if __name__ == "__main__":

    #-- check parameters
    if len(sys.argv) != 3:
        error("Not enough arguments: %d, %s" % (len(sys.argv), str(sys.argv)))
        sys.exit(0)

    #-- process arguments
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
            raw_str = string.replace(sys.argv[2], r'\x0a', '\012')
            raw_str = string.replace(raw_str, r'\x3d', '=')
            raw_str = string.replace(raw_str, r'\x2b', '+')
            str_pkl = base64.decodestring(raw_str)
            d_cvs = pickle.loads(str_pkl)

        except:
            error("UnPickling error")
            sys.exit(0)

        #-- start HTML output
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

