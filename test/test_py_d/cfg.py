#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen-node-tools

"""
test.test_py_d.cfg: configuration data for test.py
"""

import os

cmd_groups_dfl = {
	'helpscreens': ('TestSuiteHelp',{'modname':'misc','full_data':True}),
	'scripts':     ('TestSuiteScripts',{'modname':'misc'}),
	'regtest':     ('TestSuiteRegtest',{}),
}

cmd_groups_extra = {}

cfgs = {
	'1':  {}, # regtest
	'2':  {}, # scripts
}

def fixup_cfgs(): pass
