"""Plotting helpers for the bipolar north-fold example (``05_tripolar_fold.ipynb``).

Drawing only. Every xgcm call lives in the notebook, where it is meant to be read;
each function here just renders arrays that the notebook has already computed and
stored on the per-model dicts.

The seam figures all share one layout: a zoomed strip of the topmost grid rows,
with the fold seam drawn as a solid line. Rows above the line are halo (what the
boundary condition invented); rows below are untouched interior.
"""

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

LAND = "0.7"  # grey for masked (land) cells, distinct from every colormap used here


def global_vorticity(lon, lat, zeta, title):
    """03_MOM6's global vorticity map, redrawn.

    Deliberately the same figure as ``03_MOM6.ipynb``: same Robinson projection,
    same ``RdBu_r``, same 99th-percentile scale. Only the boundary condition
    behind ``zeta`` differs.
    """
    lim = float(np.nanpercentile(np.abs(zeta), 99))
    fig = plt.figure(figsize=(11, 6))
    ax = plt.axes(projection=ccrs.Robinson(central_longitude=-150))
    pm = ax.pcolormesh(lon, lat, zeta[:lat.shape[0], :lat.shape[1]],
                       transform=ccrs.PlateCarree(), cmap="RdBu_r", vmin=-lim, vmax=lim)
    ax.coastlines(linewidth=0.4)
    fig.colorbar(pm, ax=ax, shrink=0.6, label="relative vorticity [s$^{-1}$]")
    ax.set_title(title)
    plt.show()


def ocean_window(rows, nx, W):
    """Start column of the length-W window (wrapping in x) with the most ocean.

    The poles sit over land, so the figures centre on open water rather than on a
    pole. Purely a display choice: it selects which columns to draw, nothing else.
    Returns ``(start, column_indices)``.
    """
    finite = np.isfinite(rows).sum(axis=0).astype(int)
    best, score = 0, -1
    for s in range(nx):
        sc = int(finite[(np.arange(s, s + W)) % nx].sum())
        if sc > score:
            score, best = sc, s
    return best, (np.arange(best, best + W)) % nx


def attach_windows(models, K=6, W=28):
    """Pick one open-water column window per model and store it as ``m["win"]``.

    Reads the fold-padded surface speed the notebook computed (``m["speed_fold"]``)
    so that every seam figure shows the SAME region for a given model and the
    panels stay directly comparable.
    """
    for m in models:
        ny, nx = m["ny"], m["nx"]
        rows = m["speed_fold"][ny - K:ny + K]
        start, cols = ocean_window(rows, nx, W)
        m["win"] = (start, cols, W)


def _imshow(ax, arr_win, ylo, **kw):
    """Draw an already-windowed strip with nearest-neighbour shading.

    Every grid cell becomes a crisp, individually visible block (no interpolation
    blur). Masked (land) cells show as grey.
    """
    nrow, ncol = arr_win.shape
    ax.set_facecolor(LAND)
    im = ax.imshow(arr_win, origin="lower", aspect="auto", interpolation="nearest",
                   extent=[-0.5, ncol - 0.5, ylo - 0.5, ylo + nrow - 0.5], **kw)
    ax.set_xticks([0, ncol // 2, ncol - 1])
    return im


def _scale(a, pct=95):
    """A robust symmetric scale for a field (ignoring land)."""
    v = np.abs(a[np.isfinite(a)])
    return (float(np.nanpercentile(v, pct)) if v.size else 1.0) or 1.0


def halo_strip(models, naive_key, fold_key, cbar_label, suptitle, K=6, signed=False):
    """Three-row strip per model: naive halo / fold halo / their difference.

    ``naive_key`` and ``fold_key`` name arrays already stored on each model dict.
    ``signed=True`` uses a diverging colormap centred on zero (for fields that take
    both signs, e.g. divergence); otherwise a sequential 0..1 map (e.g. speed).
    """
    rlab = ["naive halo\n(extend)", "fold halo\n(mirror)", "naive − fold"]
    fig, axes = plt.subplots(3, len(models), figsize=(4.6 * len(models), 9.4))
    axes = np.atleast_2d(axes)
    for c, m in enumerate(models):
        ny = m["ny"]
        fold = m[fold_key][ny - K:ny + K]
        naive = m[naive_key][ny - K:ny + K]
        start, cols, W = m["win"]
        vmax = _scale(m[fold_key][ny - K:ny], pct=98 if signed else 95)
        diff = (naive - fold) / vmax

        seq = plt.get_cmap("RdBu_r" if signed else "viridis").copy()
        seq.set_bad(LAND)
        div = plt.get_cmap("RdBu_r").copy()
        div.set_bad(LAND)
        lo = -1 if signed else 0
        rows = [(0, naive / vmax, seq, dict(vmin=lo, vmax=1)),
                (1, fold / vmax, seq, dict(vmin=lo, vmax=1)),
                (2, diff, div, dict(vmin=-1, vmax=1))]
        for r, arr, cmap, kw in rows:
            ax = axes[r, c]
            _imshow(ax, arr[:, cols], ny - K, cmap=cmap, **kw)
            ax.axhline(ny - 0.5, color="k", lw=1.6)  # the fold seam
            if r == 0:
                ax.set_title(f"{m['label']}\n(cols {start}–{start + W - 1})", fontsize=9)
            if c == 0:
                ax.set_ylabel(rlab[r], fontsize=9)
            if r == 2:
                ax.set_xlabel("X index (windowed)")
    for r, lab in [(0, cbar_label), (1, cbar_label), (2, f"(naive−fold) / max")]:
        fig.colorbar(axes[r, -1].images[0], ax=list(axes[r, :]),
                     shrink=0.7, pad=0.02, label=lab)
    fig.suptitle(suptitle, fontsize=11, y=0.99)
    plt.show()


def component_strip(models, K=6):
    """Both velocity components near the seam: scalar fold vs vector fold.

    Reads ``m["v_scalarfold"]``, ``m["v_vectorfold"]``, ``m["u_scalarfold"]``,
    ``m["u_vectorfold"]``. In the halo the vector fold is the scalar fold with its
    sign flipped — the colours invert — for both components.
    """
    panels = [("v_scalarfold", "v", "v folded as\nscalar"),
              ("v_vectorfold", "v", "v folded as\nvector"),
              ("u_scalarfold", "u", "u folded as\nscalar"),
              ("u_vectorfold", "u", "u folded as\nvector")]
    fig, axes = plt.subplots(len(panels), len(models),
                             figsize=(4.6 * len(models), 2.7 * len(panels)))
    axes = np.atleast_2d(axes)
    for c, m in enumerate(models):
        ny = m["ny"]
        start, cols, W = m["win"]
        div = plt.get_cmap("RdBu_r").copy()
        div.set_bad(LAND)
        # one symmetric scale per component, taken from its vector fold
        scale = {comp: _scale(m[f"{comp}_vectorfold"][ny - K:ny + K]) for comp in ("v", "u")}
        for r, (key, comp, lab) in enumerate(panels):
            arr = m[key][ny - K:ny + K]
            ax = axes[r, c]
            _imshow(ax, arr[:, cols] / scale[comp], ny - K, cmap=div, vmin=-1, vmax=1)
            ax.axhline(ny - 0.5, color="k", lw=1.6)  # the fold seam
            if r == 0:
                ax.set_title(f"{m['label']}\n(cols {start}–{start + W - 1})", fontsize=9)
            if c == 0:
                ax.set_ylabel(lab, fontsize=9)
            if r == len(panels) - 1:
                ax.set_xlabel("X index (windowed)")
    fig.colorbar(axes[-1, -1].images[0], ax=list(axes.ravel()), shrink=0.5, pad=0.02,
                 label="velocity / max")
    fig.suptitle("Both velocity components near the seam: in the halo the vector fold is the "
                 "sign-flipped\nscalar fold — the colours invert — for u and v alike. The 180° "
                 "pivot flips velocities; a scalar stays.", fontsize=12, y=1.0)
    plt.show()


def seam_transect(models, K=6, ncols=4):
    """Surface speed continued across the seam into the halo, as line plots.

    Reads ``m["speed_fold"]`` / ``m["speed_naive"]``. The fold fills the halo with
    the true seam-partner row, continuing the field; the naive boundary repeats the
    edge value (a flat line).
    """
    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 4.2))
    axes = np.atleast_1d(axes)
    for k, (ax, m) in enumerate(zip(axes, models)):
        ny = m["ny"]
        Sf, Se = m["speed_fold"], m["speed_naive"]
        x = np.arange(ny - K, ny + K)
        approach = np.isfinite(Sf[ny - K:ny]).all(axis=0)
        nfin = np.isfinite(Sf[ny - K:ny + K]).sum(axis=0)
        good = np.where(approach & (nfin >= K + 2))[0]
        if good.size == 0:  # coarse, land-locked cap: fall back to most-finite columns
            good = np.argsort(nfin)[::-1][:ncols]
        sel = good[np.linspace(0, len(good) - 1, min(ncols, len(good))).astype(int)]
        for j, i in enumerate(sel):
            first = (j == 0 and k == 0)
            ax.plot(x, Se[ny - K:ny + K, i], "o--", color="C1", ms=3, alpha=.8,
                    label="naive (extend)" if first else None)
            ax.plot(x, Sf[ny - K:ny + K, i], "o-", color="C0", ms=3, alpha=.9,
                    label="fold" if first else None)
        ax.axvline(ny - 0.5, color="k", ls=":", alpha=.6, label="seam" if k == 0 else None)
        ax.set_title(m["label"], fontsize=10)
        ax.set_xlabel("Y index  (interior → halo)")
        if k == 0:
            ax.set_ylabel("surface speed [m s$^{-1}$]")
    axes[0].legend(fontsize=8, loc="best")
    fig.suptitle("Across the seam the fold continues the real field; the naive boundary flatlines",
                 fontsize=12)
    plt.tight_layout()
    plt.show()


def index_space_overview(models, field_key="speed", K=6):
    """A plain look at each model's surface speed in raw grid-index space.

    No projection, no fold machinery — just the array as it sits in memory, with
    the seam row marked. Establishes what "the top edge of the array" means before
    any xgcm operation is applied to it.
    """
    fig, axes = plt.subplots(1, len(models), figsize=(4.6 * len(models), 3.6))
    axes = np.atleast_1d(axes)
    for ax, m in zip(axes, models):
        arr = np.asarray(m[field_key].values)
        cmap = plt.get_cmap("viridis").copy()
        cmap.set_bad(LAND)
        ax.set_facecolor(LAND)
        im = ax.imshow(arr, origin="lower", aspect="auto", cmap=cmap,
                       vmin=0, vmax=_scale(arr))
        ax.axhline(m["ny"] - 0.5, color="r", lw=1.2)  # the folded top edge
        ax.set_title(m["label"], fontsize=9)
        ax.set_xlabel("X index")
    axes[0].set_ylabel("Y index")
    fig.colorbar(axes[-1].images[0], ax=list(axes), shrink=0.8, pad=0.02,
                 label="surface speed [m s$^{-1}$]")
    fig.suptitle("Surface speed in raw grid-index space; red line = the top edge that folds onto "
                 "itself", fontsize=11)
    plt.show()
