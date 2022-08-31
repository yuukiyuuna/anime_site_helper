# # -*- coding=utf-8 -*-
import os
import zipfile

def zip_file(src_dir, save_name='default', save_dir='./'):
    '''
    压缩文件夹下所有文件及文件夹
    默认压缩文件名：文件夹名
    默认压缩文件路径：文件夹上层目录
    '''
    if save_name == 'default':
        zip_name = os.path.join(save_dir, src_dir + '.zip')
    else:
        if save_name is None or save_name == '':
            zip_name = os.path.join(save_dir, src_dir + '.zip')
        else:
            zip_name = os.path.join(save_dir, save_name + '.zip')
    print(zip_name)

    z = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
    for dirpath, dirnames, filenames in os.walk(src_dir):
        fpath = dirpath.replace(src_dir, '')
        fpath = fpath and fpath + os.sep or ''
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), fpath + filename)
    z.close()
    return True



dir = r'F:\linshi\dianjuren'

files = os.listdir(dir)

for file in files:
    zip_file(os.path.join(dir, file), save_name=file, save_dir='E:\临时\电锯人')
    # os.rename(file + r'.zip', file + r'.cbz')


