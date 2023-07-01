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
mmnode-halving-calculator: Estimate date(s) of future block subsidy halving(s)
"""

import time
from decimal import Decimal

from mmgen.cfg import Config
from mmgen.util import async_run

bdr_proj = 9.95

opts_data = {
	'sets': [('mined',True,'list',True)],
	'text': {
		'desc': 'Estimate date(s) of future block subsidy halving(s)',
		'usage':'[opts]',
		'options': f"""
-h, --help          Print this help message
--, --longhelp      Print help message for long options (common options)
-l, --list          List historical and projected halvings
-m, --mined         Same as above, plus list coins mined
-r, --bdr-proj=I    Block discovery interval for projected halvings (default:
                    {bdr_proj:.5f} min)
-s, --sample-size=N Block range to calculate block discovery interval for next
                    halving estimate (default: dynamically calculated)
""" }
}

cfg = Config(opts_data=opts_data)

if cfg.bdr_proj:
	bdr_proj = float(cfg.bdr_proj)

def date(t):
	return '{}-{:02}-{:02} {:02}:{:02}:{:02}'.format(*time.gmtime(t)[:6])

def dhms(t):
	t,neg = (-t,'-') if t < 0 else (t,' ')
	return f'{neg}{t//60//60//24} days, {t//60//60%24:02}:{t//60%60:02}:{t%60:02} h/m/s'

def time_diff_warning(t_diff):
	if abs(t_diff) > 60*60:
		print('Warning: block tip time is {} {} clock time!'.format(
			dhms(abs(t_diff)),
			('behind','ahead of')[t_diff<0]))

async def main():

	proto = cfg._proto

	from mmgen.rpc import rpc_init
	c = await rpc_init( cfg, proto, ignore_wallet=True )

	tip = await c.call('getblockcount')
	assert tip > 1, 'block tip must be > 1'
	remaining = proto.halving_interval - tip % proto.halving_interval
	sample_size = int(cfg.sample_size) if cfg.sample_size else min(tip-1,max(remaining,144))

	cur,old = await c.gathered_call('getblockstats',((tip,),(tip - sample_size,)))

	clock_time = int(time.time())
	time_diff_warning(clock_time - cur['time'])
	bdr = (cur['time'] - old['time']) / sample_size
	t_rem = remaining * int(bdr)
	t_next = cur['time'] + t_rem

	if proto.name == 'BitcoinCash':
		sub = proto.coin_amt(str(cur['subsidy']))
	else:
		sub = cur['subsidy'] * proto.coin_amt.satoshi

	def print_current_stats():
		print(
			f'Current block:             {tip:>7}\n'
			f'Next halving block:        {tip + remaining:>7}\n'
			f'Halving interval:          {proto.halving_interval:>7}\n'
			f'Blocks since last halving: {proto.halving_interval - remaining:>7}\n'
			f'Blocks until next halving: {remaining:>7}\n\n'
			f'Current block subsidy:     {str(sub).rstrip("0")} {proto.coin}\n'
			f'Current block discovery interval (over last {sample_size} blocks): {bdr/60:0.2f} min\n\n'
			f'Current clock time (UTC):  {date(clock_time)}\n'
			f'Est. halving date (UTC):   {date(t_next)}\n'
			f'Est. time until halving:  {dhms(cur["time"] + t_rem - clock_time)}'
		)

	async def print_halvings():
		halving_blocknums = [i*proto.halving_interval for i in range(proto.max_halvings+1)][1:]
		hist_halvings = await c.gathered_call('getblockstats',([(n,) for n in halving_blocknums if n <= tip]))
		halving_secs = bdr_proj * 60 * proto.halving_interval
		nhist = len(hist_halvings)
		nSubsidy = int(proto.start_subsidy / proto.coin_amt.satoshi)

		block0_hash = await c.call('getblockhash',0)
		block0_date = (await c.call('getblock',block0_hash))['time']

		def gen_data():
			total_mined = 0
			date = block0_date
			for n,blk in enumerate(halving_blocknums):
				mined = (nSubsidy >> n) * proto.halving_interval
				if n == 0:
					mined -= nSubsidy # subtract unspendable genesis block subsidy
				total_mined += mined
				sub = nSubsidy >> n+1 if n+1 < proto.max_halvings else 0
				bdi = (
					(hist_halvings[n]['time'] - date) / (proto.halving_interval * 60) if n < nhist
					else bdr/60 if n == nhist
					else bdr_proj
				)
				date = (
					hist_halvings[n]['time'] if n < nhist
					else t_next + int((n - nhist) * halving_secs)
				)
				yield ( n, sub, blk, mined, total_mined, bdi, date )
				if sub == 0:
					break

		fs = (
			'  {a:<7} {b:>8}  {c:19}{d:2}  {e:10}  {f}',
			'  {a:<7} {b:>8}  {c:19}{d:2}  {e:10}  {f:17} {g:17}  {h}'
		)[bool(cfg.mined)]

		print(
			f'Historical/Estimated/Projected Halvings ({proto.coin}):\n\n'
			+ f'  Sample size for next halving estimate (E):           {sample_size} blocks\n'
			+ f'  Block discovery interval for projected halvings (P): {bdr_proj:.5f} minutes\n\n'
			+ fs.format(
				a = 'HALVING',
				b = 'BLOCK',
				c = 'DATE',
				d = '',
				e = f'BDI (mins)',
				f = f'SUBSIDY ({proto.coin})',
				g = f'MINED ({proto.coin})',
				h = f'TOTAL MINED ({proto.coin})'
			)
			+ '\n'
			+ fs.format(
				a = '-' * 7,
				b = '-' * 8,
				c = '-' * 19,
				d = '-' * 2,
				e = '-' * 10,
				f = '-' * 13,
				g = '-' * 17,
				h = '-' * 17
			)
			+ '\n'
			+ '\n'.join(fs.format(
							a = n + 1,
							b = blk,
							c = date(t),
							d = ' P' if n > nhist else '' if n < nhist else ' E',
							e = f'{bdr:8.5f}',
							f = proto.coin_amt(sub,from_unit='satoshi').fmt(iwidth=2,prec=8),
							g = proto.coin_amt(mined,from_unit='satoshi').fmt(iwidth=8,prec=8),
							h = proto.coin_amt(total_mined,from_unit='satoshi').fmt(iwidth=8,prec=8)
						) for n,sub,blk,mined,total_mined,bdr,t in gen_data())
		)

	if cfg.list:
		await print_halvings()
	else:
		print_current_stats()

async_run(main())
