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
ts_misc.py: Miscellaneous test groups for the test.py test suite
"""

from ..include.common import *
from .common import *
from .ts_base import *

class TestSuiteHelp(TestSuiteBase):
	'help, info and usage screens'
	networks = ('btc','ltc','bch')
	tmpdir_nums = []
	passthru_opts = ('daemon_data_dir','rpc_port','coin','testnet')
	cmd_group = (
		('version',               (1,'version message',[])),
		('helpscreens',           (1,'help screens',             [])),
		('longhelpscreens',       (1,'help screens (--longhelp)',[])),
	)
	color = True

	def version(self):
		t = self.spawn(f'mmnode-netrate',['--version'])
		t.expect('MMNODE-NETRATE version')
		return t

	def helpscreens(self,arg='--help',scripts=(),expect='USAGE:.*OPTIONS:'):

		scripts = list(scripts) or [s for s in os.listdir('cmds') if s.startswith('mmnode-')]

		for s in sorted(scripts):
			t = self.spawn(s,[arg],extra_desc=f'({s})')
			t.expect(expect,regex=True)
			t.read()
			t.ok()
			t.skip_ok = True

		return t

	def longhelpscreens(self):
		return self.helpscreens(arg='--longhelp',expect='USAGE:.*LONG OPTIONS:')
