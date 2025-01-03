{ pkgs, python }:

{
    system-packages = with pkgs; {
        cacert = cacert; # ticker (curl)
    };

    python-packages = with python.pkgs; {
        yahooquery = (pkgs.callPackage ./yahooquery.nix {}); # ticker
        pyyaml = pyyaml;                                     # ticker
    };
}
