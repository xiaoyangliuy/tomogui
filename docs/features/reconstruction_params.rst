Reconstruction Parameters
=========================

This page summarises the parameter tabs on the Main tab row. All fields
map directly to TomoCuPy command-line flags; refer to the TomoCuPy docs
for deeper coverage.

Recon tab
---------

**Reconstruction algorithm**
   - ``FBP`` — direct filtered backprojection (fastest, most common)
   - ``gridrec`` — grid-based FBP, often good for 360° scans
   - ``LPREC`` — log-polar; can be faster on very large sinograms

**nsino-per-chunk**
   Number of sinograms processed per chunk. Increase for faster
   reconstructions if GPU memory allows; decrease if you see OOM errors.

**binning**
   Downsampling factor. ``0`` = none, ``1`` = ½, ``2`` = ¼, etc.

**start-row / end-row**
   Slice range for Try (full volume is always used for Full unless
   otherwise specified).

Hardening tab
-------------

Beam hardening correction parameters. Leave at default unless you have a
calibrated hardening model.

Phase tab
---------

Phase retrieval:

- **method** — Paganin / Bronnikov / CTF
- **alpha** — regularisation strength
- **energy** — beam energy (keV)
- **pixel size**, **distance** — sample-to-detector geometry

Rings tab
---------

Ring artifact removal:

- **algorithm** — ``fw`` (Fourier-Wavelet), ``none``, etc.
- **sigma** — smoothing strength
- **level** — wavelet level

Geometry tab
------------

Rotation axis geometry flags (tilt, lateral shift).

Data tab
--------

Projection data preprocessing: flat / dark correction, projection range,
bright / dark frame source, etc.

Performance tab
---------------

Threading, blocked-views, chunking, and other performance knobs.

Per-dataset persistence
-----------------------

When you change a parameter, its value is written to a JSON sidecar next
to the projection file. Re-selecting the file later restores the last
values. The Batch tab's *Apply parameters to selected* action copies a
sidecar from one row to all checked rows.

See :doc:`/user_guide/reconstruction` for the end-to-end workflow.
