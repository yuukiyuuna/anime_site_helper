# -*- coding=utf-8 -*-
import json
import re

from loguru import logger
from bs4 import BeautifulSoup

class yurifan_online_manga_tools:
    # def __init__(self):
        # self.manga_url = url
        # self.page_content = page_content
        # self.page_content = open('test/wuyincang.html', 'r', encoding='utf-8').read()
        # self.page_content = open('../test/yincang.html', 'r', encoding='utf-8').read()


    def pic_info(self, page_content):
        # page_content = open('../test/yincang.html', 'r', encoding='utf-8').read()
        self.soup = BeautifulSoup(page_content)

        title = self.get_manga_title()      # 获取标题
        tags = self.get_manga_tag()         # 获取漫画标签
        pics = self.pictuers_split(self.soup.find(class_ = 'entry-content'))         # 获取图片url(隐藏积分的话则是试读部分的图片)

        # 如果为真，则调用支付积分函数，否则正常下载
        if self.soup.find(class_ = 'content-hidden'):
            logger.info('此资源为隐藏内容资源，将调用第一个用户支付积分并下载')

            dict = {
                'download_mode': 2,
                'title': title,
                'tags': tags,
                'pictures': pics
            }
        else:
            dict = {
                'download_mode': 1,
                'title': title,
                'tags': tags,
                'pictures': pics
            }

        return dict





    def get_manga_title(self):
        title = self.soup.find(class_='post-style-3-title').find('h1')
        return title.text

    def get_manga_tag(self):
        tags = self.soup.find(class_ = 'post-tags-meat').find_all(class_ = 'tag-text')
        return tags

    def get_manga_pic(self):
        pics_contents = self.soup.find(class_ = 'entry-content')
        pics = re.findall(r'src="(https://yuri.website/wp-content/uploads/.*?)"', str(pics_contents.contents))
        return pics

    # 按集数来分出
    # 通过bs4传入content
    def pictuers_split(self, content):
        pics_fake = []
        # 先检查是否有集数的字样
        if not re.findall('第[0-9]+話', str(content)) or re.findall('第[0-9]+话', str(content)) or re.findall('第[0-9]+章', str(content)):
            pics = []

            logger.debug('未检索出分集关键字')
            pics_fake = re.findall(r'src="(https://yuri.website/wp-content/uploads/.*?)"', str(content))
            # 遍历网页可能会造成图片地址重复，再此添加重复项过滤
            for i in pics_fake:
                if i not in pics:
                    pics.append(i)
            logger.debug('隐藏部分内容：%s' % str(pics))
            return {"mode": 1, "data": pics}
        else:
            logger.debug('已在内容中检索出分集关键字')
            count = 0
            contents = str(content).split('\n')
            for i in contents:
                # 如果有章节字样则新建一个列表房里，用count控制层级
                if re.findall('第[0-9]+話', i) or re.findall('第[0-9]+话', i) or re.findall('第[0-9]+章', i):
                    try:
                        linshi = []
                        for ii in pics_fake:
                            linshi.append(ii[0])
                        if re.findall('第[0-9]+話', i)[0] not in linshi:
                            pics_fake.append([re.findall('第[0-9]+話', i)[0]])
                            count += 1
                    except Exception as e:
                        None
                    try:
                        linshi = []
                        for ii in pics_fake:
                            linshi.append(ii[0])
                        if re.findall('第[0-9]+话', i)[0] not in linshi:
                            pics_fake.append([re.findall('第[0-9]+话', i)[0]])
                            count += 1
                    except Exception as e:
                        None
                    try:
                        linshi = []
                        for ii in pics_fake:
                            linshi.append(ii[0])
                        if re.findall('第[0-9]+章', i)[0] not in linshi:
                            pics_fake.append([re.findall('第[0-9]+章', i)[0]])
                            count += 1
                    except Exception as e:
                        None

                if re.findall(r'src="(https://yuri.website/wp-content/uploads/.*?)"', i):
                    pics_fake[count - 1].append(re.findall(r'src="(https://yuri.website/wp-content/uploads/.*?)"', i)[0])

            # 遍历网页可能会造成图片地址重复，再此添加重复项过滤
            pics = [[]]
            count = 0
            for i in pics_fake:
                for ii in i:
                    if ii not in pics[count]:
                        pics[count].append(ii)
                count += 1


            logger.debug(pics)
            return {"mode": 2, "data": pics}
