{
    lib,
    pkgs,
    fetchFromGitHub,
}:

with pkgs.python312.pkgs;

buildPythonPackage rec {
    pname = "yahooquery";
    version = "2.3.7";
    pyproject = true;

    disabled = pythonOlder "3.8.1";

    src = fetchFromGitHub {
        owner = "dpguthrie";
        repo = "yahooquery";
        rev = "refs/tags/v${version}";
        hash = "sha256-Iyuni1SoTB6f7nNFhN5A8Gnv9kV78frjpqvvW8qd+/M=";
    };

    patches = [ ./yahooquery-noversioning.patch ];

    build-system = [ poetry-core ];

    dependencies = [
       requests         # ^2.31.0
       pandas           # ^2.0.3
       requests-futures # ^1.0.1
       tqdm             # ^4.65.0
       lxml             # ^4.9.3
       selenium         # {version = ^4.10.0, optional = true}
       beautifulsoup4   # ^4.12.2
    ];

    doCheck = false; # skip tests

    meta = with lib; {
        description = "Python wrapper for an unofficial Yahoo Finance API";
        homepage = "https://yahooquery.dpguthrie.com";
        license = licenses.mit;
    };
}
