#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen-node-tools

# Testing status
#  mmnode-addrbal             OK
#  mmnode-blocks-info         OK
#  mmnode-feeview             -
#  mmnode-halving-calculator  OK
#  mmnode-netrate             -
#  mmnode-peerblocks          OK
#  mmnode-ticker              OK
#  mmnode-txfind              -

all_tests='unit misc scripts btc btc_rt bch_rt ltc_rt'

groups_desc="
	default  - All tests minus the extra tests
	extra    - All tests minus the default tests
	noalt    - BTC-only tests
	quick    - Default tests minus bch_rt and ltc_rt
	qskip    - The tests skipped in the 'quick' test group
"

init_groups() {
	dfl_tests=$all_tests
	extra_tests=''
	noalt_tests='unit misc scripts btc btc_rt'
	quick_tests='unit misc scripts btc btc_rt'
	qskip_tests='bch_rt ltc_rt'
}

init_tests() {
	d_unit="low-level subsystems"
	t_unit="- $unit_tests_py"

	d_misc="miscellaneous features"
	t_misc="- $test_py helpscreens"

	d_scripts="scripts not requiring a coin daemon"
	t_scripts="- $test_py scripts"

	d_btc="Bitcoin with emulated RPC data"
	t_btc="- $test_py main"

	d_btc_rt="Bitcoin regtest"
	t_btc_rt="- $test_py regtest"

	d_bch_rt="Bitcoin Cash Node (BCH) regtest"
	t_bch_rt="- $test_py --coin=bch regtest"

	d_ltc_rt="Litecoin regtest"
	t_ltc_rt="- $test_py --coin=ltc regtest"
}
