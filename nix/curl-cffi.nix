{
    stdenv,
    lib,
    python,
    buildPythonPackage,
    fetchPypi,
    curl-impersonate-chrome,
}:

buildPythonPackage rec {
    pname = "curl-cffi";
    # version = "0.13.0"; # uses option PROXY_CREDENTIAL_NO_REUSE, unavailable in current libcurl
    version = "0.10.0";
    pyproject = true;

    src = fetchPypi {
        pname = "curl_cffi";
        version = version;
        # hash = "sha256-YuzZCjgr1QI3UONgbgqnyxo6i6QcFCcLjl4Unr9yxco="; # 0.13.0
        hash = "sha256-PjezUmjKWEkvVO0CCuS1DDPuDeutQUXbn3RvBO1GbrA="; # 0.10.0
    };

    patches = [ ./use-system-libs.patch ];

    buildInputs = [ curl-impersonate-chrome ];

    build-system = with python.pkgs; [
        cffi
        setuptools
    ];

    dependencies = with python.pkgs; [
        cffi
        certifi
        typing-extensions
    ];

    env = lib.optionalAttrs stdenv.cc.isGNU {
        NIX_CFLAGS_COMPILE = "-Wno-error=incompatible-pointer-types";
    };

    pythonImportsCheck = [ "curl_cffi" ];

    meta = with lib; {
        description = "Python binding for curl-impersonate via cffi";
        homepage = "https://curl-cffi.readthedocs.io";
        license = licenses.mit;
        maintainers = with maintainers; [ chuangzhu ];
    };
}
