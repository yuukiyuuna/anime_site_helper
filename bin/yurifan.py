# -*- coding=utf-8 -*-
import os, json, time
import re

import requests
from loguru import logger
from bin.yurifan_tools import yurifan_online_manga_tools


###################################
#  网站链接：https://yuri.website/  #
###################################


class yurifan:
    def __init__(self):
        self.yurifan_url = r'https://yuri.website/'
        self.proxies = {
            'http': json.loads(open('config.json', 'r').read())['proxy'],
            'https': json.loads(open('config.json', 'r').read())['proxy']
        }

        self.req_s = requests.session()
        self.authorization = None


    # 各种请求中所需要用到的头
    def requests_headers(self, referer=None):
        if referer is None:
            referer = self.yurifan_url

        headers_disc = {}
        # 无cookie登入
        headers_disc['login_headers'] = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "referer": referer,
            "origin": "https://yuri.website"
        }
        # 登入后使用的headers
        headers_disc['auth_headers'] = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "referer": referer,
            "origin": "https://yuri.website",
            "accept": "application/json, text/plain, */*",
            "authorization": self.authorization
        }

        return headers_disc


    # 登入（获取authorization）
    def login(self, user, passwd):
        path = r'wp-json/jwt-auth/v1/token'
        url = self.yurifan_url + path
        form_data = {
            "username": user,
            "password": passwd
        }

        logger.debug('开始请求地址：%s ,form_data为：%s' %(url, str(form_data)))
        req = self.req_s.post(url, headers=self.requests_headers()['login_headers'], data=form_data)

        if req.status_code == 200:
            logger.info('登入成功，请求返回码： %d' % req.status_code)
        else:
            logger.warning('登入失败，请求返回码： %d' % req.status_code)
        logger.debug('返回消息： %s' % req.text)

        # 获取cookie中的token值，用于构建获取用户信息的请求
        self.authorization = 'Bearer ' + req.cookies['b2_token']


    # 签到
    def sgin(self, user, passwd):

        logger.info('开始执行用户 %s 的签到程序' % user)
        # 执行签到程序前先执行登入程序，是否执行登入程序则判断authorization是否为空
        if self.authorization is None:
            self.login(user=user, passwd=passwd)

        # 刷新任务列表（在登入过程中执行的）
        get_mession_url = r'https://yuri.website/wp-json/b2/v1/getUserMission'
        data = {"cournt": 6, "paged": 1}
        req = self.req_s.post(get_mession_url, headers=self.requests_headers(referer='https://yuri.website/task')['auth_headers'], data=data)
        logger.debug('开始请求地址：%s ,form_data为：%s' % (get_mession_url, str(data)))
        logger.debug('返回消息： %s' % str(req.text))


        path = r'wp-json/b2/v1/userMission'
        sgin_url = self.yurifan_url + path
        form_data = None

        logger.debug('开始请求地址：%s ,form_data为：%s' % (sgin_url, 'None'))
        req = self.req_s.post(sgin_url, headers=self.requests_headers(referer='https://yuri.website/task')['auth_headers'],
                              data=form_data)

        if req.status_code == 200:
            try:
                json_data = json.loads(req.content)
                logger.info('今日签到成功，今日获取积分为：%d' % json_data['credit'])
            except Exception:
                logger.warning('签到失败，今日已经签到')
                logger.debug('返回消息： %s' % req.text)
        else:
            logger.warning('签到失败，请求返回码： %d' % req.status_code)
            logger.debug('返回消息： %s' % req.text)


    # 下载在线观看的漫画
    def download_page_pic(self, url):
        yurifan_tools = yurifan_online_manga_tools()

        # 为规避漫画名带特殊字符等无法创建文件夹的因素
        # 文件夹名统一用yurifan中的数字来创建，会在文件夹中创建title.txt将漫画名写入
        dir_title = url.replace(self.yurifan_url, '').replace('/', '')

        # 获取该网页的源码
        req = self.req_s.get(url, headers=self.requests_headers()['login_headers'])

        page_info = yurifan_tools.pic_info(req.text)
        # 调用tools工具，下载整本漫画
        if page_info['download_mode'] == 1:      # 为不需要积分的在线漫画
            # 创建文件夹
            if not os.path.exists(dir_title):
                os.mkdir(dir_title)
                open(os.path.join(dir_title, 'info.txt'), 'w', encoding='GBK').write('标题：' + page_info['title'])
                # open(os.path.join(dir_title, 'info.txt'), 'a', encoding='GBK').write('标签：' + page_info['tags'])


                # 下载图片
                # 类型为1，包不含分集的下载
                if page_info['pictures']['mode'] == 1:
                    page_count = 1
                    for pic_url in yurifan_tools.pic_info(req.text)['pictures']['data']:
                        req = self.req_s.get(pic_url, headers=self.requests_headers(referer=url)['login_headers'])
                        logger.info('正在下载第%d张图片' %page_count)
                        open(os.path.join(dir_title, str(page_count).zfill(3)) + '.jpg', 'wb').write(req.content)

                        page_count += 1

                        time.sleep(2)
                elif page_info['pictures']['mode'] == 2:
                    for i in yurifan_tools.pic_info(req.text)['pictures']['data']:
                        page_count = 1
                        # 创建分集文件夹
                        if not os.path.exists(os.path.join(dir_title, i[0])):
                            os.mkdir(os.path.join(dir_title, i[0]))
                        for ii in i:
                            if not ii.startswith('h'):
                                continue
                            req = self.req_s.get(ii, headers=self.requests_headers(referer=url)['login_headers'])
                            logger.info('正在下载%s的第%d张图片' %(i[0], page_count))
                            open(os.path.join(os.path.join(dir_title, i[0]), str(page_count).zfill(3)) + '.jpg', 'wb').write(req.content)

                            page_count += 1

                            time.sleep(2)

        elif page_info['download_mode'] == 2:
            # 遇到隐藏文件先登入，查看是否已经购买
            # 登入直接读第一个配置
            user_conf = json.loads(open('config.json', 'r').read())['website']['yurifans'][0]
            self.login(user=user_conf['user'], passwd=user_conf['password'])

            # 创建文件夹
            if not os.path.exists(dir_title):
                os.mkdir(dir_title)
                open(os.path.join(dir_title, 'info.txt'), 'w', encoding='utf-8').write('标题：' + page_info['title'])

            # 下载图片
            # 类型为1，包不含分集的下载
            if page_info['pictures']['mode'] == 1:
                pics = []
                for pic_url in page_info['pictures']['data']:
                    pics.append(pic_url)
                logger.debug('未隐藏部分：%s' % str(pics))

                # 获取隐藏内容的图片的url，并加入到总列表中
                data = self.get_hidden_content(url)
                if data['mode'] == 1:
                    for pic_url in data['data']:
                        pics.append(pic_url)
                    logger.debug('总下载列表：%s' % str(pics))

                page_count = 1
                for pic_url in pics:
                    req = self.req_s.get(pic_url, headers=self.requests_headers(referer=url)['login_headers'])
                    logger.info('正在下载第%d张图片' % page_count)
                    logger.debug('第%d张图片url为：%s' %(page_count, req.request.url))
                    open(os.path.join(dir_title, str(page_count).zfill(3)) + '.jpg', 'wb').write(req.content)

                    page_count += 1

                    time.sleep(2)
            elif page_info['pictures']['mode'] == 2:
                pics = []
                for pic_url in page_info['pictures']['data']:
                    pics.append(pic_url)

                # 获取隐藏内容的图片的url，并加入到总列表中
                data = self.get_hidden_content(url)
                if data['mode'] == 2:
                    for pic_url in data['data']:
                        pics.append(pic_url)

                for pic_urls in pics:
                    page_count = 1
                    # 创建分集文件夹
                    if not os.path.exists(os.path.join(dir_title, pic_urls[0])):
                        os.mkdir(os.path.join(dir_title, pic_urls[0]))
                    for pic_url in pic_urls:
                        if not pic_url.startswith('h'):
                            continue
                        logger.info('正在下载%s的第%d张图片' %(pic_urls[0], page_count))
                        req = self.req_s.get(pic_url, headers=self.requests_headers(referer=url)['login_headers'])
                        open(os.path.join(os.path.join(dir_title, pic_urls[0]), str(page_count).zfill(3)) + '.jpg', 'wb').write(req.content)

                        page_count += 1

                        time.sleep(2)


    # 支付积分显示隐藏部分，包含创建订单，支付，查询三个模块
    def pay(self, url, form_data):
        # # 检查是否已经登入
        # if self.authorization is None:
        #     self.login(user, passwd)

        order_id = self.pay_build_order(url, form_data)
        time.sleep(1)
        self.pay_credit_pay(url, order_id)
        time.sleep(1)
        self.pay_pay_check(url, order_id)


    def pay_build_order(self, page_url, form_data):
        path = r'wp-json/b2/v1/buildOrder'
        url = self.yurifan_url + path
        form_data['pay_type'] = 'credit'
        form_data['order_price'] = 1
        req = self.req_s.post(url, headers=self.requests_headers(page_url)['auth_headers'], data=form_data)
        if req.status_code == 200:
            order_id = req.content.decode('utf-8')


        return str(order_id).replace('"', '')

    def pay_credit_pay(self, page_url, order_id):
        path = r'wp-json/b2/v1/creditPay'
        url = self.yurifan_url + path

        form_data = {
            "order_id": order_id
        }
        req = self.req_s.post(url, headers=self.requests_headers(page_url)['auth_headers'], data=form_data)

        if req.status_code == 200:
            try:
                if json.loads(req.text.encode('utf-8'))['data']['status']:
                    logger.warning('支付失败，请重试')
            except Exception as e:
                logger.debug('支付成功')



    def pay_pay_check(self, page_url, order_id):
        path = r'wp-json/b2/v1/payCheck'
        url = self.yurifan_url + path
        form_data = {
            "order_id": order_id
        }
        req = self.req_s.post(url, headers=self.requests_headers(page_url)['auth_headers'], data=form_data)
        if req.status_code == 200:
            if json.loads(req.text)['status'] == 'success':
                logger.info('支付积分购买完成')


    # 获取隐藏内容文本
    def get_hidden_content(self, page_url):
        path = r'wp-json/b2/v1/getHiddenContent'
        url = self.yurifan_url + path

        form_data = {
            "id": page_url.replace(self.yurifan_url, '').replace('/', ''),
            "order_id": 'null'
        }
        req = self.req_s.post(url, headers=self.requests_headers()['auth_headers'], data=form_data)

        # 获取隐藏内容(如果能获取支付信息，则未购买，走购买流程，否则为已购买)
        try:
            data = json.loads(re.findall('data-pay=\'(.*?)\'', str(req.text).replace(r'\"', '"').replace('\\\\', '\\'))[0])
            self.pay(url=url, form_data=data)
            self.get_hidden_content(page_url)

        except Exception:
            logger.info('该内容已经购买过')
            yurifan_tools = yurifan_online_manga_tools()
            data = yurifan_tools.pictuers_split(str(req.text).replace(r'\"', '"').replace(r'\/', '/')
                                                .replace(r'\\', '\\').encode('utf-8').decode('unicode_escape'))
            return data


