study_name = 'ENIGMA_MEG'

#subjects=['']
task='rest'
runs=['1']
l_freq = 0.5
h_freq = 140

resample_sfreq = 300


ch_types = ['meg']
reject = dict(mag=4e-12)

rest_epochs_duration = 2.0 
rest_epochs_overlap = 0
baseline = None
epochs_tmin = 0.0

on_error = 'continue'
N_JOBS=10

source_info_path_update = {'processing':'clean', 'suffix':'epo'}

#find_flat_channels_meg=True
#find_noisy_channels_meg=True



#ch_types = ['meg']
#mf_reference_run = '01'
#use_maxwell_filter = False
#process_er = True
#noise_cov = 'emptyroom'
