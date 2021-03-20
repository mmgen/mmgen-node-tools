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
mmgen.node_tools.BlocksInfo: Display information about a block or range of blocks
"""

import re
from collections import namedtuple
from time import strftime,gmtime
from decimal import Decimal

from mmgen.common import *

class BlocksInfo:

	total_bytes = 0
	total_weight = 0
	total_solve_time = 0

	bf = namedtuple('block_info_fields',['hdr1','hdr2','fs','bs_key','varname','deps','key'])
	# bs=getblockstats(), bh=getblockheader()
	# If 'bs_key' is set, it's included in self.bs_keys instead of 'key'
	fields = {
		'block':     bf('',     'Block',    '{:<6}',  None,                 'height',[],     None),
		'hash':      bf('',     'Hash',     '{:<64}', None,                 'H',     [],     None),
		'date':      bf('',     'Date',     '{:<19}', None,                 'df',    [],     None),
		'interval':  bf('Solve','Time ',    '{:>8}',  None,                 'td',    [],     None),
		'subsidy':   bf('Sub-', 'sidy',     '{:<5}',  'subsidy',            'su',    ['bs'],  None),
		'totalfee':  bf('',     'Total Fee','{:>10}', 'totalfee',           'tf',    ['bs'], None),
		'size':      bf('',     'Size',     '{:>7}',  None,                 'bs',    [],     'total_size'),
		'weight':    bf('',     'Weight',   '{:>7}',  None,                 'bs',    [],     'total_weight'),
		'fee90':     bf('90%',  'Fee',      '{:>3}',  'feerate_percentiles','fp',    ['bs'], 4),
		'fee75':     bf('75%',  'Fee',      '{:>3}',  'feerate_percentiles','fp',    ['bs'], 3),
		'fee50':     bf('50%',  'Fee',      '{:>3}',  'feerate_percentiles','fp',    ['bs'], 2),
		'fee25':     bf('25%',  'Fee',      '{:>3}',  'feerate_percentiles','fp',    ['bs'], 1),
		'fee10':     bf('10%',  'Fee',      '{:>3}',  'feerate_percentiles','fp',    ['bs'], 0),
		'fee_max':   bf('Max',  'Fee',      '{:>5}',  None,                 'bs',    [],     'maxfeerate'),
		'fee_avg':   bf('Avg',  'Fee',      '{:>3}',  None,                 'bs',    [],     'avgfeerate'),
		'fee_min':   bf('Min',  'Fee',      '{:>3}',  None,                 'bs',    [],     'minfeerate'),
		'nTx':       bf('',     ' nTx ',    '{:>5}',  None,                 'bh',    [],     'nTx'),
		'inputs':    bf('In- ', 'puts',     '{:>5}',  None,                 'bs',    [],     'ins'),
		'outputs':   bf('Out-', 'puts',     '{:>5}',  None,                 'bs',    [],     'outs'),
		'utxo_inc':  bf(' UTXO',' Incr',    '{:>5}',  None,                 'bs',    [],     'utxo_increase'),
		'version':   bf('',     'Version',  '{:<8}',  None,                 'bh',    [],     'versionHex'),
		'difficulty':bf('Diffi-','culty',   '{:<8}',  None,                 'di',    [],      None),
	}
	dfl_fields  = [
		'block',
		'date',
		'interval',
		'subsidy',
		'totalfee',
		'size',
		'weight',
		'fee50',
		'fee25',
		'fee10',
		'fee_avg',
		'fee_min',
		'version',
	]
	fixed_fields = [
		'block',      # until ≈ 09/01/2028 (block 1000000)
		'hash',
		'date',
		'size',       # until ≈ 6x block size increase
		'weight',     # until ≈ 2.5x block size increase
		'version',
		'subsidy',    # until ≈ 01/04/2028 (increases by 1 digit per halving until 9th halving [max 10 digits])
		'difficulty', # until 1.00e+100 (i.e. never)
	]
	# column width adjustment data:
	fs_lsqueeze = ['totalfee','inputs','outputs','nTx']
	fs_rsqueeze = []
	fs_groups = [
		('fee10','fee25','fee50','fee75','fee90','fee_avg','fee_min','fee_max'),
	]
	fs_lsqueeze2 = ['interval']

	all_stats = ['range','diff']
	dfl_stats = ['range','diff']

	funcs = {
		'df': lambda self,loc: strftime('%Y-%m-%d %X',gmtime(self.t_cur)),
		'td': lambda self,loc: (
			'-{:02}:{:02}'.format(abs(self.t_diff)//60,abs(self.t_diff)%60) if self.t_diff < 0 else
			' {:02}:{:02}'.format(self.t_diff//60,self.t_diff%60) ),
		'tf': lambda self,loc: '{:.8f}'.format(loc.bs["totalfee"] * Decimal('0.00000001')),
		'fp': lambda self,loc: loc.bs['feerate_percentiles'],
		'su': lambda self,loc: str(loc.bs['subsidy'] * Decimal('0.00000001')).rstrip('0').rstrip('.'),
		'di': lambda self,loc: '{:.2e}'.format(loc.bh['difficulty']),
	}

	range_data = namedtuple('parsed_range_data',['first','last','from_tip','nblocks','step'])

	t_fmt = lambda self,t: f'{t/86400:.2f} days' if t > 172800 else f'{t/3600:.2f} hrs'

	def __init__(self,cmd_args,opt,rpc):

		def parse_cslist(uarg,full_set,dfl_set,desc):
			usr_set = uarg.lstrip('+').split(',')
			for e in usr_set:
				if e not in full_set:
					die(1,f'{e!r}: unrecognized {desc}')
			res = dfl_set + usr_set if uarg[0] == '+' else usr_set
			# display elements in order:
			return [e for e in full_set if e in res]

		def get_fields():
			return parse_cslist(opt.fields,self.fields,self.dfl_fields,'field')

		def get_stats():
			arg = opt.stats.lower()
			return (
				self.all_stats if arg == 'all' else [] if arg == 'none' else
				parse_cslist(arg,self.all_stats,self.dfl_stats,'stat')
			)

		def gen_fs(fnames):
			for i in range(len(fnames)):
				name = fnames[i]
				ls = (' ','')[name in self.fs_lsqueeze + self.fs_lsqueeze2]
				rs = (' ','')[name in self.fs_rsqueeze]
				if i < len(fnames) - 1 and fnames[i+1] in self.fs_lsqueeze2:
					rs = ''
				if i:
					for group in self.fs_groups:
						if name in group and fnames[i-1] in group:
							ls = ''
							break
				yield ls + self.fields[name].fs + rs

		def parse_cmd_args(): # => (block_list, first, last, step)
			if not cmd_args:
				return (None,self.tip,self.tip,None)
			elif len(cmd_args) == 1:
				r = self.parse_rangespec(cmd_args[0])
				return (
					list(range(r.first,r.last+1,r.step)) if r.step else None,
					r.first,
					r.last,
					r.step
				)
			else:
				return ([self.conv_blkspec(a) for a in cmd_args],None,None,None)

		self.rpc = rpc
		self.opt = opt
		self.tip = rpc.blockcount

		self.block_list,self.first,self.last,self.step = parse_cmd_args()

		fnames = get_fields() if opt.fields else self.dfl_fields

		self.fvals = list(self.fields[name] for name in fnames)
		self.fs    = ''.join(gen_fs(fnames)).strip()
		self.deps  = set(' '.join(v.varname + ' ' + ' '.join(v.deps) for v in self.fvals).split())

		self.bs_keys = [(v.bs_key or v.key) for v in self.fvals if v.bs_key or v.varname == 'bs']
		self.bs_keys.extend(['total_size','total_weight'])

		self.ufuncs = {v.varname:self.funcs[v.varname] for v in self.fvals if v.varname in self.funcs}

		if opt.miner_info:
			fnames.append('miner')
			self.fs += '  {:<5}'
			self.miner_pats = [re.compile(pat) for pat in (
				rb'`/([_a-zA-Z0-9&. #/-]+)/',
				rb'[\xe3\xe4\xe5][\^/](.*?)\xfa',
				rb'([a-zA-Z0-9&. -]+/Mined by [a-zA-Z0-9. ]+)',
				rb'\x08/(.*Mined by [a-zA-Z0-9. ]+)',
				rb'Mined by ([a-zA-Z0-9. ]+)',
				rb'[`]([_a-zA-Z0-9&. #/-]+)[/\xfa]',
				rb'[/^]([a-zA-Z0-9&. #/-]{5,})',
				rb'[/^]([_a-zA-Z0-9&. #/-]+)/',
			)]
		else:
			self.miner_pats = None

		self.block_data = namedtuple('block_data',fnames)
		self.stats = get_stats() if opt.stats else self.dfl_stats

	def conv_blkspec(self,arg):
		if arg == 'cur':
			return self.tip
		elif is_int(arg):
			if int(arg) < 0:
				die(1,f'{arg}: block number must be non-negative')
			elif int(arg) > self.tip:
				die(1,f'{arg}: requested block height greater than current chain tip!')
			else:
				return int(arg)
		else:
			die(1,f'{arg}: invalid block specifier')

	def check_nblocks(self,arg):
		if arg <= 0:
			die(1,'nBlocks must be a positive integer')
		elif arg > self.tip:
			die(1, f"'{arg}': nBlocks must be less than current chain height")
		return arg

	def parse_rangespec(self,arg):

		class RangeParser:
			debug = False

			def __init__(rp,arg):
				rp.arg = rp.orig_arg = arg

			def parse(rp,target):
				ret = getattr(rp,'parse_'+target)()
				if rp.debug: msg(f'arg after parse({target}): {rp.arg}')
				return ret

			def finalize(rp):
				if rp.arg:
					die(1,f'{rp.orig_arg!r}: invalid range specifier')

			def parse_from_tip(rp):
				m = re.match(r'-([0-9]+)(.*)',rp.arg)
				if m:
					res,rp.arg = (m[1],m[2])
					return self.check_nblocks(int(res))

			def parse_abs_range(rp):
				m = re.match(r'([^+-]+)(-([^+-]+)){0,1}(.*)',rp.arg)
				if m:
					if rp.debug: msg(f'abs_range parse: first={m[1]}, last={m[3]}')
					rp.arg = m[4]
					return (
						self.conv_blkspec(m[1]),
						self.conv_blkspec(m[3]) if m[3] else None
					)
				return (None,None)

			def parse_add(rp):
				m = re.match(r'\+([0-9*]+)(.*)',rp.arg)
				if m:
					res,rp.arg = (m[1],m[2])
					if res.strip('*') != res:
						die(1,f"'+{res}': malformed nBlocks specifier")
					if len(res) > 30:
						die(1,f"'+{res}': overly long nBlocks specifier")
					return self.check_nblocks(eval(res)) # res is only digits plus '*', so eval safe

		p = RangeParser(arg)
		from_tip   = p.parse('from_tip')
		first,last = (self.tip-from_tip,None) if from_tip else p.parse('abs_range')
		add1       = p.parse('add')
		add2       = p.parse('add')
		p.finalize()

		if add2 and last is not None:
			die(1,f'{arg!r}: invalid range specifier')

		nblocks,step = (add1,add2) if last is None else (None,add1)

		if p.debug: msg(repr(self.range_data(first,last,from_tip,nblocks,step)))

		if nblocks:
			if first == None:
				first = self.tip - nblocks + 1
			last = first + nblocks - 1

		first = self.conv_blkspec(first)
		last  = self.conv_blkspec(last or first)

		if p.debug: msg(repr(self.range_data(first,last,from_tip,nblocks,step)))

		if first > last:
			die(1,f'{first}-{last}: invalid block range')

		return self.range_data(first,last,from_tip,nblocks,step)

	async def process_blocks(self):

		c = self.rpc
		heights = self.block_list or range(self.first,self.last+1)
		hashes = await c.gathered_call('getblockhash',[(height,) for height in heights])
		self.hdrs = await c.gathered_call('getblockheader',[(H,) for H in hashes])

		async def init(count):
			h0 = (
				self.hdrs[count] if heights[count] == 0 else
				await c.call('getblockheader',await c.call('getblockhash',heights[count]-1))
			)
			self.t_cur = h0['time']
			if count == 0:
				self.first_prev_hdr = h0

		if not self.block_list:
			await init(0)

		for n in range(len(heights)):
			if self.block_list:
				await init(n)
			ret = await self.process_block(heights[n],hashes[n],self.hdrs[n])
			if not self.opt.stats_only:
				self.output_block(ret,n)

	def output_block(self,data,n):
		Msg(self.fs.format(*data))

	async def process_block(self,height,H,hdr):
		class local_vars: pass
		loc = local_vars()
		loc.height = height
		loc.H = H
		loc.bh = hdr

		self.t_diff = hdr['time'] - self.t_cur
		self.t_cur  = hdr['time']
		self.total_solve_time += self.t_diff

		if 'bs' in self.deps:
			loc.bs = self.genesis_stats if height == 0 else await self.rpc.call('getblockstats',H,self.bs_keys)
			self.total_bytes += loc.bs['total_size']
			self.total_weight += loc.bs['total_weight']

		for varname,func in self.ufuncs.items():
			setattr(loc,varname,func(self,loc))

		if self.opt.miner_info:
			miner_info = '-' if height == 0 else await self.get_miner_string(H)

		def gen():
			for v in self.fvals:
				if v.key is None:
					yield getattr(loc,v.varname)
				else:
					yield getattr(loc,v.varname)[v.key]
			if self.opt.miner_info:
				yield miner_info

		return self.block_data(*gen())

	async def get_miner_string(self,H):
		tx0 = (await self.rpc.call('getblock',H))['tx'][0]
		bd = await self.rpc.call('getrawtransaction',tx0,1)
		if type(bd) == tuple:
			return '---'
		else:
			cb = bytes.fromhex(bd['vin'][0]['coinbase'])
			if self.opt.raw_miner_info:
				return repr(cb)
			else:
				for pat in self.miner_pats:
					m = pat.search(cb)
					if m:
						return ''.join(chr(b) for b in m[1] if 31 < b < 127).strip('^').strip('/').replace('/',' ')
			return ''

	def print_header(self):
		hdr1 = [v.hdr1 for v in self.fvals]
		hdr2 = [v.hdr2 for v in self.fvals]
		if self.opt.miner_info:
			hdr1.append('     ')
			hdr2.append('Miner')
		if ''.join(hdr1).replace(' ',''):
			Msg(self.fs.format(*hdr1))
		Msg(self.fs.format(*hdr2))

	def process_stats(self,name):
		return getattr(self,f'print_{name}_stats')()

	async def print_range_stats(self):

		# These figures don’t include the Genesis Block:
		elapsed = self.hdrs[-1]['time'] - self.first_prev_hdr['time']
		nblocks = self.hdrs[-1]['height'] - self.first_prev_hdr['height']

		Msg('Range:      {}-{} ({} blocks [{}])'.format(
			self.hdrs[0]['height'],
			self.hdrs[-1]['height'],
			self.hdrs[-1]['height'] - self.hdrs[0]['height'] + 1, # includes Genesis Block
			self.t_fmt(elapsed) ))

		if elapsed:
			avg_bdi = int(elapsed / nblocks)
			if 'bs' in self.deps:
				total_blocks = len(self.hdrs)
				rate = (self.total_bytes / 10000) / (self.total_solve_time / 36)
				Msg_r(fmt(f"""
					Avg size:   {self.total_bytes//total_blocks} bytes
					Avg weight: {self.total_weight//total_blocks} bytes
					MB/hr:      {rate:0.4f}
					"""))
			Msg(f'Avg BDI:    {avg_bdi/60:.2f} min')

	async def print_diff_stats(self):

		c = self.rpc
		rel = self.tip % 2016

		tip_hdr = (
			self.hdrs[-1] if self.hdrs[-1]['height'] == self.tip else
			await c.call('getblockheader',await c.call('getblockhash',self.tip))
		)

		bdi_avg_blks = 432 # ≈3 days
		bdi_avg_hdr = await c.call('getblockheader',await c.call('getblockhash',self.tip-bdi_avg_blks))
		bdi_avg = ( tip_hdr['time'] - bdi_avg_hdr['time'] ) / bdi_avg_blks

		if rel > bdi_avg_blks:
			rel_hdr = await c.call('getblockheader',await c.call('getblockhash',self.tip-rel))
			bdi = ( tip_hdr['time'] - rel_hdr['time'] ) / rel
			bdi_disp = bdi
		else:
			bdi_adj = float(tip_hdr['difficulty'] / bdi_avg_hdr['difficulty'])
			bdi = bdi_avg * ( (bdi_adj * (bdi_avg_blks-rel)) + rel ) / bdi_avg_blks
			bdi_disp = bdi_avg

		rem = 2016 - rel
		Msg_r(fmt(f"""
			Current height:    {self.tip}
			Next diff adjust:  {self.tip+rem} (in {rem} block{suf(rem)} [{self.t_fmt((rem)*bdi_avg)}])
			BDI (cur period):  {bdi_disp/60:.2f} min
			Cur difficulty:    {tip_hdr['difficulty']:.2e}
			Est. diff adjust: {((600 / bdi) - 1) * 100:+.2f}%
			"""))

	def process_stats_pre(self,i):
		if not (self.opt.stats_only and i == 0):
			Msg('')

	def finalize_output(self): pass

	# 'getblockstats' RPC raises exception on Genesis Block, so provide our own stats:
	genesis_stats = {
		'avgfee': 0,
		'avgfeerate': 0,
		'avgtxsize': 0,
		'feerate_percentiles': [ 0, 0, 0, 0, 0 ],
		'height': 0,
		'ins': 0,
		'maxfee': 0,
		'maxfeerate': 0,
		'maxtxsize': 0,
		'medianfee': 0,
		'mediantxsize': 0,
		'minfee': 0,
		'minfeerate': 0,
		'mintxsize': 0,
		'outs': 1,
		'subsidy': 5000000000,
		'swtotal_size': 0,
		'swtotal_weight': 0,
		'swtxs': 0,
		'total_out': 0,
		'total_size': 0,
		'total_weight': 0,
		'totalfee': 0,
		'txs': 1,
		'utxo_increase': 1,
		'utxo_size_inc': 117
	}
