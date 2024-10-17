import os
import re
import logging
import filecmp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def merge_scripts(extracted_dir, replace_dir, merge_dir):
    logging.info("开始合并脚本")

    if not os.path.exists(merge_dir):
        os.makedirs(merge_dir)

    for filename in os.listdir(extracted_dir):
        if filename.endswith('.lua'):
            extracted_file = os.path.join(extracted_dir, filename)
            replace_file = os.path.join(replace_dir, filename)
            merge_file = os.path.join(merge_dir, filename)

            if os.path.exists(replace_file):
                if is_special_case(extracted_file, replace_file):
                    # 对于特殊情况，直接复制replace文件到merge
                    with open(replace_file, 'r', encoding='utf-8') as src, open(merge_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                    logging.info(f"特殊情况：直接使用replace文件: {filename}")
                else:
                    merge_file_contents(extracted_file, replace_file, merge_file)
            else:
                # 如果replace中没有对应文件，直接复制extracted的文件到merge
                with open(extracted_file, 'r', encoding='utf-8') as src, open(merge_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logging.info(f"复制文件到merge: {filename}")

    logging.info("脚本合并完成")

def is_special_case(extracted_file, replace_file):
    # 检查是否为特殊情况
    with open(extracted_file, 'r', encoding='utf-8') as ef, open(replace_file, 'r', encoding='utf-8') as rf:
        extracted_content = ef.read()
        replace_content = rf.read()
    
    # 检查replace文件是否只包含一个修改部分，且覆盖了整个文件
    if replace_content.strip().startswith('--我的修改部分') and replace_content.strip().endswith('--我的修改完毕'):
        # 进一步检查内容
        modified_content = replace_content.split('--我的修改部分', 1)[1].rsplit('--我的修改完毕', 1)[0].strip()
        if modified_content in extracted_content:
            return True
    return False

def merge_file_contents(extracted_file, replace_file, merge_file):
    with open(extracted_file, 'r', encoding='utf-8') as f:
        extracted_content = f.read()

    with open(replace_file, 'r', encoding='utf-8') as f:
        replace_content = f.read()

    # 查找replace文件中的所有修改部分
    modified_parts = re.findall(r'(--我的修改部分.*?--我的修改完毕)', replace_content, re.DOTALL)

    # 对每个修改部分进行处理
    for part in modified_parts:
        # 提取修改部分的内容（不包括--我的修改部分和--我的修改完毕）
        modified_content = part.split('\n', 1)[1].rsplit('\n', 1)[0]
        
        # 在extracted内容中查找相应的部分
        pattern = re.compile(re.escape(modified_content.split('\n', 1)[0]) + r'.*?' + re.escape(modified_content.rsplit('\n', 1)[-1]), re.DOTALL)
        match = pattern.search(extracted_content)
        
        if match:
            # 替换整个匹配的部分
            extracted_content = extracted_content[:match.start()] + part + extracted_content[match.end():]
        else:
            logging.warning(f"在文件中未找到匹配的内容: {modified_content[:50]}...")

    # 将修改后的内容写入merge文件
    with open(merge_file, 'w', encoding='utf-8') as f:
        f.write(extracted_content)

    logging.info(f"已合并文件: {os.path.basename(merge_file)}")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    extracted_dir = os.path.join(project_root, "extracted_scripts")
    replace_dir = os.path.join(project_root, "replace")
    merge_dir = os.path.join(project_root, "merge")
    merge_scripts(extracted_dir, replace_dir, merge_dir)