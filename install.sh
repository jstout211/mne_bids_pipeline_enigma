# Download mne_bids_pipeline submodule
echo Downloading mne_bids_pipeline
git submodule init
git submodule update

#Install mamba to increase speed of conda creation
echo Installing standard MNE graphical configuration
conda install conda-forge::mamba -y 
conda create -n enigma_meg -y
conda activate enigma_meg
mamba install pip conda-forge::mne -y

#Install mne_bids_pipeline reqs
echo Installing additional mne_bids_requirements
pip install ./mne_bids_pipeline/requirements.txt

