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

all_tests='mod lint ruff pylint bandit misc scripts btc btc_rt bch_rt ltc_rt'

groups_desc="
	default  - All tests minus the extra tests
	extra    - All tests minus the default tests
	noalt    - BTC-only tests
	quick    - Default tests minus bch_rt and ltc_rt
	qskip    - The tests skipped in the 'quick' test group
"

init_groups() {
	dfl_tests='mod misc scripts btc btc_rt bch_rt ltc_rt'
	extra_tests='lint ruff pylint bandit'
	noalt_tests='mod misc scripts btc btc_rt'
	quick_tests='mod misc scripts btc btc_rt'
	qskip_tests='lint ruff pylint bandit bch_rt ltc_rt'
}

init_tests() {

	d_ruff="code errors with Ruff static analyzer"
	e_ruff="Error checking failed!"
	t_ruff="
		- $ruff check mmgen_node_tools
		- $ruff check test
	"

	d_pylint="code errors with Pylint static analyzer"
	e_pylint="Error checking failed!"
	t_pylint="
		- $pylint mmgen_node_tools
		- $pylint test
		- $pylint --disable=relative-beyond-top-level test/cmdtest_d
	"

	d_bandit="code vulnerabilities with Bandit static analyzer"
	e_bandit="Error checking failed!"
	t_bandit="
		- $bandit setup.py
		- $bandit mmgen_node_tools
	"

	d_lint="code errors and vulnerabilities with all available tools"
	e_lint="Error checking failed!"
	t_lint="
		- # ruff
		$t_ruff
		- # bandit
		$t_bandit
		- # pylint
		$t_pylint
	"

	d_mod="low-level subsystems"
	t_mod="- $modtest_py"

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
