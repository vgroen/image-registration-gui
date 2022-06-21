{
  description = "Image Registration GUI";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pname = "ir-gui";
        version = "0.1";

        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python39;
        pythonPackages = python.pkgs;
      in {
        packages."${pname}" = pkgs.callPackage (
          { stdenv, lib }:
          pythonPackages.buildPythonPackage rec {
            inherit pname version;
            src = ./.;

            propagatedBuildInputs = [
              pythonPackages.pyqt5
              pythonPackages.numpy
              pythonPackages.pillow
              pythonPackages.scipy
              pythonPackages.opencv4
              pythonPackages.pyside2
            ];

            makeWrapperArgs = [
              "--prefix PATH : ${pkgs.nixpkgs-fmt}/bin"
              "--set QT_PLUGIN_PATH ${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}"
            ];

            checkInputs = [
              pkgs.nix
            ];
          }
        ) { };

        defaultPackage = self.packages."${system}"."${pname}";

        apps = {
          "${pname}" = flake-utils.lib.mkApp {
            drv = self.packages."${system}"."${pname}";
          };
        };

        defaultApp = self.apps."${system}"."${pname}";

        devShell = pkgs.mkShell {
          QT_PLUGIN_PATH = "${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}";

          nativeBuildInputs = [
            python
          ];

          inputsFrom = [
            self.packages."${system}"."${pname}"
          ];
        };
      }
    );
}

