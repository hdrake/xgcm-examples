# xgcm example notebooks

This repository holds the example notebooks for
[xgcm](https://github.com/xgcm/xgcm). They are rendered into the xgcm
documentation at [xgcm.readthedocs.io](https://xgcm.readthedocs.io), which
includes this repository as a git submodule (`docs/xgcm-examples`) pinned to a
specific commit.

The notebooks are stored **with their executed outputs**: the docs site renders
them as-is (`mkdocs-jupyter` with `execute: false`) and does not re-run them. So
when you change a notebook, re-execute it and commit the outputs, then bump the
submodule pointer in the main xgcm repo.

> **History:** this repo previously fed the now-defunct Pangeo Gallery via
> `binderbot`. That pipeline (binder.pangeo.io and its dispatch bot) no longer
> exists, so the gallery integration and its workflows have been removed. The
> notebooks now reach users solely through the xgcm documentation.

## Contributing examples

To contribute an example, fork this repository and add a self-contained
notebook. Provide the data it needs in one of these forms:

1. **Data available in the cloud (preferred).** See `03_MOM6.ipynb`, which reads
   GFDL-CM4 output directly from the analysis-ready CMIP6 Zarr store on Google
   Cloud (read anonymously; needs `zarr`+`gcsfs`).
2. **A file in a Zenodo archive**, downloaded from within the notebook. See
   `01_mitgcm.ipynb`, `02_nemo_idealized.ipynb`, and `04_eccov4.ipynb` (which
   pulls a 12-month ECCOv4r4 subset on the native LLC90 grid). Prefer small
   datasets where possible.

After adding or changing a notebook, execute it end-to-end and commit it with
its outputs so the documentation renders correctly.

## Plotting helpers

Some grids need a lot of matplotlib/cartopy code before they can be plotted
sensibly: resampling the 13 LLC tiles onto a lon/lat mesh, or zooming in on a
strip of cells around a tripolar seam. None of that is about xgcm, so it lives in
modules beside the notebooks (`llc_plots.py` for `04_eccov4`, `tripolar_plots.py`
for `05_tripolar_fold`) and is imported.

Keep the modules to plotting only. Grid construction, `interp`, `diff`, `pad` and
anything else a reader is meant to learn from should stay inline in the notebook,
where it is visible.

Where a grid can be plotted cheaply, do that first, before reaching for a
projection. `01_mitgcm` and `02_nemo_idealized` plot straight from xarray;
`04_eccov4` shows each LLC tile in its own index space in one line; `03_MOM6`
plots in nominal index coordinates before explaining why the tripolar grid needs
2-D `lon`/`lat`. It shows the reader how the data are laid out, and it is
something they can copy.

For more on setting up a development environment, see the
[xgcm contributor guide](https://xgcm.readthedocs.io/en/latest/contributor_guide/).
