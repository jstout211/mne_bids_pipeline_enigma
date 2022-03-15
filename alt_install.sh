#!/bin/bash

# Download mne_bids_pipeline submodule
echo Downloading mne_bids_pipeline
git submodule init
git submodule update --depth 1

#Get full path for conda - so it doesn't have to be activated
conda_call=$(which conda) 

#Install mamba to increase speed of conda creation
echo Installing standard MNE graphical configuration
${conda_call} install conda-forge::mamba -y 
mamba_call=$(which mamba)
${mamba_call} env create -p $(pwd)/enigma_meg conda-forge::mne ipython pip

#Install mne_bids_pipeline reqs
echo Installing additional mne_bids_requirements
pip_call=$(pwd)/enigma_meg/bin/pip
${pip_call} install git+https://github.com/jstout211/enigma_MEG.git
${pip_call} install -r $(pwd)/mne-bids-pipeline/requirements.txt

#Copy additional scripts to mne_bids_pipeline
cp $(pwd)/add_ons/_8*.py $(pwd)/mne-bids-pipeline/scripts/source/
rm $(pwd)/mne-bids-pipeline/scripts/source/__init__.py
cp $(pwd)/add_ons/__init__.py $(pwd)/mne-bids-pipeline/scripts/source/

#Modify mne_bid_pipeline run.py to use enigma local conda environment
./mod_script_paths.py mne-bids-pipeline/run.py
