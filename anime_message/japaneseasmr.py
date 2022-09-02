# -*- coding=utf-8 -*-
import requests, datetime, json, time, random, threading, os
from filelock import FileLock
from loguru import logger
from bs4 import BeautifulSoup
from bin.telegram_tools import telegram_tool


class japaneseasmr_tools():
    def __init__(self, lock=None):
        self.url = 'https://japaneseasmr.com'
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
        }
        self.result_json_path = './data/result.json'
        self.asmr_json_path = './data/japaneseasmr.logs'
        self.lock = lock
        # 判断文件是否存在
        if not os.path.exists(self.asmr_json_path):
            logger.warning('data/japaneseasmr.logs 文件不存在，已自动创建')
            json_data = r'{"rj_code_list": [], "data": {}}'
            open(self.asmr_json_path, 'w', encoding='utf-8').write(json_data)
            del json_data

    def get_content_info(self):
        print('待写')

    def message(self, threading_lock=None):
        with open(self.result_json_path, 'r', encoding='utf-8') as f:  # 设置文件锁
            with FileLock(self.result_json_path + '.lock'):
                json_content = json.loads(f.read())
                f.close()
        # json_content = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
        logger.info('最后检测时间为：%s' % json_content['japaneseasmr']['last_update_time'])
        last_update_time = datetime.datetime.strptime(json_content['japaneseasmr']['last_update_time'], '%Y-%m-%d')
        del json_content

        # 获取内容
        count = 1
        message = []  # 存放待发送的消息数据
        info_disc_list = []
        final_signal = True  # 查到有日期等于或小于 result.json的日期则变为false退出请求网页
        new_last_update_time = last_update_time
        # 开始获取内容并生成要发送的消息
        while final_signal:
            path = '/page/%d/' % count
            logger.info('开始请求网站 %s' % (self.url + path))
            req = requests.get(self.url + path, headers=self.headers)
            if req.status_code == 200:
                logger.debug('请求成功')
            else:
                logger.warning('请求失败，返回码 %d' % req.status_code)
            soup = BeautifulSoup(req.text, 'html.parser')
            del req

            # 获取当前页面所有内容摘要
            for info in soup.select('ul[class="site-archive-posts"] li'):
                upload_date = datetime.datetime.strptime(
                    info.select('p[class="entry-tagline"] time')[0].get('datetime'), '%Y-%m-%d')
                page_url = info.select('div[class="op-square"] a')[0].get('href').rstrip('/')
                cover_url = info.select('div[class="op-square"] a img')[0].get('data-src')
                title = info.select('p[style="text-align: center;"]')[0].get_text()
                cv = info.select('p[style="text-align: center;"]')[1].get_text()
                rj_code = info.select('p[style="text-align: center;"]')[2].get_text()

                if upload_date > last_update_time:
                    msg = '''[ ](%s)%s
%s
%s
%s''' % (cover_url, title, cv, rj_code, page_url)
                    message.append(msg)
                    info_disc_list.append(
                        {'cover': cover_url, 'title': title, 'cv': cv.split(':')[1].strip(),
                         'rj_code': rj_code.split(':')[1].strip(), 'page_url': page_url})
                    if upload_date > new_last_update_time:
                        new_last_update_time = upload_date
                else:
                    final_signal = False

            count += 1

        # 更新文件
        lock = FileLock(self.result_json_path + '.lock')
        with lock:
            json_content = json.loads(open(self.result_json_path, 'r', encoding='utf-8').read())
            json_content['japaneseasmr']['last_update_time'] = datetime.datetime.strftime(new_last_update_time,
                                                                                          '%Y-%m-%d')
            open(self.result_json_path, 'w', encoding='utf-8').write(json.dumps(json_content))
        del lock, json_content

        # 删除不用的函数释放内存
        del path, soup, info, upload_date, page_url, cover_url, title, cv, rj_code, \
            last_update_time, final_signal, count
        if len(info_disc_list) > 0:
            logger.info('本次共更新 %d 个作品' % len(info_disc_list))
            logger.debug(info_disc_list)
        else:
            logger.info('未查到作品更新')

        if len(info_disc_list) > 0:
            # 将收集到的信息保存至文件中
            file_data_json = json.loads(open(self.asmr_json_path, 'r', encoding='utf-8').read())
            for info in info_disc_list:
                if info['rj_code'] not in file_data_json['rj_code_list']:
                    file_data_json['rj_code_list'].append(info['rj_code'])
                    file_data_json['data'][info['rj_code']] = info
            open(self.asmr_json_path, 'w', encoding='utf-8').write(json.dumps(file_data_json))
            del file_data_json, info_disc_list, info

        # 发送telegram消息
        threading_lock.acquire()
        telegram_api = telegram_tool(self.lock)
        # telegram_send = threading.Thread(target=telegram_api.send, args=(message, 'markdown'))
        telegram_api.send(message=message, parse_mode='markdown')

        # if len(message) > 0:
        #     telegram_send.start()  # 子线程开始执行
        # else:
        #     logger.info('未查询到新内容')

        # if telegram_api.is_alive() is True:
        #     telegram_api.join()
        #     del telegram_api
        threading_lock.release()






