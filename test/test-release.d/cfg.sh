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
#  mmnode-feeview             OK
#  mmnode-halving-calculator  OK
#  mmnode-netrate             -
#  mmnode-peerblocks          OK
#  mmnode-ticker              OK
#  mmnode-txfind              -

all_tests='unit lint misc scripts btc btc_rt bch_rt ltc_rt'

groups_desc="
	default  - All tests minus the extra tests
	extra    - All tests minus the default tests
	noalt    - BTC-only tests
	quick    - Default tests minus bch_rt and ltc_rt
	qskip    - The tests skipped in the 'quick' test group
"

init_groups() {
	dfl_tests='unit misc scripts btc btc_rt bch_rt ltc_rt'
	extra_tests='lint'
	noalt_tests='unit misc scripts btc btc_rt'
	quick_tests='unit misc scripts btc btc_rt'
	qskip_tests='lint bch_rt ltc_rt'
}

init_tests() {

	d_lint="code errors with static code analyzer"
	t_lint="
		- $pylint --errors-only mmgen_node_tools
		- $pylint --errors-only test
		- $pylint --errors-only --disable=relative-beyond-top-level test/cmdtest_py_d
	"

	d_unit="low-level subsystems"
	t_unit="- $unit_tests_py"

	d_misc="miscellaneous features"
	t_misc="- $cmdtest_py helpscreens"

	d_scripts="scripts not requiring a coin daemon"
	t_scripts="- $cmdtest_py scripts"

	d_btc="Bitcoin with emulated RPC data"
	t_btc="- $cmdtest_py main"

	d_btc_rt="Bitcoin regtest"
	t_btc_rt="- $cmdtest_py regtest"

	d_bch_rt="Bitcoin Cash Node (BCH) regtest"
	t_bch_rt="- $cmdtest_py --coin=bch regtest"

	d_ltc_rt="Litecoin regtest"
	t_ltc_rt="- $cmdtest_py --coin=ltc regtest"
}
