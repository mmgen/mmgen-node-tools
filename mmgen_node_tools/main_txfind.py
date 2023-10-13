#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2021 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""
mmnode-txfind: Find a transaction in the blockchain or mempool
"""

import sys

from mmgen.cfg import Config
from mmgen.util import msg,Msg,die,is_hex_str,async_run

opts_data = {
	'text': {
		'desc':    'Find a transaction in the blockchain or mempool',
		'usage':   '[opts] <transaction ID>',
		'options': """
-h, --help      Print this help message
--, --longhelp  Print help message for long options (common options)
-q, --quiet     Be quieter
-v, --verbose   Be more verbose
""",
	'notes': """
If transaction is in blockchain, the block number and number of confirmations
are displayed.

Requires --txindex for correct operation.
"""
	}
}

msg_data = {
	'normal': {
		'none':  'Transaction not found in blockchain or mempool',
		'block': 'Transaction is in block {b} ({c} confirmations)',
		'mem':   'Transaction is in mempool',
	},
	'quiet': {
		'none':  'None',
		'block': '{b} {c}',
		'mem':   'mempool',
	}
}

async def main(txid):
	if len(txid) != 64 or not is_hex_str(txid):
		die(2,f'{txid}: invalid transaction ID')

	if cfg.verbose:
		msg(f'TxID: {txid}')

	from mmgen.rpc import rpc_init
	c = await rpc_init(cfg,ignore_wallet=True)

	exitval = 0
	try:
		tip1 = await c.call('getblockcount')
		ret = await c.call('getrawtransaction',txid,True)
		tip2 = await c.call('getblockcount')
	except:
		Msg('\r' + msgs['none'])
		exitval = 1
	else:
		assert tip1 == tip2, 'Blockchain is updating.  Try again later'
		if 'confirmations' in ret:
			confs = ret['confirmations']
			Msg('\r' + msgs['block'].format(b = tip1 - confs + 1, c = confs))
		else:
			Msg('\r' + msgs['mem'])

	return exitval

cfg = Config(opts_data=opts_data)

msgs = msg_data['quiet' if cfg.quiet else 'normal']

if len(cfg._args) != 1:
	die(1,'One transaction ID must be specified')

sys.exit(async_run(main(cfg._args[0])))
