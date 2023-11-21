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
test.cmdtest_py_d.cfg: configuration data for cmdtest.py
"""

cmd_groups_altcoin = []

cmd_groups_dfl = {
	'main':        ('CmdTestMain',{}),
	'helpscreens': ('CmdTestHelp',{'modname':'misc','full_data':True}),
	'scripts':     ('CmdTestScripts',{'modname':'misc'}),
	'regtest':     ('CmdTestRegtest',{}),
}

cmd_groups_extra = {}

cfgs = {
	'1':  {}, # regtest
	'2':  {}, # scripts
	'3':  {}, # main
}

def fixup_cfgs():
	pass
