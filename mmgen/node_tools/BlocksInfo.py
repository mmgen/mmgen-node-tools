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

import re,json
from collections import namedtuple
from time import strftime,gmtime
from decimal import Decimal

from mmgen.common import *
from mmgen.rpc import json_encoder

class BlocksInfo:

	total_bytes = 0
	total_weight = 0
	total_solve_time = 0
	header_printed = False

	bf = namedtuple('block_info_fields',['fmt_func','src','fs','hdr1','hdr2','key1','key2'])
	# bh=getblockheader, bs=getblockstats, lo=local
	fields = {
		'block':      bf( None, 'bh', '{:<6}',  '',      'Block',     'height',              None ),
		'hash':       bf( None, 'bh', '{:<64}', '',      'Hash',      'hash',                None ),
		'date':       bf( 'da', 'bh', '{:<19}', '',      'Date',      'time',                None ),
		'interval':   bf( 'td', 'lo', '{:>8}',  'Solve', 'Time ',     'interval',            None ),
		'subsidy':    bf( 'su', 'bs', '{:<5}',  'Sub-',  'sidy',      'subsidy',             None ),
		'totalfee':   bf( 'tf', 'bs', '{:>10}', '',      'Total Fee', 'totalfee',            None ),
		'size':       bf( None, 'bs', '{:>7}',  '',      'Size',      'total_size',          None ),
		'weight':     bf( None, 'bs', '{:>7}',  '',      'Weight',    'total_weight',        None ),
		'fee90':      bf( None, 'bs', '{:>3}',  '90%',   'Fee',       'feerate_percentiles', 4 ),
		'fee75':      bf( None, 'bs', '{:>3}',  '75%',   'Fee',       'feerate_percentiles', 3 ),
		'fee50':      bf( None, 'bs', '{:>3}',  '50%',   'Fee',       'feerate_percentiles', 2 ),
		'fee25':      bf( None, 'bs', '{:>3}',  '25%',   'Fee',       'feerate_percentiles', 1 ),
		'fee10':      bf( None, 'bs', '{:>3}',  '10%',   'Fee',       'feerate_percentiles', 0 ),
		'fee_max':    bf( None, 'bs', '{:>5}',  'Max',   'Fee',       'maxfeerate',          None ),
		'fee_avg':    bf( None, 'bs', '{:>3}',  'Avg',   'Fee',       'avgfeerate',          None ),
		'fee_min':    bf( None, 'bs', '{:>3}',  'Min',   'Fee',       'minfeerate',          None ),
		'nTx':        bf( None, 'bh', '{:>5}',  '',      ' nTx ',     'nTx',                 None ),
		'inputs':     bf( None, 'bs', '{:>5}',  'In- ',  'puts',      'ins',                 None ),
		'outputs':    bf( None, 'bs', '{:>5}',  'Out-',  'puts',      'outs',                None ),
		'utxo_inc':   bf( None, 'bs', '{:>6}',  ' UTXO', ' Incr',     'utxo_increase',       None ),
		'version':    bf( None, 'bh', '{:<8}',  '',      'Version',   'versionHex',          None ),
		'difficulty': bf( 'di', 'bh', '{:<8}',  'Diffi-','culty',     'difficulty',          None ),
		'miner':      bf( None, 'lo', '{:<5}',  '',      'Miner',     'miner',               None ),
	}
	dfl_fields = (
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
	)
	fixed_fields = (
		'block',      # until ≈ 09/01/2028 (block 1000000)
		'hash',
		'date',
		'size',       # until ≈ 6x block size increase
		'weight',     # until ≈ 2.5x block size increase
		'version',
		'subsidy',    # until ≈ 01/04/2028 (increases by 1 digit per halving until 9th halving [max 10 digits])
		'difficulty', # until 1.00e+100 (i.e. never)
	)

	# column width adjustment data:
	fs_lsqueeze = ('totalfee','inputs','outputs','nTx')
	fs_rsqueeze = ()
	fs_groups = (
		('fee10','fee25','fee50','fee75','fee90','fee_avg','fee_min','fee_max'),
	)
	fs_lsqueeze2 = ('interval',)

	all_stats = ['col_avg','range','avg','total','diff']
	dfl_stats = ['range','avg','diff']
	noindent_stats = ['col_avg']

	avg_stats_skip = {'block', 'hash', 'date', 'version','miner'}
	stats_deps = {
		'avg':    set(fields) - avg_stats_skip,
		'col_avg':set(fields) - avg_stats_skip,
		'total':  {'interval','subsidy','totalfee','nTx','inputs','outputs','utxo_inc'},
		'range':  {},
		'diff':   {},
	}

	fmt_funcs = {
		'da': lambda arg: strftime('%Y-%m-%d %X',gmtime(arg)),
		'td': lambda arg: (
			'-{:02}:{:02}'.format(abs(arg)//60,abs(arg)%60) if arg < 0 else
			' {:02}:{:02}'.format(arg//60,arg%60) ),
		'tf': lambda arg: '{:.8f}'.format(arg * Decimal('0.00000001')),
		'su': lambda arg: str(arg * Decimal('0.00000001')).rstrip('0').rstrip('.'),
		'di': lambda arg: '{:.2e}'.format(arg),
	}

	range_data = namedtuple('parsed_range_data',['first','last','from_tip','nblocks','step'])

	t_fmt = lambda self,t: f'{t/86400:.2f} days' if t > 172800 else f'{t/3600:.2f} hrs'

	def __init__(self,cmd_args,opt,rpc):

		def parse_cslist(uarg,full_set,dfl_set,desc):
			m = re.match('([+-]){1}',uarg)
			pfx = m[1] if m else None
			usr_set = set((uarg[1:] if m else uarg).split(','))
			dfl_set = set(dfl_set)
			for e in usr_set:
				if e not in full_set:
					die(1,f'{e!r}: unrecognized {desc}')
			res = (
				dfl_set | usr_set if pfx == '+' else
				dfl_set - usr_set if pfx == '-' else
				usr_set
			)
			# display elements in order:
			return [e for e in full_set if e in res]

		def parse_cs_uarg(uarg,full_set,dfl_set,desc):
			return (
				full_set if uarg == 'all' else [] if uarg == 'none' else
				parse_cslist(uarg,full_set,dfl_set,desc)
			)

		def get_fields():
			return parse_cs_uarg(opt.fields,list(self.fields),self.dfl_fields,'field')

		def get_stats():
			return parse_cs_uarg(opt.stats.lower(),self.all_stats,self.dfl_stats,'stat')

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

		self.fnames = tuple(
			[f for f in self.fields if self.fields[f].src == 'bh' or f == 'interval'] if opt.header_info else
			get_fields() if opt.fields else
			self.dfl_fields
		)
		if opt.miner_info and 'miner' not in self.fnames:
			self.fnames += ('miner',)

		self.stats = get_stats() if opt.stats else self.dfl_stats

		# Display diff stats by default only if user-requested range ends with chain tip
		if 'diff' in self.stats and not opt.stats and self.last != self.tip:
			self.stats.remove('diff')

		if {'avg','col_avg'} <= set(self.stats) and opt.stats_only:
			self.stats.remove('col_avg')

		if opt.full_stats:
			add_fnames = {fname for sname in self.stats for fname in self.stats_deps[sname]}
			self.fnames = tuple(f for f in self.fields if f in {'block'} | set(self.fnames) | add_fnames )
		else:
			if 'col_avg' in self.stats and not self.fnames:
				self.stats.remove('col_avg')

		# self.fnames is now finalized

		self.fvals = [self.fields[name] for name in self.fnames]
		self.fs    = ''.join(self.gen_fs(self.fnames)).strip()

		self.bs_keys = set(
			[v.key1 for v in self.fvals if v.src == 'bs'] +
			['total_size','total_weight']
		)

		if 'miner' in self.fnames:
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

		self.block_data = namedtuple('block_data',self.fnames)
		self.deps = { v.src for v in self.fvals }

	def gen_fs(self,fnames,fill=[],fill_char='-',add_name=False):
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
			repl = (name if add_name else '') + ':' + (fill_char if name in fill else '')
			yield (ls + self.fields[name].fs.replace(':',repl) + rs)

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

		async def get_hdrs(heights):
			hashes = await c.gathered_call('getblockhash',[(height,) for height in heights])
			return await c.gathered_call('getblockheader',[(H,) for H in hashes])

		c = self.rpc

		heights = self.block_list or range(self.first,self.last+1)
		self.hdrs = await get_hdrs(heights)

		if self.block_list:
			self.prev_hdrs = await get_hdrs([(n-1 if n else 0) for n in self.block_list])
			self.first_prev_hdr = self.prev_hdrs[0]
		else:
			self.first_prev_hdr = (
				self.hdrs[0] if heights[0] == 0 else
				await c.call('getblockheader',await c.call('getblockhash',heights[0]-1))
			)

		self.t_cur = self.first_prev_hdr['time']
		self.res = []

		for n in range(len(heights)):
			if self.block_list:
				self.t_cur = self.prev_hdrs[n]['time']
			ret = await self.process_block(self.hdrs[n])
			self.res.append(ret)
			if self.fnames and not self.opt.stats_only:
				self.output_block(ret,n)

	def output_block(self,data,n):
		def gen():
			for k,v in data._asdict().items():
				func = self.fields[k].fmt_func
				yield self.fmt_funcs[func](v) if func else v
		Msg(self.fs.format(*gen()))

	async def process_block(self,hdr):

		self.t_diff = hdr['time'] - self.t_cur
		self.t_cur  = hdr['time']
		self.total_solve_time += self.t_diff

		blk_data = {
			'bh': hdr,
			'lo': { 'interval': self.t_diff }
		}

		if 'bs' in self.deps:
			bs = (
				self.genesis_stats if hdr['height'] == 0 else
				await self.rpc.call('getblockstats',hdr['hash'],list(self.bs_keys))
			)
			self.total_bytes += bs['total_size']
			self.total_weight += bs['total_weight']
			blk_data['bs'] = bs

		if 'miner' in self.fnames:
			blk_data['lo']['miner'] = '-' if hdr['height'] == 0 else await self.get_miner_string(hdr['hash'])

		def gen():
			for v in self.fvals:
				yield (
					blk_data[v.src][v.key1] if v.key2 is None else
					blk_data[v.src][v.key1][v.key2]
				)

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
		Msg('\n'.join(self.gen_header()))
		self.header_printed = True

	def gen_header(self):
		hdr1 = [v.hdr1 for v in self.fvals]
		hdr2 = [v.hdr2 for v in self.fvals]
		if ''.join(hdr1):
			yield self.fs.format(*hdr1)
		yield self.fs.format(*hdr2)

	def process_stats(self,sname):
		method = getattr(self,f'create_{sname}_stats',None)
		return self.output_stats(method() if method else self.create_stats(sname),sname)

	def fmt_stat_item(self,fs,s):
		return fs.format(s) if type(fs) == str else fs(s)

	async def output_stats(self,res,sname):

		def gen(data):
			for d in data:
				if len(d) == 2:
					yield (indent+d[0]).format(**{k:self.fmt_stat_item(*v) for k,v in d[1].items()})
				elif len(d) == 4:
					yield (indent+d[0]).format(self.fmt_stat_item(d[2],d[3]))
				elif type(d) == str:
					yield d
				else:
					assert False, f'{d}: invalid stats data'

		foo,data = await res
		indent = '' if sname in self.noindent_stats else '  '
		Msg('\n'.join(gen(data)))

	async def create_range_stats(self):
		# These figures don’t include the Genesis Block:
		elapsed = self.hdrs[-1]['time'] - self.first_prev_hdr['time']
		nblocks = self.hdrs[-1]['height'] - self.first_prev_hdr['height']
		total_blks = len(self.hdrs)
		step_disp = f', nBlocks={total_blks}, step={self.step}' if self.step else ''
		def gen():
			yield 'Range Statistics:'
			yield (
				'Range:      {start}-{end} ({range} blocks [{elapsed}]%s)' % step_disp, {
					'start':   ('{}', self.hdrs[0]['height']),
					'end':     ('{}', self.hdrs[-1]['height']),
					'range':   ('{}', self.hdrs[-1]['height'] - self.hdrs[0]['height'] + 1),
					'elapsed': (self.t_fmt, elapsed),
					'nBlocks': ('{}', total_blks),
					'step':    ('{}', self.step),
				}
			)
			if elapsed:
				yield ( 'Start:      {}',       'start_date',  self.fmt_funcs['da'], self.hdrs[0]['time']  )
				yield ( 'End:        {}',       'end_date',    self.fmt_funcs['da'], self.hdrs[-1]['time']  )
				yield ( 'Avg BDI:    {} min',   'avg_bdi',     '{:.2f}',  elapsed / nblocks / 60 )

		return ( 'range', gen() )

	async def create_diff_stats(self):

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

		return ( 'difficulty', (
			'Difficulty Statistics:',
			('Current height:    {}', 'chain_tip', '{}', self.tip),
			('Next diff adjust:  {next_diff_adjust} (in {blks_remaining} block%s [{time_remaining}])' % suf(rem),
				{
					'next_diff_adjust': ('{}', self.tip + rem),
					'blks_remaining':   ('{}', rem),
					'time_remaining':   (self.t_fmt, rem * bdi_avg)
				}
			),
			('Avg BDI:           {avg_bdi} min (over {avg_bdi_blks}-block period)',
				{
					'avg_bdi':      ('{:.2f}', bdi_disp/60),
					'avg_bdi_blks': ('{}',     max(rel,bdi_avg_blks))
				}
			),
			('Cur difficulty:    {}', 'cur_diff',            '{:.2e}',  tip_hdr['difficulty']),
			('Est. diff adjust: {}%', 'est_diff_adjust_pct', '{:+.2f}', ((600 / bdi) - 1) * 100),
		))

	async def create_col_avg_stats(self):
		def gen():
			for field in self.fnames:
				if field in self.avg_stats_skip:
					yield ( field, ('{}','') )
				else:
					ret = sum(getattr(block,field) for block in self.res) // len(self.res)
					func = self.fields[field].fmt_func
					yield ( field, ( (self.fmt_funcs[func] if func else '{}'), ret ))
		if not self.header_printed:
			self.print_header()
		fs = ''.join(self.gen_fs(self.fnames,fill=self.avg_stats_skip,add_name=True)).strip()
		return ('column_averages', ('Column averages:', (fs, dict(gen())) ))

	def avg_stats_data(self,data,spec_conv,spec_val):
		coin = self.rpc.proto.coin
		return data(
			hdr = 'Averages for processed blocks:',
			func = lambda field: sum(getattr(block,field) for block in self.res) // len(self.res),
			spec_sufs = { 'subsidy': f' {coin}', 'totalfee': f' {coin}' },
			spec_convs = {
				'interval':    spec_conv(0,  lambda arg: secs_to_ms(arg)),
				'utxo_inc':    spec_conv(-1, '{:<+}'),
				'mb_per_hour': spec_conv(0,  '{:.4f}'),
			},
			spec_vals = (
				spec_val(
					'mb_per_hour', 'MB/hr', 'interval',
					lambda values: 'bs' in self.deps,
					lambda values: (self.total_bytes / 10000) / (self.total_solve_time / 36)
				),
			)
		)

	def total_stats_data(self,data,spec_conv,spec_val):
		coin = self.rpc.proto.coin
		return data(
			hdr = 'Totals for processed blocks:',
			func = lambda field: sum(getattr(block,field) for block in self.res),
			spec_sufs = { 'subsidy': f' {coin}', 'totalfee': f' {coin}', 'reward': f' {coin}' },
			spec_convs = {
				'interval': spec_conv(0,  lambda arg: secs_to_dhms(arg)),
				'utxo_inc': spec_conv(-1, '{:<+}'),
				'reward':   spec_conv(0,  self.fmt_funcs['tf']),
			},
			spec_vals = (
				spec_val(
					'reward', 'Reward', 'totalfee',
					lambda values: {'subsidy','totalfee'} <= set(values),
					lambda values: values['subsidy'] + values['totalfee']
				),
			)
		)

	async def create_stats(self,sname):

		def convert_stats_hdr(field):
			v = self.fields[field]
			return '{} {}'.format(v.hdr1.strip(), v.hdr2.strip()).replace('- ','') if v.hdr1 else v.hdr2.strip()

		d = getattr(self,f'{sname}_stats_data')(
			namedtuple('stats_data',['hdr','func','spec_sufs','spec_convs','spec_vals']),
			namedtuple('spec_conv',['width_adj','conv']),
			namedtuple('spec_val',['name','lbl','insert_after','condition','code'])
		)

		fnames = [n for n in self.fnames if n in self.stats_deps[sname]]
		lbls   = {n:convert_stats_hdr(n) for n in fnames}
		values = {n:d.func(n) for n in fnames}
		col1_w = max((len(l) for l in lbls.values()),default=0) + 2

		for v in d.spec_vals:
			if v.condition(values):
				try:    idx = fnames.index(v.insert_after) + 1
				except: idx = 0
				fnames.insert(idx,v.name)
				lbls[v.name] = v.lbl
				values[v.name] = v.code(values)

		def gen():
			for n,fname in enumerate(fnames):
				spec_conv = d.spec_convs.get(fname)
				yield (
					'{lbl:{wid}} {{}}{suf}'.format(
						lbl = lbls[fname] + ':',
						wid = col1_w + (spec_conv.width_adj if spec_conv else 0),
						suf = d.spec_sufs.get(fname) or ''
					),
					fname,
					spec_conv.conv if spec_conv else (
						(lambda x: self.fmt_funcs[x] if x else '{}')(self.fields[fname].fmt_func)
					),
					values[fname]
				)

		return ( sname, (d.hdr,) + tuple(gen()) )

	def process_stats_pre(self,i):
		if (self.fnames and not self.opt.stats_only) or i != 0:
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

class JSONBlocksInfo(BlocksInfo):

	def __init__(self,cmd_args,opt,rpc):
		super().__init__(cmd_args,opt,rpc)
		if opt.json_raw:
			self.output_block = self.output_block_raw
			self.fmt_stat_item = self.fmt_stat_item_raw
		Msg_r('{')

	async def process_blocks(self):
		Msg_r('"block_data": [')
		await super().process_blocks()
		Msg_r(']')

	def output_block_raw(self,data,n):
		Msg_r( (', ','')[n==0] + json.dumps(data._asdict(),cls=json_encoder) )

	def output_block(self,data,n):
		def gen():
			for k,v in data._asdict().items():
				func = self.fields[k].fmt_func
				yield ( k, (self.fmt_funcs[func](v) if func else v) )
		Msg_r( (', ','')[n==0] + json.dumps(dict(gen()),cls=json_encoder) )

	def print_header(self): pass

	def fmt_stat_item_raw(self,fs,s):
		return s

	async def output_stats(self,res,sname):

		def gen(data):
			for d in data:
				if len(d) == 2:
					for k,v in d[1].items():
						yield (k,self.fmt_stat_item(*v))
				elif len(d) == 4:
					yield (d[1],self.fmt_stat_item(d[2],d[3]))
				elif type(d) != str:
					assert False, f'{d}: invalid stats data'

		varname,data = await res
		Msg_r(', "{}_data": {}'.format( varname, json.dumps(dict(gen(data)),cls=json_encoder) ))

	def process_stats_pre(self,i): pass

	def finalize_output(self):
		Msg('}')
