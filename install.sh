#!/bin/bash
if [[ $- == *i* ]]
then
	echo Shell is properly in interactive mode
else
	echo Error: Shell needs to be invoked using interactive flag
	echo Without the -i, bash cannot access conda activate in subshell
	echo bash -i $0
	exit 1
fi

# Download mne_bids_pipeline submodule
echo Downloading mne_bids_pipeline
git submodule init
git submodule update

#Install mamba to increase speed of conda creation
echo Installing standard MNE graphical configuration
conda install conda-forge::mamba -y 
conda create -p ./enigma_meg -y
conda activate $(pwd)/enigma_meg
mamba install pip conda-forge::mne -y

#Install mne_bids_pipeline reqs
echo Installing additional mne_bids_requirements
pip install -r ./mne-bids-pipeline/requirements.txt

#Copy additional scripts to mne_bids_pipeline
cp $(pwd)/add_ons/_8*.py $(pwd)/mne-bids-pipeline/scripts/source/

