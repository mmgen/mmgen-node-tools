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
mmgen_node_tools.Ticker: Display price information for cryptocurrency and other assets
"""

# v3.2.dev4: switch to new coinpaprika ‘tickers’ API call (supports ‘limit’ parameter, more historical data)
# Old ‘ticker’ API  (/v1/ticker):  data['BTC']['price_usd']
# New ‘tickers’ API (/v1/tickers): data['BTC']['quotes']['USD']['price']

# Possible alternatives:
# - https://min-api.cryptocompare.com/data/pricemultifull?fsyms=BTC,LTC&tsyms=USD,EUR

import sys,os,re,time,datetime,json,yaml,random
from subprocess import run,PIPE,CalledProcessError
from decimal import Decimal
from collections import namedtuple

from mmgen.color import red,yellow,green,blue,orange,gray
from mmgen.util import msg,msg_r,Msg,Msg_r,die,Die,suf,fmt,fmt_list,fmt_dict,list_gen
from mmgen.ui import do_pager

homedir = os.getenv('HOME')
dfl_cachedir = os.path.join(homedir,'.cache','mmgen-node-tools')
cfg_fn = 'ticker-cfg.yaml'
portfolio_fn = 'ticker-portfolio.yaml'
asset_tuple = namedtuple('asset_tuple',['symbol','id','source'])
last_api_host = None

percent_cols = {
	'd': 'day',
	'w': 'week',
	'm': 'month',
	'y': 'year',
}

class DataSource:

	source_groups = [
		{
			'cc': 'coinpaprika'
		}, {
			'fi': 'yahoospot',
			'hi': 'yahoohist',
		}
	]

	@classmethod
	def get_sources(cls,randomize=False):
		g = random.sample(cls.source_groups,k=len(cls.source_groups)) if randomize else cls.source_groups
		return {k:v for a in g for k,v in a.items()}

	class base:

		def fetch_delay(self):
			global last_api_host
			if not gcfg.testing and last_api_host and last_api_host != self.api_host:
				delay = 1 + random.randrange(1,5000) / 1000
				msg_r(f'Waiting {delay:.3f} seconds...')
				time.sleep(delay)
				msg('')
			last_api_host = self.api_host

		def get_data_from_network(self):

			curl_cmd = list_gen(
				['curl', '--tr-encoding', '--header', 'Accept: application/json',True],
				['--compressed'], # adds 'Accept-Encoding: gzip'
				['--proxy', cfg.proxy, isinstance(cfg.proxy,str)],
				['--silent', not cfg.verbose],
				[self.api_url]
			)

			if gcfg.testing:
				Msg(fmt_list(curl_cmd,fmt='bare'))
				return

			try:
				return run(curl_cmd,check=True,stdout=PIPE).stdout.decode()
			except CalledProcessError as e:
				msg('')
				from .Misc import curl_exit_codes
				msg(red(curl_exit_codes[e.returncode]))
				msg(red('Command line:\n  {}'.format( ' '.join((repr(i) if ' ' in i else i) for i in e.cmd) )))
				from mmgen.exception import MMGenCalledProcessError
				raise MMGenCalledProcessError(f'Subprocess returned non-zero exit status {e.returncode}')

		def get_data(self):

			if not os.path.exists(cfg.cachedir):
				os.makedirs(cfg.cachedir)

			if not os.path.exists(self.json_fn):
				open(self.json_fn,'w').write('{}')

			use_cached_data = cfg.cached_data and not gcfg.download

			if use_cached_data:
				data_type = 'json'
				data_in = open(self.json_fn).read()
			else:
				data_type = self.net_data_type
				elapsed = int(time.time() - os.stat(self.json_fn).st_mtime)
				if elapsed >= self.timeout or gcfg.testing:
					if gcfg.testing:
						msg('')
					self.fetch_delay()
					msg_r(f'Fetching {self.data_desc} from {self.api_host}...')
					if self.has_verbose and cfg.verbose:
						msg('')
					data_in = self.get_data_from_network()
					msg('done')
					if gcfg.testing:
						return {}
				else:
					die(1,self.rate_limit_errmsg(elapsed))

			if data_type == 'json':
				try:
					data = json.loads(data_in)
				except:
					self.json_data_error_msg(data_in)
					die(2,'Retrieved data is not valid JSON, exiting')
				json_text = data_in
			elif data_type == 'python':
				data = data_in
				json_text = json.dumps(data_in)

			if not data:
				if use_cached_data:
					die(1,
						f'No cached {self.data_desc}! Run command without the --cached-data option, '
						'or use --download to retrieve data from remote host')
				else:
					die(2,'Remote host returned no data!')
			elif 'error' in data:
				die(1,data['error'])

			if use_cached_data:
				if not cfg.quiet:
					msg(f'Using cached data from ~/{self.json_fn_rel}')
			else:
				if os.path.exists(self.json_fn):
					os.rename(self.json_fn, self.json_fn + '.bak')
				with open(self.json_fn, 'w') as fh:
					fh.write(json_text)
				if not cfg.quiet:
					msg(f'JSON data cached to ~/{self.json_fn_rel}')
				if gcfg.download:
					sys.exit(0)

			return self.postprocess_data(data)

		def json_data_error_msg(self,json_text):
			pass

		def postprocess_data(self,data):
			return data

		@property
		def json_fn_rel(self):
			return os.path.relpath(self.json_fn,start=homedir)

	class coinpaprika(base):
		desc = 'CoinPaprika'
		data_desc = 'cryptocurrency data'
		api_host = 'api.coinpaprika.com'
		ratelimit = 240
		btc_ratelimit = 10
		net_data_type = 'json'
		has_verbose = True
		dfl_asset_limit = 2000

		def __init__(self):
			self.asset_limit = int(cfg.asset_limit or self.dfl_asset_limit)

		def rate_limit_errmsg(self,elapsed):
			return (
				f'Rate limit exceeded!  Retry in {self.timeout-elapsed} seconds' +
				('' if cfg.btc_only else ', or use --cached-data or --btc')
			)

		@property
		def api_url(self):
			return (
				f'https://{self.api_host}/v1/tickers/btc-bitcoin' if cfg.btc_only else
				f'https://{self.api_host}/v1/tickers?limit={self.asset_limit}' if self.asset_limit else
				f'https://{self.api_host}/v1/tickers' )

		@property
		def json_fn(self):
			return os.path.join(
				cfg.cachedir,
				'ticker-btc.json' if cfg.btc_only else 'ticker.json' )

		@property
		def timeout(self):
			return 0 if gcfg.test_suite else self.btc_ratelimit if cfg.btc_only else self.ratelimit

		def json_data_error_msg(self,json_text):
			tor_captcha_msg = f"""
				If you’re using Tor, the API request may have failed due to Captcha protection.
				A workaround for this issue is to retrieve the JSON data with a browser from
				the following URL:

					{self.api_url}

				and save it to:

					‘{cfg.cachedir}/ticker.json’

				Then invoke the program with --cached-data and without --btc
			"""
			msg(json_text[:1024] + '...')
			msg(orange(fmt(tor_captcha_msg,strip_char='\t')))

		def postprocess_data(self,data):
			return [data] if cfg.btc_only else data

		@staticmethod
		def parse_asset_id(s,require_label):
			sym,label = (*s.split('-',1),None)[:2]
			if require_label and not label:
				die(1,f'{s!r}: asset label is missing')
			return asset_tuple(
				symbol = sym.upper(),
				id     = (s.lower() if label else None),
				source = 'cc' )

	class yahoospot(base):

		desc = 'Yahoo Finance'
		data_desc = 'spot financial data'
		api_host = 'finance.yahoo.com'
		ratelimit = 30
		net_data_type = 'python'
		has_verbose = False
		asset_id_pat = r'^\^.*|.*=[xf]$'
		json_fn_basename = 'ticker-finance.json'

		@staticmethod
		def get_id(sym,data):
			return sym.lower()

		@staticmethod
		def conv_data(sym,data,btcusd):
			price_usd = Decimal( data['regularMarketPrice']['raw'] )
			return {
				'id': sym,
				'name': data['shortName'],
				'symbol': sym.upper(),
				'price_usd': price_usd,
				'price_btc': price_usd / btcusd,
				'percent_change_1y': data['pct_chg_1y'],
				'percent_change_30d': data['pct_chg_4wks'],
				'percent_change_7d': data['pct_chg_1wk'],
				'percent_change_24h': data['regularMarketChangePercent']['raw'] * 100,
				'last_updated': data['regularMarketTime'],
			}

		def rate_limit_errmsg(self,elapsed):
			return f'Rate limit exceeded!  Retry in {self.timeout-elapsed} seconds, or use --cached-data'

		@property
		def json_fn(self):
			return os.path.join( cfg.cachedir, self.json_fn_basename )

		@property
		def timeout(self):
			return 0 if gcfg.test_suite else self.ratelimit

		@property
		def symbols(self):
			return [r.symbol for r in cfg.rows if isinstance(r,tuple) and r.source == 'fi']

		def get_data_from_network(self):

			kwargs = {
				'formatted': True,
				'asynchronous': True,
				'proxies': { 'https': cfg.proxy2 },
			}

			if gcfg.test_suite:
				kwargs.update({ 'timeout': 1, 'retry': 0 })

			if gcfg.testing:
				Msg('\nyahooquery.Ticker(\n  {},\n  {}\n)'.format(
					self.symbols,
					fmt_dict(kwargs,fmt='kwargs') ))
				return

			from yahooquery import Ticker
			return self.process_network_data( Ticker(self.symbols,**kwargs) )

		def process_network_data(self,ticker):
			return ticker.price

		@staticmethod
		def parse_asset_id(s,require_label):
			return asset_tuple(
				symbol = s.upper(),
				id     = s.lower(),
				source = 'fi' )

	class yahoohist(yahoospot):

		json_fn_basename = 'ticker-finance-history.json'
		data_desc = 'historical financial data'
		net_data_type = 'json'
		period = '1y'
		interval = '1wk'

		def process_network_data(self,ticker):
			return ticker.history(
				period   = self.period,
				interval = self.interval).to_json(orient='index')

		def postprocess_data(self,data):
			def gen():
				keys = set()
				for key,val in data.items():
					if m := re.match(r"\('(.*?)', datetime\.date\((.*)\)\)$",key):
						date = '{}-{:>02}-{:>02}'.format(*m[2].split(', '))
						if (sym := m[1]) in keys:
							d[date] = val
						else:
							keys.add(sym)
							d = {date:val}
							yield (sym,d)
			return dict(gen())

def assets_list_gen(cfg_in):
	for k,v in cfg_in.cfg['assets'].items():
		yield ''
		yield k.upper()
		for e in v:
			out = e.split('-',1)
			yield '  {:5s} {}'.format(out[0],out[1] if len(out) == 2 else '')

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
			'\n  ' + '\n  '.join(d['id'] for d in data['cc'] if d['symbol'] == dup_sym) +
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
		'id': {r.id for r in cfg.rows if isinstance(r,tuple) and r.id} - {'usd-us-dollar'},
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

	wants = {k:rows_want[k] | usr_wants[k] for k in ('id','symbol')}

	for d in data['cc']:
		if d['id'] == 'btc-bitcoin':
			btcusd = Decimal(str(d['quotes']['USD']['price']))
			break

	get_id = src_cls['fi'].get_id
	conv_func = src_cls['fi'].conv_data

	for k,v in data['fi'].items():
		id = get_id(k,v)
		if wants['id']:
			if id in wants['id']:
				if not isinstance(v,dict):
					die(2, str(v))
				if id in found['id']:
					die(1,dup_sym_errmsg(id))
				if m := data['hi'].get(k):
					spot = v['regularMarketPrice']['raw']
					hist = tuple(m.values())
					v['pct_chg_1wk'], v['pct_chg_4wks'], v['pct_chg_1y'] = (
						(spot / hist[-2]['close'] - 1) * 100,
						(spot / hist[-5]['close'] - 1) * 100, # 4 weeks ≈ 1 month
						(spot / hist[0]['close'] - 1) * 100,
					)
				else:
					v['pct_chg_1wk'] = v['pct_chg_4wks'] = v['pct_chg_1y'] = None
				yield ( id, conv_func(id,v,btcusd) )
				found['id'].add(id)
				wants['id'].remove(id)
				if id in usr_rate_assets_want['id']:
					rate_assets[k] = conv_func(id,v,btcusd) # NB: using symbol instead of ID for key
		else:
			break

	for k in ('id','symbol'):
		for d in data['cc']:
			if wants[k]:
				if d[k] in wants[k]:
					if d[k] in found[k]:
						die(1,dup_sym_errmsg(d[k]))
					if not 'price_usd' in d:
						d['price_usd'] = Decimal(str(d['quotes']['USD']['price']))
						d['price_btc'] = Decimal(str(d['quotes']['USD']['price'])) / btcusd
						d['percent_change_24h'] = d['quotes']['USD']['percent_change_24h']
						d['percent_change_7d']  = d['quotes']['USD']['percent_change_7d']
						d['percent_change_30d'] = d['quotes']['USD']['percent_change_30d']
						d['percent_change_1y']  = d['quotes']['USD']['percent_change_1y']
						# .replace('Z','+00:00') -- Python 3.9 backport
						d['last_updated'] = int(datetime.datetime.fromisoformat(d['last_updated'].replace('Z','+00:00')).timestamp())
					yield (d['id'],d)
					found[k].add(d[k])
					wants[k].remove(d[k])
					if d[k] in usr_rate_assets_want[k]:
						rate_assets[d['symbol']] = d # NB: using symbol instead of ID for key
			else:
				break

	check_assets_found(usr_wants,found)

	for asset in (cfg.usr_rows + cfg.usr_columns):
		if asset.rate:
			"""
			User-supplied rate overrides rate from source data.
			"""
			_id = asset.id or f'{asset.symbol}-user-asset-{asset.symbol}'.lower()
			ra_rate = rate_assets[asset.rate_asset.symbol]['price_usd'] if asset.rate_asset else 1
			yield ( _id, {
				'symbol': asset.symbol,
				'id': _id,
				'name': ' '.join(_id.split('-')[1:]),
				'price_usd': ra_rate / asset.rate,
				'price_btc': ra_rate / asset.rate / btcusd,
				'last_updated': None,
			})

	yield ('usd-us-dollar', {
		'symbol': 'USD',
		'id': 'usd-us-dollar',
		'name': 'US Dollar',
		'price_usd': Decimal(1),
		'price_btc': Decimal(1) / btcusd,
		'last_updated': None,
	})

def main():

	def update_sample_file(usr_cfg_file):
		usr_data = files('mmgen_node_tools').joinpath('data',os.path.basename(usr_cfg_file)).read_text()
		sample_file = usr_cfg_file + '.sample'
		sample_data = open(sample_file).read() if os.path.exists(sample_file) else None
		if usr_data != sample_data:
			os.makedirs(os.path.dirname(sample_file),exist_ok=True)
			msg('{} {}'.format(
				('Updating','Creating')[sample_data is None],
				sample_file ))
			open(sample_file,'w').write(usr_data)

	try:
		from importlib.resources import files # Python 3.9
	except ImportError:
		from importlib_resources import files

	update_sample_file(cfg_in.cfg_file)
	update_sample_file(cfg_in.portfolio_file)

	if gcfg.portfolio and not cfg_in.portfolio:
		die(1,'No portfolio configured!\nTo configure a portfolio, edit the file ~/{}'.format(
			os.path.relpath(cfg_in.portfolio_file,start=homedir)))

	if gcfg.list_ids:
		src_ids = ['cc']
	elif gcfg.download:
		if not gcfg.download in DataSource.get_sources():
			die(1,f'{gcfg.download!r}: invalid data source')
		src_ids = [gcfg.download]
	else:
		src_ids = DataSource.get_sources(randomize=True)

	src_data = { k: src_cls[k]().get_data() for k in src_ids }

	if gcfg.testing:
		return

	if gcfg.list_ids:
		do_pager('\n'.join(e['id'] for e in src_data['cc']))
		return

	global now
	now = 1659465400 if gcfg.test_suite else time.time() # 1659524400 1659445900

	data = dict(gen_data(src_data))

	(do_pager if cfg.pager else Msg_r)(
		'\n'.join(getattr(Ticker,cfg.clsname)(data).gen_output()) + '\n')

def make_cfg(gcfg_arg):

	query_tuple = namedtuple('query',['asset','to_asset'])
	asset_data  = namedtuple('asset_data',['symbol','id','amount','rate','rate_asset','source'])

	def parse_asset_id(s,require_label=False):
		return src_cls['fi' if re.match(fi_pat,s) else 'cc'].parse_asset_id(s,require_label)

	def get_rows_from_cfg(add_data=None):
		def gen():
			for n,(k,v) in enumerate(cfg_in.cfg['assets'].items()):
				yield k
				if add_data and k in add_data:
					v += tuple(add_data[k])
				for e in v:
					yield parse_asset_id(e,require_label=True)
		return tuple(gen())

	def parse_percent_cols(arg):
		if arg is None:
			return []
		res = arg.lower().split(',')
		for s in res:
			if s not in percent_cols:
				die(1,f'{arg!r}: invalid --percent-cols parameter (valid letters: {fmt_list(percent_cols)})')
		return res

	def parse_usr_asset_arg(key,use_cf_file=False):
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
				rate_asset = parse_asset_id(rate_asset) if rate_asset else None,
				source  = parsed_id.source )

		cl_opt = getattr(gcfg,key)
		cf_opt = cfg_in.cfg.get(key,[]) if use_cf_file else []
		return tuple( parse_parm(s) for s in (cl_opt.split(',') if cl_opt else cf_opt) )

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
				rate_asset = None,
				source = parsed_id.source )

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
		if cfg_in.portfolio and gcfg.portfolio:
			ret = (parse_asset_id(e,require_label=True) for e in cfg_in.portfolio)
		return ( 'portfolio', tuple(e for e in ret if (not gcfg.btc) or e.symbol == 'BTC') )

	def get_portfolio():
		return {k:Decimal(v) for k,v in cfg_in.portfolio.items() if (not gcfg.btc) or k == 'btc-bitcoin'}

	def parse_add_precision(arg):
		if not arg:
			return 0
		s = str(arg)
		if not (s.isdigit() and s.isascii()):
			die(1,f'{s}: invalid parameter for --add-precision (not an integer)')
		if int(s) > 30:
			die(1,f'{s}: invalid parameter for --add-precision (value >30)')
		return int(s)

	def create_rows():
		rows = (
			('trade_pair',) + query if (query and query.to_asset) else
			('bitcoin',parse_asset_id('btc-bitcoin')) if gcfg.btc else
			get_rows_from_cfg( add_data={'fiat':['usd-us-dollar']} if gcfg.add_columns else None )
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
		'proxy2',
		'portfolio',
		'percent_cols',
		'asset_limit',
		'cached_data',
		'elapsed',
		'name_labels',
		'pager',
		'thousands_comma',
		'update_time',
		'quiet',
		'verbose'])

	global gcfg,cfg_in,src_cls,cfg

	gcfg = gcfg_arg

	src_cls = { k: getattr(DataSource,v) for k,v in DataSource.get_sources().items() }
	fi_pat = src_cls['fi'].asset_id_pat

	cmd_args = gcfg._args
	cfg_in = get_cfg_in()

	usr_rows    = parse_usr_asset_arg('add_rows')
	usr_columns = parse_usr_asset_arg('add_columns',use_cf_file=True)
	query       = parse_query_arg(cmd_args[0]) if cmd_args else None

	def get_proxy(name):
		proxy = getattr(gcfg,name)
		return (
			'' if proxy == '' else 'none' if (proxy and proxy.lower() == 'none')
			else (proxy or cfg_in.cfg.get(name))
		)

	proxy = get_proxy('proxy')
	proxy = None if proxy == 'none' else proxy
	proxy2 = get_proxy('proxy2')

	cfg = cfg_tuple(
		rows        = create_rows(),
		usr_rows    = usr_rows,
		usr_columns = usr_columns,
		query       = query,
		adjust      = ( lambda x: (100 + x) / 100 if x else 1 )( Decimal(gcfg.adjust or 0) ),
		clsname     = 'trading' if query else 'overview',
		btc_only    = gcfg.btc or cfg_in.cfg.get('btc'),
		add_prec    = parse_add_precision(gcfg.add_precision or cfg_in.cfg.get('add_precision')),
		cachedir    = gcfg.cachedir or cfg_in.cfg.get('cachedir') or dfl_cachedir,
		proxy       = proxy,
		proxy2      = None if proxy2 == 'none' else '' if proxy2 == '' else (proxy2 or proxy),
		portfolio   =
			get_portfolio()
				if cfg_in.portfolio
				and (gcfg.portfolio or cfg_in.cfg.get('portfolio'))
				and not query
			else None,
		percent_cols    = parse_percent_cols(gcfg.percent_cols or cfg_in.cfg.get('percent_cols')),
		asset_limit     = gcfg.asset_limit     or cfg_in.cfg.get('asset_limit'),
		cached_data     = gcfg.cached_data     or cfg_in.cfg.get('cached_data'),
		elapsed         = gcfg.elapsed         or cfg_in.cfg.get('elapsed'),
		name_labels     = gcfg.name_labels     or cfg_in.cfg.get('name_labels'),
		pager           = gcfg.pager           or cfg_in.cfg.get('pager'),
		thousands_comma = gcfg.thousands_comma or cfg_in.cfg.get('thousands_comma'),
		update_time     = gcfg.update_time     or cfg_in.cfg.get('update_time'),
		quiet           = gcfg.quiet           or cfg_in.cfg.get('quiet'),
		verbose         = gcfg.verbose         or cfg_in.cfg.get('verbose'),
	)

def get_cfg_in():
	ret = namedtuple('cfg_in_data',['cfg','portfolio','cfg_file','portfolio_file'])
	cfg_file,portfolio_file = (
		[os.path.join(gcfg.data_dir_root,'node_tools',fn) for fn in (cfg_fn,portfolio_fn)]
	)
	cfg_data,portfolio_data = (
		[yaml.safe_load(open(fn).read()) if os.path.exists(fn) else None for fn in (cfg_file,portfolio_file)]
	)
	return ret(
		cfg = cfg_data or {
			'assets': {
				'coin':      [ 'btc-bitcoin', 'eth-ethereum', 'xmr-monero' ],
				             # gold futures, silver futures, Brent futures
				'commodity': [ 'gc=f', 'si=f', 'bz=f' ],
				             # Pound Sterling, Euro, Swiss Franc
				'fiat':      [ 'gbpusd=x', 'eurusd=x', 'chfusd=x' ],
				             # Dow Jones Industrials, Nasdaq 100, S&P 500
				'index':     [ '^dji', '^ixic', '^gspc' ],
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

			self.comma = ',' if cfg.thousands_comma else ''

			self.col1_wid = max(len('TOTAL'),(
				max(len(self.create_label(d['id'])) for d in data.values()) if cfg.name_labels else
				max(len(d['symbol']) for d in data.values())
			)) + 1

			self.rows = [row._replace(id=self.get_id(row)) if isinstance(row,tuple) else row for row in cfg.rows]
			self.col_usd_prices = {k:self.data[k]['price_usd'] for k in self.col_ids}

			self.prices = {row.id:self.get_row_prices(row.id)
				for row in self.rows if isinstance(row,tuple) and row.id in data}
			self.prices['usd-us-dollar'] = self.get_row_prices('usd-us-dollar')

		def format_last_update_col(self,cross_assets=()):

			if cfg.elapsed:
				from mmgen.util2 import format_elapsed_hr
				fmt_func = format_elapsed_hr
			else:
				fmt_func = lambda t,now: time.strftime('%F %X',time.gmtime(t))

			d = self.data
			max_w = 0

			if cross_assets:
				last_updated_x = [d[a.id]['last_updated'] for a in cross_assets]
				min_t = min( (int(n) for n in last_updated_x if isinstance(n,int) ), default=None )
			else:
				min_t = None

			for row in self.rows:
				if isinstance(row,tuple):
					try:
						t = int( d[row.id]['last_updated'] )
					except TypeError as e:
						d[row.id]['last_updated_fmt'] = gray('--' if 'NoneType' in str(e) else str(e))
					except KeyError as e:
						msg(str(e))
						pass
					else:
						t_fmt = d[row.id]['last_updated_fmt'] = fmt_func( (min(t,min_t) if min_t else t), now )
						max_w = max(len(t_fmt),max_w)

			self.upd_w = max_w

		def init_prec(self):
			exp = [(a.id, self.prices[a.id]['usd-us-dollar'].adjusted() ) for a in self.usr_col_assets]
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
			return self.data[id]['name'].upper()

		def gen_output(self):
			yield 'Current time: {} UTC'.format(time.strftime('%F %X',time.gmtime(now)))

			for asset in self.usr_col_assets:
				if asset.symbol != 'USD':
					usdprice = self.data[asset.id]['price_usd']
					yield '{} ({}) = {:{}.{}f} USD'.format(
						asset.symbol,
						self.create_label(asset.id),
						usdprice,
						self.comma,
						max(2, 4-usdprice.adjusted()) )

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
						lbl = 'TOTAL', pc3='', pc4='', pc1='', pc2='', upd='', amt='',
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
						d['price_btc'] if k == 'btc-bitcoin' else
						d['price_usd'] / self.col_usd_prices[k]
					) * self.adjust for k in self.col_ids }

		def fmt_row(self,d,amt=None,amt_fmt=None):

			def fmt_pct(n):
				return gray('     --') if n == None else (red,green)[n>=0](f'{n:+7.2f}')

			p = self.prices[d['id']]

			if amt is not None:
				amt_fmt = f'{amt:{19+cfg.add_prec}{self.comma}.{8+cfg.add_prec}f}'
				if '.' in amt_fmt:
					amt_fmt = amt_fmt.rstrip('0').rstrip('.')

			return self.fs_num.format(
				lbl = self.create_label(d['id']) if cfg.name_labels else d['symbol'],
				pc1 = fmt_pct(d.get('percent_change_7d')),
				pc2 = fmt_pct(d.get('percent_change_24h')),
				pc3 = fmt_pct(d.get('percent_change_1y')),
				pc4 = fmt_pct(d.get('percent_change_30d')),
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
				'pct1y':       fd(' {pc3:7}', ' {pc3:7}', 8),
				'pct1m':       fd(' {pc4:7}', ' {pc4:7}', 8),
				'pct1w':       fd(' {pc1:7}', ' {pc1:7}', 8),
				'pct1d':       fd(' {pc2:7}', ' {pc2:7}', 8),
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
					( 'pct1y', 'y' in cfg.percent_cols ),
					( 'pct1m', 'm' in cfg.percent_cols ),
					( 'pct1w', 'w' in cfg.percent_cols ),
					( 'pct1d', 'd' in cfg.percent_cols ),
					( 'update_time', cfg.update_time ),
				) if b]
			)
			cols2 = list(cols)
			if cfg.update_time:
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
				pc3 = 'CHG_1y',
				pc4 = 'CHG_30d',
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
						* data[self.asset.id]['price_usd']
						/ data[self.to_asset.id]['price_usd']
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
				self.prices[a.id]['usd-us-dollar'] = data[a.id]['price_usd']

			self.format_last_update_col(cross_assets=self.usr_col_assets)

			self.init_prec()
			self.init_fs()

		def get_row_prices(self,id):
			if id in self.data:
				d = self.data[id]
				return { k: self.col_usd_prices[self.asset.id] / d['price_usd'] for k in self.col_ids }

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
			if cfg.update_time:
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
				lbl = self.create_label(id) if cfg.name_labels else d['symbol'],
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
