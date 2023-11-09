# MMGen Node Tools

### Terminal-based utilities for Bitcoin and forkcoin full nodes

Requires modules from the [MMGen online/offline cryptocurrency wallet][6].

Currently tested on Linux only.  Some scripts may not work under Windows/MSYS2.

## Install:

If installing as user (without venv), Make sure that `~/.local/bin` is in `PATH`.

### Stable version:

First, install the [required MMGen packages][7] for your Linux distribution:

Then,

	$ python3 -m pip install --upgrade mmgen-node-tools

### Development version:

First, install the latest development version of [MMGen][6].

Then,

	$ git clone https://github.com/mmgen/mmgen-node-tools
	$ cd mmgen-node-tools
	$ python3 -m build --no-isolation
	$ python3 -m pip install dist/*.whl

## Test:

*NOTE: the tests require that the MMGen and MMGen Node Tools repositories be
located in the same directory.*

Initialize the test framework (must be run at least once after cloning, and
possibly again after a pull if tests have been updated):

	$ test/init.sh

BTC-only testing:

	$ test/test-release.sh -A

Full testing:

	$ test/test-release.sh

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

[**Forum**][4] |
[PGP Public Key][5] |
Donate: 15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w

[4]: https://bitcointalk.org/index.php?topic=567069.0
[5]: https://github.com/mmgen/mmgen/wiki/MMGen-Signing-Keys
[6]: https://github.com/mmgen/mmgen/
[7]: https://github.com/mmgen/mmgen/Install-MMGen-on-Linux
