# MMGen Node Tools

### Terminal-based utilities for Bitcoin and forkcoin full nodes

Requires modules from the [MMGen online/offline cryptocurrency wallet][6].

## Install:

If installing as user (without venv), make sure that `~/.local/bin` is in `PATH`.

#### Windows/MSYS2:

> Install [MSYS2 and the MMGen Wallet dependencies][8], skipping installation of
> scrypt, libsecp256k1 and the wallet itself if desired.
>
> Install some additional dependencies:
> ```bash
> $ pacman -S mingw-w64-ucrt-x86_64-python-pandas
> $ python3 -m pip install requests-futures
> $ python3 -m pip install --no-deps yahooquery
> ```

#### Linux:

> Install the [required MMGen Wallet packages][7] for your Linux distribution.

### Stable version:

```bash
$ python3 -m pip install --upgrade mmgen-node-tools
```

### Development version:

Install the latest development version of [MMGen Wallet][6] for your platform:

```bash
$ git clone https://github.com/mmgen/mmgen-node-tools
$ cd mmgen-node-tools
$ python3 -m build --no-isolation
$ python3 -m pip install dist/*.whl
```

## Test:

*NOTE: the tests require that the MMGen Wallet and MMGen Node Tools repositories be
located in the same directory.*

#### Windows/MSYS2:

> *Tested only on NTFS – with ReFS your mileage may vary*
>
> Turn on Developer Mode to enable symlinks:
> ```
> Settings -> Update & Security -> For developers -> Developer Mode: On
> ```
> and add this to your `~/.bashrc`:
> ```bash
> export MSYS=winsymlinks:nativestrict
> ```
> Close and reopen the MSYS2 terminal to update your environment.

Initialize the test framework (must be run at least once after cloning, and
possibly again after a pull if tests have been updated):
```
$ test/init.sh
```
BTC-only testing:
```
$ test/test-release.sh -A
```
Full testing:
```
$ test/test-release.sh
```

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

Homepage:
[Clearnet](https://mmgen.org) |
[I2P](http://mmgen-wallet.i2p) |
[Onion](http://mmgen55rtcahqfp2hn3v7syqv2wqanks5oeezqg3ykwfkebmouzjxlad.onion)    
Code repository:
[Clearnet](https://mmgen.org/project/mmgen/mmgen-node-tools) |
[I2P](http://mmgen-wallet.i2p/project/mmgen/mmgen-node-tools) |
[Onion](http://mmgen55rtcahqfp2hn3v7syqv2wqanks5oeezqg3ykwfkebmouzjxlad.onion/project/mmgen/mmgen-node-tools)    
Code repository mirrors:
[Github](https://github.com/mmgen/mmgen-node-tools) |
[Gitlab](https://gitlab.com/mmgen/mmgen-node-tools) |
[Gitflic](https://gitflic.ru/project/mmgen/mmgen-node-tools)     
[Keybase](https://keybase.io/mmgen) |
[Twitter](https://twitter.com/TheMMGenProject) |
[Reddit](https://www.reddit.com/user/mmgen-py) |
[Bitcointalk](https://bitcointalk.org/index.php?topic=567069.new#new)   
[PGP Signing Key][5]: 5C84 CB45 AEE2 250F 31A6 A570 3F8B 1861 E32B 7DA2    
Donate:    
&nbsp;⊙&nbsp;BTC:&nbsp;*bc1qxmymxf8p5ckvlxkmkwgw8ap5t2xuaffmrpexap*    
&nbsp;⊙&nbsp;BCH:&nbsp;*15TLdmi5NYLdqmtCqczUs5pBPkJDXRs83w*    
&nbsp;⊙&nbsp;XMR:&nbsp;*8B14zb8wgLuKDdse5p8f3aKpFqRdB4i4xj83b7BHYABHMvHifWxiDXeKRELnaxL5FySfeRRS5girgUvgy8fQKsYMEzPUJ8h*

[5]: https://github.com/mmgen/mmgen-wallet/wiki/MMGen-Signing-Keys
[6]: https://github.com/mmgen/mmgen-wallet/
[7]: https://github.com/mmgen/mmgen-wallet/wiki/Install-MMGen-on-Linux
[8]: https://github.com/mmgen/mmgen-wallet/wiki/Install-MMGen-on-Microsoft-Windows#a_m
