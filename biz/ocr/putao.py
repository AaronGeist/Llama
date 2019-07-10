import os

from PIL import Image


class PuTaoCaptchaParser:
    @classmethod
    def analyze(cls, image_path):

        # load image and convert to grey mode
        im = Image.open(image_path).convert("L")

        im_cropped = im.crop((10, 9, 54, 19))

        pixel_matrix = im_cropped.load()

        # turn grey pixel into white
        for col in range(0, im_cropped.height):
            for row in range(0, im_cropped.width):
                if pixel_matrix[row, col] != 0:
                    pixel_matrix[row, col] = 255

        # crop image into 5 parts, like    1 + 2 * 3
        pos_list = [(0, 0, 8, 10), (9, 0, 16, 10), (18, 0, 26, 10), (27, 0, 34, 10), (36, 0, 44, 10)]
        expression = ""
        for pos in pos_list:
            expression += cls.match(im_cropped.crop(pos))

        # calculate expression
        return eval(expression)

    # find image with maximum same pixel and return image name
    @classmethod
    def match(cls, image):
        root_path = "ocr/resources/putao/"
        image_name_dict = dict()
        for root, dirs, files in os.walk(root_path):
            for file in files:
                image_name_dict[file[0:1]] = Image.open(os.path.join(root, file)).convert("L").load()

        pixel_matrix = image.load()

        max_score = 0
        match_image_name = ""
        for image_name in image_name_dict:
            target_image = image_name_dict[image_name]
            score = 0
            for col in range(0, image.height):
                for row in range(0, image.width):
                    if pixel_matrix[row, col] == target_image[row, col]:
                        score += 1

            # record max score and corresponding image name
            if score > max_score:
                max_score = score
                match_image_name = image_name

        return match_image_name
