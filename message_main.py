# -*- coding=utf-8 -*-
import time, threading
from loguru import logger
from anime_message.japaneseasmr import japaneseasmr_tools
from anime_message.yurifans import yurifans_tools
from anime_message.abema import abema_tools

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
        try:
            yurifans_tools(lock=lock)
            logger.info('yurifans 执行成功')
        except Exception as e:
            logger.error('yurifans 执行失败')
            logger.error(e)

        time.sleep(3600)

def abema_website(lock):
    while True:
        try:
            abema_tools(lock=lock)
            logger.info('abema 执行成功')
        except Exception as e:
            logger.error('abema 执行失败')
            logger.error(e)

        time.sleep(900)



if __name__ == '__main__':

    global_lock = threading.Lock()
    # japaneseasmr = threading.Thread(target=japaneseasmr_website, args=(global_lock,))
    # yurifans = threading.Thread(target=yurifans_website, args=(global_lock,))
    abema = threading.Thread(target=abema_website, args=(global_lock,))


    #
    #
    # japaneseasmr.start()
    # yurifans.start()
    abema.start()


    # yurifan.join()
    # japaneseasmr.join()
    abema.join()
