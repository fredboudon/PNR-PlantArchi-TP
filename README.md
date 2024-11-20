# PNR Technical School: training session on Modelling Plants under Agrivoltaics


## Installation of the training material

To access git material, install first [Github Desktop](https://desktop.github.com/)

In a convenient directory, you will now download the training material by clicking on <> Code, selecting Github Desktop and following the instruction to clone the project on your computer.

Alternativelly, you can use the following commands in a shell:

    cd /path/to/your/documents
    git clone https://github.com/fredboudon/PNR-PlantArchi-TP.git


## Installation of Software using Conda


This installation is based on [Conda](https://conda.io). Conda is a package manager that can be installed on Linux, Windows, and Mac.
If you have not yet installed conda on your computer, follow these instructions:

[Conda Installation](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html). Follow instructions for Miniconda.

[Conda Download](https://conda.io/miniconda.html). Use the Python 3.10 based installation.

Then, after install of conda, run the following command in an Anaconda Shell to create the sofware environment and its notebooks extension.

    cd /path/to/your/documents/PNR-PlantArchi-TP/
    conda env create -f environment.yml

Activate the environment using

    conda activate pnr

Test your installation by running

    jupyter lab .


## Online access to the exercices

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fredboudon/lpy-training.git/imagina2021?filepath=examples)
[![NBViewer](https://img.shields.io/badge/render-nbviewer-orange.svg)](https://nbviewer.jupyter.org/github/fredboudon/lpy-training/blob/imagina2021/examples/L-systems-Topo-Turtle.ipynb)
[![NBViewer](https://img.shields.io/badge/render-nbviewer-orange.svg)](https://nbviewer.jupyter.org/github/fredboudon/lpy-training/blob/imagina2021/examples/L-systems-Rewritting.ipynb)
[![NBViewer](https://img.shields.io/badge/render-nbviewer-orange.svg)](https://nbviewer.jupyter.org/github/fredboudon/lpy-training/blob/imagina2021/examples/Lsystems-InformationTransfert.ipynb)
