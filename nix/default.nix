import (
    if builtins.pathExists ./merged-packages.nix then
        ./merged-packages.nix
    else
        ../../mmgen-wallet/nix/merged-packages.nix
    ) { add_pkgs_path = ./node-tools-packages.nix; }
