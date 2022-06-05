# -*- coding=utf-8 -*-

import os
import cv2

def pic_split(file_path, output_file_path):
    if not os.path.exists(output_file_path):
        os.mkdir(output_file_path)
    for root, dir, files in os.walk(file_path):
        if len(files) == 0:
            continue

        output_dir_path = root.replace(file_path, output_file_path)
        for file in files:
            os.chdir(root)  # cv2不能读取有中文路径，不能以绝对路径处理文件
            if file.endswith(r'jpg') or file.endswith(r'jpeg') or file.endswith(r'png'):
                output_file_name_list = file.split('.')
                if not os.path.exists(output_dir_path):
                    os.mkdir(output_dir_path)

                # 读取图片
                img = cv2.imread(file)

                high = img.shape[0]
                wight = img.shape[1]

                # 日本漫画基本右边(part2)为第一页
                part1 = img[0:high, 0:wight // 2]
                part2 = img[0:high, wight // 2:wight]

                cv2.waitKey()
                os.chdir(output_dir_path)
                cv2.imwrite(str(int(output_file_name_list[0]) * 2 + 1).zfill(4) + '.' + output_file_name_list[1], part1)
                cv2.imwrite(str(int(output_file_name_list[0]) * 2).zfill(4) + '.' + output_file_name_list[1], part2)





pic_split(r'F:\linshi\test', r'F:\linshi\test_new')