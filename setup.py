#! /usr/bin/env python

# COPYRIGHT_BEGIN
#
# Copyright (C) 2001-2006 Mantara Software (ABN 17 105 665 594).
# All Rights Reserved.
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

__version__ = "$Revision: 1.11 $"[11:-2]

from distutils.core import setup

setup (name="cvs2ticker",
       version="1.5.0",
       description="Logs CVS messages to Elvin's tickertape clients",
       author="David Arnold",
       author_email="davida@pobox.com",
       url="http://www.tickertape.org/projects/cvs2ticker/",
       licence="BSD",
       long_description="""
       This package provides a python script that is run by CVS that logs
       messages via Elvin suitable for tickertape. It creates a shared
       awareness of changes to the CVS repository.""",
       
       scripts=["cvs2ticker.py", "cvs2web.py"],
       #packages=[""],
       data_files=[("man/man1", ["cvs2ticker.1"]),
                   ],
       )

########################################################################
#  end of setup.py
