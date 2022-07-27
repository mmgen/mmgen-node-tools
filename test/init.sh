#!/bin/bash
#
# mmgen = Multi-Mode GENerator, a command-line cryptocurrency wallet
# Copyright (C)2013-2022 The MMGen Project <mmgen@tuta.io>
# Licensed under the GNU General Public License, Version 3:
#   https://www.gnu.org/licenses
# Public project repositories:
#   https://github.com/mmgen/mmgen-node-tools
#   https://gitlab.com/mmgen/mmgen-node-tools

RED="\e[31;1m" GREEN="\e[32;1m" YELLOW="\e[33;1m" BLUE="\e[34;1m" RESET="\e[0m"

set -o errtrace
set -o functrace

trap 'echo -e "${GREEN}Exiting at user request$RESET"; exit' INT
trap 'echo -e "${RED}Node Tools test suite initialization exited with error (line $BASH_LINENO) $RESET"' ERR
umask 0022

PROGNAME=$(basename $0)
while getopts h OPT
do
	case "$OPT" in
	h)  printf "  %-16s Initialize the MMGen Node Tools test suite\n" "${PROGNAME}:"
		echo   "  USAGE:           $PROGNAME"
		echo   "  OPTIONS: '-h'  Print this help message"
		exit ;;
	*)  exit ;;
	esac
done

shift $((OPTIND-1))

mm_repo='../mmgen'

die()   { echo -e ${YELLOW}ERROR: $1$RESET; false; }
becho() { echo -e $BLUE$1$RESET; }

check_mmgen_repo() {
	( cd $mm_repo; python3 ./setup.py --url | grep -iq 'mmgen' )
}

build_mmgen_extmod() {
	( cd $mm_repo; python3 ./setup.py build_ext --inplace )
}

create_dir_links() {
	for target in 'mmgen' 'scripts'; do
		src="$mm_repo/$target"
		if [ -e $target ]; then
			[ $(realpath --relative-to=. $target) == $src ] || die "'$target' does not point to '$src'"
		else
			echo "Creating symlink: $target"
			ln -s $src
		fi
	done
}

create_test_links() {
	sources='
		test/include
		test/overlay
		test/__init__.py
		test/test.py
		test/unit_tests.py
		test/test-release.sh
		test/test_py_d/common.py
		test/test_py_d/ts_base.py
		cmds/mmgen-regtest
	'
	for src in $sources; do
		pfx=$(echo $src | sed -r 's/[^/]//g' | sed 's/\//..\//g')
		if [ ! -e $src ]; then
			echo "Creating symlink: $src"
			( cd "$(dirname $src)" && ln -s "$pfx$mm_repo/$src" )
		fi
	done
}

set -e

becho 'Initializing MMGen Node Tools Test Suite'

check_mmgen_repo || die "MMGen repository not found at $mm_repo!"

build_mmgen_extmod

create_dir_links

create_test_links

becho 'OK'
