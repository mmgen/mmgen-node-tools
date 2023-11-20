#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-wallet https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen-wallet https://gitlab.com/mmgen/mmgen-node-tools

"""
mmnode-addrbal: Get balances for arbitrary addresses in the blockchain
"""

import sys

from mmgen.obj import CoinTxID,Int
from mmgen.cfg import Config
from mmgen.util import msg,Msg,die,suf,make_timestr,async_run
from mmgen.color import red

opts_data = {
	'text': {
		'desc': 'Get balances for arbitrary addresses in the blockchain',
		'usage': '[opts] address [address..]',
		'options': """
-h, --help        Print this help message
--, --longhelp    Print help message for long options (common options)
-f, --first-block With tabular output, additionally display first block info
-t, --tabular     Produce compact tabular output
"""
	}
}

def do_output(proto,addr_data,blk_hdrs):

	col1w = len(str(len(addr_data)))
	indent = ' ' * (col1w + 2)

	for n,(addr,unspents) in enumerate(addr_data.items(),1):
		Msg(f'\n{n:{col1w}}) Address: {addr.hl()}')

		if unspents:
			heights = { u['height'] for u in unspents }
			Msg('{}Balance: {}'.format(
				indent,
				proto.coin_amt(sum(u['amount'] for u in unspents)).hl2(unit=True,fs='{:,}') )),
			Msg('{}{} unspent output{} in {} block{}'.format(
				indent,
				red(str(len(unspents))),
				suf(unspents),
				red(str(len(heights))),
				suf(heights) ))
			blk_w = len(str(unspents[-1]['height']))
			fs = '%s{:%s} {:19} {:64} {:4} {}' % (indent,max(5,blk_w))
			Msg(fs.format('Block','Date','TxID','Vout','   Amount'))
			for u in unspents:
				Msg(fs.format(
					u['height'],
					make_timestr( blk_hdrs[u['height']]['time'] ),
					CoinTxID(u['txid']).hl(),
					red(str(u['vout']).rjust(4)),
					proto.coin_amt(u['amount']).fmt(color=True,iwidth=6,prec=8)
				))
		else:
			Msg(f'{indent}No balance')

def do_output_tabular(proto,addr_data,blk_hdrs):

	col1w = len(str(len(addr_data))) + 1
	max_addrw = max(len(addr) for addr in addr_data)
	fb_heights = [str(unspents[0]['height']) if unspents else '' for unspents in addr_data.values()]
	lb_heights = [str(unspents[-1]['height']) if unspents else '' for unspents in addr_data.values()]
	fb_w = max(len(h) for h in fb_heights)
	lb_w = max(len(h) for h in lb_heights)

	fs = (
		' {n:>%s} {a} {u} {b:>%s} {t:19}  {B:>%s} {T:19} {A}' % (col1w,max(5,fb_w),max(4,lb_w))
			if cfg.first_block else
		' {n:>%s} {a} {u} {B:>%s} {T:19} {A}' % (col1w,max(4,lb_w)) )

	Msg('\n' + fs.format(
		n = '',
		a = 'Address'.ljust(max_addrw),
		u = 'UTXOs',
		b = 'First',
		t = 'Block',
		B = 'Last',
		T = 'Block',
		A = '     Amount' ))

	for n,(addr,unspents) in enumerate(addr_data.items(),1):
		if unspents:
			Msg(fs.format(
				n = str(n) + ')',
				a = addr.fmt(width=max_addrw,color=True),
				u = red(str(len(unspents)).rjust(5)),
				b = unspents[0]['height'],
				t = make_timestr( blk_hdrs[unspents[0]['height']]['time'] ),
				B = unspents[-1]['height'],
				T = make_timestr( blk_hdrs[unspents[-1]['height']]['time'] ),
				A = proto.coin_amt(sum(u['amount'] for u in unspents)).fmt(color=True,iwidth=7,prec=8)
			))
		else:
			Msg(fs.format(
				n = str(n) + ')',
				a = addr.fmt(width=max_addrw,color=True),
				u = '    -',
				b = '-',
				t = '',
				B = '-',
				T = '',
				A = '     -' ))

async def main(req_addrs):

	proto = cfg._proto

	from mmgen.addr import CoinAddr
	addrs = [CoinAddr(proto,addr) for addr in req_addrs]

	from mmgen.rpc import rpc_init
	rpc = await rpc_init(cfg,ignore_wallet=True)

	height = await rpc.call('getblockcount')
	Msg(f'{proto.coin} {proto.network.upper()} [height {height}]')

	from mmgen.proto.btc.misc import scantxoutset
	res = await scantxoutset( cfg, rpc, [f'addr({addr})' for addr in addrs] )

	if not res['success']:
		die(1,'UTXO scanning failed or was interrupted')
	elif not res['unspents']:
		msg('Address has no balance' if len(addrs) == 1 else
			'Addresses have no balances' )
	else:
		addr_data = {k:[] for k in addrs}

		if 'desc' in res['unspents'][0]:
			import re
			for unspent in sorted(res['unspents'],key=lambda x: x['height']):
				addr = re.match('addr\((.*?)\)',unspent['desc'])[1]
				addr_data[addr].append(unspent)
		else:
			from mmgen.proto.btc.tx.base import scriptPubKey2addr
			for unspent in sorted(res['unspents'],key=lambda x: x['height']):
				addr = scriptPubKey2addr( proto, unspent['scriptPubKey'] )[0]
				addr_data[addr].append(unspent)

		good_addrs = len([v for v in addr_data.values() if v])

		Msg('Total: {} in {} address{}'.format(
			proto.coin_amt(res['total_amount']).hl2(unit=True,fs='{:,}'),
			red(str(good_addrs)),
			suf(good_addrs,'es')
		))

		blk_heights = {i['height'] for i in res['unspents']}
		blk_hashes = await rpc.batch_call('getblockhash', [(h,) for h in blk_heights])
		blk_hdrs = await rpc.batch_call('getblockheader', [(H,) for H in blk_hashes])

		(do_output_tabular if cfg.tabular else do_output)( proto, addr_data, dict(zip(blk_heights,blk_hdrs)) )

cfg = Config( opts_data=opts_data, init_opts={'rpc_backend':'aiohttp'} )

if len(cfg._args) < 1:
	die(1,'This command requires at least one coin address argument')

try:
	async_run(main(cfg._args))
except KeyboardInterrupt:
	sys.stderr.write('\n')
