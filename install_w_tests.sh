#!/bin/bash

# Test for the presence of the enigma meg conda env
if [ ! -e enigma_meg ]
then 
	echo Installing the mne_bids_pipeline_enigma environment first
	./install.sh
fi

#Get full path for conda - so it doesn't have to be activated
conda_call=$(which conda) 
mamba_call=$(which mamba)

conda_main_dir=$(dirname $(dirname ${conda_call}))
conda_activate=${conda_main_dir}/bin/activate

#Override install
if [ ! -e _test_env ] 
then
	echo Installing Datalad for testing env
	${mamba_call} create -p $(pwd)/_test_env main::python==3.9 conda-forge::datalad -y
fi

eval "$(conda shell.bash hook)"
conda activate $(pwd)/_test_env
echo $(which python)
echo $(which datalad)

datalad clone https://github.com/OpenNeuroDatasets/ds003568.git _test_data
datalad get _test_data/sub-23490/meg/sub-23490_task-rest_*
datalad get _test_data/sub-23490/meg/sub-23490_coordsystem.json
datalad get _test_data/sub-23490/anat
datalad get _test_data/participants.tsv
datalad get _test_data/dataset_description.json

