#!/usr/bin/env python3
#
# MMGen Node Tools, terminal-based programs for Bitcoin and forkcoin nodes
# Copyright (C)2013-2025 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen-node-tools

"""
fakemods.mmgen_node_tools.Ticker: fake module for Ticker class
"""

from .Ticker_orig import *

class overlay_fake_DataSource:
	class coinpaprika:
		api_host = 'localhost:19900'
		api_proto = 'http'

DataSource.coinpaprika.api_host = overlay_fake_DataSource.coinpaprika.api_host
DataSource.coinpaprika.api_proto = overlay_fake_DataSource.coinpaprika.api_proto
