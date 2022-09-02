# -*- coding=utf-8 -*-
import time, threading
from loguru import logger
from anime_message.japaneseasmr import japaneseasmr_tools

def japaneseasmr_website(lock):
    try:
        japaneseasmr = japaneseasmr_tools(lock=lock)
        japaneseasmr.message()
        logger.info('japaneseasmr执行成功')
    except Exception as e:
        logger.error(e)
    time.sleep(86400)




if __name__ == '__main__':

    global_lock = threading.Lock()
    japaneseasmr = threading.Thread(target=japaneseasmr_website, args=(global_lock,))


    japaneseasmr.start()
    japaneseasmr.join()