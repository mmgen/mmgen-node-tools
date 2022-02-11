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
mmnode-feeview: Visualize the fee structure of a node’s mempool
"""

from mmgen.common import *

min_prec,max_prec,dfl_prec = (0,6,4)
fee_brackets = [
	1, 2, 3, 4, 5, 6,
	8, 10, 12, 14, 16, 18,
	20, 25, 30, 35, 40, 45,
	50, 60, 70, 80, 90,
	100, 120, 140, 160, 180,
	200, 250, 300, 350, 400, 450,
	500, 600, 700, 800, 900,
	1000, 1200, 1400, 1600, 1800,
	2000, 2500, 3000, 3500, 4000, 4500,
	5000, 6000, 7000, 8000, 9000,
	10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000,
	100000, 1000000, 10000000, 100000000, 1000000000, 10000000000, 2100000000000000,
]

opts.init({
	'sets': [
		('detail',True,'ranges',True),
		('detail',True,'show_mb_col',True),
		('detail',True,'precision',6),
	],
	'text': {
		'desc': 'Visualize the fee structure of a node’s mempool',
		'usage':'[opts]',
		'options': f"""
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-c, --include-current Include current bracket’s TXs in cumulative MB value
-d, --detail          Same as --ranges --show-mb-col --precision=6
-e, --show-empty      Show all fee brackets, including empty ones
-i, --ignore-below=B  Ignore fee brackets with less than 'B' bytes of TXs
-l, --log             Log JSON-RPC mempool data to 'mempool.json'
-p, --precision=P     Use 'P' decimal points of precision for megabyte amts
                      (min: {min_prec}, max: {max_prec}, default: {dfl_prec})
-P, --pager           Pipe the output to a pager
-r, --ranges          Display fee brackets as ranges
-s, --show-mb-col     Display column with each fee bracket’s megabyte count
-w, --width=W         Force output width of 'W' columns (default: term width)
""",
	'notes': """
+ By default, fee bracket row labels include only the top of the range.
+ By default, empty fee brackets are not displayed.
+ Mempool amounts are shown in decimal megabytes.
+ Values in the Total MB column are cumulative and represent megabytes of
  transactions in the mempool with fees higher than the TOP of the current
  fee bracket.  To change this behavior, use the --include-current option.

Note that there is no global mempool in Bitcoin, and your node’s mempool may
differ significantly from those of mining nodes depending on uptime and other
factors.
"""
}
})

if opt.ignore_below:
	if opt.show_empty:
		die(1,'Conflicting options: --ignore-below, --show-empty')
	ignore_below = parse_bytespec(opt.ignore_below)

if opt.precision:
	precision = check_int_between(opt.precision,min_prec,max_prec,'--precision arg')
else:
	precision = dfl_prec

if opt.width:
	width = check_int_between(opt.width,40,1024,'--width arg')
else:
	from mmgen.term import get_terminal_size
	width = get_terminal_size()[0]

class fee_bracket:
	def __init__(self,top,bottom):
		self.top = top
		self.bottom = bottom
		self.tx_bytes = 0
		self.tx_bytes_cum = 0
		self.skip = False

def get_fake_data(fn): # for debugging
	import json
	from mmgen.rpc import json_encoder
	from decimal import Decimal
	return json.loads(open(os.path.join(fn)).read(),parse_float=Decimal)

def log(data,fn):
	import json
	from mmgen.rpc import json_encoder
	open(fn,'w').write(json.dumps(data,cls=json_encoder,sort_keys=True,indent=4))

def create_data(coin_amt,mempool):
	out = [fee_bracket(fee_brackets[i],fee_brackets[i-1] if i else 0) for i in range(len(fee_brackets))]

	# populate fee brackets:
	for tx in mempool.values():
		fee = coin_amt(tx['fee']).to_unit('satoshi')
		vsize = tx['vsize']
		for bracket in out:
			if fee / vsize < bracket.top:
				bracket.tx_bytes += vsize
				break

	# remove empty top brackets:
	while out and out[-1].tx_bytes == 0:
		out.pop()

	if not out:
		die(1,'No data!')

	out.reverse() # cumulative totals and display are top-down

	# calculate cumulative byte totals, filter rows:
	tBytes = 0
	for i in out:
		if not (i.tx_bytes or opt.show_empty):
			i.skip = True
		if opt.ignore_below and i.tx_bytes < ignore_below:
			i.skip = True
		i.tx_bytes_cum = tBytes
		tBytes += i.tx_bytes

	return out

def gen_header(host,blockcount):
	yield('MEMPOOL FEE STRUCTURE ({})\n{} UTC\nBlock {}'.format(
		host,
		make_timestr(),
		blockcount,
		))
	if opt.show_empty:
		yield('Displaying all fee brackets')
	elif opt.ignore_below:
		yield('Ignoring fee brackets with less than {} bytes ({})'.format(
			ignore_below,
			int2bytespec(ignore_below,'MB','0.6'),
			))
	if opt.include_current:
		yield('Including transactions in current fee bracket in Total MB amounts')

def fmt_mb(n):
	return int2bytespec(n,'MB',f'0.{precision}',False)

def gen_body(data):
	tx_bytes_max = max(i.tx_bytes for i in data)
	top_max = max(i.top for i in data if not i.skip)
	bot_max = max(i.bottom for i in data if not i.skip)
	col1_w = max(len(f'{bot_max}-{top_max}') if opt.ranges else len(f'{top_max}'),6)
	col2_w = len(fmt_mb(tx_bytes_max)) if opt.show_mb_col else 0
	col3_w = len(fmt_mb(data[-1].tx_bytes_cum))
	col4_w = width - col1_w - col2_w - col3_w - (4 if col2_w else 3)
	if opt.show_mb_col:
		fs = '{a:<%i} {b:>%i} {c:>%i} {d}' % (col1_w,col2_w,col3_w)
	else:
		fs = '{a:<%i} {c:>%i} {d}' % (col1_w,col3_w)

	yield(
		'\n' + fs.format(a='',      b='',                  c=f'{"Total":<{col3_w}}', d='') +
		'\n' + fs.format(a='sat/B', b=f'{"MB":<{col2_w}}', c=f'{"MB":<{col3_w}}',    d='')
	)

	for i in data:
		if not i.skip:
			cum_bytes = i.tx_bytes_cum + i.tx_bytes if opt.include_current else i.tx_bytes_cum
			yield(fs.format(
				a = '{}-{}'.format(i.bottom,i.top) if opt.ranges else i.top,
				b = fmt_mb(i.tx_bytes),
				c = fmt_mb(cum_bytes),
				d = '-' * int(col4_w * ( i.tx_bytes / tx_bytes_max )) ))

	yield(fs.format(
		a = 'TOTAL',
		b = '',
		c = fmt_mb(data[-1].tx_bytes_cum + data[-1].tx_bytes),
		d = '' ))

async def main():

	from mmgen.protocol import init_proto_from_opts
	proto = init_proto_from_opts(need_amt=True)

	from mmgen.rpc import rpc_init
	c = await rpc_init(proto)

#	pmsg(await c.call('getmempoolinfo'))
	mempool = await c.call('getrawmempool',True)
#	mempool = get_fake_data('test_data/mempool-sample.json')

	if opt.log:
		log(mempool,'mempool.json')

	data = create_data(proto.coin_amt,mempool)

	(do_pager if opt.pager else print)(
		'\n'.join(gen_header(c.host,await c.call('getblockcount'))) + '\n' +
		'\n'.join(gen_body(data))
		)

run_session(main())
