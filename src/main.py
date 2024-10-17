import os
import sys
import requests
import UnityPy
import logging
import shutil

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取脚本所在目录的父目录（项目根目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 添加项目根目录到 Python 路径
sys.path.append(project_root)

from src.decrypt import decrypt
from src.encrypt import encrypt

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")

def process_lua_scripts(sysInfo):
    # Step 1: 下载文件
    url = f"https://cdn.megagamelog.com/cross/release/{sysInfo}/curr/Custom/luascripts"
    response = requests.get(url)
    output_path = os.path.join(project_root, f"luascripts_{sysInfo}")
    with open(output_path, 'wb') as file:
        file.write(response.content)
    logging.info(f"Downloaded file to {output_path}")

    # Step 2: 解密下载的文件
    decrypted_path = os.path.join(project_root, f"luascripts_decrypted_{sysInfo}")
    decrypt(output_path, decrypted_path)
    logging.info(f"Decrypted file to {decrypted_path}")

    # Step 3: 读取并修改Unity的资源文件
    env = UnityPy.load(decrypted_path)

    merge_dir = os.path.join(project_root, "merge")
    if not os.path.exists(merge_dir):
        logging.warning(f"Merge directory not found: {merge_dir}")
        logging.info("Using extracted_scripts directory instead")
        merge_dir = os.path.join(project_root, "extracted_scripts")
        
    if not os.path.exists(merge_dir):
        logging.error(f"Neither merge nor extracted_scripts directory exists: {merge_dir}")
        return

    merge_files = [f for f in os.listdir(merge_dir) if f.endswith('.lua')]
    logging.info(f"Found {len(merge_files)} .lua files in {merge_dir}")

    try:
        modified_count = 0
        for obj in env.objects:
            if obj.class_id == 49 and obj.type_id == 0:
                data = obj.read()
                if data.name in merge_files:
                    merge_file_path = os.path.join(merge_dir, data.name)
                    with open(merge_file_path, "rb") as f:
                        data.script = f.read()
                    data.save()
                    logging.info(f"Replaced content for {data.name}")
                    modified_count += 1
                else:
                    logging.debug(f"Skipped {data.name} as it's not in merge folder")
        logging.info(f"Total files modified: {modified_count}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)

    replaced_path = os.path.join(project_root, f"luascripts_replaced_{sysInfo}")
    with open(replaced_path, "wb") as f:
        f.write(env.file.save(packer="lz4"))
    logging.info(f"Saved replaced file to {replaced_path}")

    # Step 4: 对压缩后的文件进行加密
    final_output = os.path.join(project_root, f"luascripts_{sysInfo}")
    encrypt(replaced_path, final_output, sysInfo)
    logging.info(f"Generated encrypted file for {sysInfo}: {final_output}")

if __name__ == "__main__":
    mkdir -p merge extracted_scripts
    merge_dir = os.path.join(project_root, "merge")
    extracted_dir = os.path.join(project_root, "extracted_scripts")
    
    logging.info(f"Project root: {project_root}")
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Contents of project root: {os.listdir(project_root)}")
    
    if os.path.exists(merge_dir):
        logging.info(f"Using merge directory: {merge_dir}")
    elif os.path.exists(extracted_dir):
        logging.info(f"Merge directory not found. Using extracted_scripts directory: {extracted_dir}")
        shutil.copytree(extracted_dir, merge_dir)
    else:
        logging.error("Neither merge nor extracted_scripts directory exists. Cannot proceed.")
        sys.exit(1)

    process_lua_scripts("ios")
    process_lua_scripts("android")

    logging.info("Script execution completed.")
    logging.info(f"Current directory: {os.getcwd()}")
    logging.info(f"Files in current directory: {os.listdir('.')}")
    logging.info(f"Files in project root: {os.listdir(project_root)}")
