import sys
import numpy as np

# 兼容 NumPy 2.x 生成的包含 numpy._core 的 pickle
if not hasattr(np, "_core"):
    sys.modules["numpy._core"] = np.core
import os
import numpy as np

def convert_npy_to_txt():
    current_dir = os.getcwd()

    for file in os.listdir(current_dir):
        if not file.endswith(".npy"):
            continue

        npy_path = os.path.join(current_dir, file)
        txt_path = os.path.join(current_dir, file.replace(".npy", ".txt"))

        try:
            data = np.load(npy_path, allow_pickle=True)

            if isinstance(data, np.ndarray) and np.issubdtype(data.dtype, np.number):
                np.savetxt(txt_path, data, fmt="%.8f")
            else:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(repr(data))

            print(f"[OK] {file}  →  {txt_path}")

        except Exception as e:
            print(f"[ERROR] 无法处理 {file}: {e}")


if __name__ == "__main__":
    convert_npy_to_txt()
