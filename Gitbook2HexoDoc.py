# coding: utf-8
"""Convert gitbook documents to hexo blogs."""

import os
import re

import time
import datetime

from shutil import copy2
from shutil import copytree

GITBOOK_DIR = r'./'    # gitbook 根目录
RESOURCES_DIR = r'assets'    # gitbook文档中用到的资源文件目录
POST_DIR = r'E:/workspace/blog/source/_posts'    # hexo 博客文档目录


class Gitbook2Hexo(object):
    SUMMARY = 'SUMMARY.md'
    TAB_INDENT = 2  # SUMMARY.md 文件tab缩进
    MAX_LEVEL = 3   # gitbook 文档目录最大深度

    def __init__(self, gitbook_path, post_path, res_dir):
        self.gitbook_path = gitbook_path
        self.post_path = post_path
        self.res_dir = res_dir

        if not os.path.exists(self.post_path):
            os.makedirs(self.post_path)

    def _update_post(self, file, infos):
        """Add header info.

        Format:
            ---
            layout: post
            title: "title"
            date: 2018-05-24 08:48:00
            categories: [category]
            ---
        """
        with open(file, 'r+', encoding='utf-8') as f:
            old_data = f.read()
            title = re.search(r'# (.*)', old_data)
            if title:
                infos['title'] = title[1]
                old_data = old_data[title.end():].lstrip()

            # write header info
            f.seek(0)
            f.write('---\n')
            for key, val in infos.items():
                f.write('{}: {}\n'.format(key, val))
            f.write('---\n')

            # replace resources path
            pattern = re.compile(r'\(\.\.\/{0}\/'.format(self.res_dir))
            old_data = re.subn(pattern, r'(/{0}/'.format(self.res_dir), old_data)[0]
            f.write(old_data)

    def _get_file_createtime(self, file):
        ts = os.path.getctime(file)
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))

    def _duplicate_resources(self):
        """Copy all resources from gitbook to blog."""

        try:
            dupFrom = self.gitbook_path + self.res_dir
            if os.path.exists(dupFrom):
                dupTo = os.path.dirname(self.post_path) + '/' + self.res_dir
                print('Duplicating {} from {} to {}...'.format(
                    self.res_dir, dupFrom, dupTo))

                copytree(self.gitbook_path + self.res_dir, dupTo)

        except FileExistsError as e:
            print('<WARNING> Duplicating {0} fail, {1} is existed.'.format(
                self.res_dir, dupTo))
            pass

    def convert(self):
        """Convert gitbook document to hexo blog."""

        try:
            with open(self.gitbook_path + self.SUMMARY, 'r') as f:
                data = f.read()
        except FileNotFoundError as e:
            print('[ERROR] Not found file {}'.format(self.SUMMARY))
            os._exit(1)

        pattern = re.compile(r'( *)\* *\[(.*?)\]\((.*)\)')
        fileTree = re.findall(pattern, data)

        group = [''] * self.MAX_LEVEL
        for space, title, file in fileTree:
            level = int(len(space)/self.TAB_INDENT)
            group[level] = title

            if not file:
                continue

            try:
                group_name = group[0] if not level else ', '.join(group[:level])
                group_name = '[{}]'.format(group_name)
                filepath = self.gitbook_path + file
                filetime = self._get_file_createtime(filepath)

                newfilepath = r'{}/{}-{}.md'.format(self.post_path, 
                    filetime[:10], '-'.join(title.split()).lower())
                
                copy2(filepath, newfilepath)
                print(group_name, filepath, '->', newfilepath)
                infos = {
                    'layout': 'post',
                    'title': title,
                    'date': filetime,
                    'categories': group_name
                }
                self._update_post(newfilepath, infos)

            except FileNotFoundError as e:
                print('<WARNING> Not found file {}, skipped.'.format(filepath))
                pass

        self._duplicate_resources()

        
def main():
    coverter = Gitbook2Hexo(GITBOOK_DIR, POST_DIR, RESOURCES_DIR)
    coverter.convert()

if __name__ == "__main__":
    main()
