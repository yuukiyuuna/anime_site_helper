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

    def download(self, url, output_dir=None):
        if url.endswith('/'):
            manga_name = url.split('/')[-2]
        else:
            manga_name = url.split('/')[-1]
        logger.info('识别漫画名称：%s' % manga_name)

        # 获取章节列表
        mangas_zhangjie = self.get_chapters(manga_name=manga_name)
        logger.debug(mangas_zhangjie)

        # 创建漫画文件夹
        if output_dir is not None:      # 若指定了输出文件夹
            manga_dir = os.path.join(output_dir, manga_name)
            if not os.path.exists(manga_dir):
                os.mkdir(manga_dir)

        else:                           # 若未指定输出文件夹
            manga_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0], manga_name)
            if not os.path.exists(manga_dir):
                os.mkdir(manga_dir)


        # 获取每个章节里的漫画下载地址并下载
        for manga in mangas_zhangjie:
            # 检查章节文件夹是否存在
            manga_zhangjie_dir = os.path.join(manga_dir, manga[0])
            if not os.path.exists(manga_zhangjie_dir):
                os.mkdir(manga_zhangjie_dir)

            # 获取章节内图片url
            page_info = self.get_chapter2(manga_name=manga_name, zhangjie_uuid=manga[1], zhangjie_name=manga[0])
            logger.debug(page_info)

            # 下载图片
            for page in page_info:
                manga_page_dir = os.path.join(manga_zhangjie_dir, str(page[1]).zfill(4) + r'.jpg')
                if os.path.exists(manga_page_dir):
                    continue
                logger.info('开始下载 %s 中的第 %d 图片' % (manga[0], page[1]))
                self.download_page(url=page[0], filepath=manga_page_dir)

                time.sleep(1)





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
    def get_chapter2(self, manga_name, zhangjie_uuid, zhangjie_name=''):
        path = r'api/v3/comic/%s/chapter2/%s?platform=3' % (manga_name, zhangjie_uuid)
        url = self.api_url + path

        req = requests.get(url, headers=self.headers)
        if req.status_code == 200:
            if req.json()['code'] == 200:
                logger.info('%s 内图片内容获取成功，共计 %d 张' % (zhangjie_name, len(req.json()['results']['chapter']['contents'])))

                # 获取图片url
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

            else:
                logger.error('章节列表获取失败，请求url：%s' % req.request.url)
                logger.error('网页相应：%d' % req.status_code)
                logger.error(req.content)

        elif req.status_code == 502:        # 如果出现502，则重试（网页偶尔会出现这情况）
            logger.warning('请求 %s 出现502响应，开始重试' % req.request.url)
            self.get_chapter2(manga_name=manga_name, zhangjie_uuid=zhangjie_uuid)

        else:
            logger.error('章节列表获取失败，请求url：%s' % req.request.url)
            logger.error('网页相应：%d' % req.status_code)
            logger.error(req.content)







    # 下载漫画
    def download_page(self, url, filepath):
        try:
            req = requests.get(url, headers=self.headers, verify=False)  # 关闭证书验证
            open(filepath, 'wb').write(req.content)
        except Exception as e:
            logger.warning('下载图片失败，一秒后重试')
            logger.error(e)
            self.download_page(url=url, filepath=filepath)

