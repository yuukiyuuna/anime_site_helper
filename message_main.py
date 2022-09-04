# -*- coding=utf-8 -*-
import time, threading
from loguru import logger
from anime_message.japaneseasmr import japaneseasmr_tools
from anime_message.yurifans import yurifans

def japaneseasmr_website(lock):
    while True:
        try:
            japaneseasmr = japaneseasmr_tools(lock=lock)
            japaneseasmr.message()
            logger.info('japaneseasmr 执行成功')
            del japaneseasmr
        except Exception as e:
            logger.error('japaneseasmr 执行失败')
            logger.error(e)

        time.sleep(86400)

def yurifans_website(lock):
    while True:
        # try:
        #     yurifans(lock=lock)
        #     logger.info('yurifans 执行成功')
        # except Exception as e:
        #     logger.error('yurifans 执行失败')
        #     logger.error(e)

        yurifans(lock=lock)
        time.sleep(3600)



if __name__ == '__main__':

    global_lock = threading.Lock()
    # japaneseasmr = threading.Thread(target=japaneseasmr_website, args=(global_lock,))

    yurifan = threading.Thread(target=yurifans_website, args=(global_lock,))

    #
    #
    # japaneseasmr.start()
    yurifan.start()

    yurifan.join()
    # japaneseasmr.join()