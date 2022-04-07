#!/bin/bash

if [ ! -d tests ]
then
	mkdir tests
fi

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
	${mamba_call} create -p $(pwd)/tests/_test_env main::python==3.9 conda-forge::datalad -y
fi

eval "$(conda shell.bash hook)"
conda activate $(pwd)/tests/_test_env
echo $(which python)
echo $(which datalad)

datalad clone https://github.com/OpenNeuroDatasets/ds000248.git tests/_test_data
datalad get tests/_test_data/*
echo Changing the audiovisual data to Fake Rest data for testing
for i in tests/_test_data/sub-01/meg/*; do mv $i ${i/audiovisual/rest} ; done

test_config_fname=$(pwd)/tests/test_config_rest.py
echo bids_root = $(pwd)/tests/_test_data >> ${test_config_fname}
echo deriv_root = f'{bids_root}/derivatives/ENIGMA_MEG' >> ${test_config_fname}
echo subjects_dir = f'{bids_root}/derivatives/freesurfer/subjects' >> ${test_config_fname}


#datalad clone https://github.com/OpenNeuroDatasets/ds003568.git _test_data
#datalad get _test_data/sub-23490/meg/sub-23490_task-rest_*
#datalad get _test_data/sub-23490/meg/sub-23490_coordsystem.json
#datalad get _test_data/sub-23490/anat
#datalad get _test_data/participants.tsv
#datalad get _test_data/dataset_description.json
