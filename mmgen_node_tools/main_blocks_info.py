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
mmnode-blocks-info: Display information about a block or range of blocks
"""

from mmgen.cfg import gc,Config
from mmgen.util import async_run,fmt_list
from .BlocksInfo import BlocksInfo,JSONBlocksInfo

opts_data = {
	'sets': [
		('header_info',    True,   'fields',     None),
		('header_info',    True,   'miner_info', None),
		('header_info',    True,   'stats',      'range'),
		('json_raw',       True,   'json',       True),
		('raw_miner_info', True,   'miner_info', True),
		('stats_only',     True,   'no_header',  True),
	],
	'text': {
		'desc':    'Display information about a block or range of blocks',
		'usage':   '[opts] blocknum ... | blocknum-blocknum[+step] | [blocknum|-nBlocks]+nBlocks[+step]',
		'usage2': [
			'[opts] blocknum ...',
			'[opts] blocknum-blocknum[+step]',
			'[opts] [blocknum|-nBlocks]+nBlocks[+step]',
		],
		'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-f, --full-stats      Stats that relate to a specific field are shown only
                      if that field is configured, whether by default or via
                      the --fields option.  This option adds the fields req-
                      uired to produce a full display of configured stats.
-H, --header-info     Display information from block headers only
-j, --json            Produce JSON output
-J, --json-raw        Produce JSON output with unformatted values
-m, --miner-info      Display miner info in coinbase transaction
-M, --raw-miner-info  Display miner info in uninterpreted form
-n, --no-header       Don’t print the column header
-o, --fields=         Display the specified fields (comma-separated list).
                      See AVAILABLE FIELDS below.  Prefix the list with '+'
                      to add the fields to the defaults, or '-' to remove
                      them.  The special values 'all' and 'none' select all
                      available fields or none, respectively.  The '+' and
                      '-'-prefixed lists may be concatenated to specify both
                      addition and removal of fields.  A single '-'-prefixed
                      list may be additionally prefixed by 'all'.
-s, --stats=          Display the specified stats (comma-separated list).
                      See AVAILABLE STATS below.  The prefixes and special
                      values available to the --fields option are recognized.
-S, --stats-only      Display stats only.  Suppress display of per-block data.
""",
	'notes': """
If no block number is specified, the current chain tip is assumed.

The special value 'cur' can be used to designate the chain tip wherever a
block number is expected.

If the requested range ends at the current chain tip, an estimate of the next
difficulty adjustment is also displayed. The estimate is based on the average
Block Discovery Interval from the beginning of the current {I}-block period.

All fee fields except for 'totalfee' are in satoshis per virtual byte.

AVAILABLE FIELDS: {F}

AVAILABLE STATS: {S}

EXAMPLES:

    Display info for current block:
    $ {p}

    Display info for the Genesis Block:
    $ {p} 0

    Display info for the last 20 blocks:
    $ {p} +20

    Display specified fields for blocks 165-190
    $ {p} -o block,date,size,inputs,nTx 165-190

    Display info for 10 blocks beginning at block 600000:
    $ {p} 600000+10

    Display info for every 5th block of 50-block range beginning at 1000
    blocks from chain tip:
    $ {p} -- -1000+50+5

    Display info for block 152817, adding miner field:
    $ {p} -o +miner 152817

    Display specified fields for listed blocks:
    $ {p} -o block,date,hash 245798 170 624044

    Display every difficulty adjustment from Genesis Block to chain tip:
    $ {p} -o +difficulty 0-cur+{I}

    Display roughly a block a day over the last two weeks.  Note that
    multiplication is allowed in the nBlocks spec:
    $ {p} +144*14+144

    Display only range stats for the last ten blocks:
    $ {p} -o none -s range +10

    Display data for the last ten blocks, omitting the 'size' and 'subsidy'
    fields from the defaults and skipping stats:
    $ {p} -o -size,subsidy -s none +10

    Display data for the last ten blocks, omitting the 'size' and 'version'
    fields from the defaults and adding the 'inputs' and 'utxo_inc' fields:
    $ {p} -o -version,size+utxo_inc,inputs +10

    Display all fields and stats for the last ten blocks:
    $ {p} -o all -s all +10

    Same as above, but omit the 'miner' and 'hash' fields:
    $ {p} -o all-miner,hash -s all +10

    Same as above, but display only fields relating to stats:
    $ {p} -o none -s all -f +10

    Same as above, but display stats only:
    $ {p} -o none -s all -fS +10

    Display headers-only info for the last 1000 blocks.  Speed up execution
    using the async RPC backend:
    $ {p} --rpc-backend=aio -H +1000

This program requires a txindex-enabled daemon for correct operation.
""" },
	'code': {
		'notes': lambda cfg,proto,s: s.format(
			I = proto.diff_adjust_interval,
			F = fmt_list(BlocksInfo.fields,fmt='bare'),
			S = fmt_list(BlocksInfo.all_stats,fmt='bare'),
			p = gc.prog_name,
		)
	}
}

cfg = Config(opts_data=opts_data)

async def main():

	from mmgen.rpc import rpc_init

	cls = JSONBlocksInfo if cfg.json else BlocksInfo

	m = cls( cfg, cfg._args, await rpc_init(cfg,ignore_wallet=True) )

	if m.fnames and not cfg.no_header:
		m.print_header()

	await m.process_blocks()

	if m.last:
		for i,sname in enumerate(m.stats):
			m.process_stats_pre(i)
			await m.process_stats(sname)

	m.finalize_output()

async_run(main())
