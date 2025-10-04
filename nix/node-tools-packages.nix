{ pkgs, python }:

{
    system-packages = with pkgs; {
        cacert = cacert; # ticker (curl)
    };

    python-packages = with python.pkgs; {
        yahooquery = (callPackage ./yahooquery.nix {}); # ticker
        pyyaml = pyyaml;                                # ticker
    };
}
