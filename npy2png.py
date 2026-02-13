#!/usr/bin/env python3
"""
depth_npy_to_png.py (robust)
Convert ALL depth .npy files in the CURRENT directory into visual PNGs.

Usage:
    python depth_npy_to_png.py
    python depth_npy_to_png.py --pattern "*_depth.npy" --pmin 1 --pmax 99 --cmap jet
"""

import argparse
import glob
import os
import sys
import numpy as np
import cv2

COLORMAPS = {
    "jet": cv2.COLORMAP_JET,
    "turbo": cv2.COLORMAP_TURBO,
    "magma": cv2.COLORMAP_MAGMA,
    "inferno": cv2.COLORMAP_INFERNO,
    "plasma": cv2.COLORMAP_PLASMA,
    "viridis": cv2.COLORMAP_VIRIDIS,
    "cividis": cv2.COLORMAP_CIVIDIS,
    "twilight": cv2.COLORMAP_TWILIGHT,
    "gray": None,  # handled separately
}

def squeeze_to_hw(arr: np.ndarray) -> np.ndarray:
    """
    Squeeze singleton dims so depth becomes 2D (H, W).
    Accepts (H,W), (H,W,1), (1,H,W), (1,H,W,1), etc.
    If 3D with more than one channel, take the first channel as depth.
    """
    arr = np.asarray(arr)
    # Remove all singleton dimensions
    arr = np.squeeze(arr)
    if arr.ndim == 2:
        return arr
    elif arr.ndim == 3:
        # handle channel-last or channel-first single channel
        if arr.shape[-1] == 1:
            return arr[..., 0]
        if arr.shape[0] == 1:
            return arr[0]
        # If still 3D with >1 channels, fallback to the first channel
        return arr[..., 0]
    else:
        # If 1D or higher than 3D (unexpected), try best-effort flatten to 2D
        # Best-effort: if total size matches H*W, reshape; else raise
        flat = arr.reshape(-1)
        L = flat.size
        s = int(np.sqrt(L))
        if s * s == L:
            return flat.reshape(s, s)
        raise ValueError(f"Unexpected depth shape after squeeze: {arr.shape}")

def make_vis(depth_hw: np.ndarray, pmin: float, pmax: float, cmap_name: str) -> np.ndarray:
    """Normalize depth by percentile clip and apply colormap. Returns uint8 HxWx3."""
    depth = np.nan_to_num(depth_hw, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    finite = np.isfinite(depth)
    if not finite.any():
        return np.zeros((depth.shape[0], depth.shape[1], 3), dtype=np.uint8)

    # Robust range
    dvals = depth[finite]
    vmin = np.percentile(dvals, pmin)
    vmax = np.percentile(dvals, pmax)
    if not np.isfinite(vmin): vmin = float(np.min(dvals))
    if not np.isfinite(vmax): vmax = float(np.max(dvals))
    if vmax <= vmin:
        vmax = vmin + 1e-6

    # Normalize to [0,255]
    depth_norm = np.clip((depth - vmin) / (vmax - vmin), 0.0, 1.0)
    depth_u8 = (depth_norm * 255.0).astype(np.uint8)

    if cmap_name == "gray":
        return cv2.cvtColor(depth_u8, cv2.COLOR_GRAY2BGR)

    cmap = COLORMAPS.get(cmap_name, cv2.COLORMAP_JET)
    return cv2.applyColorMap(depth_u8, cmap)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="*_depth.npy",
                    help="Glob for input .npy files in current dir (default: '*_depth.npy').")
    ap.add_argument("--pmin", type=float, default=1.0, help="Lower percentile for clipping.")
    ap.add_argument("--pmax", type=float, default=99.0, help="Upper percentile for clipping.")
    ap.add_argument("--cmap", type=str, default="jet", choices=list(COLORMAPS.keys()),
                    help="Colormap for visualization (default: jet).")
    ap.add_argument("--suffix", type=str, default="_depth_vis.png",
                    help="Output suffix to replace .npy (default: _depth_vis.png).")
    args = ap.parse_args()

    files = sorted(glob.glob(args.pattern))
    if not files:
        print(f"[!] No files match pattern: {args.pattern}")
        sys.exit(1)

    print(f"[Info] Found {len(files)} files. Converting with cmap={args.cmap}, "
          f"percentiles=({args.pmin}, {args.pmax}) ...")

    ok, fail = 0, 0
    for f in files:
        try:
            arr = np.load(f)
            depth_hw = squeeze_to_hw(arr)     # <<< 关键：挤掉多余维度
            vis = make_vis(depth_hw, args.pmin, args.pmax, args.cmap)
            out_path = f[:-4] + args.suffix   # replace .npy
            cv2.imwrite(out_path, vis)
            ok += 1
            print(f"[OK] {f} (shape {arr.shape} -> {depth_hw.shape}) -> {out_path}")
        except Exception as e:
            fail += 1
            print(f"[FAIL] {f}: {e}")

    print(f"\n[Done] Wrote {ok} PNGs. Failed: {fail}")

if __name__ == "__main__":
    main()
