# -*- coding=utf-8 -*-

import json
from bin.yurifan import yurifan


def all_conf():
    return json.loads(open('config.json', 'r').read())


if __name__ == '__main__':

    # for i in all_conf()['website']['yurifans']:
    #     a = yurifan()
    #     a.sgin(user=i['user'], passwd=i['password'])
    #     del a


    a = yurifan()
    a.download_page_pic(r'https://yuri.website/63118/')




