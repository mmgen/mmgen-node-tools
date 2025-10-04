{
    lib,
    buildPythonPackage,
    fetchPypi,
    python,
}:

buildPythonPackage rec {
    pname = "yahooquery";
    version = "2.4.1";
    pyproject = true;

    src = fetchPypi {
        pname = "yahooquery";
        version = version;
        hash = "sha256-GQPGXq5qEtlelFAGNHkhbAeEbwE7riojkXkTUxt/rls=";
    };

    build-system = with python.pkgs; [ hatchling ];

    propagatedBuildInputs = with python.pkgs; [
        (callPackage ./curl-cffi.nix {}) # >=0.10.0
        pandas
        requests-futures
        tqdm
        lxml
        beautifulsoup4
    ];

    doCheck = false; # skip tests

    meta = with lib; {
        description = "Python wrapper for an unofficial Yahoo Finance API";
        homepage = "https://yahooquery.dpguthrie.com";
        license = licenses.mit;
    };
}
