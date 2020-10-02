import os

import re
from PIL import Image
from shutil import move


class ImageSplitter:
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
    def merge(cls, root_path, sub_folder, reverse=True):
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

        im1 = image_list[0]
        image_list.pop(0)
        im1.save(os.path.join(root_path, sub_folder + ".pdf"), "PDF", resolution=100.0, save_all=True,
                 append_images=image_list)
        print("finish " + sub_folder)

    @classmethod
    def merge_all(cls, folder_path, reverse=True):
        for sub_folder in os.listdir(folder_path):
            if os.path.isdir(os.path.join(folder_path, sub_folder)):
                print(sub_folder)
                if os.path.exists(os.path.join(folder_path, sub_folder + ".pdf")):
                    print("skip " + sub_folder)
                    continue
                cls.merge(folder_path, sub_folder, reverse)


if __name__ == "__main__":
    ImageSplitter.merge_all("/Users/shakazxx/Downloads/COMICS/黑执事", reverse=True)
