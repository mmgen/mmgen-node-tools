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
test.cmdtest_d.httpd.ticker: Ticker WSGI http server
"""

from . import HTTPD

class TickerServer(HTTPD):
	name = 'ticker server'
	port = 19900
	content_type = 'application/json'

	def make_response_body(self, method, environ):

		with open('test/ref/ticker/ticker.json') as fh:
			text = fh.read()

		return text.encode()
