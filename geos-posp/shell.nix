{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
buildInputs = [
nodejs-18_x pandoc
];
shellHook = ''
        npm install
        export PATH="$PWD/node_modules/.bin/:$PATH"
    '';

}
