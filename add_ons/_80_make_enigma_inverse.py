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

import mne
from mne.minimum_norm import (make_inverse_operator, apply_inverse,
                              write_inverse_operator)
from mne.beamformer import make_lcmv, apply_lcmv_epochs
from mne_bids import BIDSPath

import config
from config import gen_log_kwargs, on_error, failsafe_run, sanitize_cond_name
from config import parallel_func

logger = logging.getLogger('mne-bids-pipeline')


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
    fname_inv = bids_path.copy().update(suffix='inv')
    fname_lcmv = bids_path.copy().update(suffix='lcmv', extension='h5')
    fname_epo = bids_path.copy().update(processing='clean', suffix='epo')

    info = mne.io.read_info(fname_info)
    
    if cfg.noise_cov == "ad-hoc":
        cov = mne.make_ad_hoc_cov(info)
    else:
        cov = mne.read_cov(fname_cov)
    forward = mne.read_forward_solution(fname_fwd)


    # inverse_operator = make_inverse_operator(info, forward, cov, loose=0.2,
    #                                          depth=0.8, rank='info')

    epochs = mne.read_epochs(fname_epo)
    filters = make_lcmv(epochs.info, forward, cov, reg=0.01, #noise_cov=noise_cov,
                        pick_ori='max-power',
                        weight_norm='unit-noise-gain', rank='info')
    
    filters.save(fname_lcmv, overwrite=True)
        
    
    stcs = apply_lcmv_epochs(epochs, filters) #return_generator=True ##############3 <<<
    
    

    hemi_str = 'hemi'  # MNE will auto-append '-lh' and '-rh'.
    fname_stc = bids_path.copy().update(
        suffix=f'lcmv+{hemi_str}',
        extension=None)


    # stc = apply_inverse(
    #     evoked=evoked,
    #     inverse_operator=inverse_operator,
    #     lambda2=lambda2,
    #     method=method,
    #     pick_ori=pick_ori
    # )
    stcs[0].save(fname_stc, overwrite=True)


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
        inverse_method=config.inverse_method,
        deriv_root=config.get_deriv_root(),
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
            run_func(cfg=get_config(), subject=subject, session=session)
            for subject, session in
            itertools.product(
                config.get_subjects(),
                config.get_sessions()
            )
        )

        config.save_logs(logs)


if __name__ == '__main__':
    main()
