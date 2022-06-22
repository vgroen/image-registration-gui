Image Registration GUI
======================

_This repository is part of the [2022 Research Project](https://github.com/TU-Delft-CSE/Research-Project) of the [TU Delft](https://github.com/TU-Delft-CSE)._

_The corresponding research paper can be found here: [Improving Image Registration Accuracy through User Interaction](https://repository.tudelft.nl/islandora/object/uuid:944abc2a-d060-4868-be69-b7bda7ebe57a?collection=education)._


## Building & Running

When using [NixOS](https://nixos.org/) with flake support, this application can easily be built and ran from source by using

```shell
nix build
# Or
nix run
```

Otherwise, install the required python packages and run `src/main.py`.

**Dependencies**
- python 3.9
    - numpy
    - opencv4
    - pillow
    - scipy
    - pyside2
    - pyqt5


Please know that this method has not yet been tested, only the Nix flake method has.

