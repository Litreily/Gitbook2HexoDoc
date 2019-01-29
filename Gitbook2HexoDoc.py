# coding: utf-8

import os
import re
import sys
import getopt

import time
import datetime

from shutil import copy2
from shutil import copytree

GITBOOK_DIR = r'./'    # gitbook 根目录
RESOURCES_DIR = r'assets'    # gitbook文档中用到的资源文件目录
POST_DIR = r'E:/workspace/blog/source/_posts'    # hexo 博客文档目录


class Gitbook2Hexo(object):
    """Convert gitbook documents to hexo blogs."""

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
            pattern = re.compile(r'(\.\.\/)+{0}\/'.format(self.res_dir))
            old_data = re.subn(pattern, r'/{0}/'.format(self.res_dir), old_data)[0]
            f.write(old_data)

    def _get_file_createtime(self, file):
        ts = os.path.getctime(file)
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))

    def _duplicate_resources(self):
        """Copy all resources from gitbook to blog."""

        try:
            dupFrom = os.path.join(self.gitbook_path, self.res_dir)
            if os.path.exists(dupFrom):
                dupTo = os.path.dirname(self.post_path) + '/' + self.res_dir
                print('Duplicating {} from {} to {}...'.format(
                    self.res_dir, dupFrom, dupTo))

                copytree(dupFrom, dupTo)
            else:
                print('<WARNING> Not found resources: ' + self.res_dir)

        except FileExistsError as e:
            print('<WARNING> Duplicating {0} fail, {1} is existed.'.format(
                self.res_dir, dupTo))
            pass

    def convert(self):
        """Convert gitbook document to hexo blog."""

        try:
            with open(os.path.join(self.gitbook_path, self.SUMMARY), 'r') as f:
                data = f.read()
        except FileNotFoundError as e:
            print('[ERROR] Not found file {}'.format(self.SUMMARY))
            sys.exit(1)

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
                filepath = os.path.join(self.gitbook_path, file.lstrip('/\\'))
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


def usage():
    print(
        'usage: {} [-h][-s src][-d dst][-r resource]\n'.format(os.path.basename(sys.argv[0])) +
        '\t-h\t\tshow this help message and exit\n'
        '\t-s --src\troot dir of gitbook documents\n'
        '\t-d --dst\tposts path of hexo blogs\n'
        '\t-r\t\tresources files dir of gitbook documents, default "assets"\n'
    )
    sys.exit(2)

def parse_args(argv):
    try:
        opts, args = getopt.getopt(argv, 'hs:d:r:', ['src=', 'dst='])
    except getopt.GetoptError as e:
        usage()

    global GITBOOK_DIR, POST_DIR, RESOURCES_DIR
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ('-s', '--src'):
            GITBOOK_DIR = arg
        elif opt in ('-d', '--dst'):
            POST_DIR = arg
        elif opt == '-r':
            RESOURCES_DIR = arg
    
        
def main(argv):
    parse_args(argv)
    coverter = Gitbook2Hexo(GITBOOK_DIR, POST_DIR, RESOURCES_DIR)
    coverter.convert()

if __name__ == "__main__":
    main(sys.argv[1:])
