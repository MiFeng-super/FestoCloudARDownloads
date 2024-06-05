import requests
import xml.etree.ElementTree as ET
import os
import re
from urllib.parse import urlparse

root_path = 'C:\\Users\\admin\\Desktop\\festocloud'
root_url = 'https://festodidacticsw.azurewebsites.net/'
root_xml = 'https://festodidacticsw.azurewebsites.net/ar/festocloud.xml'
filters = ['planexy', 'cube', 'fdar_white']


def download_file(url, filename, is_exist=True):
    print('downloading', url, end='')
    try:
        if is_exist:
            if os.path.exists(filename):
                print(' success')
                return True

        dir_name = os.path.dirname(filename)
        os.makedirs(dir_name, exist_ok=True)

        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(' success')
        return True

    except requests.exceptions.RequestException as e:
        print(' fail')
        return False


def read_file(filename):
    with open(filename, 'r') as file:
        content = file.read()
        return content


def remove_duplicates(lst):
    return list(set(lst))


def xml_metadata(element, attr):
    results = []
    for meta in element.findall('METADATA'):
        for attr in meta.findall(attr):
            for value in attr:
                results.append(value.text)
    return results


def analysis_pack(relative_name):
    tree = ET.parse(os.path.join(root_path, relative_name))
    files = [entry.get('file') for entry in tree.getroot().findall('CONTENT')]
    root = os.path.dirname(relative_name)

    preview = tree.getroot().get('preview')
    if preview != '':
        full_name = os.path.join(root_path, root, preview)
        url_name = os.path.join(root_url, root, preview)
        download_file(url_name, full_name)

    for file in files:
        if file.find('.zip') != -1:
            full_name = os.path.join(root_path, root, file)
            url_name = os.path.join(root_url, root, file)
            download_file(url_name, full_name)


def analysis_scene(relative_name):
    try:
        root = os.path.dirname(relative_name)
        full_path = os.path.join(root_path, relative_name)
        xml_content = str(read_file(full_path))
        pattern = r'(?<!TARGETBASE\s)(?:file|texture|preview)="([^"]+)"'
        matches = re.findall(pattern, xml_content)
        tree = ET.parse(full_path)
        target_bases = tree.getroot().findall('TARGETBASE')

        files = []

        for base in target_bases:
            name = base.get('file')
            files.append(name + '.dat')
            files.append(name + '.xml')

        for match in matches:
            # filter
            if match != '' and not match in filters:
                files.append(match)

        files = remove_duplicates(files)

        for name in files:
            full_name = os.path.join(root_path, root, name)
            url_name = os.path.join(root_url, root, name)
            download_file(url_name, full_name)

    except Exception as e:
        print('analysing error', relative_name)


def analysis_compilation(relative_name):
    tree = ET.parse(os.path.join(root_path, relative_name))
    urls = [entry.get('url') for entry in tree.getroot().findall('ENTRY')]
    root = os.path.dirname(relative_name)

    for url in urls:
        scene_url = os.path.join(root_url, root, url)
        scene_file = os.path.join(root_path, root, url)

        download_file(scene_url, scene_file)
        analysis_xml(scene_url)


def analysis_directory(relative_name):
    tree = ET.parse(os.path.join(root_path, relative_name))
    root = tree.getroot()
    for entry in root.findall('ENTRY'):
        urls = []
        url = entry.get('url', '')
        if url == '':
            urls.extend(xml_metadata(entry, 'url'))
        else:
            urls.append(url)

        for url in urls:
            analysis_xml(url)


def analysis_xml(xml_url):
    print('analysing', xml_url)

    parsed = urlparse(xml_url)
    relative_name = parsed.path[1:]
    absolute_name = os.path.join(root_path, parsed.path[1:])
    download_file(xml_url, absolute_name)

    tree = ET.parse(absolute_name)
    root = tree.getroot()

    if root.tag == 'DIRECTORY':
        analysis_directory(relative_name)

    if root.tag == 'COMPILATION':
        analysis_compilation(relative_name)

    if root.tag == 'AUGMENTATION':
        analysis_scene(relative_name)

    if root.tag == 'PACK':
        analysis_pack(relative_name)


def main():
    analysis_xml(root_xml)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
