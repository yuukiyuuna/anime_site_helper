# -*- coding=utf-8 -*-

import os, time
import random

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
            'webp': '0',
            'platform': '3'
        }
        self.api_url = r'https://api.copymanga.site/'
        logger.info('接口地址设定为：%s' % self.api_url)

    def download(self, url, output_dir=None, start=None, end=None):
        if url.endswith('/'):
            manga_name = url.split('/')[-2]
        else:
            manga_name = url.split('/')[-1]
        logger.info('识别漫画名称：%s' % manga_name)

        # 获取章节列表
        mangas_zhangjie_info = self.get_chapters(manga_name=manga_name)
        logger.info('获取章节成功，共获取 %d 个章节' %mangas_zhangjie_info['manga_len'])
        logger.debug(mangas_zhangjie_info)

        # 匹配需要下载的部分
        if str(start).isdigit():
            start = int(start) - 1
        elif not str(start).isdigit():
            if start in mangas_zhangjie_info['manga_title_list']:
                start = mangas_zhangjie_info['manga_title_list'].index(start)
            else:
                start = 0
        else:
            start = 0

        if str(end).isdigit():
            end = int(end)
        elif not str(end).isdigit():
            if end in mangas_zhangjie_info['manga_title_list']:
                end = mangas_zhangjie_info['manga_title_list'].index(end) + 1
            else:
                end = mangas_zhangjie_info['manga_len']
        else:
            end = mangas_zhangjie_info['manga_len']

        mangas_zhangjie = []
        for num in range(start, end):
            mangas_zhangjie.append(mangas_zhangjie_info['manga_info_list'][num])
        logger.info('成功筛选出下载范围')
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

                time.sleep(random.randint(3, 5))





    # 获取章节列表
    def get_chapters(self, manga_name):

        limit = 20
        offset = 0
        mangas_info = []
        manga_title_name = []
        while True:
            path = r'api/v3/comic/%s/group/default/chapters?limit=%d&offset=%d&format=json' \
                   %(manga_name, limit, offset)
            url = self.api_url + path

            req = requests.get(url, headers=self.headers)
            # req = requests.get(url, headers=self.headers)
            if req.status_code == 200:
                if req.json()['code'] == 200:
                    logger.debug('成功访问 %s' %req.request.url)
                    logger.debug(req.json())
                    logger.info('本次请求共获取 %d 个章节' %len(req.json()['results']['list']))

                    for manga in req.json()['results']['list']:
                        mangas_info.append([manga['name'], manga['uuid']])
                        manga_title_name.append(manga['name'])

                    if offset + limit >= req.json()['results']['total']:
                        break

                    offset += limit





                else:
                    logger.error('章节列表获取失败，返回码 %d' % req.json()['code'])
                    logger.error(req.teaxt)
                    continue
            else:
                logger.error('章节列表获取失败，返回码 %d' % req.status_code)
                logger.error(req.text)
                continue

        return {'manga_len': len(mangas_info), 'manga_title_list': manga_title_name, 'manga_info_list': mangas_info}


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
