import os
import struct
import numpy as np
from plyfile import PlyData

def write_points3D_colmap_binary(ply_path, output_path):
    # 1. 读取 PLY 数据
    print(f"正在读取: {ply_path}")
    plydata = PlyData.read(ply_path)
    vertex = plydata['vertex']
    
    # 获取点数
    num_points = len(vertex)
    print(f"点云数量: {num_points}")

    # 提取坐标 (x, y, z)
    x = vertex['x']
    y = vertex['y']
    z = vertex['z']

    # 提取颜色 (red, green, blue)，如果没有颜色则默认为白色
    if 'red' in vertex.data.dtype.names:
        r = vertex['red']
        g = vertex['green']
        b = vertex['blue']
    else:
        print("未检测到颜色，默认填充白色")
        r = np.ones(num_points, dtype=np.uint8) * 255
        g = np.ones(num_points, dtype=np.uint8) * 255
        b = np.ones(num_points, dtype=np.uint8) * 255

    # 2. 写入 COLMAP points3D.bin 格式
    # 格式定义参考: https://colmap.github.io/format.html#points3d-txt
    print(f"正在写入 COLMAP 格式: {output_path}")
    
    with open(output_path, "wb") as fid:
        # 写入文件头：点的数量 (uint64)
        fid.write(struct.pack("Q", num_points))

        # 为了加速，我们尽量批量处理，但在 Python 中混合 struct 打包比较慢
        # 这里使用循环写入，虽然慢一点但逻辑最清晰且稳健
        
        # 预设一些常量
        error = 0.0
        track_length = 0  # 关键：设为0，跳过 track 读取
        
        for i in range(num_points):
            # POINT3D_ID (uint64): 这里的 ID 从 1 开始或者 0 开始都可以，COLMAP 通常是不连续的 ID
            point_id = i + 1 
            
            # 写入 ID (uint64)
            fid.write(struct.pack("Q", point_id))
            
            # 写入 XYZ (3 * double) -> 注意 COLMAP 使用 double (float64)
            fid.write(struct.pack("ddd", float(x[i]), float(y[i]), float(z[i])))
            
            # 写入 RGB (3 * uint8)
            fid.write(struct.pack("BBB", int(r[i]), int(g[i]), int(b[i])))
            
            # 写入 Error (double)
            fid.write(struct.pack("d", error))
            
            # 写入 Track Length (uint64) -> 设为 0
            fid.write(struct.pack("Q", track_length))
            
            # Track 内容为空，不需要写入
            
            if (i + 1) % 100000 == 0:
                print(f"已处理 {i + 1} / {num_points} 个点...")

    print("转换完成！")

def batch_convert(input_folder):
    ply_files = [f for f in os.listdir(input_folder) if f.endswith('.ply')]
    
    if not ply_files:
        print("未找到 ply 文件")
        return

    # 确保输出目录存在 (通常 3DGS 需要放在 sparse/0/ 下)
    # 你可以修改这里的输出逻辑
    for ply in ply_files:
        in_path = os.path.join(input_folder, ply)
        # 输出文件名通常固定为 points3D.bin 才能被 3DGS 识别
        # 这里为了避免覆盖，我加了前缀，你需要手动改名或者调整代码
        out_name = ply.replace('.ply', '.bin') 
        out_path = os.path.join(input_folder, out_name)
        
        write_points3D_colmap_binary(in_path, out_path)

if __name__ == "__main__":
    # 使用当前目录，或者你可以手动指定路径
    current_dir = os.getcwd()
    # 也可以直接指定到 sparse/0 文件夹
    # current_dir = "./data/0214/sparse/0" 
    batch_convert(current_dir)