#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======= 在这里改输入 / 输出文件路径 =======
PLY_PATH = "R39_v5.ply"      # 你的 3DGS 生成的 .ply
POINTS3D_TXT = "points3D.txt"     # 输出成 COLMAP 风格的 txt
# ======================================

from plyfile import PlyData


def ply_to_colmap_points3D(ply_path: str, out_path: str) -> None:
    plydata = PlyData.read(ply_path)
    elem = plydata["vertex"]
    data = elem.data
    names = data.dtype.names
    print("Properties in vertex:", names)

    # 检查是否有 xyz
    for k in ("x", "y", "z"):
        if k not in names:
            raise ValueError(f"PLY 中缺少 {k}，实际属性为: {names}")

    # 颜色字段：red/green/blue 或 r/g/b
    if {"red", "green", "blue"}.issubset(names):
        color_mode = "rgb_full"
        print("Using color fields: red, green, blue")
    elif {"r", "g", "b"}.issubset(names):
        color_mode = "rgb_short"
        print("Using color fields: r, g, b")
    else:
        color_mode = "none"
        print("No color fields found, use white (255,255,255)")

    with open(out_path, "w", encoding="utf-8") as f:
        # 写注释头（可选）
        f.write("# 3D point list with one line of data per point:\n")
        f.write("# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[]\n")

        point_id = 1
        for row in data:
            x = row["x"]
            y = row["y"]
            z = row["z"]

            if color_mode == "rgb_full":
                r = int(row["red"])
                g = int(row["green"])
                b = int(row["blue"])
            elif color_mode == "rgb_short":
                r = int(row["r"])
                g = int(row["g"])
                b = int(row["b"])
            else:
                r = g = b = 255

            error = 1.0  # 随便填一个误差

            # 不写 TRACK[]，直接换行
            f.write(f"{point_id} {x} {y} {z} {r} {g} {b} {error}\n")
            point_id += 1

    print(f"Done. Wrote {point_id-1} points to {out_path}")


if __name__ == "__main__":
    ply_to_colmap_points3D(PLY_PATH, POINTS3D_TXT)
