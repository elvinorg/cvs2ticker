#! /usr/bin/env python
########################################################################
#
#              Tickertape
#              cvs loginfo producer
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/cvs2ticker.py,v $
# Version:     $RCSfile: cvs2ticker.py,v $ $Revision: 1.8 $
# Copyright:   (C) 1998-1999, David Leonard, Bill Segall & David Arnold.
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

To enable this you should 'cvs co CVSROOT' then add the following line
to the file named 'loginfo':
   	
	ALL	<path>/cvs2ticker %s [-g group]

Then update your ~/.ticker/groups file to include the group which
defaults to 'CVS', and all CVS updates will scroll by thereafter.

"""
__author__ = 'David Leonard <david.leonard@dstc.edu.au>'
__version__ = "$Revision: 1.8 $"[11:-2]


########################################################################

import Elvin, ElvinMisc
import base64, os, pickle, sys, getopt, random, string, time


########################################################################

DEFAULT_GROUP = 'CVS'
TIMEOUT = 10

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



########################################################################

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
    d_notify["Original"] = str(lines)
    d_notify["Repository"] = repository
    d_notify["Repository-Root"] = rep_dir

    #-- create tickertape message
    str_dir = d_notify["Repository-Directory"]
    rep_rel_path = str_dir[len(rep_dir)+1:]
    module = string.split(rep_rel_path, "/")[0]

    msg = "In %s:" % module
    
    if d_notify[d_section[ADDED_FILES]]:
	msg = msg + " Added " + d_notify[d_section[ADDED_FILES]]
        
    if d_notify[d_section[REMOVED_FILES]]:
	msg = msg + " Removed " + d_notify[d_section[REMOVED_FILES]]

    if d_notify[d_section[MODIFIED_FILES]]:
	msg = msg + " Modified " + d_notify[d_section[MODIFIED_FILES]]

    if d_notify.has_key(IMPORTED_KEY):
        msg = msg + " Import"
        
    #-- the bill trap
    if not string.strip(string.replace(d_section[LOG_MESSAGE], "\n", " ")):
        d_section[LOG_MESSAGE] = "%s, the slack bastard, didn't supply " \
                            "a log message." % user

    msg = msg + ':' + d_notify[d_section[LOG_MESSAGE]]

    #-- create attachment URL
    str_url = "http://internal.dstc.edu.au/cgi-bin/cvs2web.py"
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


########################################################################

if __name__ == '__main__':

    #-- parse commandline args
    progname = os.path.basename(sys.argv[0])
    Usage = "Usage: %s options\n" \
	    "[-d directory]  absolute path to CVS repository\n" \
	    "[-h host]       hostname for Elvin server (default elvin)\n" \
	    "[-p port]       port number for Elvin server (default 5678)\n" \
	    "[-g group]      Tickertape group for notifications\n" \
	    "[-r repository] name of repository\n" % progname

    # Parse the args to get the optional host and port, then connect to Elvin
    rep_dirs = []
    ports = []
    hosts = []
    groups = []
    repositories = []
    rep_dir = None
    host = None
    port = None
    group = None
    repository = None
    
    try:
	(optlist,args) = getopt.getopt(sys.argv[1:], "d:p:h:g:r:")
    except:
        sys.stderr.write(Usage + "Failed to process the arglist\n")
	# print optlist, args - fixme: optlist and args not defined here?
        # wotcha up to davey?? (br) 
	sys.exit(1)
    else:
	for (opt, arg) in optlist:
	    if opt == '-d':
		rep_dirs.append(arg)
	    if opt == '-h':
		hosts.append(arg)
	    if opt == '-p':
		ports.append(arg)
	    if opt == '-g':
		groups.append(arg)
	    if opt == '-r':
		repositories.append(arg)

	if len(rep_dirs) == 1:
	    rep_dir = rep_dirs[0]
	elif len(rep_dirs) > 1:
	    sys.stderr.write(Usage + "Can only specify one repository directory\n")
	    sys.exit(1)
	else:
	    rep_dir = "/projects/elvin/CVS"

	if len(hosts) == 1:
	    host = hosts[0]
	elif len(hosts) > 1:
	    sys.stderr.write(Usage + "Can only specify one elvin host\n")
	    sys.exit(1)

	if len(groups) == 0:
	    group = DEFAULT_GROUP
	if len(groups) == 1:
	    group = groups[0]
	elif len(groups) > 1:
	    sys.stderr.write(Usage + "Can only specify one group\n")
	    sys.exit(1)

	if len(ports) == 1:
	    try:
		port = string.atoi(ports[0])
	    except:
		sys.stderr.write(Usage + "Port must be numeric\n")
		sys.exit(1)
	    else:
		if port < 0:
		    sys.stderr.write(Usage + "Port must be positive\n")
		    sys.exit(1)
	elif len(ports) > 1:
	    sys.stderr.write(Usage + "Can only specify one elvin port\n")
	    sys.exit(1)

	if len(repositories) == 1:
	    repository = repositories[0]
	elif len(repositories) == 0:
	    repository = "elvin"
	else:
	    sys.stderr.write(Usage + "Must specify only one repository name\n")
	    sys.exit(1)

    # Fix the host and port to something useful if they didn't tell us
    (host, port) = ElvinMisc.HostAndPort(host, port)
    try:
	e = Elvin.Elvin(Elvin.EC_NAMEDHOST, host, port)
    except:
	sys.stderr.write("Unable to connect to Elvin at %s:%d\n" % (host, port))
	sys.exit(1)

    user = ElvinMisc.GetUserName()

    #-- parse log message
    d_notify = log_to_ticker(group, repository, rep_dir)
    if d_notify:
        e.notify(d_notify)

    sys.exit(0)


########################################################################
