# -*- coding=utf-8 -*-

import os, time
from loguru import logger
import requests
# 关闭证书验证（copy漫画下载图片时需要验证）
import urllib3
urllib3.disable_warnings()


class copymanga():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Dart/2.15(dart:io)',
            'source': 'copyApp',
            'version': '1.3.1',
            'region': '1',
            'webp': '0'
        }
        self.api_url = r'https://api.copymanga.org/'

    def download(self, url):
        if url.endswith('/'):
            manga_name = url.split('/')[-2]
        else:
            manga_name = url.split('/')[-1]
        logger.info('识别漫画名称：%s' % manga_name)

        # 获取章节列表
        mangas_zhangjie = self.get_chapters(manga_name=manga_name)
        logger.debug(mangas_zhangjie)

        # 创建漫画文件夹
        if not os.path.exists(manga_name):
            os.mkdir(manga_name)

        # 获取每个章节里的漫画下载地址并下载
        for manga in mangas_zhangjie:
            # 检查章节文件夹是否存在
            if not os.path.exists(os.path.join(manga_name, manga[0])):
                os.mkdir(os.path.join(manga_name, manga[0]))

            # 获取章节内图片url
            page_info = self.get_chapter2(manga_name=manga_name, zhangjie_uuid=manga[1])
            logger.debug(page_info)

            # 下载图片
            for page in page_info:
                logger.info('开始下载图片 %s' % page[0])
                print(page)
                self.download_page(url=page[0], filepath=os.path.join(os.path.join(manga_name, manga[0]),
                                                                 str(page[1]).zfill(4) + r'.jpg'))

                time.sleep(0.5)


            break



    # 获取章节列表
    def get_chapters(self, manga_name):
        path = r'api/v3/comic/%s/group/default/chapters?limit=500&offset=0&platform=3' % manga_name
        url = self.api_url + path

        req = requests.get(url, headers=self.headers)
        if req.status_code == 200:
            if req.json()['code'] == 200:
                logger.info('章节列表获取成功，共计 %d 话' % req.json()['results']['total'])
            else:
                logger.error('章节列表获取失败')
                logger.error(req.text)
        else:
            logger.error('章节列表获取失败')
            logger.error(req.text)

        mangas = []
        for manga in req.json()['results']['list']:
            mangas.append([manga['name'], manga['uuid']])

        return mangas


    # 获取章节内列表
    def get_chapter2(self, manga_name, zhangjie_uuid, zhangjie_id=None):
        path = r'api/v3/comic/%s/chapter2/%s?platform=3' % (manga_name, zhangjie_uuid)
        url = self.api_url + path

        req = requests.get(url, headers=self.headers)
        if req.status_code == 200:
            if req.json()['code'] == 200:
                logger.info('章节图片内容获取成功，共计 %d 张' % len(req.json()['results']['chapter']['contents']))
            else:
                logger.error('章节列表获取失败')
                logger.error(req.text)
        else:
            logger.error('章节列表获取失败')
            logger.error(req.text)

        pages = []
        for page in req.json()['results']['chapter']['contents']:
            pages.append([page['url']])

        # words字段与url字段对应
        if len(req.json()['results']['chapter']['contents']) == len(req.json()['results']['chapter']['words']):
            logger.debug('contents中url数量与words数量一致，按words顺序命名')
            for i in range(0, len(req.json()['results']['chapter']['words'])):
                pages[i].append(req.json()['results']['chapter']['words'][i])
        else:
            logger.debug('contents中url数量与words数量不一致，按url顺序命名')
            for i in range(0, len(req.json()['results']['chapter']['contents'])):
                pages[i].append(i)

        return pages


    # 下载漫画
    def download_page(self, url, filepath):
        req = requests.get(url, headers=self.headers, verify=False)     # 关闭证书验证
        open(filepath, 'wb').write(req.content)



a = copymanga()
a.download('https://www.copymanga.org/comic/kuangduzhiyuanshuang/')