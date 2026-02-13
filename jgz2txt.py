import os
import gzip
import json

def batch_convert_jgz_to_txt(target_dir='.'):
    """
    将指定目录下的所有 .jgz 文件转换为格式化后的 .txt 文件
    """
    # 获取目录下所有文件
    files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
    jgz_files = [f for f in files if f.endswith('.jgz')]

    if not jgz_files:
        print(f"在目录 '{target_dir}' 下没有找到 .jgz 文件。")
        return

    print(f"找到 {len(jgz_files)} 个 .jgz 文件，开始转换...\n")

    for filename in jgz_files:
        jgz_path = os.path.join(target_dir, filename)
        # 构造输出文件名：例如 data.jgz -> data.txt
        txt_filename = filename[:-4] + '.txt'
        txt_path = os.path.join(target_dir, txt_filename)

        try:
            # 1. 读取并解压 .jgz
            # mode='rt' 表示以文本模式读取 (read text)
            with gzip.open(jgz_path, 'rt', encoding='utf-8') as f_in:
                data = json.load(f_in)

            # 2. 格式化写入 .txt
            with open(txt_path, 'w', encoding='utf-8') as f_out:
                # indent=4 会把数据展开，ensure_ascii=False 保证中文正常显示
                json.dump(data, f_out, indent=4, ensure_ascii=False)

            print(f"✅ 成功: {filename} -> {txt_filename}")

        except Exception as e:
            print(f"❌ 失败: {filename} 处理出错。原因: {e}")

    print("\n所有任务完成。")

if __name__ == "__main__":
    # 默认处理当前脚本所在的目录
    current_directory = os.getcwd()
    batch_convert_jgz_to_txt(current_directory)
    
    # 如果你想指定其他路径，可以将上面两行注释，解开下面这行的注释并修改路径
    # batch_convert_jgz_to_txt(r"C:\你的\数据\路径")