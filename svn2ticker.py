#! /usr/bin/env python
########################################################################
# COPYRIGHT_BEGIN
#
#              Tickertape
#              Subversion post-commit producer
#
# File:        $Source: /home/d/work/personal/ticker-cvs/cvs2ticker/svn2ticker.py,v $
# Version:     $Id: svn2ticker.py,v 1.6 2006/11/09 22:01:03 ilister Exp $
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

svn2ticker - send a Tickertape notification describing a commit to a
Subversion repository.

"""
__author__ = "ticker-user@tickertape.org"
__version__ = "$Revision: 1.6 $"[11:-2]


########################################################################

import ConfigParser
import optparse
import os
import os.path
import random
import sha
import socket
import string
import sys
import time
import urllib

import svn.fs
import svn.delta
import svn.repos
import svn.core

import elvin

VERSION = "1.0.0"

########################################################################

COMMAND_COMMIT          = "commit"
COMMAND_REVPROPCHANGE      = "revpropchange"
COMMAND_LOCK            = "lock"
COMMAND_UNLOCK          = "unlock"

REVPROPACTION_ADD       = "A"
REVPROPACTION_MOD       = "M"
REVPROPACTION_DEL       = "D"

CONFIG_ELVIN_URL        = "elvin_url"
CONFIG_NAG              = "nag"
CONFIG_GROUP            = "group"
CONFIG_TIMEOUT          = "timeout"
CONFIG_REPLY_TO         = "reply_to"
CONFIG_VIEWVC_URL       = "viewvc_url"
CONFIG_REPOSITORY_NAME  = "repository"

ATTR_LOG_MESSAGE        = "Log-Message"
ATTR_REPOSITORY_PATH    = "Repository-Path"
ATTR_REPOSITORY_HOST    = "Repository-Host"
ATTR_REPOSITORY_NAME    = "Repository-Name"
ATTR_REVISION           = "Revision"
ATTR_ADDED_FILES        = "Added-Files"
ATTR_MODIFIED_FILES     = "Modified-Files"
ATTR_REMOVED_FILES      = "Removed-Files"
ATTR_MOVED_FILES        = "Moved-Files"
ATTR_LOCKED_FILES       = "Locked-Files"
ATTR_UNLOCKED_FILES     = "Unlocked-Files"
ATTR_FROM_V1            = "USER"
ATTR_FROM_V3            = "From"
ATTR_MESSAGE_V1         = "TICKERTEXT"
ATTR_MESSAGE_V3         = "Message"
ATTR_TIMEOUT_V1         = "TIMEOUT"
ATTR_TIMEOUT_V3         = "Timeout"
ATTR_GROUP_V1           = "TICKERTAPE"
ATTR_GROUP_V3           = "Group"
ATTR_MESSAGE_ID         = "Message-Id"
ATTR_REPLACEMENT_ID     = "Replacement-Id"
ATTR_REPLY_TO           = "Reply-To"
ATTR_IN_REPLY_TO        = "In-Reply-To"
ATTR_MIME_TYPE          = "MIME_TYPE"
ATTR_MIME_ARGS          = "MIME_ARGS"
ATTR_ATTACHMENT         = "Attachment"

########################################################################

def ticker_nfn(user, message, message_id,
               replacement_id=None, in_reply_to=None, url=None):
    """ Construct a Tickertape notification. """
    nfn = elvin.message()

    # Basic v1 attributes
    nfn.update({ATTR_MESSAGE_V1: message,
                ATTR_GROUP_V1: config.get(CONFIG_GROUP, "svn"),
                ATTR_FROM_V1: user,
                ATTR_MESSAGE_ID: message_id})

    # Add v3 tickertape attributes
    nfn.update({ATTR_MESSAGE_V3: nfn[ATTR_MESSAGE_V1],
                ATTR_GROUP_V3: nfn[ATTR_GROUP_V1],
                ATTR_FROM_V3: nfn[ATTR_FROM_V1]})

    # Optional attributes
    if config.has_key(CONFIG_REPLY_TO):
        nfn[ATTR_REPLY_TO] = config[CONFIG_REPLY_TO]
    if config.has_key(CONFIG_TIMEOUT):
        nfn[ATTR_TIMEOUT_V1] = int(config[CONFIG_TIMEOUT]) / 60
        nfn[ATTR_TIMEOUT_V3] = int(config[CONFIG_TIMEOUT])
    if replacement_id:
        nfn[ATTR_REPLACEMENT_ID] = replacement_id
    if in_reply_to:
        nfn[ATTR_IN_REPLY_TO] = in_reply_to
    if url:
        nfn.update({ATTR_MIME_TYPE: "x-elvin/url",
                    ATTR_MIME_ARGS: url,
                    ATTR_ATTACHMENT: "MIME-Version: 1.0\r\n" \
                        "Content-Type: text/uri-list\r\n" \
                        "\r\n" \
                        "%s\r\n" % url})
    return nfn

def commit_nfn(repository, revision, config):
    """ Construct a notification describing the Subversion commit."""

    nfn = elvin.message()
    hostname = socket.gethostname()
    added_files = []
    modified_files = []
    removed_files = []
    moved_files = []

    # Get access to the repository
    repos = svn.repos.open(repository)
    fs = svn.repos.fs(repos)
    root = svn.fs.revision_root(fs, revision)

    # Look up some information about this revision
    author = svn.fs.revision_prop(fs, revision,
                                  svn.core.SVN_PROP_REVISION_AUTHOR)
    revision_date = svn.fs.revision_prop(fs, revision,
                                         svn.core.SVN_PROP_REVISION_DATE)
    log_message = svn.fs.revision_prop(fs, revision,
                                       svn.core.SVN_PROP_REVISION_LOG)

    # Collect all the changes made in the revision
    editor = svn.repos.ChangeCollector(fs, root)
    ptr, baton = svn.delta.make_editor(editor)
    svn.repos.replay(root, ptr, baton)
    changes = editor.get_changes()
    changelist = changes.items()
    changelist.sort()

    # Traverse the changes, gathering information
    assert len(changelist) > 0
    common_path = os.path.dirname(changelist[0][0])
    common_dirs = common_path.split(os.sep)
    for path, change in changelist:
        # Update the longest common path
        dirs = os.path.dirname(path).split(os.sep)
        new_common = []
        while len(common_dirs) > 0 and len(dirs) > 0 \
                  and common_dirs[0] == dirs[0]:
            new_common.append(common_dirs[0])
            common_dirs = common_dirs[1:]
            dirs = dirs[1:]
        common_dirs = new_common

        # Normalise the old path, which for moved files has a leading
        # slash for some reason
        if change.base_path and change.base_path[:len(os.sep)] == os.sep:
            real_base = change.base_path[len(os.sep):]
        else:
            real_base = change.base_path

        # Work out what happened to this object
        if change.added and change.base_path and \
               changes.has_key(real_base) and not changes[real_base].path:
            # Added based on an old file that has been removed i.e. moved
            moved_files.append(real_base)

            # If we've already seen that the old file has been
            # removed, forget that
            if real_base in removed_files:
                removed_files.remove(real_base)

            # Look for any modifications in addition to the move
            if change.text_changed or change.prop_changes:
                modified_files.append(path)
        elif change.added:
            # Added (or copied)
            added_files.append(path)
        elif not change.path:
            # File no longer exists. Assume it has been removed unless
            # we can see it has been moved elsewhere.
            if path not in moved_files:
                removed_files.append(path)
        else:
            modified_files.append(path)

    # Create tickertape message
    if common_path:
        msg = "In %s:" % common_path
    else:
        msg = "In root:"

    common_path = os.path.join("", *common_dirs)
    if common_path:
        common_str = common_path + os.sep
    else:
        common_str = ""
    drop_common = lambda path: path[len(common_str):]

    # Construct strings listing affected files
    if added_files:
        nfn[ATTR_ADDED_FILES] = " ".join(added_files)
        msg = msg + " Added " + " ".join(map(drop_common, added_files))
    if removed_files:
        nfn[ATTR_REMOVED_FILES] = " ".join(removed_files)
        msg = msg + " Removed " + " ".join(map(drop_common, removed_files))
    if moved_files:
        nfn[ATTR_MOVED_FILES] = " ".join(moved_files)
        msg = msg + " Moved " + " ".join(map(drop_common, moved_files))
    if modified_files:
        nfn[ATTR_MODIFIED_FILES] = " ".join(modified_files)
        msg = msg + " Modified " + " ".join(map(drop_common, modified_files))

    # The bill trap
    if config.get(CONFIG_NAG) and not log_message.strip():
        msg += ": %s, the slack bastard, didn't supply a log message." % author
    else:
        msg += ": " + log_message.strip().replace(os.linesep, " ")

    # Add extra Subversion-specific information about the event
    nfn[ATTR_LOG_MESSAGE] = log_message
    nfn[ATTR_REPOSITORY_PATH] = repository
    nfn[ATTR_REPOSITORY_HOST] = hostname
    nfn[ATTR_REVISION] = revision
    if config.has_key(CONFIG_REPOSITORY_NAME):
        nfn[ATTR_REPOSITORY_NAME] = config[CONFIG_REPOSITORY_NAME]

    # Generate Message-Id deterministically
    # so that changes can be sent as replies.
    hasher = sha.new()
    hasher.update(hostname)
    hasher.update(repository)
    hasher.update(str(revision))
    hasher.update(str(revision_date))  # In case repository is re-created
    commit_id = hasher.hexdigest()

    # Add tickertape-specific attributes
    if config.has_key(CONFIG_VIEWVC_URL):
        url = "%s?view=rev&revision=%d" % \
              (config[CONFIG_VIEWVC_URL], revision)
    nfn.update(ticker_nfn(user=author, message=msg,
                          message_id=commit_id, replacement_id=commit_id,
                          url=url))

    return nfn

def revpropchange_nfn(repository, revision, author, property, action, config):
    """ Construct a notification describing the property change. """
    # The old property value is available on standard input, but we
    # just ignore it.

    # We could possibly do some more sophisticated things:
    # - If the commit was "recent" (perhaps based on the notification
    #   timeout, if configured) we might re-emit a modified version of
    #   the original commit notification, with a Replacement-Id to
    #   replace it.
    # - If the change is to a property with a "small" value
    #   (e.g. author) the old and new values can be included in the
    #   message.
    # - If the change is to a property with a "large" value (e.g. log
    #   message) we should find a way to make the old value available,
    #   but putting it in the ticker text is unlikely to be a good
    #   place.

    nfn = elvin.message()
    hostname = socket.gethostname()

    # Get access to the repository
    repos = svn.repos.open(repository)
    fs = svn.repos.fs(repos)
    root = svn.fs.revision_root(fs, revision)

    # Look up some information about this revision
    orig_author = svn.fs.revision_prop(fs, revision,
                                       svn.core.SVN_PROP_REVISION_AUTHOR)
    revision_date = svn.fs.revision_prop(fs, revision,
                                         svn.core.SVN_PROP_REVISION_DATE)

    # Add Subversion-specific information about the event
    nfn[ATTR_REPOSITORY_PATH] = repository
    nfn[ATTR_REPOSITORY_HOST] = hostname
    nfn[ATTR_REVISION] = revision
    if config.has_key(CONFIG_REPOSITORY_NAME):
        nfn[ATTR_REPOSITORY_NAME] = config[CONFIG_REPOSITORY_NAME]

    # Create tickertape message
    action_strings = {
        REVPROPACTION_ADD: "Added property %s to revision %d",
        REVPROPACTION_MOD: "Modified property %s in revision %d",
        REVPROPACTION_DEL: "Deleted property %s from revision %d"
        }
    msg = action_strings[action] % (property, revision)
    if author != orig_author:
        msg += " by %s" % orig_author

    # Determine Message-Id of the original commit.
    hasher = sha.new()
    hasher.update(hostname)
    hasher.update(repository)
    hasher.update(str(revision))
    hasher.update(revision_date)
    commit_id = hasher.hexdigest()

    # Generate deterministic Replacement-Id so that subsequent changes
    # to the same property will replace this notification.
    hasher.update(property)
    change_id = hasher.hexdigest()

    # Generate new random Message-Id.
    hasher.update(str(time.time()))
    hasher.update(str(random.getrandbits(32)))
    message_id = hasher.hexdigest()

    # Create attachment URL
    if config.has_key(CONFIG_VIEWVC_URL):
        url = "%s?view=rev&revision=%d" % \
              (config[CONFIG_VIEWVC_URL], revision)

    # Add tickertape-specific attributes
    nfn.update(ticker_nfn(user=author, message=msg,
                          message_id=message_id, replacement_id=change_id,
                          in_reply_to=commit_id, url=url))

    return nfn

def lock_nfn(repository, author, locking, config):
    """ Construct a notification describing the lock/unlock event. """

    nfn = elvin.message()
    hostname = socket.gethostname()

    # Read the affected paths from standard input.
    paths = map(string.strip, sys.stdin.readlines())
    paths.sort()

    assert len(paths) > 0
    common_path = os.path.dirname(paths[0])
    common_dirs = common_path.split(os.sep)
    for path in paths:
        # Update the longest common path
        dirs = os.path.dirname(path).split(os.sep)
        new_common = []
        while len(common_dirs) > 0 and len(dirs) > 0 \
                  and common_dirs[0] == dirs[0]:
            new_common.append(common_dirs[0])
            common_dirs = common_dirs[1:]
            dirs = dirs[1:]
        common_dirs = new_common

    # Create tickertape message
    if common_path:
        msg = "In %s:" % common_path
    else:
        msg = "In root:"

    # Add a list of the affected files
    common_path = os.path.join("", *common_dirs)
    if common_path:
        common_str = common_path + os.sep
    else:
        common_str = ""
    drop_common = lambda path: path[len(common_str):]
    if locking:
        action = "Locked"
        paths_attr = ATTR_LOCKED_FILES
    else:
        action = "Unlocked"
        paths_attr = ATTR_UNLOCKED_FILES
    msg += " " + action + " " + " ".join(map(drop_common, paths))

    # Add extra Subversion-specific information about the event
    nfn[ATTR_REPOSITORY_PATH] = repository
    nfn[ATTR_REPOSITORY_HOST] = hostname
    if config.has_key(CONFIG_REPOSITORY_NAME):
        nfn[ATTR_REPOSITORY_NAME] = config[CONFIG_REPOSITORY_NAME]
    nfn[paths_attr] = " ".join(paths)

    # Determine a Message-Id specific to this set of paths
    hasher = sha.new("lock")
    hasher.update(hostname)
    hasher.update(repository)
    for path in paths:
        hasher.update(path)
    paths_id = hasher.hexdigest()

    # Generate new random Message-Id
    hasher.update(str(time.time()))
    hasher.update(str(random.getrandbits(32)))
    message_id = hasher.hexdigest()

    # Add tickertape-specific attributes
    nfn.update(ticker_nfn(user=author, message=msg,
                          message_id=message_id, replacement_id=paths_id))

    return nfn


########################################################################

def parse_options():
    # Construct the parser with our set of options
    parser = optparse.OptionParser(version="%prog " + VERSION)
    parser.add_option("-a", "--author", metavar="USER",
                      help="username of person making the change " +
                      "(not required for commits)")
    parser.add_option("-A", "--property-action",
                      help="what happened to the property " +
                      "(for property changes)",
                      choices=[REVPROPACTION_ADD, REVPROPACTION_MOD, REVPROPACTION_DEL])
    parser.add_option("-c", "--command",
                      help="type of change that has occurred",
                      choices=[COMMAND_COMMIT, COMMAND_REVPROPCHANGE,
                               COMMAND_LOCK, COMMAND_UNLOCK],
                      default=COMMAND_COMMIT)
    parser.add_option("-f", "--config-file", metavar="PATH",
                      help="configuration file")
    parser.add_option("-n", "--no-send",
                      action="store_true", default=False,
                      help="print the notification rather than sending it")
    parser.add_option("-p", "--property", "--prop",
                      help="name of changed property (for property changes)")
    parser.add_option("-r", "--repository", "--repo", metavar="PATH",
                      help="location of repository on disk")
    parser.add_option("-v", "--revision", "--rev",
                      dest="revision", metavar="REV", type="int",
                      help="new or changed revision number " +
                      "(not required for locks/unlocks)")

    # Do the parsing
    (options, args) = parser.parse_args()

    # Check results for validity
    if len(args) != 0:
        parser.error("excess arguments: " + " ".join(args))
    if options.repository == None:
        parser.error("missing required repository")
    if options.config_file == None:
        parser.error("missing required configuration file")

    return options

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

    # Parse options
    options = parse_options()
    repository = svn.core.svn_path_canonicalize(options.repository)

    # Read config file
    config = read_config(options.config_file)

    # Construct notification from information in repository
    if options.command == COMMAND_COMMIT:
        nfn = commit_nfn(repository, options.revision, config)
    elif options.command == COMMAND_REVPROPCHANGE:
        nfn = revpropchange_nfn(repository, options.revision, options.author,
                                options.property, options.property_action,
                                config)
    elif options.command == COMMAND_LOCK:
        nfn = lock_nfn(repository, options.author, True, config)
    elif options.command == COMMAND_UNLOCK:
        nfn = lock_nfn(repository, options.author, False, config)

    # Connect to Elvin
    c = elvin.client()
    e = c.connection()

    if config.get(CONFIG_ELVIN_URL):
        e.append_url(config[CONFIG_ELVIN_URL])
        e.set_discovery(0)
    else:
        e.set_discovery(1)

    e.open()

    # Send notification
    if options.no_send:
        sys.stdout.write(str(nfn))
    else:
        e.notify(nfn)

    # Exit
    e.close()
    sys.exit(0)


########################################################################
