# import html2text
#
# md_text = open('website/about.html', 'r', encoding='utf-8').read()
#
# markdown = html2text.html2text(md_text)
# with open('make2.md', 'w', encoding='utf-8') as file:
#     file.write(markdown)


import os
import html2text

def get_files(source_dir, source_ext):
    """
    遍历源目录，获取符合指定扩展名的文件列表，并返回源文件路径。

    参数:
    source_dir (str): 源文件目录路径。
    source_ext (str): 要查找的源文件扩展名（如 '.md'）。

    返回:
    list: 一个包含源文件路径的列表。
    """
    file_pairs = []

    # 遍历源目录及其子目录中的所有文件
    for src_root, _, files in os.walk(source_dir):
        for filename in files:
            # 检查文件扩展名是否符合源文件要求
            if filename.endswith(source_ext):
                # 构建源文件路径
                src_path = os.path.join(src_root, filename)
                file_pairs.append(src_path)

    return file_pairs

def convert_files(source_dir, output_dir, source_ext):
    """
    将源目录中的指定类型文件批量转换为目标格式，并保持原目录结构。

    参数:
    source_dir (str): 源文件目录路径。
    output_dir (str): 转换后文件的输出目录路径。
    source_ext (str): 要转换的源文件的扩展名（例如 '.html'）。
    target_format (str): 目标文件格式（例如 'pdf', 'docx' 等）。
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取源文件及其目标路径的列表
    files_to_convert = get_files(source_dir, source_ext)
    # print(files_to_convert)
    for src_path in files_to_convert:
        # 构建目标文件名和路径
        rel_path = os.path.relpath(src_path, source_dir)
        new_filename = rel_path.rsplit('.', 1)[0] + '.md'
        print(new_filename)
        new_filepath = os.path.join(output_dir, new_filename)

        # 转换单个文件
        md_text = open(src_path, 'r', encoding='utf-8').read()
        markdown_content = html2text.html2text(md_text)
        with open(new_filepath, 'w', encoding='utf-8') as md_file:
            md_file.write(markdown_content)

if __name__ == "__main__":

    source_dir = 'website/test2md/html'  # 源文件目录
    output_dir = 'website/test2md/h2md'  # 输出文件目录
    source_ext = '.html'  # 源文件扩展名

    # 调用文件转换函数
    convert_files(source_dir, output_dir, source_ext)
