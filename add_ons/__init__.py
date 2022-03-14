from . import _01_make_bem_surfaces
from . import _02_make_forward
from . import _03_make_cov
from . import _04_make_inverse
from . import _05_group_average
from . import _80_make_enigma_inverse
from . import _81_calc_parcel_psds

SCRIPTS = (
    _01_make_bem_surfaces,
    _02_make_forward,
    _03_make_cov,
    _04_make_inverse,
    _05_group_average,
    _80_make_enigma_inverse,
    _81_calc_parcel_psds,
)
