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
mmnode-ticker: Display price information for cryptocurrency and other assets
"""

opts_data = {
	'sets': [
		('widest', True, 'percent_cols',    'd,w,m,y'),
		('widest', True, 'name_labels',     True),
		('widest', True, 'thousands_comma', True),
		('widest', True, 'update_time',     True),
		('wide',   True, 'percent_cols',    'd,w'),
		('wide',   True, 'name_labels',     True),
		('wide',   True, 'thousands_comma', True),
		('wide',   True, 'update_time',     True),
	],
	'text': {
		'desc':  'Display prices for cryptocurrency and other assets',
		'usage': '[opts] [TRADE_SPECIFIER]',
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-a, --asset-limit=N   Retrieve data for top ‘N’ cryptocurrencies by market
                      cap (default: {al}).  To retrieve all available data,
                      specify a value of zero.
-A, --adjust=P        Adjust prices by percentage ‘P’.  In ‘trading’ mode,
                      spot and adjusted prices are shown in separate columns.
-b, --btc             Fetch and display data for Bitcoin only
-c, --add-columns=LIST Add columns for asset specifiers in LIST (comma-
                      separated, see ASSET SPECIFIERS below).  Can also be
                      used to supply a USD exchange rate for missing assets.
-C, --cached-data     Use cached data from previous network query instead of
                      live data from server
-D, --cachedir=D      Read and write cached JSON data to directory ‘D’
                      instead of ‘~/{dfl_cachedir}’
-d, --download=D      Retrieve and cache asset data ‘D’ from network (valid
                      options: {ds})
-e, --add-precision=N Add ‘N’ digits of precision to columns
-E, --elapsed         Show elapsed time in UPDATED column (see --update-time)
-F, --portfolio       Display portfolio data
-l, --list-ids        List IDs of all available assets
-n, --name-labels     Label rows with asset names rather than symbols
-p, --percent-cols=C  Add daily, weekly, monthly, or yearly percentage change
                      columns ‘C’ (specify with comma-separated letters
                      {pc})
-P, --pager           Pipe the output to a pager
-q, --quiet           Produce quieter output
-r, --add-rows=LIST   Add rows for asset specifiers in LIST (comma-separated,
                      see ASSET SPECIFIERS below). Can also be used to supply
                      a USD exchange rate for missing assets.
-t, --testing         Print command(s) to be executed to stdout and exit
-T, --thousands-comma Use comma as a thousands separator
-u, --update-time     Include UPDATED (last update time) column
-v, --verbose         Be more verbose
-w, --wide            Display most optional columns (same as -unT -p d,w)
-W, --widest          Display all optional columns (same as -unT -p d,w,m,y)
-x, --proxy=P         Connect via proxy ‘P’.  Set to the empty string to
                      completely disable or ‘none’ to allow override from
                      environment. Consult the curl manpage for --proxy usage.
-X, --proxy2=P        Alternate proxy for non-crypto financial data.  Defaults
                      to value of --proxy
""",
	'notes': """

The script has two display modes: ‘overview’, the default, and ‘trading’, the
latter being enabled when a TRADE_SPECIFIER argument (see below) is supplied
on the command line.

Overview mode displays prices of all configured assets, and optionally the
user’s portfolio, while trading mode displays the price of a given quantity
of an asset in relation to other assets, optionally comparing an offered
price to the spot price.

ASSETS consist of either a symbol (e.g. ‘xmr’) or full ID (see --list-ids)
consisting of symbol plus label (e.g. ‘xmr-monero’).  In cases where the
symbol is ambiguous, the full ID must be used.  For Yahoo Finance assets
the symbol and ID are identical:

Examples:

  ltc           - specify asset by symbol
  ltc-litecoin  - same as above, but use full ID instead of symbol
  ^dji          - Dow Jones Industrial Average (Yahoo)
  gc=f          - gold futures (Yahoo)

ASSET SPECIFIERS have the following format:

  ASSET[:RATE[:RATE_ASSET]]

If the asset referred to by ASSET is not in the source data (see --list-ids),
an arbitrarily chosen label may be used.  RATE is the exchange rate of the
asset in relation to RATE_ASSET, if present, otherwise USD.  When RATE is
postfixed with the letter ‘r’, its meaning is reversed, i.e. interpreted as
‘ASSET/RATE_ASSET’ instead of ‘RATE_ASSET/ASSET’.  Asset specifier examples:

  inr:79.5               - INR is not in the source data, so supply rate of
                           79.5 INR to the Dollar (USD/INR)
  inr:0.01257r           - same as above, but use reverse rate (INR/USD)
  inr-indian-rupee:79.5  - same as first example, but add an arbitrary label
  omr-omani-rial:2.59r   - Omani Rial is pegged to the Dollar at 2.59 USD
  bgn-bulgarian-lev:0.5113r:eurusd=x
                         - Bulgarian Lev is pegged to the Euro at 0.5113 EUR

A TRADE_SPECIFIER is a single argument in the format:

  ASSET:AMOUNT[:TO_ASSET[:TO_AMOUNT]]

  Examples:

    xmr:17.34          - price of 17.34 XMR in all configured assets
    xmr-monero:17.34   - same as above, but with full ID
    xmr:17.34:eurusd=x - price of 17.34 XMR in EUR only
    xmr:17.34:eurusd=x:2800 - commission on an offer of 17.34 XMR for 2800 EUR

  TO_AMOUNT, if included, is used to calculate the percentage difference or
  commission on an offer compared to the spot price.

  If either ASSET or TO_ASSET refer to assets not present in the source data,
  a USD rate for the missing asset(s) must be supplied via the --add-columns
  or --add-rows options.


                                 PROXY NOTE

The remote server used to obtain the crypto price data, {cc.api_host},
blocks Tor behind a Captcha wall, so a Tor proxy cannot be used directly.
If you’re concerned about privacy, connect via a VPN, or better yet, VPN over
Tor.  Then set up an HTTP proxy (e.g. Privoxy) on the VPN’ed host and set the
‘proxy’ option in the config file or --proxy on the command line accordingly.
Or run the script directly on the VPN’ed host with ’proxy’ or --proxy set to
the null string.

Alternatively, you may download the JSON source data in a Tor-proxied browser
from {cc.api_url}, save it as ‘ticker.json’ in your
configured cache directory and run the script with the --cached-data option.

Financial data is obtained from {fi.desc}, which currently allows Tor.


                             RATE LIMITING NOTE

To protect user privacy, filtering and processing of cryptocurrency data is
performed client side so that the remote server does not know which assets
are being examined.  This is done by fetching data for the top {al} crypto
assets by market cap (configurable via the --asset-limit option) with each
invocation of the script.  A rate limit of {cc.ratelimit} seconds between calls is thus
imposed to prevent abuse of the remote server.  When the --btc option is in
effect, this limit is reduced to {cc.btc_ratelimit} seconds.  To bypass the rate limit
entirely, use --cached-data.

Note that financial data obtained from {fi.api_host} is filtered in the
request, which has privacy implications.  The rate limit for financial data
is {fi.ratelimit} seconds.


                                  EXAMPLES

# Basic display in ‘overview’ mode:
$ mmnode-ticker

# Display BTC price only:
$ mmnode-ticker --btc

# Wide display, add EUR and OMR columns, OMR/USD rate, extra precision and
# proxy:
$ mmnode-ticker -w -c eurusd=x,omr-omani-rial:2.59r -e2 -x http://vpnhost:8118

# Wide display, elapsed update time, add EUR, BGN columns and BGN/EUR rate:
$ mmnode-ticker -wE -c eurusd=x,bgn-bulgarian-lev:0.5113r:eurusd=x

# Widest display with all percentage change columns, use cached data from
# previous network query, show portfolio (see above), pipe output to pager,
# add DOGE row:
$ mmnode-ticker -WCFP -r doge

# Display 17.234 XMR priced in all configured assets (‘trading’ mode):
$ mmnode-ticker xmr:17.234

# Same as above, but add INR price at specified USDINR rate:
$ mmnode-ticker -c inr:79.5 xmr:17.234

# Same as above, but view INR price only at specified rate, adding label:
$ mmnode-ticker -c inr-indian-rupee:79.5 xmr:17.234:inr

# Calculate commission on an offer of 2700 USD for 0.123 BTC, compared to
# current spot price:
$ mmnode-ticker usd:2700:btc:0.123

# Calculate commission on an offer of 200000 INR for 0.1 BTC, compared to
# current spot price, at specified USDINR rate:
$ mmnode-ticker -n -c inr-indian-rupee:79.5 inr:200000:btc:0.1


CONFIGURED ASSETS:
{assets}

Customize output by editing the file
    ~/{cfg}

To add a portfolio, edit the file
    ~/{pf_cfg}
"""
	},
	'code': {
		'options': lambda s: s.format(
			dfl_cachedir = os.path.relpath(dfl_cachedir,start=homedir),
			ds           = fmt_dict(DataSource.get_sources(),fmt='equal_compact'),
			al           = DataSource.coinpaprika.dfl_asset_limit,
			pc           = fmt_list(Ticker.percent_cols,fmt='bare'),
		),
		'notes': lambda s: s.format(
			assets = fmt_list(assets_list_gen(cfg_in),fmt='col',indent='  '),
			cfg    = os.path.relpath(cfg_in.cfg_file,start=homedir),
			pf_cfg = os.path.relpath(cfg_in.portfolio_file,start=homedir),
			al     = DataSource.coinpaprika.dfl_asset_limit,
			cc     = src_cls['cc'](),
			fi     = src_cls['fi'](),
		)
	}
}

import os

from mmgen.util import fmt_list,fmt_dict
from mmgen.cfg import Config
from . import Ticker

gcfg = Config( opts_data=opts_data, do_post_init=True )

Ticker.make_cfg(gcfg)

from .Ticker import dfl_cachedir,homedir,DataSource,assets_list_gen,cfg_in,src_cls

gcfg._post_init()

Ticker.main()
