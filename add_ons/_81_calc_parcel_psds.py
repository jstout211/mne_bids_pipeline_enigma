"""
====================
12. Inverse solution
====================

Compute and apply an inverse solution for each evoked data set.
"""

import itertools
import logging
from typing import Optional
from types import SimpleNamespace

import numpy as np
import os
import pandas as pd

from enigmeg.mod_label_extract import mod_source_estimate
from enigmeg.spectral_peak_analysis import calc_spec_peak

import mne
from mne.minimum_norm import (make_inverse_operator, apply_inverse,
                              write_inverse_operator)
from mne.beamformer import read_beamformer, apply_lcmv_epochs
from mne_bids import BIDSPath

import config
from config import gen_log_kwargs, on_error, failsafe_run, sanitize_cond_name
from config import parallel_func

logger = logging.getLogger('mne-bids-pipeline')

def write_aparc_sub(subjid=None, subjects_dir=None):
    '''Check for fsaverage and aparc_sub and download
    Morph fsaverage aparc_sub labels to single subject data
    
    https://mne.tools/stable/auto_examples/visualization/plot_parcellation.html
    '''
    mne.datasets.fetch_fsaverage(verbose='ERROR') #True requires TQDM
    mne.datasets.fetch_aparc_sub_parcellation(subjects_dir=subjects_dir,
                                          verbose='ERROR')
    
    sub_labels=mne.read_labels_from_annot('fsaverage',parc='aparc_sub', 
                                   subjects_dir=subjects_dir)        
    subject_labels=mne.morph_labels(sub_labels, subject_to=subjid, 
                                 subjects_dir=subjects_dir)
    mne.write_labels_to_annot(subject_labels, subject=subjid, 
                              parc='aparc_sub', subjects_dir=subjects_dir, 
                              overwrite=True)
    
def get_freq_idx(bands, freq_bins):
    ''' Get the frequency indexes'''
    output=[]
    for band in bands:
        tmp = np.nonzero((band[0] < freq_bins) & (freq_bins < band[1]))[0]   ### <<<<<<<<<<<<< Should this be =<...
        output.append(tmp)
    return output



@failsafe_run(on_error=on_error, script_path=__file__)
def run_inverse(*, cfg, subject, session=None):
    bids_path = BIDSPath(subject=subject,
                         session=session,
                         task=cfg.task,
                         acquisition=cfg.acq,
                         run=None,
                         recording=cfg.rec,
                         space=cfg.space,
                         extension='.fif',
                         datatype=cfg.datatype,
                         root=cfg.deriv_root,
                         check=False)

    fname_info = bids_path.copy().update(**cfg.source_info_path_update)
    fname_fwd = bids_path.copy().update(suffix='fwd')
    fname_cov = bids_path.copy().update(suffix='cov')
    fname_lcmv = bids_path.copy().update(suffix='lcmv', extension='.h5')
    fname_epo = bids_path.copy().update(processing='clean', suffix='epo')

    info = mne.io.read_info(fname_info)
    
    filters = read_beamformer(fname_lcmv)
    epochs = mne.read_epochs(fname_epo)
    fwd = mne.read_forward_solution(fname_fwd)

    if not (cfg.fs_subjects_dir / cfg.fs_subject / 'label' / 'lh.aparc_sub.annot').exists():
        write_aparc_sub(subjid=cfg.fs_subject, subjects_dir=cfg.fs_subjects_dir)

    labels_lh=mne.read_labels_from_annot(cfg.fs_subject, parc='aparc_sub',
                                        subjects_dir=cfg.fs_subjects_dir, hemi='lh') 
    labels_rh=mne.read_labels_from_annot(cfg.fs_subject, parc='aparc_sub',
                                        subjects_dir=cfg.fs_subjects_dir, hemi='rh') 
    labels=labels_lh + labels_rh 
    
    results_stcs = apply_lcmv_epochs(epochs, filters, return_generator=True)#True)#, max_ori_out='max_power')
    
    #Monkey patch of mne.source_estimate to perform 15 component SVD
    label_ts = mod_source_estimate.extract_label_time_course(results_stcs, 
                                                              labels, 
                                                              fwd['src'],
                                                              mode='pca15_multitaper')
    
#     #Convert list of numpy arrays to ndarray (Epoch/Label/Sample)
    label_stack = np.stack(label_ts)

#     #HACK HARDCODED FREQ BINS
    freq_bins = np.linspace(1,45,22)#177)    ######################################3######### FIX

#     #Initialize 
    label_power = np.zeros([len(labels), len(freq_bins)])  
    alpha_peak = np.zeros(len(labels))
    
#     #Create PSD for each label
    for label_idx in range(len(labels)):
        print(str(label_idx))
        current_psd = label_stack[:,label_idx, :].mean(axis=0) 
        label_power[label_idx,:] = current_psd
        
        spectral_image_path = os.path.join(bids_path.fpath.parent, 'Spectra_'+
                                            labels[label_idx].name + '.png')

        try:
            tmp_fmodel = calc_spec_peak(freq_bins, current_psd, 
                            out_image_path=spectral_image_path)
            
            #FIX FOR MULTIPLE ALPHA PEAKS
            potential_alpha_idx = np.where((8.0 <= tmp_fmodel.peak_params[:,0] ) & \
                                    (tmp_fmodel.peak_params[:,0] <= 12.0 ) )[0]
            if len(potential_alpha_idx) != 1:
                alpha_peak[label_idx] = np.nan         #############FIX ###########################3 FIX     
            else:
                alpha_peak[label_idx] = tmp_fmodel.peak_params[potential_alpha_idx[0]][0]
        except:
            alpha_peak[label_idx] = np.nan  #Fix <<<<<<<<<<<<<<    
        
#     #Save the label spectrum to assemble the relative power
    freq_bin_names=[str(binval) for binval in freq_bins]
    label_spectra_dframe = pd.DataFrame(label_power, columns=[freq_bin_names])
    label_spectra_dframe.to_csv( os.path.join(bids_path.fpath.parent, 'label_spectra.csv') , index=False)
    with open(os.path.join(bids_path.fpath.parent, 'label_spectra.npy'), 'wb') as f:
        np.save(f, label_power)
    
    relative_power = label_power / label_power.sum(axis=1, keepdims=True)

#     #Define bands
    bands = [[1,3], [3,6], [8,12], [13,35], [35,55]]
    band_idxs = get_freq_idx(bands, freq_bins)

#     #initialize output
    band_means = np.zeros([len(labels), len(bands)]) 
    #Loop over all bands, select the indexes assocaited with the band and average    
    for mean_band, band_idx in enumerate(band_idxs):
        band_means[:, mean_band] = relative_power[:, band_idx].mean(axis=1) 
    
    output_filename = os.path.join(bids_path.fpath.parent, 'Band_rel_power.csv')
    

    bands_str = [str(i) for i in bands]
    label_names = [i.name for i in labels]
    
    output_dframe = pd.DataFrame(band_means, columns=bands_str, 
                                  index=label_names)
    output_dframe['AlphaPeak'] = alpha_peak
    output_dframe.to_csv(output_filename, sep='\t')    
# # =============================================================================
# # 
# # =============================================================================



def get_config(
    subject: Optional[str] = None,
    session: Optional[str] = None
) -> SimpleNamespace:
    cfg = SimpleNamespace(
        task=config.get_task(),
        datatype=config.get_datatype(),
        acq=config.acq,
        rec=config.rec,
        space=config.space,
        source_info_path_update=config.source_info_path_update,
        inverse_targets=config.inverse_targets,
        noise_cov=config.noise_cov,
        ch_types=config.ch_types,
        conditions=config.conditions,
        use_template_mri=config.use_template_mri,
        fs_subjects_dir=config.get_fs_subjects_dir(),
        fs_subject=config.get_fs_subject(subject=subject),
        inverse_method=config.inverse_method,
        deriv_root=config.get_deriv_root(),
        bids_root=config.get_bids_root(),
        n_jobs=config.get_n_jobs(),
    )
    return cfg


def main():
    """Run inv."""
    if not config.run_source_estimation:
        msg = '    … skipping: run_source_estimation is set to False.'
        logger.info(**gen_log_kwargs(message=msg))
        return

    with config.get_parallel_backend():
        parallel, run_func, _ = parallel_func(
            run_inverse,
            n_jobs=config.get_n_jobs()
        )
        logs = parallel(
            run_func(cfg=get_config(subject), subject=subject, session=session)
            for subject, session in
            itertools.product(
                config.get_subjects(),
                config.get_sessions()
            )
        )

        config.save_logs(logs)


if __name__ == '__main__':
    main()
