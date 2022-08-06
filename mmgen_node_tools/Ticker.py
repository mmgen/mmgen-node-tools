#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen https://gitlab.com/mmgen/mmgen-node-tools

"""
mmgen_node_tools.Ticker: Display price information for cryptocurrency and other assets
"""

api_host = 'api.coinpaprika.com'
api_url  = f'https://{api_host}/v1/ticker'
ratelimit = 240
btc_ratelimit = 10

# We use deprecated coinpaprika ‘ticker’ API for now because it returns ~45% less data.
# Old ‘ticker’ API  (/v1/ticker):  data['BTC']['price_usd']
# New ‘tickers’ API (/v1/tickers): data['BTC']['quotes']['USD']['price']

# Possible alternatives:
# - https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,LTC&tsyms=USD,EUR

import sys,os,time,json,yaml
from subprocess import run,PIPE,CalledProcessError
from decimal import Decimal
from collections import namedtuple
from mmgen.opts import opt
from mmgen.globalvars import g
from mmgen.color import *
from mmgen.util import die,fmt_list,msg,msg_r,Msg,do_pager,suf,fmt

homedir = os.getenv('HOME')
cachedir = os.path.join(homedir,'.cache','mmgen-node-tools')
cfg_fn = 'ticker-cfg.yaml'
portfolio_fn = 'ticker-portfolio.yaml'

def assets_list_gen(cfg_in):
	for k,v in cfg_in.cfg['assets'].items():
		yield('')
		yield(k.upper())
		for e in v:
			yield('  {:4s} {}'.format(*e.split('-',1)))

def gen_data(data):
	"""
	Filter the raw data and return it as a dict keyed by the IDs of the assets
	we want to display.

	Add dummy entry for USD and entry for user-specified asset, if any.

	Since symbols in source data are not guaranteed to be unique (e.g. XAG), we
	must search the data twice: first for unique IDs, then for symbols while
	checking for duplicates.
	"""

	def dup_sym_errmsg(dup_sym):
		return (
			f'The symbol {dup_sym!r} is shared by the following assets:\n' +
			'\n  ' + '\n  '.join(d['id'] for d in data if d['symbol'] == dup_sym) +
			'\n\nPlease specify the asset by one of the full IDs listed above\n' +
			f'instead of {dup_sym!r}'
		)

	def check_assets_found(wants,found,keys=['symbol','id']):
		error = False
		for k in keys:
			missing = wants[k] - found[k]
			if missing:
				msg(
					('The following IDs were not found in source data:\n{}' if k == 'id' else
					'The following symbols could not be resolved:\n{}').format(
						fmt_list(missing,fmt='col',indent='  ')
				))
				error = True
		if error:
			die(1,'Missing data, exiting')

	rows_want = {
		'id':     {r.id for r in cfg.rows if getattr(r,'id',None)} - {'usd-us-dollar'},
		'symbol': {r.symbol for r in cfg.rows if isinstance(r,tuple) and r.id is None} - {'USD'},
	}
	usr_rate_assets = tuple(u.rate_asset for u in cfg.usr_rows + cfg.usr_columns if u.rate_asset)
	usr_rate_assets_want = {
		'id':     {a.id for a in usr_rate_assets if a.id},
		'symbol': {a.symbol for a in usr_rate_assets if not a.id}
	}
	usr_assets = cfg.usr_rows + cfg.usr_columns + tuple(c for c in (cfg.query or ()) if c)
	usr_wants = {
		'id': (
			{a.id for a in usr_assets + usr_rate_assets if a.id} -
			{a.id for a in usr_assets if a.rate and a.id} - {'usd-us-dollar'} )
		,
		'symbol': (
			{a.symbol for a in usr_assets + usr_rate_assets if not a.id} -
			{a.symbol for a in usr_assets if a.rate} - {'USD'} ),
	}

	found = { 'id': set(), 'symbol': set() }
	rate_assets = {}

	for k in ['id','symbol']:
		wants = rows_want[k] | usr_wants[k]
		if wants:
			for d in data:
				if d[k] in wants:
					if d[k] in found[k]:
						die(1,dup_sym_errmsg(d[k]))
					yield (d['id'],d)
					found[k].add(d[k])
					if d[k] in usr_rate_assets_want[k]:
						rate_assets[d['symbol']] = d # NB: using symbol instead of ID
					if k == 'id' and len(found[k]) == len(wants):
						break

	for d in data:
		if d['id'] == 'btc-bitcoin':
			btcusd = Decimal(d['price_usd'])
			break

	for asset in (cfg.usr_rows + cfg.usr_columns):
		if asset.rate:
			"""
			User-supplied rate overrides rate from source data.
			"""
			_id = asset.id or f'{asset.symbol}-user-asset-{asset.symbol}'.lower()
			ra_rate = Decimal(rate_assets[asset.rate_asset.symbol]['price_usd']) if asset.rate_asset else 1
			yield ( _id, {
				'symbol': asset.symbol,
				'id': _id,
				'price_usd': str(Decimal(ra_rate/asset.rate)),
				'price_btc': str(Decimal(ra_rate/asset.rate/btcusd)),
				'last_updated': int(now),
			})

	yield ('usd-us-dollar', {
		'symbol': 'USD',
		'id': 'usd-us-dollar',
		'price_usd': '1.0',
		'price_btc': str(Decimal(1/btcusd)),
		'last_updated': int(now),
	})

	check_assets_found(usr_wants,found)

def get_src_data(curl_cmd):

	tor_captcha_msg = f"""
		If you’re using Tor, the API request may have failed due to Captcha protection.
		A workaround for this issue is to retrieve the JSON data with a browser from
		the following URL:

		    {api_url}

		and save it to:

		    ‘{cfg.cachedir}/ticker.json’

		Then invoke the program with --cached-data and without --btc
	"""

	def rate_limit_errmsg(timeout,elapsed):
		return (
			f'Rate limit exceeded!  Retry in {timeout-elapsed} seconds' +
			('' if cfg.btc_only else ', or use --cached-data or --btc')
		)

	if not os.path.exists(cachedir):
		os.makedirs(cachedir)

	if cfg.btc_only:
		fn = os.path.join(cfg.cachedir,'ticker-btc.json')
		timeout = 5 if g.test_suite else btc_ratelimit
	else:
		fn = os.path.join(cfg.cachedir,'ticker.json')
		timeout = 5 if g.test_suite else ratelimit

	fn_rel = os.path.relpath(fn,start=homedir)

	if not os.path.exists(fn):
		open(fn,'w').write('{}')

	if opt.cached_data:
		json_text = open(fn).read()
	else:
		elapsed = int(time.time() - os.stat(fn).st_mtime)
		if elapsed >= timeout:
			msg_r(f'Fetching data from {api_host}...')
			try:
				cp = run(curl_cmd,check=True,stdout=PIPE)
			except CalledProcessError as e:
				msg('')
				from .Misc import curl_exit_codes
				msg(red(curl_exit_codes[e.returncode]))
				msg(red('Command line:\n  {}'.format( ' '.join((repr(i) if ' ' in i else i) for i in e.cmd) )))
				from mmgen.exception import MMGenCalledProcessError
				raise MMGenCalledProcessError(f'Subprocess returned non-zero exit status {e.returncode}')
			json_text = cp.stdout.decode()
			msg('done')
		else:
			die(1,rate_limit_errmsg(timeout,elapsed))

	try:
		data = json.loads(json_text)
	except:
		msg(json_text[:1024] + '...')
		msg(orange(fmt(tor_captcha_msg,strip_char='\t')))
		die(2,'Retrieved data is not valid JSON, exiting')

	if not data:
		if opt.cached_data:
			die(1,'No cached data!  Run command without --cached-data option to retrieve data from remote host')
		else:
			die(2,'Remote host returned no data!')
	elif 'error' in data:
		die(1,data['error'])

	if opt.cached_data:
		msg(f'Using cached data from ~/{fn_rel}')
	else:
		open(fn,'w').write(json_text)
		msg(f'JSON data cached to ~/{fn_rel}')

	return data

def main(cfg_parm,cfg_in_parm):

	def update_sample_file(usr_cfg_file):
		src_data = files('mmgen_node_tools').joinpath('data',os.path.basename(usr_cfg_file)).read_text()
		sample_file = usr_cfg_file + '.sample'
		sample_data = open(sample_file).read() if os.path.exists(sample_file) else None
		if src_data != sample_data:
			os.makedirs(os.path.dirname(sample_file),exist_ok=True)
			msg('{} {}'.format(
				('Updating','Creating')[sample_data is None],
				sample_file ))
			open(sample_file,'w').write(src_data)

	def get_curl_cmd():
		return ([
					'curl',
					'--tr-encoding',
					'--compressed', # adds 'Accept-Encoding: gzip'
					'--silent',
					'--header', 'Accept: application/json',
				] +
				(['--proxy', cfg.proxy] if cfg.proxy else []) +
				[api_url + ('/btc-bitcoin' if cfg.btc_only else '')]
			)

	global cfg,cfg_in
	cfg = cfg_parm
	cfg_in = cfg_in_parm

	try:
		from importlib.resources import files # Python 3.9
	except ImportError:
		from importlib_resources import files

	update_sample_file(cfg_in.cfg_file)
	update_sample_file(cfg_in.portfolio_file)

	if opt.portfolio and not cfg_in.portfolio:
		die(1,'No portfolio configured!\nTo configure a portfolio, edit the file ~/{}'.format(
			os.path.relpath(cfg_in.portfolio_file,start=homedir)))

	curl_cmd = get_curl_cmd()

	if opt.print_curl:
		Msg(curl_cmd + '\n' + ' '.join(curl_cmd))
		return

	parsed_json = [get_src_data(curl_cmd)] if cfg.btc_only else get_src_data(curl_cmd)

	if opt.list_ids:
		do_pager('\n'.join(e['id'] for e in parsed_json))
		return

	global now
	now = 1659465400 if g.test_suite else time.time() # 1659524400 1659445900

	(do_pager if opt.pager else Msg)(
		'\n'.join(getattr(Ticker,cfg.clsname)(dict(gen_data(parsed_json))).gen_output())
	)

def make_cfg(cmd_args,cfg_in):

	def get_rows_from_cfg(add_data=None):
		def gen():
			for n,(k,v) in enumerate(cfg_in.cfg['assets'].items()):
				yield(k)
				if add_data and k in add_data:
					v += tuple(add_data[k])
				for e in v:
					yield parse_asset_id(e,True)
		return tuple(gen())

	def parse_asset_id(s,require_label=False):
		sym,label = (*s.split('-',1),None)[:2]
		if require_label and not label:
			die(1,f'{s!r}: asset label is missing')
		return asset_tuple( sym.upper(), (s.lower() if label else None) )

	def parse_usr_asset_arg(s):
		"""
		asset_id[:rate[:rate_asset]]
		"""
		def parse_parm(s):
			ss = s.split(':')
			assert len(ss) in (1,2,3), f'{s}: malformed argument'
			asset_id,rate,rate_asset = (*ss,None,None)[:3]
			parsed_id = parse_asset_id(asset_id)

			return asset_data(
				symbol = parsed_id.symbol,
				id     = parsed_id.id,
				amount = None,
				rate   = (
					None if rate is None else
					1 / Decimal(rate[:-1]) if rate.lower().endswith('r') else
					Decimal(rate) ),
				rate_asset = parse_asset_id(rate_asset) if rate_asset else None )

		return tuple(parse_parm(s2) for s2 in s.split(',')) if s else ()

	def parse_query_arg(s):
		"""
		asset_id:amount[:to_asset_id[:to_amount]]
		"""
		def parse_query_asset(asset_id,amount):
			parsed_id = parse_asset_id(asset_id)
			return asset_data(
				symbol = parsed_id.symbol,
				id     = parsed_id.id,
				amount = None if amount is None else Decimal(amount),
				rate   = None,
				rate_asset = None )

		ss = s.split(':')
		assert len(ss) in (2,3,4), f'{s}: malformed argument'
		asset_id,amount,to_asset_id,to_amount = (*ss,None,None)[:4]

		return query_tuple(
			asset = parse_query_asset(asset_id,amount),
			to_asset = parse_query_asset(to_asset_id,to_amount) if to_asset_id else None
		)

	def gen_uniq(obj_list,key,preload=None):
		found = set([getattr(obj,key) for obj in preload if hasattr(obj,key)] if preload else ())
		for obj in obj_list:
			id = getattr(obj,key)
			if id not in found:
				yield obj
			found.add(id)

	def get_usr_assets():
		return (
			'user_added',
			usr_rows +
			(tuple(asset for asset in query if asset) if query else ()) +
			usr_columns )

	def get_portfolio_assets(ret=()):
		if cfg_in.portfolio and opt.portfolio:
			ret = (parse_asset_id(e,True) for e in cfg_in.portfolio)
		return ( 'portfolio', tuple(e for e in ret if (not opt.btc) or e.symbol == 'BTC') )

	def get_portfolio():
		return {k:Decimal(v) for k,v in cfg_in.portfolio.items() if (not opt.btc) or k == 'btc-bitcoin'}

	def parse_add_precision(s):
		if not s:
			return 0
		if not (s.isdigit() and s.isascii()):
			die(1,f'{s}: invalid parameter for --add-precision (not an integer)')
		if int(s) > 30:
			die(1,f'{s}: invalid parameter for --add-precision (value >30)')
		return int(s)

	def create_rows():
		rows = (
			('trade_pair',) + query if (query and query.to_asset) else
			('bitcoin',parse_asset_id('btc-bitcoin')) if opt.btc else
			get_rows_from_cfg( add_data={'fiat':['usd-us-dollar']} if opt.add_columns else None )
		)

		for hdr,data in (
			(get_usr_assets(),) if query else
			(get_usr_assets(), get_portfolio_assets())
		):
			if data:
				uniq_data = tuple(gen_uniq(data,'symbol',preload=rows))
				if uniq_data:
					rows += (hdr,) + uniq_data
		return rows

	cfg_tuple = namedtuple('global_cfg',[
		'rows',
		'usr_rows',
		'usr_columns',
		'query',
		'adjust',
		'clsname',
		'btc_only',
		'add_prec',
		'cachedir',
		'proxy',
		'portfolio' ])

	query_tuple   = namedtuple('query',['asset','to_asset'])
	asset_data    = namedtuple('asset_data',['symbol','id','amount','rate','rate_asset'])
	asset_tuple   = namedtuple('asset_tuple',['symbol','id'])

	usr_rows    = parse_usr_asset_arg(opt.add_rows)
	usr_columns = parse_usr_asset_arg(opt.add_columns)
	query       = parse_query_arg(cmd_args[0]) if cmd_args else None

	return cfg_tuple(
		rows        = create_rows(),
		usr_rows    = usr_rows,
		usr_columns = usr_columns,
		query       = query,
		adjust      = ( lambda x: (100 + x) / 100 if x else 1 )( Decimal(opt.adjust or 0) ),
		clsname     = 'trading' if query else 'overview',
		btc_only    = opt.btc,
		add_prec    = parse_add_precision(opt.add_precision),
		cachedir    = opt.cachedir or cfg_in.cfg.get('cachedir') or cachedir,
		proxy       = None if opt.proxy == '' else (opt.proxy or cfg_in.cfg.get('proxy')),
		portfolio   = get_portfolio() if cfg_in.portfolio and opt.portfolio and not query else None
	)

def get_cfg_in():
	ret = namedtuple('cfg_in_data',['cfg','portfolio','cfg_file','portfolio_file'])
	cfg_file,portfolio_file = (
		[os.path.join(g.data_dir_root,'node_tools',fn) for fn in (cfg_fn,portfolio_fn)]
	)
	cfg_data,portfolio_data = (
		[yaml.safe_load(open(fn).read()) if os.path.exists(fn) else None for fn in (cfg_file,portfolio_file)]
	)
	return ret(
		cfg = cfg_data or {
			'assets': {
				'coin':      [ 'btc-bitcoin', 'eth-ethereum', 'xmr-monero' ],
				'commodity': [ 'xau-gold-spot-token', 'xag-silver-spot-token', 'xbr-brent-crude-oil-spot' ],
				'fiat':      [ 'gbp-pound-sterling-token', 'eur-euro-token' ],
				'index':     [ 'dj30-dow-jones-30-token', 'spx-sp-500', 'ndx-nasdaq-100-token' ],
			},
			'proxy': 'http://vpn-gw:8118'
		},
		portfolio = portfolio_data,
		cfg_file = cfg_file,
		portfolio_file = portfolio_file,
	)

class Ticker:

	class base:

		offer = None
		to_asset = None

		def __init__(self,data):

			self.comma = ',' if opt.thousands_comma else ''

			self.col1_wid = max(len('TOTAL'),(
				max(len(self.create_label(d['id'])) for d in data.values()) if opt.name_labels else
				max(len(d['symbol']) for d in data.values())
			)) + 1

			self.rows = [row._replace(id=self.get_id(row)) if isinstance(row,tuple) else row for row in cfg.rows]
			self.col_usd_prices = {k:Decimal(self.data[k]['price_usd']) for k in self.col_ids}

			self.prices = {row.id:self.get_row_prices(row.id)
				for row in self.rows if isinstance(row,tuple) and row.id in data}
			self.prices['usd-us-dollar'] = self.get_row_prices('usd-us-dollar')

		def format_last_update_col(self,cross_assets=()):

			if opt.elapsed:
				from .Util import format_elapsed_hr
				fmt_func = format_elapsed_hr
			else:
				fmt_func = lambda t,now: time.strftime('%F %X',time.gmtime(t)) # ticker API
				# t.replace('T',' ').replace('Z','') # tickers API

			d = self.data
			max_w = 0
			min_t = min( (int(d[a.id]['last_updated']) for a in cross_assets), default=None )

			for row in self.rows:
				if isinstance(row,tuple):
					try:
						t = int(d[row.id]['last_updated'])
					except KeyError:
						pass
					else:
						t_fmt = d[row.id]['last_updated_fmt'] = fmt_func( (min(t,min_t) if min_t else t), now )
						max_w = max(len(t_fmt),max_w)

			self.upd_w = max_w

		def init_prec(self):
			exp = [(a.id,Decimal.adjusted(self.prices[a.id]['usd-us-dollar'])) for a in self.usr_col_assets]
			self.uprec = { k: max(0,v+4) + cfg.add_prec for k,v in exp }
			self.uwid  = { k: 12 + max(0, abs(v)-6) + cfg.add_prec for k,v in exp }

		def get_id(self,asset):
			if asset.id:
				return asset.id
			else:
				for d in self.data.values():
					if d['symbol'] == asset.symbol:
						return d['id']

		def create_label(self,id):
			return ' '.join(id.split('-')[1:]).upper()

		def gen_output(self):
			yield 'Current time: {} UTC'.format(time.strftime('%F %X',time.gmtime(now)))

			for asset in self.usr_col_assets:
				if asset.symbol != 'USD':
					usdprice = Decimal(self.data[asset.id]['price_usd'])
					yield '{} ({}) = {:{}.{}f} USD'.format(
						asset.symbol,
						self.create_label(asset.id),
						usdprice,
						self.comma,
						max(2,int(-usdprice.adjusted())+4) )

			if hasattr(self,'subhdr'):
				yield self.subhdr

			if self.show_adj:
				yield (
					('Offered price differs from spot' if self.offer else 'Adjusting prices')
					+ ' by '
					+ yellow('{:+.2f}%'.format( (self.adjust-1) * 100 ))
				)

			yield ''

			if cfg.portfolio:
				yield blue('PRICES')

			if self.table_hdr:
				yield self.table_hdr

			for row in self.rows:
				if isinstance(row,str):
					yield ('-' * self.hl_wid)
				else:
					try:
						yield self.fmt_row(self.data[row.id])
					except KeyError:
						yield gray(f'(no data for {row.id})')

			yield '-' * self.hl_wid

			if cfg.portfolio:
				self.fs_num = self.fs_num2
				self.fs_str = self.fs_str2
				yield ''
				yield blue('PORTFOLIO')
				yield self.table_hdr
				yield '-' * self.hl_wid
				for sym,amt in cfg.portfolio.items():
					try:
						yield self.fmt_row(self.data[sym],amt=amt)
					except KeyError:
						yield gray(f'(no data for {sym})')
				yield '-' * self.hl_wid
				if not cfg.btc_only:
					yield self.fs_num.format(
						lbl = 'TOTAL', pc1='', pc2='', upd='', amt='',
						**{ k.replace('-','_'): v for k,v in self.prices['total'].items() }
					)

	class overview(base):

		def __init__(self,data):
			self.data = data
			self.adjust = cfg.adjust
			self.show_adj = self.adjust != 1
			self.usr_col_assets = [asset._replace(id=self.get_id(asset)) for asset in cfg.usr_columns]
			self.col_ids = ('usd-us-dollar',) + tuple(a.id for a in self.usr_col_assets) + ('btc-bitcoin',)

			super().__init__(data)

			self.format_last_update_col()

			if cfg.portfolio:
				self.prices['total'] = { col_id: sum(self.prices[row.id][col_id] * cfg.portfolio[row.id]
					for row in self.rows if isinstance(row,tuple) and row.id in cfg.portfolio and row.id in data)
						for col_id in self.col_ids }

			self.init_prec()
			self.init_fs()

		def get_row_prices(self,id):
			if id in self.data:
				d = self.data[id]
				return { k: (
						Decimal(d['price_btc']) if k == 'btc-bitcoin' else
						Decimal(d['price_usd']) / self.col_usd_prices[k]
					) * self.adjust for k in self.col_ids }

		def fmt_row(self,d,amt=None,amt_fmt=None):

			def fmt_pct(d):
				if d in ('',None):
					return gray('     --')
				n = Decimal(d)
				return (red,green)[n>=0](f'{n:+7.2f}')

			p = self.prices[d['id']]

			if amt is not None:
				amt_fmt = f'{amt:{19+cfg.add_prec}{self.comma}.{8+cfg.add_prec}f}'
				if '.' in amt_fmt:
					amt_fmt = amt_fmt.rstrip('0').rstrip('.')

			return self.fs_num.format(
				lbl = (self.create_label(d['id']) if opt.name_labels else d['symbol']),
				pc1 = fmt_pct(d.get('percent_change_7d')),
				pc2 = fmt_pct(d.get('percent_change_24h')),
				upd = d.get('last_updated_fmt'),
				amt = amt_fmt,
				**{ k.replace('-','_'): v * (1 if amt is None else amt) for k,v in p.items() }
			)

		def init_fs(self):

			col_prec = {'usd-us-dollar':2+cfg.add_prec,'btc-bitcoin':8+cfg.add_prec }  # | self.uprec # Python 3.9
			col_prec.update(self.uprec)
			col_wid  = {'usd-us-dollar':8+cfg.add_prec,'btc-bitcoin':12+cfg.add_prec } # """
			col_wid.update(self.uwid)
			max_row = max(
				( (k,v['btc-bitcoin']) for k,v in self.prices.items() ),
				key = lambda a: a[1]
			)
			widths = { k: len('{:{}.{}f}'.format( self.prices[max_row[0]][k], self.comma, col_prec[k] ))
						for k in self.col_ids }

			fd = namedtuple('format_str_data',['fs_str','fs_num','wid'])

			col_fs_data = {
				'label':       fd(f'{{lbl:{self.col1_wid}}}',f'{{lbl:{self.col1_wid}}}',self.col1_wid),
				'pct7d':       fd(' {pc1:7}', ' {pc1:7}', 8),
				'pct24h':      fd(' {pc2:7}', ' {pc2:7}', 8),
				'update_time': fd('  {upd}',  '  {upd}',  max((19 if cfg.portfolio else 0),self.upd_w) + 2),
				'amt':         fd('  {amt}',  '  {amt}',  21),
			}
#			} | { k: fd( # Python 3.9
			col_fs_data.update({ k: fd(
						'  {{{}:>{}}}'.format( k.replace('-','_'), widths[k] ),
						'  {{{}:{}{}.{}f}}'.format( k.replace('-','_'), widths[k], self.comma, col_prec[k] ),
						widths[k]+2
					) for k in self.col_ids
			})

			cols = (
				['label','usd-us-dollar'] +
				[asset.id for asset in self.usr_col_assets] +
				[a for a,b in (
					( 'btc-bitcoin',  not cfg.btc_only ),
					( 'pct7d', opt.percent_change ),
					( 'pct24h', opt.percent_change ),
					( 'update_time', opt.update_time ),
				) if b]
			)
			cols2 = list(cols)
			if opt.update_time:
				cols2.pop()
			cols2.append('amt')

			self.fs_str = ''.join(col_fs_data[c].fs_str for c in cols)
			self.fs_num = ''.join(col_fs_data[c].fs_num for c in cols)
			self.hl_wid = sum(col_fs_data[c].wid for c in cols)

			self.fs_str2 = ''.join(col_fs_data[c].fs_str for c in cols2)
			self.fs_num2 = ''.join(col_fs_data[c].fs_num for c in cols2)
			self.hl_wid2 = sum(col_fs_data[c].wid for c in cols2)

		@property
		def table_hdr(self):
			return self.fs_str.format(
				lbl = '',
				pc1 = ' CHG_7d',
				pc2 = 'CHG_24h',
				upd = 'UPDATED',
				amt = '         AMOUNT',
				usd_us_dollar = 'USD',
				btc_bitcoin = '  BTC',
				**{ a.id.replace('-','_'): a.symbol for a in self.usr_col_assets }
			)

	class trading(base):

		def __init__(self,data):
			self.data = data
			self.asset = cfg.query.asset._replace(id=self.get_id(cfg.query.asset))
			self.to_asset = (
				cfg.query.to_asset._replace(id=self.get_id(cfg.query.to_asset))
				if cfg.query.to_asset else None )
			self.col_ids = [self.asset.id]
			self.adjust = cfg.adjust
			if self.to_asset:
				self.offer = self.to_asset.amount
				if self.offer:
					real_price = (
						self.asset.amount
						* Decimal(data[self.asset.id]['price_usd'])
						/ Decimal(data[self.to_asset.id]['price_usd'])
					)
					if self.adjust != 1:
						die(1,'the --adjust option may not be combined with TO_AMOUNT in the trade specifier')
					self.adjust = self.offer / real_price
				self.hl_ids = [self.asset.id,self.to_asset.id]
			else:
				self.hl_ids = [self.asset.id]

			self.show_adj = self.adjust != 1 or self.offer

			super().__init__(data)

			self.usr_col_assets = [self.asset] + ([self.to_asset] if self.to_asset else [])
			for a in self.usr_col_assets:
				self.prices[a.id]['usd-us-dollar'] = Decimal(data[a.id]['price_usd'])

			self.format_last_update_col(cross_assets=self.usr_col_assets)

			self.init_prec()
			self.init_fs()

		def get_row_prices(self,id):
			if id in self.data:
				d = self.data[id]
				return { k: self.col_usd_prices[self.asset.id] / Decimal(d['price_usd']) for k in self.col_ids }

		def init_fs(self):
			self.max_wid = max(
				len('{:{}{}.{}f}'.format(
						v[self.asset.id] * self.asset.amount,
						16 + cfg.add_prec,
						self.comma,
						8 + cfg.add_prec
					))
					for v in self.prices.values()
			)
			self.fs_str = '{lbl:%s} {p_spot}' % self.col1_wid
			self.hl_wid = self.col1_wid + self.max_wid + 1
			if self.show_adj:
				self.fs_str += ' {p_adj}'
				self.hl_wid += self.max_wid + 1
			if opt.update_time:
				self.fs_str += '  {upd}'
				self.hl_wid += self.upd_w + 2

		def fmt_row(self,d):
			id = d['id']
			p = self.prices[id][self.asset.id] * self.asset.amount
			p_spot = '{:{}{}.{}f}'.format( p, self.max_wid, self.comma, 8+cfg.add_prec )
			p_adj = (
				'{:{}{}.{}f}'.format( p*self.adjust, self.max_wid, self.comma, 8+cfg.add_prec )
				if self.show_adj else '' )

			return self.fs_str.format(
				lbl = (self.create_label(id) if opt.name_labels else d['symbol']),
				p_spot = green(p_spot) if id in self.hl_ids else p_spot,
				p_adj  = yellow(p_adj) if id in self.hl_ids else p_adj,
				upd = d.get('last_updated_fmt'),
			)

		@property
		def table_hdr(self):
			return self.fs_str.format(
				lbl = '',
				p_spot = '{t:>{w}}'.format(
					t = 'SPOT PRICE',
					w = self.max_wid ),
				p_adj = '{t:>{w}}'.format(
					t = ('OFFERED' if self.offer else 'ADJUSTED') + ' PRICE',
					w = self.max_wid ),
				upd = 'UPDATED'
			)

		@property
		def subhdr(self):
			return (
				'{a}: {b:{c}} {d}'.format(
					a = 'Offer' if self.offer else 'Amount',
					b = self.asset.amount,
					c = self.comma,
					d = self.asset.symbol
				) + (
				(
					' =>' +
					(' {:{}}'.format(self.offer,self.comma) if self.offer else '') +
					' {} ({})'.format(
						self.to_asset.symbol,
						self.create_label(self.to_asset.id) )
				) if self.to_asset else '' )
			)
