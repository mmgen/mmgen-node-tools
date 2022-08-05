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
mmnode-ticker: Display price information for cryptocurrency and other assets
"""

import sys,os
from mmgen.common import *
from .Ticker import *

opts_data = {
	'sets': [
		('wide', True, 'percent_change',  True),
		('wide', True, 'name_labels',     True),
		('wide', True, 'thousands_comma', True),
		('wide', True, 'update_time',     True),
	],
	'text': {
		'desc':  'Display prices for cryptocurrency and other assets',
		'usage': '[opts] [TRADE_SPECIFIER]',
		'options': f"""
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-A, --adjust=P        Adjust prices by percentage ‘P’.  In ‘trading’ mode,
                      spot and adjusted prices are shown in separate columns.
-b, --btc             Fetch and display data for Bitcoin only
-c, --add-columns=LIST Add columns for asset specifiers in LIST (comma-
                      separated, see ASSET SPECIFIERS below).  Can also be
                      used to supply a USD exchange rate for missing assets.
-C, --cached-data     Use cached data from previous network query instead of
                      live data from server
-d, --cachedir=D      Read and write cached JSON data to directory ‘D’
                      instead of ‘~/{os.path.relpath(cachedir,start=homedir)}’
-e, --add-precision=N Add ‘N’ digits of precision to columns
-E, --elapsed         Show elapsed time in UPDATED column (see --update-time)
-F, --portfolio       Display portfolio data
-l, --list-ids        List IDs of all available assets
-n, --name-labels     Label rows with asset names rather than symbols
-p, --percent-change  Add percentage change columns
-P, --pager           Pipe the output to a pager
-r, --add-rows=LIST   Add rows for asset specifiers in LIST (comma-separated,
                      see ASSET SPECIFIERS below). Can also be used to supply
                      a USD exchange rate for missing assets.
-T, --thousands-comma Use comma as a thousands separator
-u, --update-time     Include UPDATED (last update time) column
-U, --print-curl      Print cURL command to standard output and exit
-w, --wide            Display all optional columns (equivalent to -punT)
-x, --proxy=P         Connect via proxy ‘P’.  Set to the empty string to
                      disable.  Consult the curl manpage for --proxy usage.
""",
	'notes': """

The script has two display modes: ‘overview’, the default, and ‘trading’, the
latter being enabled when a TRADE_SPECIFIER argument (see below) is supplied
on the command line.

Overview mode displays prices of all configured assets, and optionally the
user’s portfolio, while trading mode displays the price of a given quantity
of an asset in relation to other assets, optionally comparing an offered
price to the spot price.

ASSETS consist of either a symbol (e.g. ‘xmr’) or full ID consisting of
symbol plus label (e.g. ‘xmr-monero’).  In cases where the symbol is
ambiguous, the full ID must be used.  Examples:

  chf                   - specify asset by symbol
  chf-swiss-franc-token - same as above, but use full ID instead of symbol

ASSET SPECIFIERS consist of an ASSET followed by an optional colon and USD
rate.  If the asset is not in the source data (see --list-ids), the label
part of the ID may be arbitrarily chosen by the user.  When the letter ‘r’
is appended to the USD rate, the rate is reversed, i.e. treated as ‘USD per
asset’ instead of ‘asset per USD’.  Asset specifier examples:

  inr:79.5              - INR is not in the source data, so supply USD rate
  inr-indian-rupee:79.5 - same as above, but add an arbitrary label
  omr-omani-rial:2.59r  - OMR is pegged to USD with fixed value of 2.59 USD

A TRADE_SPECIFIER is a single argument in the format:

  ASSET:AMOUNT[:TO_ASSET[:TO_AMOUNT]]

  Examples:

    xmr:17.34          - price of 17.34 XMR in all configured assets
    xmr-monero:17.34   - same as above, but with full ID
    xmr:17.34:eur      - price of 17.34 XMR in EUR only
    xmr:17.34:eur:2800 - commission on an offer of 17.34 XMR for 2800 EUR

  TO_AMOUNT, if included, is used to calculate the percentage difference or
  commission on an offer compared to the spot price.

  If either ASSET or TO_ASSET refer to assets not present in the source data,
  a USD rate for the missing asset(s) must be supplied via the --add-columns
  or --add-rows options.


                                 PROXY NOTE

The remote server used to obtain the price data, {api_host!r}, blocks
Tor behind a Captcha wall, so a Tor proxy cannot be used directly.  If you’re
concerned about privacy, connect via a VPN, or better yet, VPN over Tor. Then
set up an HTTP proxy (e.g. Privoxy) on the VPN’ed host and set the ‘proxy’
option in the config file or --proxy on the command line accordingly.  Or run
the script directly on the VPN’ed host with ’proxy’ or --proxy set to the
null string.

Alternatively, you may download the JSON source data in a Tor-proxied browser
from ‘{api_url}’, save it as ‘ticker.json’ in your
configured cache directory, and run the script with the --cached-data option.


                             RATE LIMITING NOTE

To protect user privacy, all filtering and processing of data is performed
client side so that the remote server does not know which assets are being
examined.  This means that data for ALL available assets (currently over 4000)
is fetched with each invocation of the script.  A rate limit of {L} seconds
between calls is thus imposed to prevent abuse of the remote server.  When the
--btc option is in effect, this limit is reduced to {B} seconds.  To bypass the
rate limit entirely, use --cached-data.


                                  EXAMPLES

# Basic display in ‘overview’ mode:
$ mmnode-ticker

# Display BTC price only:
$ mmnode-ticker --btc

# Wide display, add EUR and OMR columns, OMRUSD rate, extra precision and
# proxy:
$ mmnode-ticker -w -c eur,omr-omani-rial:2.59r -e2 -x http://vpnhost:8118

# Wide display, use cached data from previous network query, show portfolio
# (see above), pipe output to pager, add DOGE row:
$ mmnode-ticker -wCFP -r doge

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
		'notes': lambda s: s.format(
			assets    = fmt_list(assets_list_gen(cfg_in),fmt='col',indent='  '),
			cfg       = os.path.relpath(cfg_in.cfg_file,start=homedir),
			pf_cfg    = os.path.relpath(cfg_in.portfolio_file,start=homedir),
			api_host  = api_host,
			api_url   = api_url,
			L         = ratelimit,
			B         = btc_ratelimit,
		)
	}
}

cmd_args = opts.init(opts_data,do_post_init=True)

cfg_in = get_cfg_in()

cfg = make_cfg(cmd_args,cfg_in)

opts.post_init()

main(cfg,cfg_in)
