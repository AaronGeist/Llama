import os

from PIL import Image


class ImageSplitter:
    line_blank_rate = 0.99

    @classmethod
    def merge(cls, root_path, sub_folder):
        folder_path = os.path.join(root_path, sub_folder)

        image_path_list = list()
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                image_path_list.append(os.path.join(root, file))

        image_path_list.sort()

        # load image and convert to grey mode
        image_list = list()
        for image_path in image_path_list:
            try:
                im = Image.open(image_path)

                # if image too wide, split it
                if im.width > 1000 and im.width > im.height:
                    print("split " + image_path)
                    image_list.append(im.crop((0, 0, im.width / 2, im.height)))
                    image_list.append(im.crop((im.width / 2, 0, im.width, im.height)))
                else:
                    image_list.append(im)
            except Exception as e:
                print(e)

        im1 = image_list[0]
        image_list.pop(0)
        im1.save(os.path.join(root_path, sub_folder + ".pdf"), "PDF", resolution=100.0, save_all=True,
                 append_images=image_list)
        print("finish " + sub_folder)

    @classmethod
    def merge_all(cls, folder_path):
        for sub_folder in os.listdir(folder_path):
            if os.path.isdir(os.path.join(folder_path, sub_folder)):
                print(sub_folder)
                if os.path.exists(os.path.join(folder_path, sub_folder + ".pdf")):
                    print("skip " + sub_folder)
                    continue
                cls.merge(folder_path, sub_folder)


if __name__ == "__main__":
    ImageSplitter.merge_all("/Users/shakazxx/Downloads/COMICS/犬夜叉 全56卷 日文掃圖/new")
