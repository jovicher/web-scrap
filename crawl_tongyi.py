import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from mimetypes import guess_extension


# 创建一个目录来保存下载的文件
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


# 根据Content-Type获取文件扩展名
def get_file_extension(response, url):
    content_type = response.headers.get('Content-Type', '').split(';')[0]
    extension = guess_extension(content_type)

    if extension:
        return extension
    else:
        # 如果无法从Content-Type获取扩展名，尝试从URL提取
        parsed_url = urlparse(url)
        return os.path.splitext(parsed_url.path)[1]


# 下载文件并按类型分类存放
def download_file(url, base_folder, visited_files, max_retries=3):
    try:
        if url in visited_files:
            return  # 如果文件已经下载过，跳过

        # 尝试多次下载文件
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30)  # 将超时时间增加到30秒
                response.raise_for_status()  # 如果状态码不是200，抛出HTTPError
                break  # 如果请求成功，跳出重试循环
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt + 1 == max_retries:
                    raise  # 在最后一次尝试后仍失败，抛出异常
                time.sleep(2 ** attempt)  # 指数级退避策略等待时间

        # 提取文件名和扩展名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = parsed_url.path.replace("/", "_")

        # 确定文件扩展名
        file_extension = get_file_extension(response, url)
        if not filename.endswith(file_extension):
            filename += file_extension

        # 根据文件类型创建子目录
        file_type = file_extension.replace('.', '').lower()
        if not file_type or file_type not in ['html', 'css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'mp4', 'mp3',
                                              'webm', 'ogg', 'pdf']:
            file_type = 'other'

        folder = os.path.join(base_folder, file_type)
        create_directory(folder)

        filepath = os.path.join(folder, filename)

        # 如果文件已存在，添加数字后缀避免覆盖
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{base}_{counter}{ext}"
            counter += 1

        with open(filepath, 'wb') as f:
            f.write(response.content)
        visited_files.add(url)  # 记录已下载的文件
        print(f"Downloaded {url} to {filepath}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url} after {max_retries} attempts. Reason: {str(e)}")


# 爬取页面并下载所有资源
def scrape_website(base_url, folder="website", visited=None, visited_files=None):
    if visited is None:
        visited = set()
    if visited_files is None:
        visited_files = set()

    # 跳过已经访问过的页面
    if base_url in visited:
        return

    visited.add(base_url)
    create_directory(folder)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=30)  # 将超时时间增加到30秒
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve the website: {base_url}. Reason: {str(e)}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 保存HTML文件
    parsed_url = urlparse(base_url)
    if parsed_url.path == "/" or parsed_url.path == "":
        html_filename = os.path.join(folder, 'index.html')
    else:
        html_filename = os.path.join(folder, parsed_url.path.strip("/").replace("/", "_") + '.html')

    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print(f"Saved HTML to {html_filename}")

    # 下载所有链接的资源（CSS, JS, Images, Videos, Audios, Iframes）
    futures = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for tag in soup.find_all(['link', 'script', 'img', 'video', 'audio', 'iframe']):
            src = None
            if tag.name == 'link' and 'href' in tag.attrs:
                src = tag['href']
            elif tag.name == 'script' and 'src' in tag.attrs:
                src = tag['src']
            elif tag.name == 'img' and 'src' in tag.attrs:
                src = tag['src']
            elif tag.name in ['video', 'audio', 'iframe'] and 'src' in tag.attrs:
                src = tag['src']

            if src:
                # 处理相对URL
                resource_url = urljoin(base_url, src)
                futures.append(executor.submit(download_file, resource_url, folder, visited_files))

        # 递归爬取所有子链接
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            full_url = urljoin(base_url, href)
            # 仅爬取与主域名相同的链接
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                futures.append(executor.submit(scrape_website, full_url, folder, visited, visited_files))

        # 等待所有线程完成
        for future in as_completed(futures):
            future.result()

    print("Scraping completed!")


if __name__ == "__main__":
    # 目标网站URL
    website_url = "http://www.tonetech.com.cn"

    # 执行爬取
    scrape_website(website_url)
