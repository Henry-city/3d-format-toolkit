#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys

try:
    from read_write_model import (
        read_cameras_text, write_cameras_binary,
        read_images_text,  write_images_binary,
        read_points3D_text, write_points3D_binary
    )
except Exception as e:
    print("❌ 无法导入 read_write_model.py，请将该文件放到脚本同目录或加入 PYTHONPATH。")
    raise

def find_case_insensitive(d, name):
    want = name.lower()
    try:
        for f in os.listdir(d):
            if f.lower() == want:
                p = os.path.join(d, f)
                if os.path.isfile(p):
                    return p
    except FileNotFoundError:
        pass
    return None

def convert_dir(d):
    converted = []
    cam_p = find_case_insensitive(d, "cameras.txt")
    img_p = find_case_insensitive(d, "images.txt")
    pts_p = find_case_insensitive(d, "points3D.txt")

    try:
        if cam_p:
            cams = read_cameras_text(cam_p)
            write_cameras_binary(cams, os.path.join(d, "cameras.bin"))
            converted.append("cameras")
        if img_p:
            imgs = read_images_text(img_p)
            write_images_binary(imgs, os.path.join(d, "images.bin"))
            converted.append("images")
        if pts_p:
            pts  = read_points3D_text(pts_p)
            write_points3D_binary(pts, os.path.join(d, "points3D.bin"))
            converted.append("points3D")
    except Exception as e:
        print(f"❌ 转换失败：{d} -> {e}")
        return False

    if converted:
        print(f"✅ {d}: {'/'.join(converted)}.txt → .bin")
        return True
    return False

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    total = 0
    # 先尝试根目录
    if convert_dir(root):
        total += 1
    # 再递归子目录
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath == root:
            continue
        if convert_dir(dirpath):
            total += 1
    print(f"🏁 共转换 {total} 个目录。")

if __name__ == "__main__":
    main()
