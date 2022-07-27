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
ts_regtest.py: Regtest tests for the test.py test suite
"""

import os
from mmgen.opts import opt
from mmgen.util import die,gmsg
from ..include.common import *
from .common import *

from .ts_base import *

class TestSuiteRegtest(TestSuiteBase):
	'various operations via regtest mode'
	networks = ('btc','ltc','bch')
	passthru_opts = ('coin',)
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [1]
	color = True
	deterministic = False
	cmd_group = (
		('setup',                     'regtest (Bob and Alice) mode setup'),
		('stop',                      'stopping regtest daemon'),
	)

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return
		if self.proto.testnet:
			die(2,'--testnet and --regtest options incompatible with regtest test suite')

		os.environ['MMGEN_TEST_SUITE_REGTEST'] = '1'

	def __del__(self):
		os.environ['MMGEN_TEST_SUITE_REGTEST'] = ''

	def setup(self):
		stop_test_daemons(self.proto.network_id,force=True,remove_datadir=True)
		from shutil import rmtree
		try: rmtree(joinpath(self.tr.data_dir,'regtest'))
		except: pass
		t = self.spawn('mmgen-regtest',['-n','setup'])
		for s in ('Starting','Creating','Creating','Creating','Mined','Setup complete'):
			t.expect(s)
		return t

	def stop(self):
		if opt.no_daemon_stop:
			self.spawn('',msg_only=True)
			msg_r('(leaving daemon running by user request)')
			return 'ok'
		else:
			return self.spawn('mmgen-regtest',['stop'])
