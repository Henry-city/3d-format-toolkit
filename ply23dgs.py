#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pcd_to_3dgs_ply.py

把带颜色的点云 PLY 转成 3DGS (gaussian-splatting) 可直接加载的 PLY。

输出字段兼容：
x y z
f_dc_0 f_dc_1 f_dc_2
f_rest_0 ... f_rest_K
opacity
scale_0 scale_1 scale_2   (log-space)
rot_0 rot_1 rot_2 rot_3   (quaternion, wxyz)

默认 SH_DEGREE=0（只有 DC 颜色），更省内存；要更高阶也支持。
"""

import os
import numpy as np
from plyfile import PlyData, PlyElement

# ========================== 你只需要改这里 ==========================

INPUT_PLY_PATH  = "/home/tangyuan/project/map/newScene/ground/ground_points.ply"
OUTPUT_PLY_PATH = "/home/tangyuan/project/map/newScene/ground/3dda.ply"

# 初始高斯椭球大小（单位：和你的点云一致，通常是米）
# 可以是一个标量（所有轴相同），也可以是长度为3的 list/tuple
INIT_GAUSS_SCALE = 0.01   # 例如 3cm

# 初始可见度（0~1），会转成 logit 存到 opacity 字段
INIT_OPACITY = 0.8

# SH 最大阶数（gaussian-splatting 默认 max_sh_degree=3；你也可以用 0）
SH_DEGREE = 0

# 如果输入点云没有颜色，用这个默认颜色 (RGB 0~255)
DEFAULT_COLOR = (255, 255, 255)

# ================================================================


# SH 常数：gaussian-splatting 的 RGB<->SH 变换
C0 = 0.28209479177387814


def rgb_to_sh_dc(rgb01: np.ndarray) -> np.ndarray:
    """
    把 RGB(0~1) 转成 SH 的 DC 项系数（shape: N×3）
    对应 repo 的 RGB2SH: (rgb - 0.5)/C0
    """
    return (rgb01 - 0.5) / C0


def logit(p: float) -> float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(np.log(p / (1 - p)))


def read_ply_xyzrgb(path: str):
    ply = PlyData.read(path)
    v = ply["vertex"].data

    x = np.asarray(v["x"], dtype=np.float32)
    y = np.asarray(v["y"], dtype=np.float32)
    z = np.asarray(v["z"], dtype=np.float32)
    xyz = np.stack([x, y, z], axis=1)

    # 兼容不同颜色字段命名
    color_fields = None
    for cand in [("red", "green", "blue"),
                 ("r", "g", "b"),
                 ("diffuse_red", "diffuse_green", "diffuse_blue")]:
        if all(c in v.dtype.names for c in cand):
            color_fields = cand
            break

    if color_fields is None:
        rgb = np.tile(np.array(DEFAULT_COLOR, dtype=np.float32), (xyz.shape[0], 1))
    else:
        rgb = np.stack([v[color_fields[0]],
                        v[color_fields[1]],
                        v[color_fields[2]]], axis=1).astype(np.float32)

    return xyz, rgb


def build_3dgs_ply(xyz: np.ndarray, rgb255: np.ndarray):
    N = xyz.shape[0]

    # colors -> [0,1]
    rgb01 = np.clip(rgb255 / 255.0, 0.0, 1.0).astype(np.float32)

    # DC SH
    f_dc = rgb_to_sh_dc(rgb01)  # N×3

    # extra SH（高阶全 0）
    rest_per_channel = (SH_DEGREE + 1) ** 2 - 1
    rest_count = 3 * rest_per_channel
    f_rest = np.zeros((N, rest_count), dtype=np.float32)

    # opacity -> logit
    opacity_val = logit(INIT_OPACITY)
    opacity = np.full((N, 1), opacity_val, dtype=np.float32)

    # scales（log-space）
    if np.isscalar(INIT_GAUSS_SCALE):
        scale_xyz = np.array([INIT_GAUSS_SCALE]*3, dtype=np.float32)
    else:
        scale_xyz = np.array(INIT_GAUSS_SCALE, dtype=np.float32).reshape(3)

    scale_xyz = np.maximum(scale_xyz, 1e-8)
    scales = np.log(scale_xyz)[None, :].repeat(N, axis=0).astype(np.float32)

    # rotations：单位四元数 (w,x,y,z)
    rots = np.zeros((N, 4), dtype=np.float32)
    rots[:, 0] = 1.0

    # 可选 normals（填 0）
    normals = np.zeros((N, 3), dtype=np.float32)

    # 组装结构化数组 dtype
    dtype_list = [
        ("x", "f4"), ("y", "f4"), ("z", "f4"),
        ("nx", "f4"), ("ny", "f4"), ("nz", "f4"),
        ("f_dc_0", "f4"), ("f_dc_1", "f4"), ("f_dc_2", "f4"),
    ]

    for i in range(rest_count):
        dtype_list.append((f"f_rest_{i}", "f4"))

    dtype_list += [
        ("opacity", "f4"),
        ("scale_0", "f4"), ("scale_1", "f4"), ("scale_2", "f4"),
        ("rot_0", "f4"), ("rot_1", "f4"), ("rot_2", "f4"), ("rot_3", "f4"),
    ]

    out = np.empty(N, dtype=np.dtype(dtype_list))

    out["x"], out["y"], out["z"] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    out["nx"], out["ny"], out["nz"] = normals[:, 0], normals[:, 1], normals[:, 2]

    out["f_dc_0"], out["f_dc_1"], out["f_dc_2"] = f_dc[:, 0], f_dc[:, 1], f_dc[:, 2]

    for i in range(rest_count):
        out[f"f_rest_{i}"] = f_rest[:, i]

    out["opacity"] = opacity[:, 0]
    out["scale_0"], out["scale_1"], out["scale_2"] = scales[:, 0], scales[:, 1], scales[:, 2]
    out["rot_0"], out["rot_1"], out["rot_2"], out["rot_3"] = rots[:, 0], rots[:, 1], rots[:, 2], rots[:, 3]

    return out


def save_ply(vertices_struct: np.ndarray, path: str):
    el = PlyElement.describe(vertices_struct, "vertex")
    PlyData([el], text=False).write(path)


def main():
    assert os.path.isfile(INPUT_PLY_PATH), f"找不到输入文件: {INPUT_PLY_PATH}"
    os.makedirs(os.path.dirname(OUTPUT_PLY_PATH), exist_ok=True)

    xyz, rgb = read_ply_xyzrgb(INPUT_PLY_PATH)
    print(f"[OK] load input: {xyz.shape[0]} points")

    vtx = build_3dgs_ply(xyz, rgb)
    save_ply(vtx, OUTPUT_PLY_PATH)

    rest_count = 3 * ((SH_DEGREE + 1) ** 2 - 1)
    print(f"[OK] save 3DGS ply -> {OUTPUT_PLY_PATH}")
    print(f"     SH_DEGREE={SH_DEGREE}, f_rest_count={rest_count}")
    print(f"     INIT_SCALE={INIT_GAUSS_SCALE}, INIT_OPACITY={INIT_OPACITY}")


if __name__ == "__main__":
    main()
