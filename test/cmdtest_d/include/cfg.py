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
test.cmdtest_d.include.cfg: configuration data for cmdtest.py
"""

from collections import namedtuple

cmd_groups_altcoin = []

gd = namedtuple('cmd_groups_data', ['clsname', 'params'])

cmd_groups_dfl = {
	'main':        gd('CmdTestMain', {}),
	'helpscreens': gd('CmdTestHelp', {'modname': 'misc', 'full_data': True}),
	'scripts':     gd('CmdTestScripts', {'modname': 'misc'}),
	'regtest':     gd('CmdTestRegtest', {}),
}

cmd_groups_extra = {}

cfgs = {
	'1':  {}, # regtest
	'2':  {}, # scripts
	'3':  {}, # main
}

def fixup_cfgs():
	import os

	for k in cfgs:
		cfgs[k]['tmpdir'] = os.path.join('test', 'tmp', str(k))

fixup_cfgs()
