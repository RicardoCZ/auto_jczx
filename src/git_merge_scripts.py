import os
import shutil
import subprocess
import logging
import time
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        logging.error(f"Command failed: {command}")
        logging.error(f"Error: {error.decode('utf-8')}")
        raise Exception(f"Command failed: {command}")
    return output.decode('utf-8')

def safe_remove_dir(dir_path, max_retries=5, delay=1):
    for _ in range(max_retries):
        try:
            shutil.rmtree(dir_path)
            return
        except Exception as e:
            logging.warning(f"Failed to remove directory {dir_path}: {str(e)}")
            time.sleep(delay)
    logging.error(f"Failed to remove directory {dir_path} after {max_retries} attempts")

def git_merge_scripts(extracted_dir, replace_dir, merge_dir):
    logging.info("开始使用 Git 合并脚本")

    # 创建一个带有唯一标识符的临时目录
    unique_id = uuid.uuid4().hex
    temp_dir = os.path.join(os.path.dirname(extracted_dir), f"temp_git_merge_{unique_id}")
    os.makedirs(temp_dir, exist_ok=True)
    original_dir = os.getcwd()
    os.chdir(temp_dir)

    try:
        # 初始化 Git 仓库
        run_command("git init")

        # 设置 Git 用户名和邮箱
        run_command('git config user.name "GitHub Action"')
        run_command('git config user.email "action@github.com"')

        # 创建并切换到 extracted 分支
        run_command("git checkout -b extracted")
        
        # 复制 extracted_scripts 到临时目录并提交
        for item in os.listdir(extracted_dir):
            src = os.path.join(extracted_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        run_command("git add .")
        run_command('git commit -m "Add extracted scripts"')

        # 创建并切换到 replace 分支
        run_command("git checkout -b replace")

        # 删除所有文件，然后复制 replace 文件夹的内容
        for item in os.listdir(temp_dir):
            if item != ".git":
                path = os.path.join(temp_dir, item)
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)

        for item in os.listdir(replace_dir):
            src = os.path.join(replace_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        run_command("git add .")
        run_command('git commit -m "Add replace scripts"')

        # 切换回 extracted 分支并尝试合并 replace 分支
        run_command("git checkout extracted")
        try:
            run_command("git merge replace -X theirs")
        except Exception:
            logging.info("合并冲突发生，使用 replace 的版本解决冲突")
            run_command("git checkout --theirs .")
            run_command("git add .")
            run_command('git commit -m "Resolve conflicts using replace version"')

        # 复制合并后的文件到 merge 目录
        if not os.path.exists(merge_dir):
            os.makedirs(merge_dir)
        for item in os.listdir(temp_dir):
            if item != ".git":
                src = os.path.join(temp_dir, item)
                dst = os.path.join(merge_dir, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)

        logging.info("Git 合并完成")

    except Exception as e:
        logging.error(f"Git 合并过程中发生错误: {str(e)}")
    finally:
        # 切回原始目录
        os.chdir(original_dir)
        # 安全地删除临时目录
        safe_remove_dir(temp_dir)

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extracted_dir = os.path.join(project_root, "extracted_scripts")
    replace_dir = os.path.join(project_root, "replace")
    merge_dir = os.path.join(project_root, "merge")
    git_merge_scripts(extracted_dir, replace_dir, merge_dir)