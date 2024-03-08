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
test.cmdtest_py_d.ct_regtest: Regtest tests for the cmdtest.py test suite
"""

import sys,os

from mmgen.util import msg_r,die,gmsg
from mmgen.protocol import init_proto
from mmgen.proto.btc.regtest import MMGenRegtest

from ..include.common import cfg,imsg,stop_test_daemons,joinpath
from .ct_base import CmdTestBase

args1 = ['--bob']
args2 = ['--bob','--rpc-backend=http']

def gen_addrs(proto,network,keys):
	from mmgen.tool.api import tool_api
	tool = tool_api(cfg)
	tool.init_coin(proto.coin,'regtest')
	tool.addrtype = proto.mmtypes[-1]
	return [tool.privhex2addr('{:064x}'.format(key)) for key in keys]

class CmdTestRegtest(CmdTestBase):
	'various operations via regtest mode'
	networks = ('btc','ltc','bch')
	passthru_opts = ('coin',)
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [1]
	color = True
	deterministic = False
	bdb_wallet = True

	cmd_group_in = (
		('setup',                       'regtest mode setup'),
		('subgroup.netrate',            []),
		('subgroup.halving_calculator', []),
		('subgroup.fund_addrbal',       []),
		('subgroup.addrbal',            ['fund_addrbal']),
		('subgroup.blocks_info',        ['addrbal']),
		('subgroup.feeview',            []),
		('stop',                        'stopping regtest daemon'),
	)
	cmd_subgroups = {
	'netrate': (
		"'mmnode-netrate' script",
		('netrate1', "netrate (--help)"),
		('netrate2', "netrate"),
	),
	'halving_calculator': (
		"'mmnode-halving-calculator' script",
		('halving_calculator1', "halving calculator (--help)"),
		('halving_calculator2', "halving calculator"),
		('halving_calculator3', "halving calculator (--list)"),
		('halving_calculator4', "halving calculator (--mined)"),
		('halving_calculator5', "halving calculator (--mined --bdr-proj=5)"),
		('halving_calculator6', "halving calculator (--mined --sample-size=20)"),
	),
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
	),
	'blocks_info': (
		"'mmnode-blocks-info' script",
		('blocks_info1',              "blocks-info (--help)"),
		('blocks_info2',              "blocks-info (no args)"),
		('blocks_info3',              "blocks-info +100"),
		('blocks_info4',              "blocks-info --miner-info --fields=all --stats=all +1"),
	),
	'feeview': (
		"'mmnode-feeview' script",
		('feeview_setup',             'setting up feeview test'),
		('feeview1',                  "'mmnode-feeview'"),
		('feeview2',                  "'mmnode-feeview --columns=40 --include-current'"),
		('feeview3',                  "'mmnode-feeview --precision=6'"),
		('feeview4',                  "'mmnode-feeview --detail'"),
		('feeview5',                  "'mmnode-feeview --show-empty --log'"),
		('feeview6',                  "'mmnode-feeview --ignore-below=1MB'"),
		('feeview7',                  "'mmnode-feeview --ignore-below=20kB'"),
		('feeview8',                  "'mmnode-feeview' (empty mempool)"),
	),
	}

	def __init__(self,trunner,cfgs,spawn):
		CmdTestBase.__init__(self,trunner,cfgs,spawn)
		if trunner == None:
			return
		if cfg._proto.testnet:
			die(2,'--testnet and --regtest options incompatible with regtest test suite')
		self.proto = init_proto( cfg, self.proto.coin, network='regtest', need_amt=True )
		self.addrs = gen_addrs(self.proto,'regtest',[1,2,3,4,5])

		self.use_bdb_wallet = self.bdb_wallet or self.proto.coin != 'BTC'
		self.regtest = MMGenRegtest(cfg, self.proto.coin, bdb_wallet=self.use_bdb_wallet)

	def setup(self):
		stop_test_daemons(self.proto.network_id,force=True,remove_datadir=True)
		from shutil import rmtree
		try:
			rmtree(joinpath(self.tr.data_dir,'regtest'))
		except:
			pass
		t = self.spawn(
			'mmgen-regtest',
			(['--bdb-wallet'] if self.use_bdb_wallet else [])
			+ ['--setup-no-stop-daemon', 'setup'])
		for s in ('Starting','Creating','Creating','Creating','Mined','Setup complete'):
			t.expect(s)
		return t

	def netrate(self, add_args, expect_str, exit_val=None):
		t = self.spawn('mmnode-netrate', args1 + add_args, exit_val=exit_val)
		t.expect(expect_str,regex=True)
		return t

	def netrate1(self):
		return self.netrate( ['--help'], 'USAGE:.*' )

	def netrate2(self):
		t = self.netrate([], r'sent:.*', exit_val=-15)
		t.kill(15)
		if sys.platform == 'win32':
			return 'ok'
		return t

	def halving_calculator(self,add_args,expect_list):
		t = self.spawn('mmnode-halving-calculator',args1+add_args)
		t.match_expect_list(expect_list)
		return t

	def halving_calculator1(self):
		return self.halving_calculator(['--help'],['USAGE:'])

	def halving_calculator2(self):
		return self.halving_calculator([],['Current block: 393',f'Current block subsidy: 12.5 {cfg.coin}'])

	def halving_calculator3(self):
		return self.halving_calculator(['--list'],['33 4950','0'])

	def halving_calculator4(self):
		return self.halving_calculator(['--mined'],['0 0.0000015 14949.9999835'])

	def halving_calculator5(self):
		return self.halving_calculator(['--mined','--bdr-proj=5'],['5.00000 0 0.0000015 14949.9999835'])

	def halving_calculator6(self):
		return self.halving_calculator(['--mined','--sample-size=20'],['33 4950','0 0.0000015 14949.9999835'])

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
				f'Balance: 0.357 {cfg.coin}',
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

	def blocks_info(self,args,expect_list):
		t = self.spawn('mmnode-blocks-info',args)
		t.match_expect_list(expect_list)
		return t

	def blocks_info1(self):
		return self.blocks_info( args1 + ['--help'], ['USAGE:','OPTIONS:'])

	def blocks_info2(self):
		return self.blocks_info( args1, [
			'Current height: 396',
		])

	def blocks_info3(self):
		return self.blocks_info( args1 + ['+100'], [
			'Range: 297-396',
			'Current height: 396',
			'Next diff adjust: 2016'
		])

	def blocks_info4(self):
		n1,i1,o1,n2,i2,o2 = (2,1,3,6,3,9) if cfg.coin == 'BCH' else (2,1,4,6,3,12)
		return self.blocks_info( args1 + ['--miner-info','--fields=all','--stats=all','+3'], [
			'Averages',
			f'nTx: {n1}',
			f'Inputs: {i1}',
			f'Outputs: {o1}',
			'Totals',
			f'nTx: {n2}',
			f'Inputs: {i2}',
			f'Outputs: {o2}',
			'Current height: 396',
			'Next diff adjust: 2016'
		])

	async def feeview_setup(self):

		def create_pairs(nPairs):

			from mmgen.tool.api import tool_api
			from collections import namedtuple

			t = tool_api(cfg)
			t.init_coin(self.proto.coin,self.proto.network)
			t.addrtype = 'compressed' if self.proto.coin == 'BCH' else 'bech32'
			wp = namedtuple('wifaddrpair',['wif','addr'])

			def gen():
				for n in range(0xfaceface,nPairs+0xfaceface):
					wif = t.hex2wif(f'{n:064x}')
					yield wp( wif, t.wif2addr(wif) )

			return list(gen())

		def gen_fees(n_in,low,high):

			# very approximate tx size estimation:
			ibytes,wbytes,obytes = (148,0,34) if self.proto.coin == 'BCH' else (43,108,31)
			x = (ibytes + (wbytes//4) + (obytes * nPairs)) * self.proto.coin_amt(self.proto.coin_amt.satoshi)

			n = n_in - 1
			vmax = high - low

			for i in range(n_in):
				yield (low + (i/n)**6 * vmax) * x

		async def do_tx(inputs,outputs,wif):
			tx_hex = await r.rpc_call( 'createrawtransaction', inputs, outputs )
			tx = await r.rpc_call( 'signrawtransactionwithkey', tx_hex, [wif], [], self.proto.sighash_type )
			assert tx['complete'] == True
			return tx['hex']

		async def do_tx1():
			us = await r.rpc_call('listunspent',wallet='miner')
			tx_input = us[7] # 25 BTC in coinbase -- us[0] could have < 25 BTC
			fee = self.proto.coin_amt('0.001')
			outputs = {p.addr:tx1_amt for p in pairs[:nTxs]}
			outputs.update({burn_addr: tx_input['amount'] - (tx1_amt*nTxs) - fee})
			return await do_tx(
				[{ 'txid': tx_input['txid'], 'vout': 0 }],
				outputs,
				await r.miner_wif)

		async def do_tx2(tx,pairno):
			fee = fees[pairno]
			outputs = {p.addr:tx2_amt for p in pairs}
			outputs.update({burn_addr: tx1_amt - (tx2_amt*len(pairs)) - fee})
			return await do_tx(
				[{ 'txid': tx['txid'], 'vout': pairno }],
				outputs,
				pairs[pairno].wif )

		async def do_txs(tx_in):
			for pairno in range(nTxs):
				tx_hex = await do_tx2(tx_in,pairno)
				await r.rpc_call('sendrawtransaction',tx_hex)

		self.spawn('',msg_only=True)

		r = self.regtest
		nPairs = 100
		nTxs = 25
		tx1_amt = self.proto.coin_amt('{:0.4f}'.format(24 / nTxs)) # 25 BTC subsidy, leave extra for fee
		tx2_amt = self.proto.coin_amt('0.00005')                   # make this as small as possible

		imsg(f'Creating {nPairs} key-address pairs')
		pairs = create_pairs(nPairs+1)
		burn_addr = pairs.pop()[1]

		imsg(f'Creating funding transaction with {nTxs} outputs of value {tx1_amt} {self.proto.coin}')
		tx1_hex = await do_tx1()

		imsg(f'Relaying funding transaction')
		await r.rpc_call('sendrawtransaction',tx1_hex)

		imsg(f'Mining a block')
		await r.generate(1,silent=True)

		imsg(f'Generating fees for mempool transactions')
		fees = list(gen_fees(nTxs,2,120))

		imsg(f'Creating and relaying {nTxs} mempool transactions with {nPairs} outputs each')
		await do_txs(await r.rpc_call('decoderawtransaction',tx1_hex))

		return 'ok'

	def _feeview(self,args,expect_list=[]):
		t = self.spawn('mmnode-feeview',args)
		if expect_list:
			t.match_expect_list(expect_list)
		return t

	def feeview1(self):
		return self._feeview([])

	def feeview2(self):
		return self._feeview(['--columns=40','--include-current'])

	def feeview3(self):
		return self._feeview(['--precision=6'])

	def feeview4(self):
		return self._feeview(['--detail'])

	def feeview5(self):
		return self._feeview(['--show-empty','--log',f'--outdir={self.tmpdir}'])

	def feeview6(self):
		return self._feeview(['--ignore-below=1MB'])

	def feeview7(self):
		return self._feeview(['--ignore-below=4kB'])

	async def feeview8(self):
		imsg('Clearing mempool')
		await self.regtest.generate(1,silent=True)
		return self._feeview([])

	def stop(self):
		if cfg.no_daemon_stop:
			self.spawn('',msg_only=True)
			msg_r('(leaving daemon running by user request)')
			return 'ok'
		else:
			return self.spawn('mmgen-regtest',['stop'])
