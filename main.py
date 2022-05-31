# -*- coding=utf-8 -*-

import json
from bin.yurifan import yurifan
from bin.copymanga import copymanga


def all_conf():
    return json.loads(open('config.json', 'r').read())


if __name__ == '__main__':

    # for i in all_conf()['website']['yurifans']:
    #     a = yurifan()
    #     a.sgin(user=i['user'], passwd=i['password'])
    #     del a


    # a = yurifan()
    # a.download_page_pic(r'https://yuri.website/47975/')


    a = copymanga()
    a.download(url=r'https://www.copymanga.org/comic/kuangduzhiyuanjia', output_dir=r'F:\linshi')



