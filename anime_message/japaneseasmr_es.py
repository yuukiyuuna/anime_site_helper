# -*- coding=utf-8 -*-

import requests, json, copy, os, re, tqdm, time
from loguru import logger
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
import threading


class japaneseasmr_with_es():
    def __init__(self):
        asmr_json_path = '../data/japaneseasmr.logs'
        self.asmr_json_data = json.loads(open(asmr_json_path, 'r', encoding='utf-8').read())
        self.es = Elasticsearch(hosts=['elastic:elastic123456@es.xiaofeituo.com:9200'])
        self.es.indices.create(index='asmr_dlsite_v0.5', ignore=[400])

        self.headers_api = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
        }
        self.proxies = {"http": "http://192.168.31.200:1082", "https": "http://192.168.31.200:1082"}

        self.product_info_dict = {
            'rjcode': '',               # str       # 作品rj号，也是es的_id
            'title': '',                # str       # 作品标题，由dlsite ajax接口获取
            'regist_date': '',          # date      # 发布时间，由dlsite ajax接口获取
            'cv': [],                   # str       # 声优
            'age_category': 3,          # int       # 作品分集，小于18为R18，由dlsite ajax接口获取
            'tags': [],                 # list      # 作品标签
            'content': '',              # str       # 作品详情介绍
            'media_source_data': [],    # list      # 媒体数据 {"type":"", "title": "", "remote":"", "local": ""}
            'img_source_data': {
                'main_img':{
                    'remote': '',       # str
                    'local': ''         # str
                },
                'imgs': {
                    'remote': [],       # list
                    'local': []         # list
                }
            },
            'original': {
                'dlsite': '',           # str       # dlsite源数据
                'japaneseasmr': ''      # str       # japaneseasmr源数据
            },
            'other':{
                'is_download': False    # bure      # 是否已入库
            }
        }

        # self.product_info_dict = {
        #     'rjcode': '',               # str   # not null      # 作品rj号，也是es的_id
        #     'title': '',                # str       # 作品标题，由dlsite ajax接口获取
        #     'regist_date': '',          # date      # 发布时间，由dlsite ajax接口获取
        #     'cv': [],                   # str       # 声优
        #     'mp3_remote': {},           # str       # mp3真实地址，url
        #     'mp3_local': {},            # mp3本地存储地址
        #     'cover_img_remote': '',     # 封面图，url，若空值则用本地
        #     'cover_img_local': '',      # 封面图，本地地址 "/root/a.jpg"
        #     'imgs_remote': [],          # 图片，url，若空值则用本地
        #     'imgs_local': [],           # 图片，本地地址 "/root/a.jpg"
        #     'age_category': 3,          # 作品分集，小于18为R18，由dlsite ajax接口获取
        #     'tags': [],                 # 作品标签
        #     'content': '',
        #     'original': {
        #         'dlsite': {},           # dlsite源数据
        #         'japaneseasmr': {}      # japaneseasmr源数据
        #     },
        #     'other':{
        #         'is_download': False    # 是否已入库
        #     }
        # }

        self.asmr_save_dir = r'E:\临时\a'

    # 根据json的信息从dlsite获取数据
    def get_dlsite_info(self, rjcode, values):
        logger.info('开始处理 %s 数据' %rjcode)
        logger.debug(values)
        dlsite_api = r'https://www.dlsite.com/maniax/product/info/ajax?product_id=%s&cdn_cache_min=1' % rjcode

        # 访问 dlsite api 获取数据
        req = requests.get(dlsite_api, headers=self.headers_api, proxies=self.proxies)
        del dlsite_api
        if req.status_code == 200:
            dlsite_data_json = req.json()
            logger.debug('访问 %s 成功' % req.request.url)
            logger.debug(req.json())
            del req
        else:
            logger.error("访问 %s 失败, 返回码：%d    " %(req.request.url, req.status_code))
            logger.error(req.text)
            del req
            return {'status': False, 'data': None}



        # 数据赋值
        data_dict = copy.deepcopy(self.product_info_dict)       # 复制数据结构
        data_dict['rjcode'] = rjcode        # 从 japaneseasmr 的 json 中获取
        data_dict['title'] = dlsite_data_json[rjcode]['work_name']      # 从 dlsite 中获取
        data_dict['regist_date'] = dlsite_data_json[rjcode]['regist_date']      # 从 dlsite 中获取
        data_dict['age_category'] = dlsite_data_json[rjcode]['age_category']    # 从 dlsite 中获取
        # 从 json 中获取
        data_dict['img_source_data']['main_img']['remote'] = 'https://myhome.hancloud.top/asmr/dlsite/%s/%s' \
                                                             %(rjcode, values['cover'].split('/')[-1].strip())
        data_dict['img_source_data']['main_img']['local'] = os.path.join(os.path.join(r'/mnt/sda/asmr/dlsite', rjcode),
                                                                         values['cover'].split('/')[-1].strip())
        data_dict['content'] = values['content']        # 从 json 中获取
        if values['imgs']:      # imgs 有可能为空，所以先判断是否为空
            for img in values['imgs']:
                data_dict['img_source_data']['imgs']['remote'].append('https://myhome.hancloud.top/asmr/dlsite/%s/%s'
                                                                      % (rjcode, img.split('/')[-1].strip()))
                data_dict['img_source_data']['imgs']['local'].append(os.path.join(
                    os.path.join(r'/mnt/sda/asmr/dlsite', rjcode),img.split('/')[-1].strip()))

        for key_mp3, value_mp3 in values['mp3'].items():
            data_dict['media_source_data'].append({'type': 'mp3', 'title': key_mp3,
                                                   'remote': 'https://myhome.hancloud.top/asmr/dlsite/%s/%s'
                                                             %(rjcode, value_mp3.split('/')[-1].strip()),
                                                   'local': os.path.join(os.path.join(r'/mnt/sda/asmr/dlsite', rjcode),
                                                                               value_mp3.split('/')[-1].strip())})

        data_dict['original']['dlsite'] = json.dumps(dlsite_data_json, ensure_ascii=False)
        data_dict['original']['japaneseasmr'] = json.dumps(values, ensure_ascii=False)
        del dlsite_data_json


        # 获取dlsite正文内容
        cv_list = []
        tag_list = []

        # 详情页请求url
        dlsite_product_content_url = r'https://www.dlsite.com/maniax/work/=/product_id/%s.html' % rjcode
        req = requests.get(dlsite_product_content_url, headers=self.headers_api, proxies=self.proxies)
        if req.status_code == 200:
            del dlsite_product_content_url
            logger.debug('访问详情页 %s 成功' %req.request.url)
            soup = BeautifulSoup(req.text, features="html.parser")
            if soup.select('table[id="work_outline"] tr'):
                logger.debug('网页源码 id=work_outline 查找成功')
                logger.debug(soup.select('table[id="work_outline"] tr'))
                for tr in soup.select('table[id="work_outline"] tr'):
                    if tr.select('th')[0].get_text() == '声优' or tr.select('th')[0].get_text() == '声優':
                        logger.debug('成功查找到声优： %s' % tr.select('td')[0].get_text().strip())
                        if re.search('/', tr.select('td')[0].get_text()):
                            for cv in tr.select('td')[0].get_text().strip().split('/'):
                                cv_list.append(cv.strip())
                        else:
                            cv_list.append(tr.select('td')[0].get_text().strip())
                    elif tr.select('th')[0].get_text() == '分类' or tr.select('th')[0].get_text() == 'ジャンル':
                        logger.debug('成功查找到分类： %s' % tr.select('td')[0].get_text())
                        for tag in tr.select('td')[0].get_text().split('\n'):
                            if tag:
                                tag_list.append(tag.strip())
            del req
        else:
            logger.error("访问详情页 %s 失败，返回码 %d" %(req.request.url, req.status_code))
            del req

        data_dict['cv'] = cv_list
        if not data_dict['cv']:
            logger.warning('未能从 dlsite 详情页中获取到声优信息，从 japaneseasmr 中补齐')
            data_dict['cv'] = values['cv']
        data_dict['tags'] = tag_list
        if not data_dict['tags']:
            logger.warning('未能从 dlsite 详情页中获取到tag')
        # 将 japaneseasmr 中的tag加入到 tag 中
        for tag in values['tags']:
            if tag.get('tag_ja'):
                if tag['tag_ja'] not in data_dict['tags']:
                    data_dict['tags'].append(tag['tag_ja'])


        logger.debug(data_dict)
        return {'status': True, 'data': data_dict}

    def video_download(self, url, referer, file_name, file_type='', save_dir=None):
        if save_dir is None:
            file_full_path = os.path.join(os.getcwd(), file_name + file_type)
        else:
            file_full_path= os.path.join(save_dir, file_name + file_type)
        logger.info('开始下载音频 %s' %url)
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "referer": referer
        }
        req = requests.get(url=url, headers=headers, stream=True)
        total_size = req.headers['Content-Length']
        del req, save_dir, file_name, referer
        logger.info('本音频大小为：%s' %total_size)

        # 是否一下载过该文件，该文件是否被下载完成
        if os.path.exists(file_full_path):
            file_size = os.path.getsize(file_full_path)
            if int(total_size) > file_size:
                start_byte = file_size + 1
                logger.info('文件已存在，大小为 %d ，开始继续下载' %start_byte)
            else:
                start_byte = None
                logger.info('文件已存在，大小为 %d' % file_size)
            del file_size
        else:
            start_byte = 0
            logger.info('文件不存在，准备下载文件')

        if start_byte is not None:
            pbar = tqdm.tqdm(total=int(total_size), initial=start_byte, unit='B', unit_scale=True, desc=file_full_path)
            headers['Range'] = r'bytes=%d-%s' %(start_byte, total_size)
            req = requests.get(url=url, headers=headers, stream=True)
            with open(file_full_path, 'ab') as f:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(1024)
            pbar.close()


    # download
    def push_es(self):
        for key, values in self.asmr_json_data.items():
            try:
                result = self.es.get(index='asmr_dlsite_v0.5', id=key)
                logger.info('es 中已存在 %s 的数据，跳过' %key)
            except:
                logger.info('开始查找 %s 信息并存入es中' %key)
                try:
                    data = self.get_dlsite_info(key, values)
                    if data['status']:
                        result = self.es.create(index='asmr_dlsite_v0.5', id=key,
                                                document=json.dumps(data['data'], ensure_ascii=False))
                except Exception as e:
                    logger.exception(e)



    def download(self):
        query = {
                'match': {
                    "other.is_download": False
                }
            }

        result = self.es.search(index='asmr_dlsite_v0.5', query=query, _source_includes=['original.japaneseasmr'])
        logger.debug('请求es数据成功')
        logger.debug(result)

        if result['hits']['total']['value'] > 0:
            # 下载
            for data in result['hits']['hits']:
                rj_code = data['_id']
                values = json.loads(data['_source']['original']['japaneseasmr'])
                del data

                # 判断声音存放的文件夹是否存在
                if not os.path.exists(self.asmr_save_dir):
                    os.mkdir(self.asmr_save_dir)
                if not os.path.exists(os.path.join(self.asmr_save_dir, rj_code)):
                    os.mkdir(os.path.join(self.asmr_save_dir, rj_code))

                # 下载对应图片
                if values['imgs']:
                    for img_url in values['imgs']:
                        self.video_download(url=img_url, referer=values['page_url'],
                                            file_name=img_url.split('/')[-1].strip(),
                                            save_dir=os.path.join(self.asmr_save_dir, rj_code))
                    del img_url
                else:
                    self.video_download(url=values['cover'], referer=values['page_url'],
                                        file_name=values['cover'].split('/')[-1].strip(),
                                        save_dir=os.path.join(self.asmr_save_dir, rj_code))

                # 下载音频
                # 因为有的mp3下载链接不止一个
                for mp3_url in values['mp3']:
                    self.video_download(url=values['mp3'][mp3_url], referer=values['page_url'],
                                        file_name=values['mp3'][mp3_url].split('/')[-1].strip(),
                                        save_dir=os.path.join(self.asmr_save_dir, rj_code))
                del mp3_url

                # 验证
                # 验证图片
                download_status = False
                files_count = len(os.listdir(os.path.join(self.asmr_save_dir, rj_code)))
                if values['imgs']:
                    if len(values['mp3'].keys()) + len(values['imgs']) <= files_count:
                        print('全部下载完成')
                        download_status = True

                    else:
                        print('未下载完成')
                else:
                    if len(values['mp3'].keys()) + 1 <= files_count:
                        print('全部下载完成')
                        download_status = True
                    else:
                        print('未下载完成')

                # 存入es
                if download_status is True:
                    self.es.update(index='asmr_dlsite_v0.5', id=rj_code, doc={"other": {"is_download": True}})


                del download_status



def th1():
    sys = japaneseasmr_with_es()
    sys.push_es()


def th2():
    sys = japaneseasmr_with_es()
    while True:
        time.sleep(5)
        sys.download()




if __name__ == '__main__':

    # th1()

    th2()

