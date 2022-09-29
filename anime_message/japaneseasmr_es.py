# -*- coding=utf-8 -*-

import requests, json, copy, os, re, tqdm
from loguru import logger
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup


class japaneseasmr_with_es():
    def __init__(self):
        asmr_json_path = '../data/japaneseasmr.logs'
        self.asmr_json_data = json.loads(open(asmr_json_path, 'r', encoding='utf-8').read())
        self.es = Elasticsearch(hosts=['elastic:elastic123456@192.168.31.200:9200'])
        self.es.indices.create(index='asmr_dlsite_v0.1', ignore=[400])

        self.headers_api = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
        }
        self.proxies = {"http": "http://192.168.31.200:1082", "https": "http://192.168.31.200:1082"}

        self.product_info_dict = {
            'rjcode': '',               # 作品rj号，也是es的_id
            'title': '',                # 作品标题，由dlsite ajax接口获取
            'regist_date': '',          # 发布时间，由dlsite ajax接口获取
            'cv': [],
            'cover_img_remote': '',     # 封面图，url，若空值则用本地
            'cover_img_local': '',      # 封面图，本地地址 "/root/a.jpg"
            'imgs_remote': [],          # 图片，url，若空值则用本地
            'imgs_local': [],           # 图片，本地地址 "/root/a.jpg"
            'age_category': 3,          # 作品分集，小于18为R18，由dlsite ajax接口获取
            'tags': [],                 # 作品标签
            'content': '',
            'original': {
                'dlsite': {},           # dlsite源数据
                'japaneseasmr': {}      # japaneseasmr源数据
            },
            'other':{
                'is_download': False    # 是否已入库
            }
        }

        self.asmr_save_dir = r'E:\临时\a'

    # 根据json的信息从dlsite获取数据
    def get_dlsite_info(self, rjcode, values):
        dlsite_api = r'https://www.dlsite.com/maniax/product/info/ajax?product_id=%s&cdn_cache_min=1' % rjcode

        try:
            req = requests.get(dlsite_api, headers=self.headers_api, proxies=self.proxies)
            if req.status_code == 200:
                dlsite_data_json = req.json()
                del req
            else:
                logger.error("返回码：%d    获取dlsite api信息失败" % req.status_code)
                del req
        except Exception as e:
            logger.error("获取dlsite api信息失败")
            logger.error(e)

        # 数据赋值
        data_dict = copy.deepcopy(self.product_info_dict)
        data_dict['rjcode'] = rjcode
        data_dict['title'] = dlsite_data_json[rjcode]['work_name']
        data_dict['regist_date'] = dlsite_data_json[rjcode]['regist_date']
        data_dict['age_category'] = dlsite_data_json[rjcode]['age_category']
        data_dict['cover_img_local'] = os.path.join(os.path.join(r'/mnt/sda/asmr/dlsite', rjcode),
                                                    values['cover'].split('/')[-1].strip())
        data_dict['content'] = values['content']
        for img in values['imgs']:
            data_dict['imgs_local'].append(os.path.join(os.path.join(r'/mnt/sda/asmr/dlsite', rjcode),
                                                        img.split('/')[-1].strip()))
        data_dict['original']['dlsite'] = dlsite_data_json
        data_dict['original']['japaneseasmr'] = values
        dlsite_product_content_url = r'https://www.dlsite.com/maniax/work/=/product_id/%s.html' % rjcode

        del dlsite_data_json

        # 获取dlsite正文内容
        cv_list = []
        tag_list = []
        try:
            req = requests.get(dlsite_product_content_url, headers=self.headers_api, proxies=self.proxies)
            if req.status_code == 200:
                soup = BeautifulSoup(req.text, features="html.parser")
                if soup.select('table[id="work_outline"] tr'):
                    for tr in soup.select('table[id="work_outline"] tr'):
                        if tr.select('th')[0].get_text() == '声优' or tr.select('th')[0].get_text() == '声優':
                            if re.search('/', tr.select('td')[0].get_text()):
                                for cv in tr.select('td')[0].get_text().split('/'):
                                    cv_list.append(cv.strip())
                            else:
                                cv_list.append(tr.select('td')[0].get_text().strip())
                        elif tr.select('th')[0].get_text() == '分类' or tr.select('th')[0].get_text() == 'ジャンル':
                            for tag in tr.select('td')[0].get_text().split('\n'):
                                if tag:
                                    tag_list.append(tag.strip())
                del req
            else:
                logger.error("返回码：%d    获取dlsite内容主页失败" % req.status_code)
                logger.error(req.request.url)
                del req
        except Exception as e:
            logger.error("获取dlsite内容主页失败")
            logger.error(e)


        data_dict['cv'] = cv_list
        if not data_dict['cv']:
            data_dict['cv'] = values['cv']
        data_dict['tags'] = tag_list
        if not data_dict['tags']:
            for tag in values['tags']:
                if tag.get('tag_ja'):
                    data_dict['tags'].append(tag['tag_ja'])

        # 删除主键空值
        if data_dict['original']['dlsite'][rjcode].get('locale_price'):
            if data_dict['original']['dlsite'][rjcode]['locale_price'].get(''):
                del data_dict['original']['dlsite'][rjcode]['locale_price']['']
        if data_dict['original']['dlsite'][rjcode].get('locale_price_str'):
            if data_dict['original']['dlsite'][rjcode]['locale_price_str'].get(''):
                del data_dict['original']['dlsite'][rjcode]['locale_price_str']['']
        if data_dict['original']['dlsite'][rjcode].get('locale_official_price'):
            if data_dict['original']['dlsite'][rjcode]['locale_official_price'].get(''):
                del data_dict['original']['dlsite'][rjcode]['locale_official_price']['']
        if data_dict['original']['dlsite'][rjcode].get('locale_official_price_str'):
            if data_dict['original']['dlsite'][rjcode]['locale_official_price_str'].get(''):
                del data_dict['original']['dlsite'][rjcode]['locale_official_price_str']['']
        return data_dict

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
                result = self.es.get(index='asmr_dlsite_v0.1', id=key)
                print('%s 已存在，跳过' %key)
            except:
                print('%s 不存在' %key)
                json_data = self.get_dlsite_info(key, values)
                result = self.es.create(index='asmr_dlsite_v0.1', id=key,
                                      document=json.dumps(json_data, ensure_ascii=False))



    def download(self):
        page = 1
        page_size = 5
        query = {
                'match': {
                    "other.is_download": False
                }
            }

        result = self.es.search(index='asmr_dlsite_v0.1', query=query, _source_includes=['original.japaneseasmr'])

        if result['hits']['total']['value'] > 0:
            result = result['hits']['hits']
            # 下载
            for data in result:
                rj_code = data['_id']
                vaules = data['_source']['original']['japaneseasmr']
                del data

                # 判断声音存放的文件夹是否存在
                if not os.path.exists(self.asmr_save_dir):
                    os.mkdir(self.asmr_save_dir)
                if not os.path.exists(os.path.join(self.asmr_save_dir, rj_code)):
                    os.mkdir(os.path.join(self.asmr_save_dir, rj_code))

                # 下载对应图片
                if vaules['imgs']:
                    for img_url in vaules['imgs']:
                        self.video_download(url=img_url, referer=vaules['page_url'],
                                            file_name=img_url.split('/')[-1].strip(),
                                            save_dir=os.path.join(self.asmr_save_dir, rj_code))
                    del img_url
                else:
                    self.video_download(url=vaules['cover'], referer=vaules['page_url'],
                                        file_name=vaules['cover'].split('/')[-1].strip(),
                                        save_dir=os.path.join(self.asmr_save_dir, rj_code))

                # 下载音频
                # 因为有的mp3下载链接不止一个
                for mp3_name, mp3_url in vaules['mp3'].items():
                    self.video_download(url=mp3_url, referer=vaules['page_url'], file_name=mp3_name.strip(),
                                        file_type='.mp3', save_dir=os.path.join(self.asmr_save_dir, rj_code))
                del mp3_name, mp3_url

                # 验证
                # 验证图片
                download_status = False
                files_count = len(os.listdir(os.path.join(self.asmr_save_dir, rj_code)))
                if vaules['imgs']:
                    if len(vaules['mp3'].keys()) + len(vaules['imgs']) <= files_count:
                        print('全部下载完成')
                        download_status = True

                    else:
                        print('未下载完成')
                else:
                    if len(vaules['mp3'].keys()) + 1 <= files_count:
                        print('全部下载完成')
                        download_status = True
                    else:
                        print('未下载完成')

                # 存入es
                if download_status is True:
                    self.es.update(index='asmr_dlsite_v0.1', id=rj_code, doc={"other": {"is_download": True}})


                del download_status


    def test(self):
        self.es.delete(index='asmr_dlsite_v0.1', id=22)
        # a = {"test": 1, "test44": {"test3": "test3", "test4": "test4"},"test3": 3}
        # self.es.index(index='asmr_dlsite_v0.1', document=json.dumps(a))
        # self.es.update(index='asmr_dlsite_v0.1', id='UOPbiYMByPRpvfOegzdT', doc={"test44": { "test4": "dasfsdafdas"}})





a = japaneseasmr_with_es()
# a.push_es()
a.download()
# a.test()