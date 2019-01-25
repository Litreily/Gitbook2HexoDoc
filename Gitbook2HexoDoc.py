# coding: utf-8
"""Convert gitbook documents to hexo blogs

1. get all markdown files' name from SUMARRY.md
2. get create time of markdown file and create post filename
3. copy markdown to post directory
4. add post header info based on date, filename and group name
"""

import os
import re

import time
import datetime
from shutil import copy2, copytree

GITBOOK_DIR = r'./'
POST_DIR = r'E:/workspace/blog/source/_posts'

class Gitbook2Hexo(object):
    SUMMARY = 'SUMMARY.md'
    MAX_LEVEL = 3 # max tree deep level
    TAB_INDENT = 2

    def __init__(self, gitbook_path, post_path):
        self.gitbook_path = gitbook_path
        self.post_path = post_path

        if not os.path.exists(self.post_path):
            os.makedirs(self.post_path)

    def _updatePost(self, file, infos):
        """ Add header info
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

            # replace assets path
            pattern = re.compile(r'\(\.\.\/assets\/')
            old_data = re.subn(pattern, r'(/assets/', old_data)[0]
            print(old_data)
            f.write(old_data)

    def _getFileCreateTime(self, file):
        ts = os.path.getctime(file)
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))

    def _duplicateAssets(self):
        """Copy all images from gitbook to blog"""
        try:
            dupFrom = self.gitbook_path + 'assets'
            if os.path.exists(dupFrom):
                dupTo = r'{}/{}'.format(os.path.dirname(self.post_path), 'assets')
                print('Duplicating assets from {} to {}...'.format(dupFrom, dupTo))
                copytree(self.gitbook_path + 'assets', dupTo)
        except FileExistsError as e:
            print('<WARNING> Duplicating assets fail, {0} is existed.'.format(dupTo))
            pass

    def convert(self):
        """Convert gitbook document to hexo blog"""
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
                filetime = self._getFileCreateTime(filepath)

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
                self._updatePost(newfilepath, infos)

            except FileNotFoundError as e:
                print('<WARNING> Not found file {}, skipped.'.format(filepath))
                pass

        self._duplicateAssets()

        
def main():
    coverter = Gitbook2Hexo(GITBOOK_DIR, POST_DIR)
    coverter.convert()

if __name__ == "__main__":
    main()
