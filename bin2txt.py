import os

def bin_to_txt(bin_file):
    # 假设 bin 文件是以二进制形式存储的数据，转换为文本
    try:
        # 打开 bin 文件并读取
        with open(bin_file, 'rb') as f:
            data = f.read()
        
        # 创建 txt 文件的路径
        txt_file = bin_file.replace('.bin', '.txt')
        
        # 将二进制数据转换为字符串，并保存为 txt 文件
        with open(txt_file, 'w') as f:
            f.write(data.decode('utf-8', errors='ignore'))  # 使用 ignore 忽略无效字符

        print(f"已将 {bin_file} 转换为 {txt_file}")
    except Exception as e:
        print(f"转换文件 {bin_file} 时出错: {e}")

def convert_bin_files_in_directory():
    # 获取当前目录路径
    current_dir = os.getcwd()
    
    # 遍历当前目录下所有文件
    for filename in os.listdir(current_dir):
        # 仅处理扩展名为 .bin 的文件
        if filename.endswith('.bin'):
            bin_file = os.path.join(current_dir, filename)
            bin_to_txt(bin_file)

if __name__ == "__main__":
    convert_bin_files_in_directory()
