#!/usr/local/bin/python1.6
########################################################################
#
#              Tickertape
#              cvs loginfo producer
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/cvs2ticker.py,v $
# Version:     $RCSfile: cvs2ticker.py,v $ $Revision: 1.19 $
# Copyright:   (C) 1998-2000, David Leonard, Bill Segall & David Arnold.
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

cvs2ticker - pass CVS loginfo messages through to tickertape

"""
__author__ = 'David Leonard <david.leonard@dstc.edu.au>'
__version__ = "$Revision: 1.19 $"[11:-2]


########################################################################
########################################################################
#
#  CONFIGURATION SECTION
#

DEFAULT_GROUP = "CVS"
TIMEOUT       = 10
CVS2WEB_URL   = "http://internal.dstc.edu.au/cgi-bin/cvs2web.py"


#  end of configuration
########################################################################
########################################################################

import base64, os, pickle, sys, getopt, random, string, time
from elvin.client import ElvinClient
from elvin.sync import SyncLoop
from elvin.notification import Notification


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

def log_to_ticker(ticker_group, repository, rep_dir):
    """Generate a notification dictionary describing the CVS event.

    *ticker_group*  -- Tickertape group to notify
    *repository*    -- string repository name
    *rep_dir*       -- absolute path to repository
    Returns         -- dictionary for Elvin notification

    This is pretty ugly ... one day i should tidy up dl's old stuff.
    """

    #-- initialise parsed info
    d_notify = {}
    cur_section = None
    extratext = ""

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
            d_notify[cur_section] = d_notify[cur_section] + ' ' + string.strip(line)

        elif string.find(line, VENDOR_TAG) == 0:
            cur_section = None
            d_notify[VENDOR_KEY] = line[len(VENDOR_TAG)+1:]

        elif string.find(line, RELEASE_TAG) == 0:
            cur_section = None
            if not d_notify.has_key(RELEASE_TAG):
                d_notify[RELEASE_KEY] = line[len(RELEASE_TAG)+1:]
            else:
                d_notify[RELEASE_KEY] = d_notify[RELEASE_KEY] + " " + string.strip(line)
            
        elif cur_section == d_section[LOG_MESSAGE]:
            d_notify[cur_section] = d_notify[cur_section] + ' ' + line
        
        else:
            cur_section = None

            #-- process remaining lines
            if string.find(line, TEXT_INDIR) == 0:
                d_notify["Working-Directory"] = line[len(TEXT_INDIR):]

            elif string.find(line, TEXT_UPDATE) == 0:
                d_notify["Repository-Directory"] = line[len(TEXT_UPDATE):]

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

    #-- create tickertape message
    str_dir = d_notify["Repository-Directory"]
    rep_rel_path = str_dir[len(rep_dir)+1:]
    module = string.replace(string.split(rep_rel_path, "/")[0], '+', '%2b')

    msg = "In %s:" % module
    
    if d_notify[d_section[ADDED_FILES]]:
        msg = msg + " Added" + d_notify[d_section[ADDED_FILES]]
        
    if d_notify[d_section[REMOVED_FILES]]:
        msg = msg + " Removed" + d_notify[d_section[REMOVED_FILES]]

    if d_notify[d_section[MODIFIED_FILES]]:
        msg = msg + " Modified" + d_notify[d_section[MODIFIED_FILES]]

    if d_notify.has_key(IMPORTED_KEY):
        msg = msg + " Import"
        
    #-- the bill trap
    if not string.strip(d_notify[d_section[LOG_MESSAGE]]):
        d_notify[d_section[LOG_MESSAGE]] = "%s, the slack bastard, didn't supply " \
                                 "a log message." % user

    msg = msg + ':' + d_notify[d_section[LOG_MESSAGE]]

    #-- create attachment URL
    str_url = CVS2WEB_URL
    str_url = str_url + "?%s+%s" % (user, url_escape(pickle.dumps(d_notify)))

    #-- add tickertape-specific attributes
    d_notify.update({'TIMEOUT' : TIMEOUT,
            'TICKERTEXT' : msg,
            'TICKERTAPE' : ticker_group,
            'USER' : user,
                    'MIME_TYPE':   "x-elvin/url",
                    'MIME_ARGS':   str_url,
                    'Message-Id':  str(random.randint(1, 0x7ffffff))})
    return d_notify


def url_escape(s):
    """Escape characters in s for inclusion in an URL"""

    s = base64.encodestring(s)
    s = string.replace(s, '\012', r'\x0a')
    s = string.replace(s, '=', r'\x3d')
    s = string.replace(s, '+', r'\x2b')
    
    return s


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
    repository = None
    d_notify = None
    
    #-- check mandatory args
    if len(sys.argv) < 3:
        error_exit("Not enough arguments.")

    rep_dir = sys.argv[-1]
    
    #-- parse options
    try:
        (optlist,args) = getopt.getopt(sys.argv[1:-1], "e:g:n:")
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
                
    #-- set default option values
    if not group:
        group = DEFAULT_GROUP

    if not repository:
        repository = rep_dir
        
    c = ElvinClient(SyncLoop)
    e = c.connection()

    for url in urls:
        e.insert_server(0, url)
    e.open()

    #-- get user
    user = GetUserName()

    #-- parse log message
    d_notify = log_to_ticker(group, repository, rep_dir)
    if d_notify:
        e.notify(d_notify)

    sys.exit(0)


########################################################################
