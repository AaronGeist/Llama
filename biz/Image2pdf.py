import os

import re
from math import floor

from PIL import Image
from shutil import move

from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


class Image2pdf:
    line_blank_rate = 0.99

    @classmethod
    def sort_key(cls, s):
        # 排序关键字匹配
        # 匹配开头数字序号
        if s:
            try:
                c = re.findall('^\d+', s)
            except:
                c = -1
            return int(c)

    @classmethod
    def merge(cls, root_path, sub_folder, reverse=True, resize=1.0):
        folder_path = os.path.join(root_path, sub_folder)

        image_path_list = list()
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                try:
                    if len(file.split("_")[0]) == 1 and int(file.split("_")[0]) < 10:
                        move(os.path.join(root, file), os.path.join(root, "00" + file))
                        file = "00" + file
                    if len(file.split("_")[0]) == 2 and 10 <= int(file.split("_")[0]) < 100:
                        move(os.path.join(root, file), os.path.join(root, "0" + file))
                        file = "0" + file
                except:
                    pass
                image_path_list.append(os.path.join(root, file))

        image_path_list.sort()

        # load image and convert to grey mode
        image_list = list()
        for image_path in image_path_list:
            try:
                im = Image.open(image_path).convert("RGB")

                # if image too wide, split it
                if im.width > 1000 and im.width > im.height:
                    print("split " + image_path)
                    if reverse:
                        image_list.append(im.crop((im.width / 2, 0, im.width, im.height)))
                        image_list.append(im.crop((0, 0, im.width / 2, im.height)))
                    else:
                        image_list.append(im.crop((0, 0, im.width / 2, im.height)))
                        image_list.append(im.crop((im.width / 2, 0, im.width, im.height)))
                else:
                    image_list.append(im)
            except Exception as e:
                print(image_path)
                print(e)

        # compression required
        if resize < 1.0:
            new_image_list = list()
            for image in image_list:
                new_image_list.append(
                    image.resize((floor(image.width * resize), floor(image.height * resize)), Image.ANTIALIAS))

            image_list = new_image_list

        if len(image_list) == 0:
            print(folder_path)

        im1 = image_list[0]
        image_list.pop(0)
        im1.save(os.path.join(root_path, sub_folder + ".pdf"), "PDF", resolution=100.0, save_all=True,
                 append_images=image_list)
        print("finish " + sub_folder)

    @classmethod
    def merge_all(cls, folder_path="archive", reverse=True, resize=1.0, split_output=True):
        sub_folder_cnt = 0

        if split_output:
            for sub_folder in os.listdir(folder_path):
                if os.path.isdir(os.path.join(folder_path, sub_folder)):
                    sub_folder_cnt += 1
                    print(sub_folder)
                    if os.path.exists(os.path.join(folder_path, sub_folder + ".pdf")):
                        print("skip " + sub_folder)
                        continue
                    cls.merge(folder_path, sub_folder, reverse, resize)

        if sub_folder_cnt == 0:
            pos = folder_path.rfind("/")
            root = folder_path[:pos]
            sub_folder = folder_path[pos + 1:]
            cls.merge(root, sub_folder, reverse, resize)


if __name__ == "__main__":
    Image2pdf.merge_all("/Users/shakazxx/Downloads/COMICS/电锯人/第96話 這個味道", reverse=True, split_output=False)
    # Image2pdf.merge_all("archive_2", reverse=True)
