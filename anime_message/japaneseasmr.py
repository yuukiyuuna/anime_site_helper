# -*- coding=utf-8 -*-
import bs4, random, re, time
import requests, datetime, json, os, tqdm
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
        self.asmr_save_dir = r'E:\1download\tmp'
        self.lock = lock
        # 判断文件是否存在
        if not os.path.exists(self.asmr_json_path):
            logger.warning('./data/japaneseasmr.logs 文件不存在，已自动创建')
            json_data = r'{}'
            open(self.asmr_json_path, 'w', encoding='utf-8').write(json_data)
            del json_data

    def get_content_info(self, url):
        req = requests.get(url=url, headers=self.headers)
        soup = bs4.BeautifulSoup(req.text, features="html.parser")
        del req
        # 获得封面图片
        imgs_list = []
        for img_urls in soup.select('div[class="fotorama"] a'):
            if img_urls:
                if img_urls.get('href') not in imgs_list:
                    imgs_list.append(img_urls.get('href'))
            del img_urls
        logger.debug('搜索图片的结果 %s' % imgs_list)
        # 获取作品简介
        if soup.select('div[class="work_parts_area"] p'):
            content_info = str(soup.select('div[class="work_parts_area"] p')[0]).replace(r'<p>', '').replace(r'</p>',
                                                                                                             '').replace(
                r'<br/><br/>', '\n').replace(r'<br/>', '\n')
        else:
            content_info = ''
        # 获取作品音频
        ## 获取音频对应的名称
        name_list = []
        mp3_url_list = []
        for name in soup.select('div[id="audioplayer"] p'):
            if name:
                name_list.append(name.get_text())
        for mp3_url in soup.select('audio[controlslist="nodownload"] source'):
            if mp3_url:
                mp3_url_list.append(mp3_url.get('src'))
        del name_list[0], name, mp3_url
        if len(name_list) == len(mp3_url_list):
            mp3_url_info = {}
            for i in range(0, len(name_list)):
                mp3_url_info[name_list[i]] = mp3_url_list[i]
            logger.debug(name_list)
            logger.debug(mp3_url_list)
        else:
            logger.error('作品名称和作品链接数量不一致，请检查源网站html结构是否发生改变')
            logger.error(name_list)
            logger.error(mp3_url_list)
        del name_list, mp3_url_list, i
        # 获取tag
        tags = []
        for tag in soup.select('p[class="post-meta post-tags"] a'):
            # 判断是否存在中括号，中括号中一般为日文tag
            if re.search(r'【.*?】', tag.get_text()):
                logger.debug('识别到包含双文的tag： %s' %tag.get_text())
                japan_tag = re.findall(r'【(.*?)】', tag.get_text())[0].strip()
                englist_tag = tag.get_text().split('【')[0].strip()
                # 识别到两个tag，两个tag均过滤出来的才加入tags中
                if japan_tag and englist_tag:
                    tags.append({"tag_en": englist_tag, "tag_ja": japan_tag})
                    logger.debug('已成功识别英文tag： %s ，日文tag： %s' %(englist_tag, japan_tag))
                else:
                    logger.debug('识别英、日文tag失败，tag_en: %s, tag_ja: %s' %(englist_tag, japan_tag))
                    continue
                del japan_tag, englist_tag
            # 匹配到不包括中括号但为全英文及数字，放入英文tag
            elif re.search(r'^[a-zA-Z0-9/ ]+$', tag.get_text().strip()):
                logger.debug('识别到仅英文tag： %s' %tag.get_text())
                tags.append({"tag_en": tag.get_text().strip()})
            # 匹配到不包括中括号且不是全英文及数字，放入日文tag
            else:
                logger.debug('未匹配tag： %s ， 直接加入tag库中' % tag.get_text())
                tags.append({"tag_ja": tag.get_text().strip()})
            del tag
        logger.debug('搜索tag的结果 %s' %tags)
        del soup

        return {'imgs': imgs_list, 'mp3': mp3_url_info, 'content': content_info, 'tags': tags}

        # # 将结果写入文件
        # with FileLock(self.asmr_json_path + '.lock'):
        #     file_data_json = json.loads(open(self.asmr_json_path, 'r', encoding='utf-8').read())
        #     if file_data_json.get(rj_code):
        #         file_data_json[rj_code]['imgs'] = imgs_list
        #         file_data_json[rj_code]['mp3'] = mp3_url_info
        #         file_data_json[rj_code]['content'] = content_info
        #         file_data_json[rj_code]['tags'] = tags
        #
        #         open(self.asmr_json_path, 'w', encoding='utf-8').write(json.dumps(file_data_json))

    def video_download(self, url, referer, file_name, save_dir=None):
        if save_dir is None:
            file_full_path = os.path.join(os.getcwd(), file_name + '.mp3')
        else:
            file_full_path= os.path.join(save_dir, file_name + '.mp3')
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

    def message(self, threading_lock=None):
        with FileLock(self.result_json_path + '.lock'):         # 设置文件锁
            json_content = json.loads(open(self.result_json_path, 'r', encoding='utf-8').read())
        # json_content = json.loads(open('../data/result.json', 'r', encoding='utf-8').read())
        logger.info('读取配置文件成功， 最后检测时间为：%s' % json_content['japaneseasmr']['last_update_time'])
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
        with FileLock(self.result_json_path + '.lock'):
            json_content = json.loads(open(self.result_json_path, 'r', encoding='utf-8').read())
            json_content['japaneseasmr']['last_update_time'] = datetime.datetime.strftime(new_last_update_time,
                                                                                          '%Y-%m-%d')
            open(self.result_json_path, 'w', encoding='utf-8').write(json.dumps(json_content))
        del json_content

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
                if not file_data_json.get(info['rj_code']):
                    file_data_json[info['rj_code']] = info
            open(self.asmr_json_path, 'w', encoding='utf-8').write(json.dumps(file_data_json))
            del file_data_json, info_disc_list, info

        # 发送telegram消息
        self.lock.acquire()
        try:
            telegram_api = telegram_tool()
            message.reverse()       # 列表倒序
            # telegram_send = threading.Thread(target=telegram_api.send, args=(message, 'markdown'))
            telegram_api.send(message=message, parse_mode='markdown')
        except Exception as e:
            logger.error('japaneseasmr 发送消息失败')
            logger.error(e)
        self.lock.release()

    # 获取首页信息，只会单独调用该函数，功能和message函数重合
    def get_info_all(self, count=1, info_disc_list=[]):
        while True:
            path = '/page/%d/' % count

            try:
                logger.info('开始请求网站 %s' % (self.url + path))
                req = requests.get(self.url + path, headers=self.headers)
                if req.status_code == 200:
                    logger.debug('请求成功')
                elif req.status_code == 404:
                    break
                else:
                    logger.warning('请求失败，返回码 %d' % req.status_code)
                soup = BeautifulSoup(req.text, 'html.parser')
                del req

                # 获取当前页面所有内容摘要
                for info in soup.select('ul[class="site-archive-posts"] li'):
                    # 防止未知错误识别失败，失败则自动跳过
                    try:
                        page_url = info.select('div[class="op-square"] a')[0].get('href').rstrip('/')
                        cover_url = info.select('div[class="op-square"] a img')[0].get('data-src')
                        # 有的时候获取不到标题
                        if len(info.select('p[style="text-align: center;"]')) == 3:
                            title = info.select('p[style="text-align: center;"]')[0].get_text()
                            cv = info.select('p[style="text-align: center;"]')[1].get_text()
                            rj_code = info.select('p[style="text-align: center;"]')[2].get_text()
                        else:
                            title = info.select('h2[class="entry-title"]')[0].get_text()
                            cv = info.select('p[style="text-align: center;"]')[0].get_text()
                            rj_code = info.select('p[style="text-align: center;"]')[1].get_text()
                        result = self.get_content_info(url=page_url)
                        info_disc_list.append({'cover': cover_url, 'title': title, 'cv': cv.split(':')[1].strip(),
                                               'rj_code': rj_code.split(':')[1].strip(), 'page_url': page_url,
                                               'imgs': result['imgs'],
                                               'mp3': result['mp3'], 'content': result['content'],
                                               'tags': result['tags']})
                        del info, page_url, cover_url, title, cv, rj_code, result
                    except Exception as e:
                        logger.error(e)
                        logger.error('识别首页信息内容失败，跳过该作品')
                        logger.error(soup.select('ul[class="site-archive-posts"] li'))
                        continue

                # 结果写入文件
                with FileLock(self.asmr_json_path + '.lock'):
                    file_data_json = json.loads(open(self.asmr_json_path, 'r', encoding='utf-8').read())
                    while len(info_disc_list) > 0:
                        info2 = info_disc_list.pop()
                        file_data_json[info2['rj_code']] = info2

                    open(self.asmr_json_path, 'w', encoding='utf-8').write(json.dumps(file_data_json))

                count += 1
                time.sleep(random.randint(3, 5))

            except Exception as e:
                logger.error(e)
                logger.error('请求网页错误，准备重试 %s' %(self.url + path))
                time.sleep(random.randint(3, 5))
                self.get_info_all(count=count, info_disc_list=info_disc_list)

    # 根据文件下载所有
    def download_all(self):
        # 读取信息(目前为全量读取，后续优化)
        with FileLock(self.asmr_json_path + '.lock'):  # 设置文件锁
            json_content = json.loads(open(self.asmr_json_path, 'r', encoding='utf-8').read())

        # 判断声音存放的文件夹是否存在
        if not os.path.exists(self.asmr_save_dir):
            os.mkdir(self.asmr_save_dir)

        for rj_code, vaules in json_content.items():
            if not os.path.exists(os.path.join(self.asmr_save_dir, rj_code)):
                os.mkdir(os.path.join(self.asmr_save_dir, rj_code))

            # 因为有的mp3下载链接不止一个
            for mp3_name, mp3_url in vaules['mp3'].items():
                self.video_download(url=mp3_url, referer=vaules['page_url'], file_name=mp3_name,
                                    save_dir=os.path.join(self.asmr_save_dir, rj_code))






