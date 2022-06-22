{
  # Flake setup from:
  #  https://github.com/nix-gui/nix-gui
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
        packages.${pname} = pkgs.callPackage (
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

        packages.default = self.packages.${system}.${pname};
        defaultPackage = self.packages.${system}.default;

        apps = rec {
          ${pname} = flake-utils.lib.mkApp {
            drv = self.packages.${system}.${pname};
          };
        };

        apps.default = self.apps.${system}.${pname};
        defaultApp = self.apps.${system}.default;

        devShells = {
          default = pkgs.mkShell {
            QT_PLUGIN_PATH = "${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}";

            nativeBuildInputs = [
              python
            ];

            inputsFrom = [
              self.packages.${system}.${pname}
            ];
          };
        };

        devShell = self.devShells.${system}.default;
      }
    );
}

