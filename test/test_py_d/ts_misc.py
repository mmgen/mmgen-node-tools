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
test.test_py_d.ts_misc: Miscellaneous test groups for the test.py test suite
"""

import shutil
from ..include.common import *
from .common import *
from .ts_base import *

refdir = os.path.join('test','ref','ticker')

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

class TestSuiteScripts(TestSuiteBase):
	'scripts not requiring a coin daemon'
	networks = ('btc',)
	tmpdir_nums = [2]
	passthru_opts = ()
	color = True

	cmd_group_in = (
		('subgroup.ticker_setup', []),
		('subgroup.ticker',       ['ticker_setup']),
	)
	cmd_subgroups = {
	'ticker_setup': (
		"setup for 'ticker' subgroup",
		('ticker_setup', 'ticker setup'),
	),
	'ticker': (
		"'mmnode-ticker' script",
		('ticker1',  'ticker [--help)'),
		('ticker2',  'ticker (bad proxy)'),
		('ticker3',  'ticker [--cached-data]'),
		('ticker4',  'ticker [--cached-data --wide]'),
		('ticker5',  'ticker [--cached-data --wide --adjust=-0.766] (usr cfg file)'),
		('ticker6',  'ticker [--cached-data --wide --portfolio] (missing portfolio)'),
		('ticker7',  'ticker [--cached-data --wide --portfolio]'),
		('ticker8',  'ticker [--cached-data --wide --elapsed]'),
		('ticker9',  'ticker [--cached-data --wide --portfolio --elapsed --add-rows=fake-fakecoin:0.0123 --add-precision=2]'),
		('ticker10', 'ticker [--cached-data xmr:17.234]'),
		('ticker11', 'ticker [--cached-data xmr:17.234:btc]'),
		('ticker12', 'ticker [--cached-data --adjust=1.23 xmr:17.234:btc]'),
		('ticker13', 'ticker [--cached-data --wide --elapsed -c inr-indian-rupee:79.5 inr:200000:btc:0.1]'),
		('ticker14', 'ticker [--cached-data --wide --btc]'),
		('ticker15', 'ticker [--cached-data --wide --btc btc:2:usd:45000]'),
		('ticker16', 'ticker [--cached-data --wide --elapsed -c eur,omr-omani-rial:2.59r'),
		('ticker17', 'ticker [--cached-data --wide --elapsed -c bgn-bulgarian-lev:0.5113r:eur'),
		('ticker18', 'ticker [--cached-data --wide --elapsed -c eur,bgn-bulgarian-lev:0.5113r:eur-euro-token'),
	)
	}

	@property
	def ticker_args(self):
		return [ f'--cachedir={self.tmpdir}', '--proxy=http://asdfzxcv:32459' ]

	@property
	def nt_datadir(self):
		return os.path.join( cfg.data_dir_root, 'node_tools' )

	def ticker_setup(self):
		self.spawn('',msg_only=True)
		shutil.copy2(os.path.join(refdir,'ticker.json'),self.tmpdir)
		shutil.copy2(os.path.join(refdir,'ticker-btc.json'),self.tmpdir)
		return 'ok'

	def ticker(self,args=[],expect_list=None,cached=True):
		t = self.spawn(
			f'mmnode-ticker',
			(['--cached-data'] if cached else []) + self.ticker_args + args )
		if expect_list:
			t.match_expect_list(expect_list)
		return t

	def ticker1(self):
		t = self.ticker(['--help'])
		t.expect('USAGE:')
		return t

	def ticker2(self):
		t = self.ticker(cached=False)
		if not cfg.skipping_deps:
			t.expect('Creating')
			t.expect('Creating')
		t.expect('proxy host could not be resolved')
		t.req_exit_val = 3
		return t

	def ticker3(self):
		return self.ticker(
			[],
			[
				'USD BTC',
				'BTC 23250.77 1.00000000 ETH 1659.66 0.07146397'
			])


	def ticker4(self):
		return self.ticker(
			['--wide','--add-columns=eur,inr-indian-rupee:79.5'],
			[
				r'EUR \(EURO TOKEN\) = 1.0186 USD ' +
				r'INR \(INDIAN RUPEE\) = 0.012579 USD',
				'USD EUR INR BTC CHG_7d CHG_24h UPDATED',
				'BITCOIN',
				r'ETHEREUM 1,659.66 1,629.3906 131,943.14 0.07146397 \+21.42 \+1.82',
				r'MONERO 158.97 156.0734 12,638.36 0.00684527 \+7.28 \+1.21 2022-08-02 18:25:59',
				r'INDIAN RUPEE 0.01 0.0123 1.00 0.00000054 -- --',
			])

	def ticker5(self):
		shutil.copy2(os.path.join(refdir,'ticker-cfg.yaml'),self.nt_datadir)
		t = self.ticker(
			['--wide','--adjust=-0.766'],
			[
				'Adjusting prices by -0.77%',
				'USD BTC CHG_7d CHG_24h UPDATED',
				r'LITECOIN 58.56 0.00252162 \+12.79 \+0.40 2022-08-02 18:25:59',
				r'MONERO 157.76 0.00679284 \+7.28 \+1.21'
			])
		os.unlink(os.path.join(self.nt_datadir,'ticker-cfg.yaml'))
		return t

	def ticker6(self):
		t = self.ticker( ['--wide','--portfolio'], None )
		t.expect('No portfolio')
		t.req_exit_val = 1
		return t

	def ticker7(self): # demo
		shutil.copy2(os.path.join(refdir,'ticker-portfolio.yaml'),self.nt_datadir)
		t = self.ticker(
			['--wide','--portfolio'],
			[
				'USD BTC CHG_7d CHG_24h UPDATED',
				r'ETHEREUM 1,659.66 0.07146397 \+21.42 \+1.82 2022-08-02 18:25:59',
				'CARDANO','ALGORAND',
				'PORTFOLIO','BITCOIN','ETHEREUM','MONERO','CARDANO','ALGORAND','TOTAL'
			])
		os.unlink(os.path.join(self.nt_datadir,'ticker-portfolio.yaml'))
		return t

	def ticker8(self):
		return self.ticker(
			['--wide','--elapsed'],
			[
				'USD BTC CHG_7d CHG_24h UPDATED',
				r'BITCOIN 23,250.77 1.00000000 \+11.15 \+0.89 10 minutes ago'
			])

	def ticker9(self):
		shutil.copy2(
			os.path.join(refdir,'ticker-portfolio-bad.yaml'),
			os.path.join(self.nt_datadir,'ticker-portfolio.yaml') )
		t = self.ticker(
			['--wide','--portfolio','--elapsed','--add-rows=fake-fakecoin:0.0123','--add-precision=2'],
			[
				'USD BTC CHG_7d CHG_24h UPDATED',
				r'BITCOIN 23,250.7741 1.0000000000 \+11.15 \+0.89 10 minutes ago',
				r'FAKECOIN 81.3008 0.0034966927 -- -- --',
				r'\(no data for noc-nocoin\)',
			])
		os.unlink(os.path.join(self.nt_datadir,'ticker-portfolio.yaml'))
		return t

	def ticker10(self):
		return self.ticker(
			['XMR:17.234'],
			[
				r'XMR \(MONERO\) = 158.97 USD ' +
				'Amount: 17.234 XMR',
				'SPOT PRICE',
				'BTC 0.11783441',
				'XMR 17.23400000',
				'XAU','NDX',
			])

	def ticker11(self):
		return self.ticker(
			['XMR:17.234:BTC'],
			[
				r'XMR \(MONERO\) = 158.97 USD ' +
				r'BTC \(BITCOIN\) = 23250.77 USD ' +
				'Amount: 17.234 XMR',
				'SPOT PRICE',
				'XMR 17.23400000 BTC 0.11783441',
			])

	def ticker12(self):
		return self.ticker(
			['--adjust=1.23','--wide','XMR:17.234:BTC'],
			[
				r'XMR \(MONERO\) = 158.97 USD ' +
				r'BTC \(BITCOIN\) = 23,250.77 USD ' +
				'Amount: 17.234 XMR',
				r'Adjusting prices by \+1.23%',
				'SPOT PRICE ADJUSTED PRICE',
				'MONERO 17.23400000 17.44597820 2022-08-02 18:25:59 ' +
				'BITCOIN 0.11783441 0.11928377 2022-08-02 18:25:59',
			])

	def ticker13(self):
		return self.ticker(
			['-wE','-c','inr-indian-rupee:79.5','inr:200000:btc:0.1'],
			[
				'Offer: 200,000 INR',
				'Offered price differs from spot by -7.58%',
				'SPOT PRICE OFFERED PRICE UPDATED',
				'INDIAN RUPEE 200,000.00000000 184,843.65372424 -- ' +
				'BITCOIN 0.10819955 0.10000000 10 minutes ago'
			])

	def ticker14(self):
		shutil.copy2(os.path.join(refdir,'ticker-portfolio.yaml'),self.nt_datadir)
		t = self.ticker(
			['--btc','--wide','--portfolio','--elapsed'],
			[
				'PRICES',
				r'BITCOIN 23,368.86 \+6.05 -1.87 1 day 9 hours 2 minutes ago',
				'PORTFOLIO',
				r'BITCOIN 28,850.44 \+6.05 -1.87 1.23456789'
			])
		os.unlink(os.path.join(self.nt_datadir,'ticker-portfolio.yaml'))
		return t

	def ticker15(self):
		return self.ticker(
			['--btc','--wide','--elapsed','-r','inr:79.5','btc:2:usd:45000'],
			[
				r'BTC \(BITCOIN\) = 23,368.86 USD',
				'Offered price differs from spot by -3.72%',
				'SPOT PRICE OFFERED PRICE UPDATED',
				'BITCOIN 2.00000000 1.92563954 1 day 9 hours 2 minutes ago ' +
				'US DOLLAR 46,737.71911598 45,000.00000000 --',
			])

	def ticker16(self):
		return self.ticker(
			['--wide','--elapsed','-c','eur,omr-omani-rial:2.59r'],
			[
				r'EUR \(EURO TOKEN\) = 1.0186 USD ' +
				r'OMR \(OMANI RIAL\) = 2.5900 USD',
				'USD EUR OMR BTC CHG_7d CHG_24h UPDATED',
				r'BITCOIN 23,250.77 22,826.6890 8,977.1328 1.00000000 \+11.15 \+0.89 10 minutes ago',
				'OMANI RIAL 2.59 2.5428 1.0000 0.00011139 -- -- --'
			])

	def ticker17(self):
		# BGN pegged at 0.5113 EUR
		return self.ticker(
			['--wide','--elapsed','-c','bgn-bulgarian-lev:0.5113r:eur'],
			[
				r'BGN \(BULGARIAN LEV\) = 0.52080 USD',
				'USD BGN BTC CHG_7d CHG_24h UPDATED',
				'BITCOIN 23,250.77 44,644.414 1.00000000',
				'BULGARIAN LEV 0.52 1.000 0.00002240',
			])

	def ticker18(self):
		return self.ticker(
			['--wide','--elapsed','-c','eur,bgn-bulgarian-lev:0.5113r:eur-euro-token'],
			[
				r'BGN \(BULGARIAN LEV\) = 0.52080 USD',
				'USD EUR BGN BTC CHG_7d CHG_24h UPDATED',
				'BITCOIN 23,250.77 22,826.6890 44,644.414 1.00000000',
				'BULGARIAN LEV 0.52 0.5113 1.000 0.00002240',
			])
