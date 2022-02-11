# MMGen node tools

Helper utilities for Bitcoin and forkcoin full nodes.

Requires modules from the [MMGen online/offline cryptocurrency wallet][6].

Currently tested on Linux only.  Some scripts may not work under Windows/MSYS2.

## Install:

First, install [MMGen][6].

Then,

    $ git clone https://github.com/mmgen/mmgen-node-tools
    $ cd mmgen-node-tools
    $ python3 -m build --no-isolation
    $ python3 -m pip install --user dist/*.whl

Also make sure that `~/.local/bin` is in `PATH`.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

[**Forum**][4] |
[PGP Public Key][5] |
Donate: 15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w

[4]: https://bitcointalk.org/index.php?topic=567069.0
[5]: https://github.com/mmgen/mmgen/wiki/MMGen-Signing-Keys
[6]: https://github.com/mmgen/mmgen/
