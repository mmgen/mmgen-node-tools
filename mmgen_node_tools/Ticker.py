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

import os, re, time, datetime, json, yaml, random
from subprocess import run, PIPE, CalledProcessError
from decimal import Decimal
from collections import namedtuple

from mmgen.color import red, yellow, green, blue, orange, gray, cyan, pink
from mmgen.util import msg, msg_r, rmsg, Msg, Msg_r, die, fmt, fmt_list, fmt_dict, list_gen, suf, is_int
from mmgen.ui import do_pager

homedir = os.getenv('HOME')
dfl_cachedir = os.path.join(homedir, '.cache', 'mmgen-node-tools')
cfg_fn = 'ticker-cfg.yaml'
portfolio_fn = 'ticker-portfolio.yaml'
asset_tuple = namedtuple('asset_tuple', ['symbol', 'id', 'source'])
last_api_host = None

percent_cols = {
	'd': 'day',
	'w': 'week',
	'm': 'month',
	'y': 'year'}

sp = namedtuple('sort_parameter', ['key', 'sort_dfl', 'desc'])
sort_params = {
	'd': sp('percent_change_24h', 0.0,        '1-day percent change'),
	'w': sp('percent_change_7d',  0.0,        '1-week percent change'),
	'm': sp('percent_change_30d', 0.0,        '1-month percent change'),
	'y': sp('percent_change_1y',  0.0,        '1-year percent change'),
	'p': sp('price_usd',          Decimal(0), 'asset price'),
	'c': sp('market_cap',         0,          'market cap')}

class RowDict(dict):

	def __iter__(self):
		return (e for v in self.values() for e in v)

class DataSource:

	source_groups = [
		{
			'cc': 'coinpaprika'
		}, {
			'fi': 'yahoospot',
			'hi': 'yahoohist',
		}]

	@classmethod
	def get_sources(cls, randomize=False):
		g = random.sample(cls.source_groups, k=len(cls.source_groups)) if randomize else cls.source_groups
		return {k: v for a in g for k, v in a.items()}

	class base:

		def fetch_delay(self):
			global last_api_host
			if not gcfg.testing and last_api_host and last_api_host != self.api_host:
				delay = 1 + random.randrange(1, 5000) / 1000
				msg_r(f'Waiting {delay:.3f} seconds...')
				time.sleep(delay)
				msg('')
			last_api_host = self.api_host

		def get_data_from_network(self):

			curl_cmd = list_gen(
				['curl', '--tr-encoding', '--header', 'Accept: application/json', True],
				['--compressed'], # adds 'Accept-Encoding: gzip'
				['--proxy', cfg.proxy, isinstance(cfg.proxy, str)],
				['--silent', not cfg.verbose],
				['--connect-timeout', str(gcfg.http_timeout), gcfg.http_timeout],
				[self.api_url])

			if gcfg.testing:
				Msg(fmt_list(curl_cmd, fmt='bare'))
				return

			try:
				return run(curl_cmd, check=True, stdout=PIPE).stdout.decode()
			except CalledProcessError as e:
				msg('')
				from .Misc import curl_exit_codes
				msg(red(curl_exit_codes[e.returncode]))
				msg(red('Command line:\n  {}'.format(
					' '.join((repr(i) if ' ' in i else i) for i in e.cmd))))
				from mmgen.exception import MMGenCalledProcessError
				raise MMGenCalledProcessError(
					f'Subprocess returned non-zero exit status {e.returncode}')

		def get_data(self):

			if not os.path.exists(cfg.cachedir):
				os.makedirs(cfg.cachedir)

			use_cached_data = cfg.cached_data and not gcfg.download

			if use_cached_data:
				data_type = 'json'
				try:
					data_in = open(self.json_fn).read()
				except FileNotFoundError:
					die(1, f'Cannot use cached data, because {self.json_fn_disp} does not exist')
			else:
				data_type = self.net_data_type
				try:
					mtime = os.stat(self.json_fn).st_mtime
				except FileNotFoundError:
					mtime = 0
				if (elapsed := int(time.time() - mtime)) >= self.timeout or gcfg.testing:
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
					die(1, self.rate_limit_errmsg(elapsed))

			match data_type:
				case 'json':
					try:
						data = json.loads(data_in)
					except:
						self.json_data_error_msg(data_in)
						die(2, 'Retrieved data is not valid JSON, exiting')
					json_text = data_in
				case 'python':
					data = data_in
					json_text = json.dumps(data_in)

			if not data:
				if use_cached_data:
					die(1,
						f'No cached {self.data_desc}! Run command without the --cached-data option, '
						'or use --download to retrieve data from remote host')
				else:
					die(2, 'Remote host returned no data!')
			elif 'error' in data:
				die(1, data['error'])

			self.data = self.postprocess_data(data)

			if use_cached_data:
				self.json_text = None
				if not cfg.quiet:
					msg(f'Using cached data from {self.json_fn_disp}')
			else:
				self.json_text = json_text
				if cache_data(self, no_overwrite=True):
					self.json_text = None

			return self

		def json_data_error_msg(self, json_text):
			pass

		def postprocess_data(self, data):
			return data

		@property
		def json_fn_disp(self):
			return '~/' + os.path.relpath(self.json_fn, start=homedir)

	class coinpaprika(base):
		desc = 'CoinPaprika'
		data_desc = 'cryptocurrency data'
		api_host = 'api.coinpaprika.com'
		api_proto = 'https'
		ratelimit = 240
		btc_ratelimit = 10
		net_data_type = 'json'
		has_verbose = True
		dfl_asset_limit = 2000
		max_asset_idx = 1_000_000

		def __init__(self):
			self.asset_limit = int(cfg.asset_limit) if is_int(cfg.asset_limit) else self.dfl_asset_limit

		def rate_limit_errmsg(self, elapsed):
			rem = self.timeout - elapsed
			return (
				f'Rate limit exceeded!  Retry in {rem} second{suf(rem)}' +
				('' if cfg.btc_only else ', or use --cached-data or --btc'))

		@property
		def api_url(self):
			return (
				f'{self.api_proto}://{self.api_host}/v1/tickers/btc-bitcoin'
					if cfg.btc_only else
				f'{self.api_proto}://{self.api_host}/v1/tickers?limit={self.asset_limit}'
					if self.asset_limit else
				f'{self.api_proto}://{self.api_host}/v1/tickers')

		@property
		def json_fn(self):
			return os.path.join(
				cfg.cachedir,
				'ticker-btc.json' if cfg.btc_only else 'ticker.json')

		@property
		def timeout(self):
			return 0 if gcfg.test_suite else self.btc_ratelimit if cfg.btc_only else self.ratelimit

		def json_data_error_msg(self, json_text):
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
			msg(orange(fmt(tor_captcha_msg, strip_char='\t')))

		def postprocess_data(self, data):
			return [data] if cfg.btc_only else data

		@staticmethod
		def parse_asset_id(s, require_label=True):
			sym, label = (*s.split('-', 1), None)[:2]
			if require_label and not label:
				die(1, f'{s!r}: asset label is missing')
			return asset_tuple(
				symbol = sym.upper(),
				id     = (s.lower() if label else None),
				source = 'cc')

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
		def get_id(sym, data):
			return sym.lower()

		@staticmethod
		def conv_data(sym, data, btcusd):
			price_usd = Decimal(data['regularMarketPrice']['raw'])
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
				'market_cap': 0, # dummy - required for sorting
				'last_updated': data['regularMarketTime']}

		def rate_limit_errmsg(self, elapsed):
			rem = self.timeout - elapsed
			return f'Rate limit exceeded!  Retry in {rem} second{suf(rem)}, or use --cached-data'

		@property
		def json_fn(self):
			return os.path.join(cfg.cachedir, self.json_fn_basename)

		@property
		def timeout(self):
			return 0 if gcfg.test_suite else self.ratelimit

		@property
		def symbols(self):
			return [r.symbol for r in cfg.rows if r.source == 'fi']

		def get_data_from_network(self):

			kwargs = {
				'formatted': True,
				'asynchronous': True,
				'proxies': {'https': cfg.proxy2}}

			if gcfg.test_suite:
				kwargs.update({'timeout': 1, 'retry': 0})

			if gcfg.http_timeout:
				kwargs.update({'timeout': gcfg.http_timeout})

			if gcfg.testing:
				Msg('\nyahooquery.Ticker(\n  {},\n  {}\n)'.format(
					self.symbols,
					fmt_dict(kwargs, fmt='kwargs')))
				return

			from yahooquery import Ticker
			return self.process_network_data(Ticker(self.symbols,**kwargs))

		def process_network_data(self, ticker):
			return ticker.price

		@staticmethod
		def parse_asset_id(s, require_label=True):
			return asset_tuple(
				symbol = s.upper(),
				id     = s.lower(),
				source = 'fi')

	class yahoohist(yahoospot):

		json_fn_basename = 'ticker-finance-history.json'
		data_desc = 'historical financial data'
		net_data_type = 'json'
		period = '1y'
		interval = '1wk'

		def process_network_data(self, ticker):
			return ticker.history(
				period   = self.period,
				interval = self.interval).to_json(orient='index')

		def postprocess_data(self, data):
			def gen():
				keys = set()
				d = {}
				for key, val in data.items():
					if m := re.match(r"\('(.*?)', datetime\.date\((.*)\)\)$", key):
						date = '{}-{:>02}-{:>02}'.format(*m[2].split(', '))
						if (sym := m[1]) in keys:
							d[date] = val
						else:
							keys.add(sym)
							d = {date: val}
							yield (sym, d)
			return dict(gen())

def assets_list_gen(cfg_in):
	for k, v in cfg_in.cfg['assets'].items():
		yield ''
		yield k.upper()
		for e in v:
			out = e.split('-', 1)
			yield '  {:5s} {}'.format(out[0], out[1] if len(out) == 2 else '')

def gen_data(data):
	"""
	Filter the raw data and return it as a dict keyed by the IDs of the assets
	we want to display.

	Add dummy entry for USD and entry for user-specified asset, if any.

	Since symbols in source data are not guaranteed to be unique (e.g. XAG), we
	must search the data twice: first for unique IDs, then for symbols while
	checking for duplicates.
	"""

	def dup_sym_errmsg(data_type, dup_sym):
		return (
			f'The symbol {dup_sym!r} is shared by the following assets:\n' +
			'\n  ' + '\n  '.join(d['id'] for d in data[data_type].data if d['symbol'] == dup_sym) +
			'\n\nPlease specify the asset by one of the full IDs listed above\n' +
			f'instead of {dup_sym!r}')

	def check_assets_found(wants, found, keys=['symbol', 'id']):
		error = False
		for k in keys:
			missing = wants[k] - found[k]
			if missing:
				msg(
					('The following IDs were not found in source data:\n{}' if k == 'id' else
					'The following symbols could not be resolved:\n{}').format(
						fmt_list(missing, fmt='col', indent='  ')))
				error = True
		if error:
			die(1, 'Missing data, exiting')

	class process_data:

		def cc():
			nonlocal btcusd
			for d in data['cc'].data:
				if d['id'] == 'btc-bitcoin':
					btcusd = Decimal(str(d['quotes']['USD']['price']))
					break
			else:
				raise ValueError('malformed cryptocurrency data')
			for k in ('id', 'symbol'):
				for d in data['cc'].data:
					if wants[k]:
						if d[k] in wants[k]:
							if d[k] in found[k]:
								die(1, dup_sym_errmsg('cc', d[k]))
							if not 'price_usd' in d:
								d['price_usd'] = Decimal(str(d['quotes']['USD']['price']))
								d['price_btc'] = Decimal(str(d['quotes']['USD']['price'])) / btcusd
								d['percent_change_24h'] = d['quotes']['USD']['percent_change_24h']
								d['percent_change_7d']  = d['quotes']['USD']['percent_change_7d']
								d['percent_change_30d'] = d['quotes']['USD']['percent_change_30d']
								d['percent_change_1y']  = d['quotes']['USD']['percent_change_1y']
								d['market_cap']  = d['quotes']['USD']['market_cap']
								d['last_updated'] = int(datetime.datetime.fromisoformat(
									d['last_updated']).timestamp())
							yield (d['id'], d)
							found[k].add(d[k])
							wants[k].remove(d[k])
							if d[k] in usr_rate_assets_want[k]:
								rate_assets[d['symbol']] = d # NB: using symbol instead of ID for key
					else:
						break

		def fi():
			get_id = src_cls['fi'].get_id
			conv_func = src_cls['fi'].conv_data
			for k, v in data['fi'].data.items():
				id = get_id(k, v)
				if wants['id']:
					if id in wants['id']:
						if not isinstance(v, dict):
							die(2, str(v))
						if id in found['id']:
							die(1, dup_sym_errmsg('fi', id))
						if hist := hist_close.get(k):
							spot = v['regularMarketPrice']['raw']
							v['pct_chg_1wk']  = (spot / hist.close_1wk  - 1) * 100
							v['pct_chg_4wks'] = (spot / hist.close_4wks - 1) * 100 # 4 weeks ≈ 1 month
							v['pct_chg_1y']   = (spot / hist.close_1y   - 1) * 100
						else:
							v['pct_chg_1wk'] = v['pct_chg_4wks'] = v['pct_chg_1y'] = None
						yield (id, conv_func(id, v, btcusd))
						found['id'].add(id)
						wants['id'].remove(id)
						if id in usr_rate_assets_want['id']: # NB: using symbol instead of ID for key:
							rate_assets[k] = conv_func(id, v, btcusd)
				else:
					break

		def hi():
			ret = namedtuple('historical_closing_prices', ['close_1wk', 'close_4wks', 'close_1y'])
			nonlocal hist_close
			for k, v in data['hi'].data.items():
				hist = tuple(v.values())
				hist_close[k] = ret(hist[-2]['close'], hist[-5]['close'], hist[0]['close'])
			return ()

	rows_want = {
		'id': {r.id for r in cfg.rows if r.id} - {'usd-us-dollar'},
		'symbol': {r.symbol for r in cfg.rows if r.id is None} - {'USD'}}
	usr_rate_assets = tuple(u.rate_asset for u in cfg.usr_rows + cfg.usr_columns if u.rate_asset)
	usr_rate_assets_want = {
		'id':     {a.id for a in usr_rate_assets if a.id},
		'symbol': {a.symbol for a in usr_rate_assets if not a.id}}
	usr_assets = cfg.usr_rows + cfg.usr_columns + tuple(c for c in (cfg.query or ()) if c)
	usr_wants = {
		'id': (
			{a.id for a in usr_assets + usr_rate_assets if a.id} -
			{a.id for a in usr_assets if a.rate and a.id} - {'usd-us-dollar'})
		,
		'symbol': (
			{a.symbol for a in usr_assets + usr_rate_assets if not a.id} -
			{a.symbol for a in usr_assets if a.rate} - {'USD'})}

	found = {'id': set(), 'symbol': set()}
	rate_assets = {}

	wants = {k: rows_want[k] | usr_wants[k] for k in ('id', 'symbol')}

	btcusd = Decimal('1') # dummy
	hist_close = {}

	parse_fail = False
	for data_type in ('cc', 'hi', 'fi'): # 'fi' depends on 'cc' and 'hi' so must go last
		if data_type in data:
			try:
				yield from getattr(process_data, data_type)()
			except Exception as e:
				rmsg(f'Error in source data {data_type!r}: {e}')
				parse_fail = True
			else:
				cache_data(data[data_type])

	if parse_fail:
		die(2, 'Invalid data encountered, exiting')

	if gcfg.download:
		return

	check_assets_found(usr_wants, found)

	for asset in (cfg.usr_rows + cfg.usr_columns):
		if asset.rate:
			"""
			User-supplied rate overrides rate from source data.
			"""
			_id = asset.id or f'{asset.symbol}-user-asset-{asset.symbol}'.lower()
			ra_rate = rate_assets[asset.rate_asset.symbol]['price_usd'] if asset.rate_asset else 1
			yield (_id, {
				'symbol': asset.symbol,
				'id': _id,
				'name': ' '.join(_id.split('-')[1:]),
				'price_usd': ra_rate / asset.rate,
				'price_btc': ra_rate / asset.rate / btcusd,
				'last_updated': None})

	yield ('usd-us-dollar', {
		'symbol': 'USD',
		'id': 'usd-us-dollar',
		'name': 'US Dollar',
		'price_usd': Decimal(1),
		'price_btc': Decimal(1) / btcusd,
		'percent_change_24h': 0.0,
		'percent_change_7d': 0.0,
		'percent_change_30d': 0.0,
		'percent_change_1y': 0.0,
		'market_cap': 0,
		'last_updated': None})

def cache_data(data_src, no_overwrite=False):
	if data_src.json_text:
		if os.path.exists(data_src.json_fn):
			if no_overwrite:
				return False
			os.rename(data_src.json_fn, data_src.json_fn + '.bak')
		with open(data_src.json_fn, 'w') as fh:
			fh.write(data_src.json_text)
		if not cfg.quiet:
			msg(f'JSON data cached to {data_src.json_fn_disp}')
		return True

def main():

	def update_sample_file(usr_cfg_file):
		usr_data = files('mmgen_node_tools').joinpath('data', os.path.basename(usr_cfg_file)).read_text()
		sample_file = usr_cfg_file + '.sample'
		sample_data = open(sample_file).read() if os.path.exists(sample_file) else None
		if usr_data != sample_data:
			os.makedirs(os.path.dirname(sample_file), exist_ok=True)
			msg('{} {}'.format(
				('Updating', 'Creating')[sample_data is None],
				sample_file))
			open(sample_file, 'w').write(usr_data)

	try:
		from importlib.resources import files # Python 3.9
	except ImportError:
		from importlib_resources import files

	update_sample_file(cfg_in.cfg_file)
	update_sample_file(cfg_in.portfolio_file)

	if gcfg.portfolio and not cfg_in.portfolio:
		die(1, 'No portfolio configured!\nTo configure a portfolio, edit the file ~/{}'.format(
			os.path.relpath(cfg_in.portfolio_file, start=homedir)))

	if gcfg.list_ids:
		src_ids = ['cc']
	elif gcfg.download:
		if not gcfg.download in DataSource.get_sources():
			die(1, f'{gcfg.download!r}: invalid data source')
		src_ids = [gcfg.download]
	else:
		src_ids = DataSource.get_sources(randomize=True)

	src_data = {k: src_cls[k]().get_data() for k in src_ids}

	if gcfg.testing:
		return

	if gcfg.list_ids:
		do_pager('\n'.join(e['id'] for e in src_data['cc'].data))
		return

	global cfg

	if cfg.asset_range:
		n, m = cfg.asset_range
		cfg = cfg._replace(rows = RowDict({
			'asset_list':
				tuple(
					asset_tuple(e['symbol'], e['id'], source='cc')
						for e in src_data['cc'].data[n-1:m]),
			'extra':
				tuple(
					[asset_tuple('BTC', 'btc-bitcoin', source='cc')]
					+ [r for r in cfg.rows if r.source == 'fi'])}))

	global now
	now = 1659465400 if gcfg.test_suite else time.time() # 1659524400 1659445900

	data = dict(gen_data(src_data))

	if gcfg.download:
		return

	(do_pager if cfg.pager else Msg_r)(
		'\n'.join(getattr(Ticker, cfg.clsname)(data).gen_output()) + '\n')

def make_cfg(gcfg_arg):

	query_tuple = namedtuple('query', ['asset', 'to_asset'])
	asset_data  = namedtuple('asset_data', ['symbol', 'id', 'amount', 'rate', 'rate_asset', 'source'])

	def parse_asset_id(s, require_label=True):
		return src_cls['fi' if re.match(fi_pat, s) else 'cc'].parse_asset_id(s, require_label)

	def parse_percent_cols(arg):
		if arg is None or arg.lower() in ('none', ''):
			return []
		res = arg.lower().split(',')
		for s in res:
			if s not in percent_cols:
				die(1, '{!r}: invalid --percent-cols parameter (valid letters: {})'.format(
					arg,
					fmt_list(percent_cols)))
		return res

	def parse_usr_asset_arg(key, use_cf_file=False):
		"""
		asset_id[:rate[:rate_asset]]
		"""
		def parse_parm(s):
			ss = s.split(':')
			assert len(ss) in (1, 2, 3), f'{s}: malformed argument'
			asset_id, rate, rate_asset = (*ss, None, None)[:3]
			parsed_id = parse_asset_id(asset_id, require_label=False)

			return asset_data(
				symbol = parsed_id.symbol,
				id     = parsed_id.id,
				amount = None,
				rate   = (
					None if rate is None else
					1 / Decimal(rate[:-1]) if rate.lower().endswith('r') else
					Decimal(rate)),
				rate_asset = parse_asset_id(rate_asset, require_label=False) if rate_asset else None,
				source  = parsed_id.source)

		cl_opt = getattr(gcfg, key)
		if cl_opt is None or cl_opt.lower() in ('none', ''):
			return ()
		cf_opt = cfg_in.cfg.get(key,[]) if use_cf_file else []
		return tuple(parse_parm(s) for s in (cl_opt.split(',') if cl_opt else cf_opt))

	def parse_asset_range(s):
		max_idx = DataSource.coinpaprika.max_asset_idx
		match s.split('-'):
			case [a, b] if is_int(a) and is_int(b):
				n, m = (int(a), int(b))
			case [a] if is_int(a):
				n, m = (1, int(a))
			case _:
				return None
		if n < 1 or m < 1 or n > m:
			raise ValueError(f'‘{s}’: invalid asset range specifier')
		if m > max_idx:
			raise ValueError(f'‘{s}’: end of range must be <= {max_idx}')
		return (n, m)

	def parse_query_arg(s):
		"""
		asset_id:amount[:to_asset_id[:to_amount]]
		"""
		def parse_query_asset(asset_id, amount):
			parsed_id = parse_asset_id(asset_id, require_label=False)
			return asset_data(
				symbol = parsed_id.symbol,
				id     = parsed_id.id,
				amount = None if amount is None else Decimal(amount),
				rate   = None,
				rate_asset = None,
				source = parsed_id.source)

		ss = s.split(':')
		assert len(ss) in (2, 3, 4), f'{s}: malformed argument'
		asset_id, amount, to_asset_id, to_amount = (*ss, None, None)[:4]

		return query_tuple(
			asset = parse_query_asset(asset_id, amount),
			to_asset = parse_query_asset(to_asset_id, to_amount) if to_asset_id else None)

	def gen_uniq(obj_list, key, preload=None):
		found = set([getattr(obj, key) for obj in preload if hasattr(obj, key)] if preload else ())
		for obj in obj_list:
			id = getattr(obj, key)
			if id not in found:
				yield obj
			found.add(id)

	def get_usr_assets():
		return (
			usr_rows
			+ (tuple(asset for asset in query if asset) if query else ())
			+ usr_columns)

	def get_portfolio_assets():
		if cfg_in.portfolio and gcfg.portfolio:
			ret = (parse_asset_id(e) for e in cfg_in.portfolio)
			return tuple(e for e in ret if (not gcfg.btc) or e.symbol == 'BTC')
		else:
			return ()

	def get_portfolio():
		return tuple((k, Decimal(v)) for k, v in cfg_in.portfolio.items()
			if (not gcfg.btc) or k == 'btc-bitcoin')

	def parse_add_precision(arg):
		if not arg:
			return 0
		s = str(arg)
		if not (s.isdigit() and s.isascii()):
			die(1, f'{s}: invalid parameter for --add-precision (not an integer)')
		if int(s) > 30:
			die(1, f'{s}: invalid parameter for --add-precision (value >30)')
		return int(s)

	def create_rows():
		rows = RowDict(
			{'trade_pair': query} if (query and query.to_asset) else
			{'bitcoin': [parse_asset_id('btc-bitcoin')]} if gcfg.btc else
			{k: tuple(parse_asset_id(e) for e in v) for k, v in cfg_in.cfg['assets'].items()})
		for hdr, data in (
				('user_uniq', get_usr_assets()),
				('portfolio_uniq', get_portfolio_assets()),
				('pchg_unit_uniq', [pchg_unit] if pchg_unit else None)):
			if data:
				if uniq_data := tuple(gen_uniq(data, 'symbol', preload=rows)):
					rows[hdr] = uniq_data
				else:
					rows[hdr] = ()
		return rows

	def get_cfg_var(name):
		if name in gcfg._uopts:
			return getattr(gcfg, name)
		else:
			return getattr(gcfg, name) or cfg_in.cfg.get(name)

	def get_proxy(name):
		proxy = getattr(gcfg, name)
		return (
			'' if proxy == '' else 'none' if (proxy and proxy.lower() == 'none')
			else (proxy or cfg_in.cfg.get(name)))

	def get_sort_opt():
		match get_cfg_var('sort'):
			case None:
				return None
			case s if s in sort_params:
				return (s, True)
			case s if s in ['r' + ch for ch in sort_params]:
				return (s[1], False)
			case s:
				die(1,
					f'{s!r}: invalid parameter for --sort option (must be one of {fmt_list(sort_params)})'
					'\nTo reverse the sort, prefix the code letter with ‘r’')

	cfg_tuple = namedtuple('global_cfg',[
		'rows',
		'usr_rows',
		'usr_columns',
		'query',
		'asset_range',
		'adjust',
		'clsname',
		'btc_only',
		'add_prec',
		'cachedir',
		'proxy',
		'proxy2',
		'portfolio',
		'sort',
		'percent_cols',
		'pchg_unit',
		'asset_limit',
		'cached_data',
		'elapsed',
		'name_labels',
		'pager',
		'thousands_comma',
		'update_time',
		'quiet',
		'verbose'])

	global gcfg, cfg_in, src_cls, cfg

	gcfg = gcfg_arg

	src_cls = {k: getattr(DataSource, v) for k, v in DataSource.get_sources().items()}
	fi_pat = src_cls['fi'].asset_id_pat

	cfg_in = get_cfg_in()

	if cmd_args := gcfg._args:
		if len(cmd_args) > 1:
			die(1, 'Only one command-line argument is allowed')
		asset_range = parse_asset_range(cmd_args[0])
		query = None if asset_range else parse_query_arg(cmd_args[0])
	else:
		asset_range = None
		query = None

	usr_rows    = parse_usr_asset_arg('add_rows')
	usr_columns = parse_usr_asset_arg('add_columns', use_cf_file=True)

	proxy = get_proxy('proxy')
	proxy = None if proxy == 'none' else proxy
	proxy2 = get_proxy('proxy2')

	portfolio = (
		get_portfolio() if cfg_in.portfolio and get_cfg_var('portfolio') and not query
		else None)

	if portfolio and asset_range:
		die(1, '--portfolio not supported in market cap view')

	pchg_unit = (lambda s: parse_asset_id(s, require_label=False) if s else None)(
		get_cfg_var('pchg_unit'))

	cfg = cfg_tuple(
		rows        = create_rows(),
		usr_rows    = usr_rows,
		usr_columns = usr_columns,
		query       = query,
		asset_range = asset_range,
		adjust      = (lambda x: (100 + x) / 100 if x else 1)(Decimal(gcfg.adjust or 0)),
		clsname     = 'trading' if query else 'overview',
		btc_only    = get_cfg_var('btc'),
		add_prec    = parse_add_precision(get_cfg_var('add_precision')),
		cachedir    = get_cfg_var('cachedir') or dfl_cachedir,
		proxy       = proxy,
		proxy2      = None if proxy2 == 'none' else '' if proxy2 == '' else (proxy2 or proxy),
		portfolio   = portfolio,
		sort        = get_sort_opt(),
		percent_cols    = parse_percent_cols(get_cfg_var('percent_cols')),
		pchg_unit       = pchg_unit,
		asset_limit     = get_cfg_var('asset_limit'),
		cached_data     = get_cfg_var('cached_data'),
		elapsed         = get_cfg_var('elapsed'),
		name_labels     = get_cfg_var('name_labels'),
		pager           = get_cfg_var('pager'),
		thousands_comma = get_cfg_var('thousands_comma'),
		update_time     = get_cfg_var('update_time'),
		quiet           = get_cfg_var('quiet'),
		verbose         = get_cfg_var('verbose'))

	return (src_cls, cfg_in)

def get_cfg_in():
	ret = namedtuple('cfg_in_data', ['cfg', 'portfolio', 'cfg_file', 'portfolio_file'])
	cfg_file, portfolio_file = (
		[os.path.join(gcfg.data_dir_root, 'node_tools', fn)
			for fn in (cfg_fn, portfolio_fn)])
	cfg_data, portfolio_data = (
		[yaml.safe_load(open(fn).read()) if os.path.exists(fn) else None
			for fn in (cfg_file, portfolio_file)])
	return ret(
		cfg = cfg_data or {
			'assets': {
				'coin':      [ 'btc-bitcoin', 'eth-ethereum', 'xmr-monero' ],
				             # gold futures, silver futures, Brent futures
				'commodity': [ 'gc=f', 'si=f', 'bz=f' ],
				             # Pound Sterling, Euro, Swiss Franc
				'fiat':      [ 'gbpusd=x', 'eurusd=x', 'chfusd=x' ],
				             # Dow Jones Industrials, Nasdaq 100, S&P 500
				'index':     [ '^dji', '^ixic', '^gspc' ]},
			'proxy': 'http://vpn-gw:8118'},
		portfolio      = portfolio_data,
		cfg_file       = cfg_file,
		portfolio_file = portfolio_file)

class Ticker:

	class base:

		offer = None
		to_asset = None
		hidden_groups = ('extra', 'pchg_unit_uniq')

		def __init__(self, data):

			global cfg

			self.comma = ',' if cfg.thousands_comma else ''

			self.col1_wid = max(len('TOTAL'), (
				max(len(self.create_label(d['id'])) for d in data.values()) if cfg.name_labels else
				max(len(d['symbol']) for d in data.values())))

			self.rows = RowDict(
				{k: tuple(row._replace(id=self.get_id(row)) for row in v) for k, v in cfg.rows.items()})

			if cfg.asset_range:
				self.max_rank = 0
				for group, rows in self.rows.items():
					if group not in self.hidden_groups:
						for row in rows:
							self.max_rank = max(self.max_rank, int(data[row.id]['rank']))

			if cfg.sort:
				code, reverse = cfg.sort
				key = sort_params[code].key
				sort_dfl = sort_params[code].sort_dfl
				sort_func    = lambda row: data.get(row.id, {key: sort_dfl})[key]
				pf_sort_func = lambda row: data.get(row[0], {key: sort_dfl})[key]
				for group in self.rows.keys():
					if group not in self.hidden_groups:
						self.rows[group] = sorted(self.rows[group], key=sort_func, reverse=reverse)
				if cfg.portfolio:
					cfg = cfg._replace(
						portfolio = sorted(cfg.portfolio, key=pf_sort_func, reverse=reverse))

			if cfg.pchg_unit:
				self.pchg_data = self.data[self.get_id(cfg.pchg_unit)]
				self.pchg_factors = {k: (self.pchg_data[k] / 100) + 1 for k in (
					'percent_change_24h',
					'percent_change_7d',
					'percent_change_30d',
					'percent_change_1y')}

			self.col_usd_prices = {k: self.data[k]['price_usd'] for k in self.col_ids}
			self.prices = {row.id: self.get_row_prices(row.id) for row in self.rows if row.id in data}
			self.prices['usd-us-dollar'] = self.get_row_prices('usd-us-dollar')

		def format_last_updated_col(self, cross_assets=()):

			if cfg.elapsed:
				from mmgen.util2 import format_elapsed_hr
				fmt_func = format_elapsed_hr
			else:
				fmt_func = lambda t, now: time.strftime('%F %X', time.gmtime(t))

			d = self.data
			max_w = 0

			if cross_assets:
				last_updated_x = [d[a.id]['last_updated'] for a in cross_assets]
				min_t = min((int(n) for n in last_updated_x if isinstance(n, int)), default=None)
			else:
				min_t = None

			for row in self.rows:
				try:
					t = int(d[row.id]['last_updated'])
				except TypeError as e:
					d[row.id]['last_updated_fmt'] = gray('--' if 'NoneType' in str(e) else str(e))
				except KeyError as e:
					msg(str(e))
					pass
				else:
					t_fmt = d[row.id]['last_updated_fmt'] = fmt_func(
						(min(t, min_t) if min_t else t),
						now = now)
					max_w = max(len(t_fmt), max_w)

			self.upd_w = max_w

		def init_prec(self):
			exp = [(a.id, self.prices[a.id]['usd-us-dollar'].adjusted()) for a in self.usr_col_assets]
			self.uprec = {k: max(0, v+4) + cfg.add_prec for k, v in exp}
			self.uwid  = {k: 12 + max(0, abs(v)-6) + cfg.add_prec for k, v in exp}

		def get_id(self, asset):
			if asset.id:
				return asset.id
			else:
				m = asset.symbol
				for d in self.data.values():
					if m == d['symbol']:
						return d['id']

		def create_label(self, id):
			return self.data[id]['name'].upper()

		def gen_output(self):

			def process_rows(rows):
				yield '-' * self.hl_wid
				for row in rows:
					try:
						yield self.fmt_row(self.data[row.id])
					except KeyError:
						yield gray(f'(no data for {row.id})')

			yield 'Current time: {}'.format(cyan(time.strftime('%F %X', time.gmtime(now)) + ' UTC'))

			if cfg.sort:
				text = sort_params[cfg.sort[0]].desc + ('' if cfg.sort[1] else ' [reversed]')
				yield f'Sort order: {pink(text.upper())}'

			if cfg.pchg_unit:
				yield 'Percent change unit: {}'.format(orange('{} ({})'.format(
					self.pchg_data['symbol'],
					self.pchg_data['name'].upper())))

			for asset in self.usr_col_assets:
				if asset.symbol != 'USD':
					usdprice = self.data[asset.id]['price_usd']
					yield '{} ({}) = {:{}.{}f} USD'.format(
						asset.symbol,
						self.create_label(asset.id),
						usdprice,
						self.comma,
						max(2, 4-usdprice.adjusted()))

			if hasattr(self, 'subhdr'):
				yield self.subhdr

			if self.show_adj:
				yield (
					('Offered price differs from spot' if self.offer else 'Adjusting prices')
					+ ' by '
					+ yellow('{:+.2f}%'.format((self.adjust-1) * 100)))

			yield ''

			if cfg.portfolio:
				yield blue('PRICES')

			if self.table_hdr:
				yield self.table_hdr

			if cfg.asset_range:
				yield from process_rows(self.rows['asset_list'])
			else:
				for group, rows in self.rows.items():
					if rows and group not in self.hidden_groups:
						yield from process_rows(rows)

			yield '-' * self.hl_wid

			if cfg.portfolio:
				self.fs_num = self.fs_num2
				self.fs_str = self.fs_str2
				yield ''
				yield blue('PORTFOLIO')
				yield self.table_hdr
				yield '-' * self.hl_wid
				for sym, amt in cfg.portfolio:
					try:
						yield self.fmt_row(self.data[sym], amt=amt)
					except KeyError:
						yield gray(f'(no data for {sym})')
				yield '-' * self.hl_wid
				if not cfg.btc_only:
					yield self.fs_num.format(
						lbl = 'TOTAL', pc3='', pc4='', pc1='', pc2='', upd='', amt='',
						**{k.replace('-', '_'): v for k, v in self.prices['total'].items()})

	class overview(base):

		def __init__(self, data):
			self.data = data
			self.adjust = cfg.adjust
			self.show_adj = self.adjust != 1
			self.usr_col_assets = [asset._replace(id=self.get_id(asset)) for asset in cfg.usr_columns]
			self.col_ids = ('usd-us-dollar', 'btc-bitcoin') + tuple(a.id for a in self.usr_col_assets)

			super().__init__(data)

			self.format_last_updated_col()

			if cfg.portfolio:
				pf_dict = dict(cfg.portfolio)
				self.prices['total'] = {col_id: sum(self.prices[row.id][col_id] * pf_dict[row.id]
					for row in self.rows
						if row.id in pf_dict and row.id in data)
							for col_id in self.col_ids}

			self.init_prec()
			self.init_fs()

		def get_row_prices(self, id):
			if id in self.data:
				d = self.data[id]
				return {k: (
						d['price_btc'] if k == 'btc-bitcoin' else
						d['price_usd'] / self.col_usd_prices[k]
					) * self.adjust for k in self.col_ids}

		def fmt_row(self, d, amt=None, amt_fmt=None):

			def fmt_pct(d, key, wid=7):
				if (n := d.get(key)) is None:
					return gray('     --')
				if cfg.pchg_unit:
					n = ((((n / 100) + 1) / self.pchg_factors[key]) - 1) * 100
				return (red, green)[n>=0](f'{n:+{wid}.2f}')

			p = self.prices[d['id']]

			if amt is not None:
				amt_fmt = f'{amt:{19+cfg.add_prec}{self.comma}.{8+cfg.add_prec}f}'
				if '.' in amt_fmt:
					amt_fmt = amt_fmt.rstrip('0').rstrip('.')

			return self.fs_num.format(
				idx = int(d['rank']) if cfg.asset_range else None,
				mcap = d.get('market_cap') / 1_000_000_000 if cfg.asset_range else None,
				lbl = self.create_label(d['id']) if cfg.name_labels else d['symbol'],
				pc1 = fmt_pct(d, 'percent_change_7d'),
				pc2 = fmt_pct(d, 'percent_change_24h'),
				pc3 = fmt_pct(d, 'percent_change_1y', wid=8),
				pc4 = fmt_pct(d, 'percent_change_30d'),
				upd = d.get('last_updated_fmt'),
				amt = amt_fmt,
				**{k.replace('-', '_'): v * (1 if amt is None else amt) for k, v in p.items()})

		def init_fs(self):

			col_prec = {'usd-us-dollar': 2+cfg.add_prec, 'btc-bitcoin': 8+cfg.add_prec} | self.uprec
			max_row = max(
				((k, v['btc-bitcoin']) for k, v in self.prices.items()),
				key = lambda a: a[1])
			widths = {k: len('{:{}.{}f}'.format(self.prices[max_row[0]][k], self.comma, col_prec[k]))
						for k in self.col_ids}

			fd = namedtuple('format_str_data', ['fs_str', 'fs_num', 'wid'])

			col_fs_data = {
				'label':       fd(f'{{lbl:{self.col1_wid}}}', f'{{lbl:{self.col1_wid}}}', self.col1_wid),
				'pct1y':       fd(' {pc3:8}', ' {pc3:8}', 9),
				'pct1m':       fd(' {pc4:7}', ' {pc4:7}', 8),
				'pct1w':       fd(' {pc1:7}', ' {pc1:7}', 8),
				'pct1d':       fd(' {pc2:7}', ' {pc2:7}', 8),
				'update_time': fd('  {upd}',  '  {upd}',
					max((19 if cfg.portfolio else 0), self.upd_w) + 2),
				'amt':         fd('  {amt}',  '  {amt}',  21)
			} | {k: fd(
				'  {{{}:>{}}}'.format(k.replace('-', '_'), widths[k]),
				'  {{{}:{}{}.{}f}}'.format(k.replace('-', '_'), widths[k], self.comma, col_prec[k]),
				widths[k] + 2
			) for k in self.col_ids}

			cols = (
				['label', 'usd-us-dollar']
				+ [asset.id for asset in self.usr_col_assets]
				+ [a for a, b in (
					('btc-bitcoin',  not cfg.btc_only),
					('pct1y',       'y' in cfg.percent_cols),
					('pct1m',       'm' in cfg.percent_cols),
					('pct1w',       'w' in cfg.percent_cols),
					('pct1d',       'd' in cfg.percent_cols),
					('update_time', cfg.update_time))
						if b])

			if cfg.asset_range:
				num_w = len(str(self.max_rank))
				col_fs_data.update({
					'idx': fd(' ' * (num_w + 2), f'{{idx:{num_w}}}) ', num_w + 2),
					'mcap': fd('{mcap:>12}', '{mcap:12.5f}', 12)})
				cols = ['idx', 'label', 'mcap'] + cols[1:]

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
				mcap = 'MarketCap(B)',
				pc1 = ' CHG_7d',
				pc2 = 'CHG_24h',
				pc3 = '  CHG_1y',
				pc4 = 'CHG_30d',
				upd = 'UPDATED',
				amt = '         AMOUNT',
				usd_us_dollar = 'USD',
				btc_bitcoin = '  BTC',
				**{a.id.replace('-', '_'): a.symbol for a in self.usr_col_assets})

	class trading(base):

		def __init__(self, data):
			self.data = data
			self.asset = cfg.query.asset._replace(id=self.get_id(cfg.query.asset))
			self.to_asset = (
				cfg.query.to_asset._replace(id=self.get_id(cfg.query.to_asset))
				if cfg.query.to_asset else None)
			self.col_ids = [self.asset.id]
			self.adjust = cfg.adjust
			if self.to_asset:
				self.offer = self.to_asset.amount
				if self.offer:
					real_price = (
						self.asset.amount
						* data[self.asset.id]['price_usd']
						/ data[self.to_asset.id]['price_usd'])
					if self.adjust != 1:
						die(1,
							'the --adjust option may not be combined with TO_AMOUNT '
							'in the trade specifier')
					self.adjust = self.offer / real_price
				self.hl_ids = [self.asset.id, self.to_asset.id]
			else:
				self.hl_ids = [self.asset.id]

			self.show_adj = self.adjust != 1 or self.offer

			super().__init__(data)

			self.usr_col_assets = [self.asset] + ([self.to_asset] if self.to_asset else [])
			for a in self.usr_col_assets:
				self.prices[a.id]['usd-us-dollar'] = data[a.id]['price_usd']

			self.format_last_updated_col(cross_assets=self.usr_col_assets)

			self.init_prec()
			self.init_fs()

		def get_row_prices(self, id):
			if id in self.data:
				d = self.data[id]
				return {k: self.col_usd_prices[self.asset.id] / d['price_usd'] for k in self.col_ids}

		def init_fs(self):
			self.max_wid = max(
				len('{:{}{}.{}f}'.format(
						v[self.asset.id] * self.asset.amount,
						16 + cfg.add_prec,
						self.comma,
						8 + cfg.add_prec))
					for v in self.prices.values())
			self.fs_str = '{lbl:%s} {p_spot}' % self.col1_wid
			self.hl_wid = self.col1_wid + self.max_wid + 1
			if self.show_adj:
				self.fs_str += ' {p_adj}'
				self.hl_wid += self.max_wid + 1
			if cfg.update_time:
				self.fs_str += '  {upd}'
				self.hl_wid += self.upd_w + 2

		def fmt_row(self, d):
			id = d['id']
			p = self.prices[id][self.asset.id] * self.asset.amount
			p_spot = '{:{}{}.{}f}'.format(p, self.max_wid, self.comma, 8+cfg.add_prec)
			p_adj = (
				'{:{}{}.{}f}'.format(p*self.adjust, self.max_wid, self.comma, 8+cfg.add_prec)
				if self.show_adj else '')

			return self.fs_str.format(
				lbl = self.create_label(id) if cfg.name_labels else d['symbol'],
				p_spot = green(p_spot) if id in self.hl_ids else p_spot,
				p_adj  = yellow(p_adj) if id in self.hl_ids else p_adj,
				upd = d.get('last_updated_fmt'))

		@property
		def table_hdr(self):
			return self.fs_str.format(
				lbl = '',
				p_spot = '{t:>{w}}'.format(
					t = 'SPOT PRICE',
					w = self.max_wid),
				p_adj = '{t:>{w}}'.format(
					t = ('OFFERED' if self.offer else 'ADJUSTED') + ' PRICE',
					w = self.max_wid),
				upd = 'UPDATED')

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
					(' {:{}}'.format(self.offer, self.comma) if self.offer else '') +
					' {} ({})'.format(
						self.to_asset.symbol,
						self.create_label(self.to_asset.id))
				) if self.to_asset else ''))
