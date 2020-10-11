import os

from PIL import Image


class ImageSplitter:
    line_blank_rate = 0.99

    @classmethod
    def split(cls, root, file):

        image_path = os.path.join(root, file)

        # load image and convert to grey mode
        try:
            im = Image.open(image_path).convert("L")
        except Exception as e:
            return

        if im.height / im.width < 3:
            return

        print("processing: " + image_path)

        # im.show()

        recommend_height = im.width * 1.2
        max_height = im.width * 1.5

        # print(recommend_height)

        pixel_matrix = im.load()
        color_im = im.convert("RGB")
        color_pixel_matrix = color_im.load()

        white_row_list = list()
        # turn grey pixel into white
        last_row_white_ratio = 0
        for row in range(0, im.height):
            white_cnt = 0
            change_cnt = 0
            last_col_changed = False
            max_continuous_change_cnt = 0
            for col in range(0, im.width):
                if pixel_matrix[col, row] > 200:
                    pixel_matrix[col, row] = 255
                    # color_pixel_matrix[col, row] = (255, 255, 255)
                    white_cnt += 1
                else:
                    pixel_matrix[col, row] = 0
                    # color_pixel_matrix[col, row] = (0, 0, 0)

                if row > 0 and pixel_matrix[col, row] != pixel_matrix[col, row - 1]:
                    if last_col_changed is False:
                        last_col_changed = True
                    change_cnt += 1
                else:
                    if change_cnt > 0:
                        max_continuous_change_cnt = max(max_continuous_change_cnt, change_cnt)
                    last_col_changed = False
                    change_cnt = 0

            white_ratio = white_cnt / im.width
            if white_ratio > cls.line_blank_rate:
                white_row_list.append((row, white_ratio))
                # print("hit " + str(row))
                for c in range(0, im.width):
                    color_pixel_matrix[c, row] = (0, 255, 0)
            elif abs(white_ratio - last_row_white_ratio) > 0.4:
                white_row_list.append((row, 1))
                print("possible " + str(row))
                for c in range(0, im.width):
                    color_pixel_matrix[c, row] = (255, 0, 0)

            elif max_continuous_change_cnt / im.width > 0.3:
                white_row_list.append((row, 1))
                for c in range(0, im.width):
                    color_pixel_matrix[c, row] = (0, 0, 255)

            last_row_white_ratio = white_ratio

        # color_im.show()
        # im.show()
        # print(white_row_list)

        white_line_list = list()
        last_candidate = 0
        last_ratio = 0
        for row in white_row_list:
            if row[0] > (im.height - 100):
                continue

            if row[0] - last_candidate > recommend_height:
                if row[0] - last_candidate > max_height:
                    print("too long page: " + str(row[0] - last_candidate))
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

        for row in white_line_list:
            for col in range(0, im.width):
                color_pixel_matrix[col, row] = (255, 0, 255)

        color_im.show()

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

            # os.remove(image_path)

    @classmethod
    def split_all(cls, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 获取文件路径
                cls.split(root, file)
                # input("test")


if __name__ == "__main__":
    ImageSplitter.split_all("/Users/shakazxx/Downloads/COMICS/電鋸人/第86話 約會電鋸")
