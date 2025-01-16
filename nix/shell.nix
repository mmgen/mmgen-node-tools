import ../../mmgen-wallet/nix/shell.nix {
    repo = "mmgen-node-tools";
    add_pkgs_path = ./node-tools-packages.nix;
}
