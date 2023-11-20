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

wallet_repo='../mmgen-wallet'

die()   { echo -e ${YELLOW}ERROR: $1$RESET; false; }
becho() { echo -e $BLUE$1$RESET; }

check_mmgen_repo() {
	( cd $wallet_repo; python3 ./setup.py --url | grep -iq 'mmgen' )
}

build_mmgen_extmod() {
	( cd $wallet_repo; python3 ./setup.py build_ext --inplace )
}

create_dir_links() {
	for link_name in 'mmgen' 'scripts'; do
		target="$wallet_repo/$link_name"
		if [ -e $link_name ]; then
			[ $(realpath --relative-to=. $link_name) == $target ] || die "'$link_name' does not point to '$target'"
		else
			echo "Creating symlink: $link_name"
			ln -s $target
		fi
	done
}

create_test_links() {
	paths='
		test/include                   symbolic
		test/overlay/__init__.py       symbolic
		test/overlay/fakemods/mmgen    symbolic
		test/__init__.py               symbolic
		test/cmdtest.py                hard
		test/unit_tests.py             hard
		test/test-release.sh           symbolic
		test/cmdtest_py_d/common.py    symbolic
		test/cmdtest_py_d/ct_base.py   symbolic
		cmds/mmgen-regtest             symbolic
	'
	while read path type; do
		[ "$path" ] || continue
		pfx=$(echo $path | sed -r 's/[^/]//g' | sed 's/\//..\//g')
		symlink_arg=$(if [ $type == 'symbolic' ]; then echo --symbolic; fi)
		target="$wallet_repo/$path"
		if [ ! -e "$target" ]; then
			echo "Target path $target is missing! Cannot proceed"
			exit 1
		fi
		fs="%-8s %-16s %s -> %s\n"
		if [ $type == 'hard' ]; then
			if [ -L $path ]; then
				printf "$fs" "Deleting" "symbolic link:" $path $target
				rm -rf $path
			elif [ -e $path ]; then
				if [ "$(stat --printf=%i $path)" -ne "$(stat --printf=%i $target)" ]; then
					printf "$fs" "Deleting" "stale hard link:" $path "?"
					rm -rf $path
				fi
			fi
		fi
		if [ ! -e $path ]; then # link is either absent or a broken symlink
			printf "$fs" "Creating" "$type link:" $path $target
			( cd "$(dirname $path)" && ln -f $symlink_arg $pfx$target )
		fi
	done <<<$paths
}

set -e

becho 'Initializing MMGen Node Tools Test Suite'

check_mmgen_repo || die "MMGen Wallet repository not found at $wallet_repo!"

build_mmgen_extmod

create_dir_links

create_test_links

becho 'OK'
