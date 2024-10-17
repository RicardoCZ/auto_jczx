import os
import sys
import requests
import UnityPy

# 获取脚本所在目录的父目录（项目根目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到 Python 路径
sys.path.append(project_root)

from src.decrypt import decrypt
from src.encrypt import encrypt


def process_lua_scripts(sysInfo):
    # Step 1: 下载文件
    url = f"https://cdn.megagamelog.com/cross/release/{sysInfo}/curr/Custom/luascripts"
    response = requests.get(url)
    output_path = os.path.join(project_root, f"luascripts_{sysInfo}")
    with open(output_path, 'wb') as file:
        file.write(response.content)

    # Step 2: 解密下载的文件
    decrypted_path = os.path.join(project_root, f"luascripts_decrypted_{sysInfo}")
    decrypt(output_path, decrypted_path)

    # Step 3: 读取并修改Unity的资源文件
    env = UnityPy.load(decrypted_path)

    try:
        for obj in env.objects:
            if hasattr(obj, 'type') and hasattr(obj.type, 'name') and obj.type.name == "TextAsset":
                data = obj.read()
                if hasattr(data, 'name') and data.name in replace_list:
                    fp = os.path.join(project_root, "replace", data.name)
                    if os.path.exists(fp):
                        with open(fp, "rb") as f:
                            data.script = f.read()
                        data.save()
                    else:
                        print(f"文件不存在：{fp}")
    except Exception as e:
        print(f"发生错误：{str(e)}")

    replaced_path = os.path.join(project_root, f"luascripts_replaced_{sysInfo}")
    with open(replaced_path, "wb") as f:
        f.write(env.file.save(packer="lz4"))

    # Step 4: 对压缩后的文件进行加密
    final_output = os.path.join(project_root, f"luascripts_{sysInfo}")
    encrypt(replaced_path, final_output, sysInfo)

    print(f"Generated file for {sysInfo}: {final_output}")


if __name__ == "__main__":
    replace_dir = os.path.join(project_root, "replace")
    replace_list = [f.name for f in os.scandir(replace_dir) if f.is_file()]
    process_lua_scripts("ios")
    process_lua_scripts("android")

print("Script execution completed.")
print("Current directory:", os.getcwd())
print("Files in current directory:", os.listdir("."))
print("Files in project root:", os.listdir(project_root))
