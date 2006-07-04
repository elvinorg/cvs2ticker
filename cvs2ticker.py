#! /usr/bin/env python
########################################################################
# COPYRIGHT_BEGIN
#
#              Tickertape
#              cvs loginfo producer
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/cvs2ticker.py,v $
# Version:     $Id: cvs2ticker.py,v 1.39 2006/07/04 09:30:29 d Exp $
#
# Copyright    (C) 1998-2006 Mantara Software
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

cvs2ticker - pass CVS loginfo messages through to tickertape

"""
__author__ = 'ticker-user@tickertape.org'
__version__ = "$Revision: 1.39 $"[11:-2]


########################################################################
########################################################################
#
#  CONFIGURATION SECTION
#

DEFAULT_GROUP = "CVS"
TIMEOUT       = 10
CVS2WEB_URL   = "http://www.tickertape.org/cgi-bin/cvs2web.py"


#  end of configuration
########################################################################
########################################################################

import base64, os, pickle, sys, getopt, random, string, time, urllib
import elvin


########################################################################

LOG_MESSAGE    = 'Log Message:'
MODIFIED_FILES = 'Modified Files:'
ADDED_FILES    = 'Added Files:'
REMOVED_FILES  = 'Removed Files:'
TEXT_UPDATE    = 'Update of '
TEXT_INDIR     = 'In directory '

VENDOR_TAG     = 'Vendor Tag:'
VENDOR_KEY     = 'Vendor-Tag'
RELEASE_TAG    = 'Release Tags:'
RELEASE_KEY    = 'Release-Tags'
PLAIN_TAG      = '      Tag:'
PLAIN_KEY      = 'Tag'

TEXT_IMPORT    = 'cvs import:'
STATUS         = 'Status:'
IMPORTED_KEY   = 'Imported-Files'

d_section     = {LOG_MESSAGE:    "Log-Message",
                 MODIFIED_FILES: "Modified-Files", 
                 ADDED_FILES:    "Added-Files",
                 REMOVED_FILES:  "Removed-Files",
                 STATUS:         "Status",
                 }

USAGE = "Usage: %s [options] path\n" \
        "[-e elvin-url]  Elvin server if you want to be spcific\n" \
        "[-g group]      Tickertape group for notifications\n" \
        "[-r group]      Tickertape group responses should go to\n" \
        "[-n name]       friendly name for the repository\n" \
        "path            absolute path to repository files\n"


########################################################################

def GetUserName():
    """Find and return the user name

    Raises Exc_noname"""

    if os.environ.has_key('LOGNAME'):
        user = os.environ['LOGNAME']
    elif os.environ.has_key('USER'):
        user = os.environ['USER']
    else:
        raise Exc_noname, "Can't get user name"

    return user


def log_to_ticker(ticker_group, reply_group, repository, rep_dir, bastard):
    """Generate a notification dictionary describing the CVS event.

    *ticker_group*  -- Tickertape group to notify
    *reply_group*   -- Tickertape group replies should go to
    *repository*    -- string repository name
    *rep_dir*       -- absolute path to repository
    Returns         -- dictionary for Elvin notification

    This is pretty ugly ... one day i should tidy up dl's old stuff.
    """

    #-- initialise parsed info
    d_notify = {}
    cur_section = None
    extratext = ""
    found_files = 0    # whether there have been any added/removed/etc

    for key in d_section.values():
        d_notify[key] = ""

    #-- read and process log message
    lines = sys.stdin.readlines()
    for line in lines:

        #-- remove trailing newline
        if line[-1] == "\n":
            line = line[:-1]

        #-- skip blank lines
        if not string.strip(line):
            continue

        if line in d_section.keys():
            #-- handle multi-line sections
            cur_section = d_section[line]

        elif line[0] == "\t":
            found_files = 1
            d_notify[cur_section] = d_notify[cur_section] + ' ' + string.strip(line)

        elif string.find(line, VENDOR_TAG) == 0:
            cur_section = None
            d_notify[VENDOR_KEY] = line[len(VENDOR_TAG)+1:]

        elif string.find(line, RELEASE_TAG) == 0:
            cur_section = None
            if not d_notify.has_key(RELEASE_KEY):
                d_notify[RELEASE_KEY] = string.strip(line[len(RELEASE_TAG)+1:])
            else:
                d_notify[RELEASE_KEY] = d_notify[RELEASE_KEY] + ' ' + string.strip(line[len(PLAIN_TAG)+1:])
        elif string.find(line, PLAIN_TAG) == 0:
            if not d_notify.has_key(PLAIN_KEY):
                d_notify[PLAIN_KEY] = string.strip(line[len(PLAIN_TAG)+1:])
            else:
                d_notify[PLAIN_KEY] = d_notify[PLAIN_KEY] + ', ' + string.strip(line[len(PLAIN_TAG)+1:])
        elif cur_section == d_section[LOG_MESSAGE]:
            d_notify[cur_section] = d_notify[cur_section] + ' ' + line

        else:
            cur_section = None

            #-- process remaining lines
            if string.find(line, TEXT_INDIR) == 0:
                d_notify["Working-Directory"] = line[len(TEXT_INDIR):]

            elif string.find(line, TEXT_UPDATE) == 0:
                d_notify["Repository-Directory"] = os.path.normpath(line[len(TEXT_UPDATE):])

            elif line[0:2] == "N ":
                if not d_notify.has_key(IMPORTED_KEY):
                    d_notify[IMPORTED_KEY] = line[2:]
                else:
                    d_notify[IMPORTED_KEY] = d_notify[IMPORTED_KEY] + ' ' + line[2:]

            elif line[0:2] == "I ":
                #-- ignore these, since CVS does ...
                pass

            else:
                extratext = extratext + ' ' + line

    #-- add non-parsed text
    d_notify["Extras"] = extratext
    d_notify["Original"] = reduce(lambda s,e: s+e, lines, "")
    d_notify["Repository"] = repository
    d_notify["Repository-Root"] = rep_dir
    str_dir = d_notify["Repository-Directory"]
    rep_rel_path = str_dir[len(rep_dir)+1:]
    module = string.replace(string.split(rep_rel_path, "/")[0], '+', '%2b')
    d_notify["Relative-Directory"] = rep_rel_path
    d_notify["Module"] = module

    #-- create tickertape message
    msg = "In %s:" % rep_rel_path

    if d_notify[d_section[ADDED_FILES]]:
        msg = msg + " Added" + d_notify[d_section[ADDED_FILES]]

    if d_notify[d_section[REMOVED_FILES]]:
        msg = msg + " Removed" + d_notify[d_section[REMOVED_FILES]]

    if d_notify[d_section[MODIFIED_FILES]]:
        msg = msg + " Modified" + d_notify[d_section[MODIFIED_FILES]]

    if d_notify.has_key(IMPORTED_KEY):
        msg = msg + " Import"

    if d_notify.has_key(PLAIN_KEY):
        msg = msg + " (tag " + d_notify[PLAIN_KEY] + ")"

    #-- the bill trap
    if bastard:
        if not string.strip(d_notify[d_section[LOG_MESSAGE]]):
            d_notify[d_section[LOG_MESSAGE]] = "%s, the slack bastard, didn't supply a log message." % user

    if found_files:
        msg = msg + ':' + d_notify[d_section[LOG_MESSAGE]]
    else:
        msg = msg + d_notify[d_section[LOG_MESSAGE]]

    #-- create attachment URL
    str_url = CVS2WEB_URL
    str_url = str_url + "?%s+%s" % (user, urllib.quote(pickle.dumps(d_notify)))

    #-- add tickertape-specific attributes
    d_notify.update({'TIMEOUT' : TIMEOUT,
                     'TICKERTEXT' : msg,
                     'TICKERTAPE' : ticker_group,
                     'USER' : user,
                     'MIME_TYPE':   "x-elvin/url",
                     'MIME_ARGS':   str_url,
                     'Message-Id':  str(random.randint(1, 0x7ffffff))})

    #-- add v3 tickertape attributes
    d_notify.update({'Timeout': d_notify['TIMEOUT'] * 60,
                     'Message': d_notify['TICKERTEXT'],
                     'Group': d_notify['TICKERTAPE'],
                     'From': d_notify['USER']})

    if reply_group:
        d_notify['Reply-To'] = reply_group;

    d_notify['Attachment'] = 'MIME-Version: 1.0\r\n' \
                             'Content-Type: text/uri-list\r\n' \
                             '\r\n' \
                             '%s\r\n' % str_url
    return d_notify


def error_exit(msg):
    """Print error message and exit."""

    #-- get executable name
    progname = os.path.basename(sys.argv[0])

    #-- message
    sys.stderr.write(USAGE % progname)
    sys.stderr.write("\n%s\n\n" % msg)

    #-- quit
    sys.exit(1)


########################################################################

if __name__ == '__main__':

    #-- initialise
    urls = []
    group = None
    reply_group = None
    repository = None
    d_notify = None
    bastard = 1

    #-- check mandatory args
    if len(sys.argv) < 3:
        error_exit("Not enough arguments.")

    rep_dir = sys.argv[-1]

    #-- parse options
    try:
        (optlist,args) = getopt.getopt(sys.argv[1:-1], "e:g:n:r:b")
    except:
        error_exit("Failed to process the arglist: %s" % str(sys.argv[1:-1]))

    for (opt, arg) in optlist:
        if opt == '-e':
            urls.append(arg)

        if opt == '-g':
            if not group:
                group = arg
            else:
                error_exit("Only one group specification allowed.")

        if opt == '-n':
            if not repository:
                repository = arg
            else:
                error_exit("Only one name specification allowed.")

        if opt == '-r':
            if not reply_group:
                reply_group = arg
            else:
                error_exit("Only one reply group specification allowed.")

        if opt == '-b':
            bastard = 0

    #-- set default option values
    if not group:
        group = DEFAULT_GROUP

    if not repository:
        repository = rep_dir

    c = elvin.client()
    e = c.connection()

    for url in urls:
        e.append_url(url)
        e.set_discovery(0)
    else:
        e.set_discovery(1)

    e.open()

    #-- get user
    user = GetUserName()

    #-- parse log message
    d_notify = log_to_ticker(group, reply_group, repository, rep_dir, bastard)
    if d_notify:
        e.notify(d_notify)

    sys.exit(0)


########################################################################
