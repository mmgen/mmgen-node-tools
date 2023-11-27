#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet
#   https://gitlab.com/mmgen/mmgen-wallet

"""
cmdtest_py_d.ct_main: Basic operations tests for the cmdtest.py test suite
"""

import sys,time

from ..include.common import cfg
from .ct_base import CmdTestBase

class CmdTestMain(CmdTestBase):
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
			('peerblocks2', 'interactive (popen spawn)'),
			('peerblocks3', 'interactive, 80 columns (pexpect_spawn [on Linux])'),
		),
	}

	def peerblocks(self,args,expect_list=None,pexpect_spawn=False):
		t = self.spawn(
			f'mmnode-peerblocks',
			args,
			pexpect_spawn = pexpect_spawn )
		if cfg.exact_output: # disable echoing of input
			t.p.logfile = None
			t.p.logfile_read = sys.stdout
		if expect_list:
			t.match_expect_list(expect_list)
		return t

	def peerblocks1(self):
		t = self.peerblocks(['--help'])
		if t.pexpect_spawn:
			t.send('q')
		return t

	def peerblocks2(self,args=[],pexpect_spawn=False):

		t = self.peerblocks(args,pexpect_spawn=pexpect_spawn)

		for i in range(5):
			t.expect('PEERS')

		t.send('x')

		for i in range(3):
			t.expect('PEERS')

		sleep_secs = 0.2

		t.send('0')
		time.sleep(sleep_secs)
		t.send('\n' if pexpect_spawn else '0\n') # TODO: check for readline availability
		t.expect('Unable to disconnect peer 0')
		t.expect('PEERS')

		t.send('1')
		time.sleep(sleep_secs)
		t.send('1\n' if pexpect_spawn else '11\n')
		t.expect('11: invalid peer number')
		t.expect('PEERS')

		t.send('2')
		time.sleep(sleep_secs)
		t.send('\n' if pexpect_spawn else '2\n')
		t.expect('Disconnecting peer 2')
		t.expect('PEERS')

		t.send('q')

		return t

	def peerblocks3(self):
		return self.peerblocks2(
			['--columns=80'],
			pexpect_spawn = sys.platform != 'win32' )
