## Prerequisites

This repository contains an OpenDiHu example. The [OpenDiHu's online documentation](https://opendihu.readthedocs.io/en/latest/) provides extensive information on how to configure, build, install and run OpenDiHu. Here we provide a quick guide for Ubuntu 22.04 users:

- Extract the code from **opendihu.tar.xz**
- Install dependencies 
    ```
    sudo apt-get install -y build-essential cmake petsc-dev bison flex libeigen3-dev libxml2-dev libboost-all-dev libffi-dev wget unzip
    ```

- Build OpenDiHu
    ```
    cd opendihu
    make release_without_tests

    ```
    - Define `$OPENDIHU_HOME`. Replace `path/to/opendihu` with the path where OpenDiHu is located in your system.
    ```
    export OPENDIHU_HOME=path/to/opendihu         
    ```
    - Download [input files](https://zenodo.org/records/4705982) and define `$OPENDIHU_INPUT`. 
     ```
    export OPENDIHU_INPUT=path/to/input         
    ```
    - Trouble-shooting: The following fixes run time errors in parallel execution of OpenDiHu.
    ```
    export OMPI_MCA_osc="^ucx"
    export OMPI_MCA_btl="self,tcp"
    ```

## Building

OpenDiHu uses scons to build the executables. The easiest way to build the solvers is by adding the following shortcuts:

```bash
alias sr='$OPENDIHU_HOME/scripts/shortcuts/sr.sh'
alias mkorn='$OPENDIHU_HOME/scripts/shortcuts/mkorn.sh'
```

Then you can build the executables by simply running `mkorn && sr` in the current directory. This will create a `build_release/` executables with the executables. 

## Running

We provide a script which starts all four participants from the current directory. Thus you can just run

```
./muscle_contraction ../settings_muscle_contraction.py variables.py
```