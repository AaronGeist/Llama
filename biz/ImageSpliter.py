import os

from PIL import Image


class ImageSplitter:
    line_blank_rate = 0.99

    @classmethod
    def split(cls, root, file):

        image_path = os.path.join(root, file)

        # load image and convert to grey mode
        try:
            im = Image.open(image_path).convert("1")
        except Exception as e:
            return

        if im.height / im.width < 3:
            return

        print("processing: " + image_path)

        # im.show()

        recommend_height = im.width * 1.4
        # print(recommend_height)

        pixel_matrix = im.load()

        white_row_list = list()
        # turn grey pixel into white
        last_row_ratio = 0
        for row in range(0, im.height):
            cnt = 0
            for col in range(0, im.width):
                if pixel_matrix[col, row] != 0:
                    pixel_matrix[col, row] = 255
                    cnt += 1

            ratio = cnt / im.width
            if ratio > cls.line_blank_rate:
                white_row_list.append((row, ratio))
                # print("hit " + str(row))
            elif abs(ratio - last_row_ratio) > 0.9:
                white_row_list.append((row, ratio))
                # print("possible " + str(row))

        # print(white_row_list)

        white_line_list = list()
        last_candidate = 0
        last_ratio = 0
        for row in white_row_list:
            if row[0] > (im.height - 100):
                continue

            if row[0] - last_candidate > recommend_height:
                white_line_list.append(row[0])
                last_candidate = row[0]
                last_ratio = row[1]
            elif row[0] - last_candidate < 30 and row[1] > last_ratio and last_candidate != 0:
                white_line_list.remove(last_candidate)
                white_line_list.append(row[0])
                last_candidate = row[0]
                last_ratio = row[1]

        if len(white_line_list) == 0:
            print(">>>>>  Cannot split " + image_path)
            return

        # print(white_line_list)
        pair = list()
        pair.append((0, white_line_list[0]))
        for index in range(0, len(white_line_list) - 1):
            pair.append((white_line_list[index], white_line_list[index + 1]))
        pair.append((white_line_list[-1], im.height))

        file_name = file[:file.rfind(".")]

        index = 0
        for p in pair:
            new_im = im.crop((0, p[0], im.width, p[1]))
            # new_im.show()
            new_im.save(os.path.join(root, "%s_%03d.jpg" % (file_name, index)))
            index += 1

        os.remove(image_path)

    @classmethod
    def split_all(cls, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 获取文件路径
                cls.split(root, file)
                # input("test")


if __name__ == "__main__":
    ImageSplitter.split_all("/Users/shakazxx/workspace/github/Llama/biz/output/排球少年!!")
