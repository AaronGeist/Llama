import os

import re
import shutil

from shutil import copytree


class Reorg:
    folder_size = 10

    root_folder = "archive/"

    @classmethod
    def process(cls, folder_path):

        id_map = dict()
        new_id_map = dict()
        id_list = list()

        sub_folders = os.listdir(folder_path)
        if len(sub_folders) < 40:
            print("Total %d, skip re-organization!" % len(sub_folders))
            return

        for sub_folder in sub_folders:
            if os.path.isdir(os.path.join(folder_path, sub_folder)):
                # print(sub_folder)
                id = re.search(".+?(\d*(.\d)*).+?", sub_folder).group(1)
                if id == "":
                    print(">>>>>>>>>>>>>>>>> cannot find id " + sub_folder)
                    continue
                else:
                    id = int(id)
                    id_map[id] = sub_folder
                    new_id_map[id] = sub_folder.replace(str(id), str(id).zfill(3))
                    id_list.append(id)

        id_list.sort()

        if not os.path.exists(cls.root_folder):
            os.makedirs(cls.root_folder, exist_ok=True)
        else:
            shutil.rmtree(cls.root_folder)

        start = 0
        end = 0
        cnt = 0
        ids = list()
        size = 1
        if len(id_list) >= 100:
            size = 3
        elif len(id_list) >= 10:
            size = 2

        for id in id_list:
            ids.append(id)
            if cnt == 0:
                start = id

            if cnt == cls.folder_size - 1:
                end = id
                # mkdir and copy
                print("%s - %s" % (start, end))
                folder = cls.root_folder + "第%s-%s话" % (str(start).zfill(size), str(end).zfill(size))
                if not os.path.exists(folder):
                    os.makedirs(folder, exist_ok=True)

                for inner_id in ids:
                    copytree(os.path.join(folder_path, id_map[inner_id]), os.path.join(folder, new_id_map[inner_id]))

                # reset cnt
                cnt = 0
                ids.clear()
                continue

            cnt += 1

        left_size = len(id_list) % cls.folder_size
        if left_size > 0:
            end = id_list[-1]
            print("Creating %s - %s" % (start, end))
            folder = cls.root_folder + "第%s-%s话" % (str(start).zfill(size), str(end).zfill(size))
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

            for inner_id in ids:
                copytree(os.path.join(folder_path, id_map[inner_id]), os.path.join(folder, new_id_map[inner_id]))


if __name__ == "__main__":
    Reorg.process("/Users/shakazxx/workspace/github/Llama/biz/output/龍珠超")
