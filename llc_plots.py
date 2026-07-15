"""Plotting helper for the ECCOv4 LLC example (``04_eccov4.ipynb``).

Plotting only, no xgcm. The LLC (lat-lon-cap) grid stores the globe as 13 square
tiles whose axes point in different directions, so a geographic map needs the
tiles resampled onto a regular lon/lat mesh first. That is all this module does.
"""

import cartopy as cart
import numpy as np
import pyresample
from matplotlib import pyplot as plt


class LLCMapper:
    """Resample 2-D cell-centred LLC fields onto a regular lon/lat grid and map them.

    Built once per dataset (the resampling weights depend only on the grid), then
    called with any ``(tile, j, i)`` field:

        mapper = LLCMapper(ds)
        mapper(ds.Depth)
        mapper(sst, cmap='RdBu_r')

    Parameters
    ----------
    ds : xarray.Dataset
        Must carry the LLC cell-centre coordinates ``XC`` / ``YC``.
    dx, dy : float
        Resolution, in degrees, of the target regular lon/lat mesh. The default
        0.25° comfortably oversamples the ~1° LLC90 grid, so the resampling does
        not visibly blur the field.
    """

    def __init__(self, ds, dx=0.25, dy=0.25):
        # the LLC cell centres, flattened across all 13 tiles into one point cloud
        lons_1d = ds.XC.values.ravel()
        lats_1d = ds.YC.values.ravel()
        self.orig_grid = pyresample.geometry.SwathDefinition(lons=lons_1d, lats=lats_1d)

        # the regular lon/lat mesh we resample onto
        lon_tmp = np.arange(-180, 180, dx) + dx / 2
        lat_tmp = np.arange(-90, 90, dy) + dy / 2
        self.new_grid_lon, self.new_grid_lat = np.meshgrid(lon_tmp, lat_tmp)
        self.new_grid = pyresample.geometry.GridDefinition(lons=self.new_grid_lon,
                                                           lats=self.new_grid_lat)

    def __call__(self, da, ax=None, projection=cart.crs.Robinson(), lon_0=-60,
                 **plt_kwargs):
        assert set(da.dims) == set(['tile', 'j', 'i']), \
            "da must have dimensions ['tile', 'j', 'i']"

        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': projection})

        # nearest-neighbour resample from the LLC point cloud onto the regular mesh.
        # radius_of_influence caps how far a target cell will reach for a source
        # point (100 km ~ one LLC90 cell), so genuine gaps stay empty rather than
        # being filled from far away.
        field = pyresample.kd_tree.resample_nearest(self.orig_grid, da.values,
                                                    self.new_grid,
                                                    radius_of_influence=100000,
                                                    fill_value=None)

        vmax = plt_kwargs.pop('vmax', np.nanmax(field))
        vmin = plt_kwargs.pop('vmin', np.nanmin(field))
        x, y = self.new_grid_lon, self.new_grid_lat

        # Draw in two halves split at the projection's antimeridian. pcolormesh
        # would otherwise stretch cells the whole way across the map wherever the
        # mesh wraps past the seam. `lon_0` is the seam longitude; convert it to
        # the matching column index of the regular mesh.
        split_lon_idx = round(x.shape[1] / (360 / (lon_0 if lon_0 > 0 else lon_0 + 360)))

        common = dict(vmax=vmax, vmin=vmin, transform=cart.crs.PlateCarree(), **plt_kwargs)
        ax.pcolormesh(x[:, :split_lon_idx], y[:, :split_lon_idx], field[:, :split_lon_idx],
                      zorder=1, **common)
        p = ax.pcolormesh(x[:, split_lon_idx:], y[:, split_lon_idx:], field[:, split_lon_idx:],
                          zorder=2, **common)

        ax.add_feature(cart.feature.LAND, facecolor='0.5', zorder=3)
        label = da.name if da.name is not None else ''
        if 'units' in da.attrs:
            label += ' [%s]' % da.attrs['units']
        plt.colorbar(p, shrink=0.4, label=label)
        return ax
