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
from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import die,gmsg
from mmgen.protocol import init_proto
from ..include.common import *
from .common import *

from .ts_base import *

args1 = ['--bob']
args2 = ['--bob','--rpc-backend=http']

def gen_addrs(proto,network,keys):
	from mmgen.tool.api import tool_api
	tool = tool_api()
	tool.init_coin(proto.coin,'regtest')
	tool.addrtype = proto.mmtypes[-1]
	return [tool.privhex2addr('{:064x}'.format(key)) for key in keys]

class TestSuiteRegtest(TestSuiteBase):
	'various operations via regtest mode'
	networks = ('btc','ltc','bch')
	passthru_opts = ('coin',)
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [1]
	color = True
	deterministic = False
	cmd_group_in = (
		('setup',                       'regtest mode setup'),
		('subgroup.fund_addrbal',       []),
		('subgroup.addrbal',            ['fund_addrbal']),
		('stop',                        'stopping regtest daemon'),
	)
	cmd_subgroups = {
	'fund_addrbal': (
		"funding addresses for 'addrbal' subgroup",
		('sendto1', 'sending funds to address #1 (1)'),
		('sendto2', 'sending funds to address #1 (2)'),
		('sendto3', 'sending funds to address #2'),
	),
	'addrbal': (
		"'mmnode-addrbal' script",
		('addrbal_single',            'getting address balance (single address)'),
		('addrbal_multiple',          'getting address balances (multiple addresses)'),
		('addrbal_multiple_tabular1', 'getting address balances (multiple addresses, tabular output)'),
		('addrbal_multiple_tabular2', 'getting address balances (multiple addresses, tabular, show first block)'),
		('addrbal_nobal1',            'getting address balances (no balance)'),
		('addrbal_nobal2',            'getting address balances (no balances)'),
		('addrbal_nobal3',            'getting address balances (one null balance)'),
		('addrbal_nobal3_tabular1',   'getting address balances (one null balance, tabular output)'),
		('addrbal_nobal3_tabular2',   'getting address balances (one null balance, tabular, show first block)'),
	)
	}

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return
		if self.proto.testnet:
			die(2,'--testnet and --regtest options incompatible with regtest test suite')
		self.proto = init_proto(self.proto.coin,network='regtest',need_amt=True)
		self.addrs = gen_addrs(self.proto,'regtest',[1,2,3,4,5])

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

	def sendto(self,addr,amt):
		return self.spawn('mmgen-regtest',['send',addr,amt])

	def sendto1(self): return self.sendto(self.addrs[0],'0.123')
	def sendto2(self): return self.sendto(self.addrs[0],'0.234')
	def sendto3(self): return self.sendto(self.addrs[1],'0.345')

	def addrbal(self,args,expect_list):
		t = self.spawn('mmnode-addrbal',args)
		t.match_expect_list(expect_list)
		return t

	def addrbal_single(self):
		return self.addrbal(
			args2 + [self.addrs[0]],
			[
				f'Balance: 0.357 {g.coin}',
				'2 unspent outputs in 2 blocks',
				'394','0.123',
				'395','0.234'
			])

	def addrbal_multiple(self):
		return self.addrbal(
			args2 + [self.addrs[1],self.addrs[0]],
			[
				'396','0.345',
				'394','0.123',
				'395','0.234'
			])

	def addrbal_multiple_tabular1(self):
		return self.addrbal(
			args2 + ['--tabular',self.addrs[1],self.addrs[0]],
			[
				self.addrs[1] + ' 1 396','0.345',
				self.addrs[0] + ' 2 395','0.357'
			])

	def addrbal_multiple_tabular2(self):
		return self.addrbal(
			args2 + ['--tabular','--first-block',self.addrs[1],self.addrs[0]],
			[
				self.addrs[1] + ' 1 396','396','0.345',
				self.addrs[0] + ' 2 394','395','0.357'
			])

	def addrbal_nobal1(self):
		return self.addrbal(
			args2 + [self.addrs[2]], ['Address has no balance'] )

	def addrbal_nobal2(self):
		return self.addrbal(
			args2 + [self.addrs[2],self.addrs[3]], ['Addresses have no balances'] )

	def addrbal_nobal3(self):
		return self.addrbal(
			args2 + [self.addrs[4],self.addrs[0],self.addrs[3]],
			[
				'No balance',
				'2 unspent outputs in 2 blocks',
				'394','0.123','395','0.234',
				'No balance'
			])

	def addrbal_nobal3_tabular1(self):
		return self.addrbal(
			args2 + ['--tabular',self.addrs[4],self.addrs[0],self.addrs[3]],
			[
				self.addrs[4] + ' - - -',
				self.addrs[0] + ' 2 395','0.357',
				self.addrs[3] + ' - - -',
			])

	def addrbal_nobal3_tabular2(self):
		return self.addrbal(
			args2 + ['--tabular','--first-block',self.addrs[4],self.addrs[0],self.addrs[3]],
			[
				self.addrs[4] + ' - - - -',
				self.addrs[0] + ' 2 394','395','0.357',
				self.addrs[3] + ' - - - -',
			])

	def stop(self):
		if opt.no_daemon_stop:
			self.spawn('',msg_only=True)
			msg_r('(leaving daemon running by user request)')
			return 'ok'
		else:
			return self.spawn('mmgen-regtest',['stop'])
