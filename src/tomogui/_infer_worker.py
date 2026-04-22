"""Standalone inference worker for Batch AI Reco.

Spawned as a subprocess by the GUI, pinned to one GPU via CUDA_VISIBLE_DEVICES.
Processes a list of projection HDF5 files: for each, reads the try_center
TIFFs produced by tomocupy's try reconstruction, runs DINOv2 inference, and
writes center_of_rotation.txt inside the same try_dir. The GUI then reads
those txt files and updates the table.

Usage:
    python -m tomogui._infer_worker <data_folder> <model_path> <file1> [file2 ...]
"""
from __future__ import annotations

import glob
import os
import re
import sys
import traceback

import numpy as np
from PIL import Image


_CENTER_RE = re.compile(r'center(\d+\.\d+)')


def _process_one(proj_file, data_folder, model_cache):
    proj_name = os.path.splitext(os.path.basename(proj_file))[0]
    try_dir = os.path.join(f"{data_folder}_rec", "try_center", proj_name)
    tiffs = sorted(glob.glob(os.path.join(try_dir, "*.tiff")))
    if not tiffs:
        print(f"[infer-worker] SKIP {proj_name}: no try TIFFs in {try_dir}", flush=True)
        return False
    imgs, cors = [], []
    for t in tiffs:
        m = _CENTER_RE.search(os.path.basename(t))
        if not m:
            continue
        cors.append(float(m.group(1)))
        imgs.append(np.array(Image.open(t)).astype(np.float32))
    if not imgs:
        print(f"[infer-worker] SKIP {proj_name}: no parsable center values", flush=True)
        return False
    # Use the existing inference_pipeline. It loads the model internally;
    # `model_cache` is a placeholder so we can swap in a pre-loaded model later.
    from argparse import Namespace
    from tomogui._tomocor_infer.inference import inference_pipeline
    args = Namespace(
        infer_use_8bits=True,
        infer_downsample_factor=2,
        infer_num_windows=3,
        infer_seed_number=10,
        infer_model_path=model_cache["path"],
        infer_window_size=518,
    )
    try:
        inference_pipeline(args, np.array(imgs), np.array(cors), try_dir)
    except Exception:
        print(f"[infer-worker] FAIL {proj_name}:", flush=True)
        traceback.print_exc()
        return False
    # inference_pipeline writes center_of_rotation.txt in try_dir
    cor_txt = os.path.join(try_dir, 'center_of_rotation.txt')
    if not os.path.exists(cor_txt):
        return False
    # Print result so parent process can optionally stream it
    try:
        with open(cor_txt) as f:
            lines = [line.strip() for line in f if line.strip()]
        if lines:
            print(f"[infer-worker] OK {proj_file} => {lines[-1]}", flush=True)
            return True
    except Exception:
        pass
    return False


def main(argv):
    if len(argv) < 3:
        print("Usage: python -m tomogui._infer_worker "
              "<data_folder> <model_path> <file1> [file2 ...]", file=sys.stderr)
        return 2
    data_folder = argv[0]
    model_path = argv[1]
    files = argv[2:]
    gpu = os.environ.get("CUDA_VISIBLE_DEVICES", "?")
    print(f"[infer-worker] GPU={gpu}  files={len(files)}", flush=True)
    model_cache = {"path": model_path}
    n_ok = 0
    for f in files:
        if _process_one(f, data_folder, model_cache):
            n_ok += 1
    print(f"[infer-worker] done GPU={gpu}  OK={n_ok}/{len(files)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
