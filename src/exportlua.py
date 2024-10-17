import os
import sys
import requests
import UnityPy
import logging
from git_merge_scripts import git_merge_scripts

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取脚本所在目录的父目录（项目根目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到 Python 路径
sys.path.append(project_root)

from src.decrypt import decrypt

def extract_specific_luascripts():
    # Step 1: 下载文件
    url = "https://cdn.megagamelog.com/cross/release/ios/curr/Custom/luascripts"
    response = requests.get(url)
    output_path = os.path.join(project_root, "luascripts_ios")
    with open(output_path, 'wb') as file:
        file.write(response.content)
    logging.info(f"Downloaded file to {output_path}")

    # Step 2: 解密下载的文件
    decrypted_path = os.path.join(project_root, "luascripts_decrypted_ios")
    decrypt(output_path, decrypted_path)
    logging.info(f"Decrypted file to {decrypted_path}")

    # 获取replace文件夹中的lua文件列表
    replace_dir = os.path.join(project_root, "replace")
    replace_files = [f.rstrip('.lua') for f in os.listdir(replace_dir) if f.endswith('.lua')]
    logging.info(f"Files in replace directory: {replace_files}")

    # Step 3: 读取并提取指定的Unity资源文件
    env = UnityPy.load(decrypted_path)

    extract_dir = os.path.join(project_root, "extracted_scripts")
    os.makedirs(extract_dir, exist_ok=True)

    extracted_count = 0
    try:
        for obj in env.objects:
            if obj.class_id == 49 and obj.type_id == 0:  # TextAsset
                data = obj.read()
                asset_name = data.name.rstrip('.lua')  # 移除可能存在的 .lua 后缀
                if asset_name in replace_files:
                    script_name = asset_name + '.lua'
                    script_path = os.path.join(extract_dir, script_name)
                    with open(script_path, "wb") as f:
                        f.write(data.script)
                    logging.info(f"Extracted {script_name} to {script_path}")
                    extracted_count += 1
    except Exception as e:
        logging.error(f"An error occurred during extraction: {str(e)}", exc_info=True)

    logging.info(f"Total scripts extracted: {extracted_count}")
    logging.info(f"Extraction completed. Scripts have been extracted to {extract_dir}")

    # Step 4: 调用 Git 合并脚本
    merge_dir = os.path.join(project_root, "merge")
    git_merge_scripts(extract_dir, replace_dir, merge_dir)

if __name__ == "__main__":
    try:
        extract_specific_luascripts()
        logging.info("Script extraction and merging completed successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)