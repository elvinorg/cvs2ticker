#! /usr/bin/env python
########################################################################
#  Copyright (C) DSTC Pty Ltd (ACN 052 372 577) 2000-2001.
#  All Rights Reserved.
#
#  This software is the property of the DSTC Pty Ltd.  Use of this
#  software is strictly in accordance with the license agreement in
#  the accompanying COPYING file.  If your distribution of this
#  software does not contain a COPYING file then you have no rights to
#  use this software in any manner and should contact DSTC at the
#  address below to determine an appropriate licensing arrangement.
#
#     DSTC Pty Ltd
#     University of Queensland
#     St Lucia, 4072
#     Australia
#     Tel: +61 7 3365 4310
#     Fax: +61 7 3365 4311
#     Email: enquiries@dstc.edu.au
#
#  This software is being provided "AS IS" without warranty of any
#  kind.  In no event shall DSTC Pty Ltd be liable for damage of any
#  kind arising out of or in connection with the use or performance of
#  this software.
########################################################################

__version__ = "$Revision: 1.2 $"[11:-2]

########################################################################

from distutils.core import setup

setup (name="cvs2ticker",
       version="1.3.0",
       description="Logs CVS messages to Elvin's tickertape clients",
       author="David Arnold",
       author_email="elvin@dstc.edu.au",
       url="http://elvin.dstc.edu.au/projects/cvs2ticker",
       licence="Copyright (C) DSTC, 2000-2001.",
       long_description="""
       This package provides a python script that is run by CVS that logs
       messages via Elvin suitable for tickertape. It creates a shared
	   awareness of changes to the CVS repository.""",
       
       scripts=["cvs2ticker.py", "cvs2ticker"],
       #packages=[""],
       data_files=[("man/man1", ["man/cvs2ticker.1"]),
                   ],
       )

########################################################################
#  end of setup.py