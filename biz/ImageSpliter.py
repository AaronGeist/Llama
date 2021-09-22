import os
from math import floor

from PIL import Image


class ImageSplitter:
    line_blank_rate = 0.99

    @classmethod
    def split(cls, root, file):

        image_path = os.path.join(root, file)

        # load image
        try:
            im = Image.open(image_path)
        except Exception as e:
            return

        if im.height / im.width < 2:
            return

        print("processing: " + image_path)

        # im.show()

        # convert to grey mode & color mode
        im_grey = im.convert("L")
        im_color = im.convert("RGB")

        recommend_height = floor(im.width * 1.43)

        raw_pixel_matrix = im_grey.load()
        grey_pixel_matrix = im_grey.load()
        color_pixel_matrix = im_color.load()

        white_row_list = list()
        broken_line_row_list = list()

        last_row_white_ratio = 0
        for row in range(10, im.height):
            white_cnt = 0
            change_cnt = 0
            last_col_changed = False
            max_continuous_change_cnt = 0
            for col in range(0, im.width):
                # turn image into white & black pixel
                if grey_pixel_matrix[col, row] > 200:
                    grey_pixel_matrix[col, row] = 255
                    white_cnt += 1
                else:
                    grey_pixel_matrix[col, row] = 0

                if row > 0 and grey_pixel_matrix[col, row] != grey_pixel_matrix[col, row - 1]:
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
                for c in range(0, im.width):
                    color_pixel_matrix[c, row] = (0, 255, 0)  # green
            # elif abs(white_ratio - last_row_white_ratio) > 0.4:
            #     white_row_list.append((row, 1))
            #     for c in range(0, im.width):
            #         color_pixel_matrix[c, row] = (255, 0, 0)  # red

            elif max_continuous_change_cnt / im.width > 0.3:
                white_row_list.append((row, 1))
                for c in range(0, im.width):
                    color_pixel_matrix[c, row] = (0, 0, 255)  # blue

            last_row_white_ratio = white_ratio

        black_threshold = 30
        line_length_threshold = 100
        line_list = list()
        for col in range(0, im.width):
            start = -1
            for row in range(10, im.height):
                if col > 0 and raw_pixel_matrix[col, row] < black_threshold <= raw_pixel_matrix[col - 2, row]:
                    if start == -1:
                        start = row
                else:
                    if start != -1:
                        if row - start > line_length_threshold:
                            line_list.append((col, (start, row)))
                        start = -1

        for col in range(0, im.width):
            start = -1
            for row in range(10, im.height):
                if col < im.width - 2 and raw_pixel_matrix[col, row] < black_threshold <= raw_pixel_matrix[
                            col + 2, row]:
                    if start == -1:
                        start = row
                else:
                    if start != -1:
                        if row - start > line_length_threshold:
                            line_list.append((col, (start, row)))
                        start = -1

        # print(line_list)

        # merge lines
        merged_line_list = dict()
        for (col, (start, end)) in line_list:
            is_merged = False
            for i in range(1, 3):
                if col - i in merged_line_list:
                    lines = merged_line_list[col - i]
                    for line in lines:
                        start_old = line[0]
                        end_old = line[1]
                        if start <= start_old and end >= end_old:
                            merged_line_list[col - i].remove(line)
                            merged_line_list[col - i].append((start, end))
                            is_merged = True
                        elif start_old < start < end_old < end:
                            merged_line_list[col - i].remove(line)
                            merged_line_list[col - i].append((start_old, end))
                            is_merged = True
                        elif start < start_old < end < end_old:
                            merged_line_list[col - i].remove(line)
                            merged_line_list[col - i].append((start, end_old))
                            is_merged = True
                        elif start_old < start and end_old > end:
                            # skip add this line
                            is_merged = True
            if not is_merged:
                if col not in merged_line_list:
                    merged_line_list[col] = list()
                merged_line_list[col].append((start, end))

        # print(merged_line_list)

        white_line_list = list()

        for col in merged_line_list.keys():
            for item in merged_line_list[col]:
                start = item[0]
                end = item[1]
                white_row_list.append((start, 1))
                white_row_list.append((end, 1))

        row = 0
        while row < im.height - recommend_height:
            picked_row_candidate = -1
            for row_candidate_info in white_row_list:
                row_candidate = row_candidate_info[0]
                if abs((row_candidate - row) - recommend_height) < 30:
                    # print("picked: " + str(row_candidate))
                    picked_row_candidate = row_candidate
                    row = row_candidate
                    break
            if picked_row_candidate != -1:
                white_line_list.append(picked_row_candidate)
            else:
                row += recommend_height
                if row < im.height:
                    white_line_list.append(row)

        # print(white_line_list)

        for col in merged_line_list.keys():
            for item in merged_line_list[col]:
                start = item[0]
                end = item[1]
                for col in range(im.width):
                    color_pixel_matrix[col, start] = (0, 255, 255)
                    color_pixel_matrix[col, end] = (0, 255, 255)

        for col in merged_line_list.keys():
            for item in merged_line_list[col]:
                start = item[0]
                end = item[1]
                for row in range(start, end + 1):
                    color_pixel_matrix[col, row] = (0, 255, 255)
                    color_pixel_matrix[col + 1, row] = (0, 255, 255)
                    color_pixel_matrix[col - 1, row] = (0, 255, 255)

        # for row in white_line_list:
        #     for col in range(0, im.width):
        #         if row - 1 >= 0:
        #             color_pixel_matrix[col, row - 1] = (255, 0, 255)
        #         color_pixel_matrix[col, row] = (255, 0, 255)
        #         if row + 1 <= im.height:
        #             color_pixel_matrix[col, row + 1] = (255, 0, 255)

        # im_color.show()

        # print(white_line_list)
        pair = list()
        pair.append((0, white_line_list[0]))
        for index in range(0, len(white_line_list) - 1):
            pair.append((white_line_list[index], white_line_list[index + 1]))

        if 1.9 * recommend_height > im.height - white_line_list[-1] > recommend_height:
            pair.append((white_line_list[-1], white_line_list[-1] + recommend_height))
            pair.append((white_line_list[-1] + recommend_height, im.height))
        elif im.height - white_line_list[-1] > 200:
            pair.append((white_line_list[-1], im.height))

        file_name = file[:file.rfind(".")]

        index = 0
        for p in pair:
            new_im = im.crop((0, p[0], im.width, p[1]))
            # new_im.show()
            new_im.save(os.path.join(root, "%s_%03d_cut.jpg" % (file_name, index)))
            index += 1
        # im_color.save(os.path.join(root, "%s_preview.jpg" % file_name))

        os.remove(image_path)

    @classmethod
    def is_vertical_line_broken(cls, matrix, col, row):
        black_threshold = 30
        vertical_threshold = 200
        width_threshold = 2
        # if we have vertical line here
        for i in range(vertical_threshold):
            for j in range(width_threshold):
                if matrix[col - j, row - i] > black_threshold:
                    return False, 0, None

        # if broken on top
        broken_pixel = 0
        for j in range(width_threshold):
            if matrix[col - j, row - vertical_threshold - i] > black_threshold:
                print("break point: %s,%s,%s" % (str(col - j), str(row - vertical_threshold - i),
                                                 str(matrix[col - j, row - vertical_threshold - i])))
                broken_pixel += 1

        if broken_pixel == width_threshold:
            return True, row - vertical_threshold, "top"

        # if broken on bottom
        broken_pixel = 0
        for j in range(width_threshold):
            if matrix[col - j, row + 1] > black_threshold:
                print("break point: %s,%s,%s" % (str(col - j), str(row + 1 + i),
                                                 str(matrix[col - j, row + 1 + i])))
                broken_pixel += 1

        if broken_pixel == width_threshold:
            return True, row, "bottom"

        return False, None, None

    @classmethod
    def split_all(cls, folder_path):
        for root, dirs, files in os.walk(folder_path):

            # remove legacy files if exist
            # for file in files:
            #     image_path = os.path.join(root, file)
            #     if "cut" in image_path or "preview" in image_path:
            #         os.remove(image_path)

            for file in files:
                # 获取文件路径
                cls.split(root, file)


if __name__ == "__main__":
    ImageSplitter.split_all("/Users/shakazxx/Downloads/COMICS/电锯人/第96話 這個味道")
    # ImageSplitter.split_all("/Users/shakazxx/Downloads/COMICS/咒术回战")
