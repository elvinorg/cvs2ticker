#! /usr/bin/python
########################################################################
# COPYRIGHT_BEGIN
#
#              Tickertape
#              cvs loginfo producer
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/cvs2ticker.py,v $
# Version:     $Id: cvs2ticker.py,v 1.42 2006/09/30 03:10:58 d Exp $
#
# Copyright    (C) 1998-1999 David Leonard
# Copyright    (C) 1998-2006 Mantara Software
# Copyright    (C) 2006 David Arnold, Ian Lister, Bill Segall
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
__version__ = "$Revision: 1.42 $"[11:-2]


########################################################################

import base64, getopt, os, pickle, sha, string, sys, time, urllib
import elvin

VERSION = "1.5.0"

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

########################################################################

def log_to_ticker(**config):
    """Generate a notification dictionary describing the CVS event.

    *config*  -- keyword arguments.  See below.
    Returns   -- dictionary for Elvin notification

    Keyword arguments:
      user            -- User's login name
      group           -- Tickertape group for postings
      reply_to        -- Tickertape group for replies
      repository      -- Repository name
      repository_path -- Absolute path of repository root directory
      nag             -- Nag about empty log messages

    FIXME: This is ugly ... one day i should tidy up dl's old stuff.
    """

    # Initialise parsed info
    d_notify = {}
    cur_section = None
    extratext = ""
    found_files = 0    # whether there have been any added/removed/etc
    user = config["user"]

    for key in d_section.values():
        d_notify[key] = ""

    # Read and process log message
    lines = sys.stdin.readlines()
    for line in lines:

        # Remove trailing newline
        if line[-1] == "\n":
            line = line[:-1]

        # Skip blank lines
        if not string.strip(line):
            continue

        if line in d_section.keys():
            # Handle multi-line sections
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

            # Process remaining lines
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
                # Ignore these, since CVS does ...
                pass

            else:
                extratext = extratext + ' ' + line

    # Add non-parsed text
    d_notify["Extras"] = extratext
    d_notify["Original"] = reduce(lambda s,e: s+e, lines, "")
    d_notify["Repository"] = config["repository"]
    d_notify["Repository-Root"] = config["repository_path"]
    str_dir = d_notify["Repository-Directory"]
    rep_rel_path = str_dir[len(config["repository_path"]):]
    module = string.replace(string.split(rep_rel_path, "/")[0], '+', '%2b')
    d_notify["Relative-Directory"] = rep_rel_path
    d_notify["Module"] = module

    # Generate Message-Id
    hasher = sha.new()
    hasher.update(str(time.time()))
    hasher.update(str(d_notify))
    msg_id = hasher.hexdigest()

    # Create tickertape message
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

    # The bill trap
    if config["nag"]:
        if not string.strip(d_notify[d_section[LOG_MESSAGE]]):
            d_notify[d_section[LOG_MESSAGE]] = "%s, the slack bastard, didn't supply a log message." % user

    if found_files:
        msg = msg + ':' + d_notify[d_section[LOG_MESSAGE]]
    else:
        msg = msg + d_notify[d_section[LOG_MESSAGE]]

    # Create attachment URL
    str_url = config["cvs2web_url"]
    str_url = str_url + "?%s+%s" % (user, urllib.quote(pickle.dumps(d_notify)))

    # Add tickertape-specific attributes
    d_notify.update({'TIMEOUT' : int(config["timeout"]),
                     'TICKERTEXT' : msg,
                     'TICKERTAPE' : config["group"],
                     'USER' : user,
                     'MIME_TYPE':   "x-elvin/url",
                     'MIME_ARGS':   str_url,
                     'Message-Id': msg_id})

    # Add v3 tickertape attributes
    d_notify.update({'Timeout': d_notify['TIMEOUT'] * 60,
                     'Message': d_notify['TICKERTEXT'],
                     'Group': d_notify['TICKERTAPE'],
                     'From': d_notify['USER']})

    if config.has_key("reply_to"):
        d_notify['Reply-To'] = config["reply_to"]

    d_notify['Attachment'] = 'MIME-Version: 1.0\r\n' \
                             'Content-Type: text/uri-list\r\n' \
                             '\r\n' \
                             '%s\r\n' % str_url
    return d_notify


def usage(msg=None):
    """Print error and usage message."""

    # Get executable name
    progname = os.path.basename(sys.argv[0])

    # Message
    if msg:
        sys.stderr.write("%s\n" % msg)

    sys.stderr.write("Usage: %s -f config_file\n" % progname)

    return


def read_config(path):
    """Parse configuration file."""

    d = {}

    try:
        f = open(path)
        lines = f.readlines()
        f.close()
    except:
        return
    
    for line in lines:

        line = line.strip()

        if len(line) == 0 or line[0] == "#":
            continue

        if line.find("=") == -1:
            return

        key, value = line.split("=", 1)

        d[key.strip()] = value.strip()

    return d


########################################################################

if __name__ == '__main__':

    # Initialise
    config_path = ""

    # Parse options
    try:
        (optlist,args) = getopt.getopt(sys.argv[1:], "f:hHv")
    except:
        usage("Failed to process the arglist: %s" % str(sys.argv[1:]))
        sys.exit(1)

    for (opt, arg) in optlist:
        if opt == '-f':
            config_path = arg

        if opt in ['-h', '-H', '-?']:
            usage()
            sys.exit(0)

        if opt == '-v':
            print VERSION
            sys.exit(0)

    # Read config file
    if not config_path:
        usage("Missing required option -f")
        sys.exit(1)

    config = read_config(config_path)
    if not config:
        usage("Error reading config file")
        sys.exit(1)

    # Get user name
    if os.environ.has_key('LOGNAME'):
        config["user"] = os.environ['LOGNAME']
    elif os.environ.has_key('USER'):
        config["user"] = os.environ['USER']
    else:
        usage("Error: cannot determine user name")
        sys.exit(1)

    # Parse message and send notification
    d_notify = log_to_ticker(**config)
    if not d_notify:
        usage("Error: failed to generate notification")
        sys.exit(1)

    # Connect to Elvin
    c = elvin.client()
    e = c.connection()

    if config["elvin_url"]:
        e.append_url(config["elvin_url"])
        e.set_discovery(0)
    else:
        e.set_discovery(1)

    e.open()

    # Send notification
    e.notify(d_notify)

    # Exit
    e.close()
    sys.exit(0)


########################################################################
