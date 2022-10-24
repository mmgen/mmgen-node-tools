#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen
#   https://gitlab.com/mmgen/mmgen

"""
test_py_d.ts_main: Basic operations tests for the test.py test suite
"""

import time

from ..include.common import *
from .common import *
from .ts_base import *

class TestSuiteMain(TestSuiteBase):
	'basic operations with fake RPC data'
	tmpdir_nums = [3]
	networks = ('btc',) # fake data, so test peerblocks for BTC mainnet only
	passthru_opts = ('daemon_data_dir','rpc_port','coin','testnet','rpc_backend')
	segwit_opts_ok = True
	color = True
	need_daemon = True

	cmd_group_in = (
		('subgroup.peerblocks', []),
	)

	cmd_subgroups = {
		'peerblocks': (
			"'mmnode-peerblocks' script",
			('peerblocks1', '--help'),
			('peerblocks2', 'interactive'),
			('peerblocks3', 'interactive, 80 columns'),
		),
	}

	def peerblocks(self,args,expect_list=None):
		t = self.spawn(
			f'mmnode-peerblocks',
			args )
		if opt.exact_output: # disable echoing of input
			t.p.logfile = None
			t.p.logfile_read = sys.stdout
		if expect_list:
			t.match_expect_list(expect_list)
		return t

	def peerblocks1(self):
		t = self.peerblocks(['--help'])
		if opt.pexpect_spawn:
			t.send('q')
		return t

	def peerblocks2(self,args=[]):

		t = self.peerblocks(args)

		for i in range(5):
			t.expect('PEERS')

		t.send('x')

		for i in range(3):
			t.expect('PEERS')

		t.send('0')
		time.sleep(0.2)
		t.send('\n')
		t.expect('Unable to disconnect peer 0')
		t.expect('PEERS')

		t.send('1')
		time.sleep(0.2)
		t.send('1\n')
		t.expect('11: invalid peer number')
		t.expect('PEERS')

		t.send('2')
		time.sleep(0.2)
		t.send('\n')
		t.expect('Disconnecting peer 2')
		t.expect('PEERS')

		t.send('q')

		return t

	def peerblocks3(self):
		return self.peerblocks2(['--columns=80'])
