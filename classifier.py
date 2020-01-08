# -*- coding:utf-8 -*-
"""
@Date: 2019-08-16
@Author: Tiko
@Email: twx@bupt.edu.cn
"""
import re
import sys
import os
import chardet
from tqdm import trange


class classifier:
    def __init__(self):
        self.plat = os.name
        self.screen_cleaner()
        print("\n【欢迎来到Tiko分类器 v1.4】\n")
        print("\t代码整理")
        input("\n--->按下回车键开始--->")
        self.screen_cleaner()
        self.data = {}
        self.pattern = []
        self.classes = {}
        self.dir = ""

    def menu(self):
        print("\n输入数字并回车进入相应功能")
        print("1: 加载数据文件(tsv)")
        print("2: 加载正则表达式文件(tsv)")
        print("3: 开始进行手动分类")
        print("4: 开始进行自动分类(显示分类信息)")
        print("5: 开始进行自动分类(不显示分类信息)")
        print("6: 将已分类数据保存至文件(tsv)")
        print("0: 退出系统")

    def classifier_closer(self):
        if self.classes:
            if not self.re_confirm("还有数据尚未保存，是否确认退出?"):
                pass
        print("\n【退出Tiko分类器】\n")
        sys.exit()

    def screen_cleaner(self):
        """
        根据平台进行清屏操作
        """
        if self.plat is 'nt':
            os.system('cls')
        else:
            os.system("clear")

    def re_confirm(self, msg):
        c = input("\n[!]" + msg + "[Y/N]:\n")
        confirm = True if c in "yY" else False
        return confirm

    def get_file_encoding(self, file):
        """
        辨别文件编码方式
        :param file: 文件路径
        :return: 文件编码方式
        """
        with open(file, 'rb') as f:
            return chardet.detect(f.read())['encoding']

    def data_file_loader(self):
        """
        将数据读取到list中，需要为tsv格式，headers会被当成数据
        :return: dict(info=文件信息组成的dict，list=格式化处理后的数据)
        """
        self.data = {"info": {}}
        file_path = input("请输入本地文件路径：")
        print()
        print("【正在获取文件信息，请稍候...】")
        info = self.get_file_info(file_path)
        self.data['info'] = info
        if info['found']:
            print("[+]文件所在文件夹：%s" % info['file_dir'])
            print("[+]文件名：%s" % info['file_name'])
            print("[+]文件格式：%s" % info['file_ex'][1:])
            print("[+]是否存在历史信息：%s" % ("是" if info['history'] > 0 else "否"))
            print("[+]文件编码信息：%s" % info['encoding'])
            with open(file_path, "r", encoding=info['encoding']) as f:
                f_lines = f.readlines()
                f_list = []
                for line in f_lines:
                    if info['file_ex'] == ".tsv":
                        line_cuted = line.split('\t')
                        list_tag = line_cuted[0].split(',')[:-1]
                    else:
                        line_cuted = line.split(',')
                        list_tag = line_cuted[:-1]
                    text = "".join(line_cuted[-1].split())
                    f_list.append([list_tag, text])

                pre_len = len(f_list)
                print("[+]原始数据条数：%s" % pre_len)
                print("[+]未分类数据条数：%s" % str(pre_len - info['history']))
                self.data['list'] = f_list
            if info['encoding'] == "UTF-8" or "GB2312":
                print("【文件读取完毕，可以开始进行分类】")
                self.dir = self.data['info']['file_dir'] + "/" + self.data['info']['file_name']
            else:
                print("【文件已读取完毕，但编码方式未知，分类过程中可能会出现乱码】")
        else:
            print("[!]文件不存在，请检查文件路径")
            self.data = None

    def get_file_info(self, file):
        """
            获取文件信息
            :param file: 文件路径
            :return: 包含文件信息的dict
        """
        file_dir = os.path.dirname(file)
        file_name_full = os.path.basename(file)
        (file_name, file_ex) = os.path.splitext(file_name_full)
        h_file_path = file_dir + "/" + file_name + "/history.txt"

        info = {"found": os.path.exists(file), 'file_dir': file_dir, 'file_name': file_name, 'file_ex': file_ex, 'h_file_path': h_file_path}
        # 判断文件是否存在并获取文件编码方式
        if info['found']:
            info['encoding'] = self.get_file_encoding(file)

            # 判断是否存在历史分类信息
            try:
                with open(h_file_path, "r", encoding="UTF-8") as f:
                    info['history'] = int(f.read())
            except FileNotFoundError:
                info["history"] = 0
        return info

    def pattern_file_loader(self):
        """
        读取tab分割的正则表达式储存文件，每行为一类，第一项为类名
        :return: [包含所有类名的list， dict(类名=[正则表达式list])]
        """
        file = input("请输入本地文件路径：")
        pattern_list = []
        tags = []
        if os.path.exists(file):
            encoding = self.get_file_encoding(file)
            with open(file, "r", encoding=encoding) as f:
                f_lines = f.readlines()
                for line in f_lines:
                    line_cuted = line.split('\t')
                    tag = "".join(line_cuted[0].split())
                    patterns = line_cuted[1:]
                    pattern_list.append(patterns)
                    tags.append(tag)
            tag_pattern = {tags[i]: pattern_list[i] for i in range(len(f_lines))}
            pattern_dict = [tags, tag_pattern]
            print("\n[+]已读取{}条tag\n".format(len(f_lines)))
            self.pattern = pattern_dict
        else:
            print("[!]文件不存在，请检查文件路径")
            self.pattern = None
            return

    def classifier(self, p):
        """
        完成分类前的准备工作，比如建立文件夹和读取历史记录信息
        :param p: 分类方式标记
        :return: 返回分类好的数据
        """
        if not self.data:
            print("[!]缺少必要数据，无法进行自动分类，请先完成数据加载。")
            return
        patterns = self.pattern
        if "auto" in p and not patterns:
            print("[!]缺少必要数据，无法进行自动分类，请先完成数据和规则加载。")
            return

        global i
        self.classes = {}
        self.screen_cleaner()
        dir_path = self.dir
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        i = self.data['info']['history']
        if os.path.exists(self.data['info']['h_file_path']):
            with open(self.data['info']['h_file_path']) as f:
                i = int(f.read())
                
        length = len(self.data['list'])
        if p == "manual":
            self.classifier_m(self.data, i, length)
        elif p == "auto_1":
            self.classifier_auto(self.data, patterns, i, length)
        elif p == "auto_2":
            self.classifier_auto(self.data, patterns, i, length, log=False)

    def classifier_m(self, data, i, length):
        """
        手动分类
        :param data: 包含有文件信息和数据的dict，当前版本仍然需要文件信息来完成自动保存记录
        :param i: 分类开始位置
        :param length: 需要分类的数据条数
        :return: 分类好的信息
        """
        classes = {}
        try:
            for i in trange(i, length):
                line = data['list'][i]
                # 这一部分需要根据数据格式进行修改
                text = "".join(line[-1].split())
                tags = line[0]
                print('\n\n' + str(tags) + '\n')
                print(text + '\n')

                c = ""
                while len(c) < 1:
                    c = input("请输入类别号：")
                try:
                    classes[c].append(line)
                except KeyError:
                    classes[c] = [line]

                self.screen_cleaner()
            self.classes.update(classes)
        except KeyboardInterrupt:
            self.screen_cleaner()
            if self.re_confirm("是否更新历史信息?"):
                self.classes.update(classes)
                with open(data['info']['h_file_path'], "w", encoding="UTF-8") as f:
                    f.write(str(i))

    def classifier_auto(self, data, patterns, i, length, log=True):
        """
        自动分类
        :param data: 包含有文件信息和数据的dict
        :param patterns: 自动分类规则
        :param i: 分类开始位置
        :param length: 需要分类的数据条数
        :param log: 是否输出分类过程的信息，类似Debug模式
        :return: 返回分类好的数据
        """
        classes = {}
        try:
            with trange(i, length) as t:
                for i in t:
                    line = data['list'][i]
                    # 这一部分需要根据数据格式进行修改
                    text = "".join(line[-1].split())
                    tags = line[0]
                    if log:
                        print('\n\n' + str(tags) + '\n')
                        print(text + '\n')

                    c = ""
                    for tag in tags:
                        if tag not in patterns[0]:
                            if log:
                                print("\n[!]Tag【{0}】不存在对应的规则\n".format(tag))
                            c = "包含未经处理的Tag"
                        else:
                            flag = 0
                            for pattern_c in patterns[1][tag]:
                                pattern_c = "".join(pattern_c.split())
                                try:
                                    if re.match(pattern_c, text):
                                        if log:
                                            print("\n[+]Tag【{0}】与规则【{1}】匹配\n".format(tag, pattern_c))
                                        flag = 1
                                        if len(c) < 1:
                                            c = "匹配"
                                except re.error:
                                    if log:
                                        print("\n[!]正则表达式【{0}】格式错误\n".format(pattern_c))
                                        input()
                            if flag == 0:
                                if log:
                                    print("\n[-]Tag【{0}】不存在与文本相匹配的规则\n".format(tag))
                                if c != "包含未经处理的Tag":
                                    c = "不匹配"

                    if log:
                        print("\n分类信息：{}".format(c))
                        input()
                    try:
                        # if line not in classes[c]:  # 去重
                        classes[c].append(line)
                    except KeyError:
                        classes[c] = [line]
                    if log:
                        self.screen_cleaner()
            t.close()
            self.classes.update(classes)
        except KeyboardInterrupt:
            t.close()
            self.screen_cleaner()
            if self.re_confirm("是否更新历史信息?"):
                self.classes.update(classes)
                with open(data['info']['h_file_path'], "w", encoding="UTF-8") as f:
                    f.write(str(i))
        t.close()

    def save_to_file(self):
        """
        将数据保存至文件中
        :return: 返回成功1 否0
        """
        if not self.classes:
            print("[!]无数据，请先进行至少一条数据分类。")
            return
        file_ex = self.data['info']['file_ex']
        res = 1
        for cls in self.classes:
            file_cls = cls.replace("|", ",")   # 替换一些不能出现在文件名中的字符
            file_cls = file_cls.replace("/", ",")
            print("[+]正在将 {0} 条数据储存至 {1} ".format(str(len(self.classes[cls])), str(self.dir + "/" + file_cls + file_ex)))
            try:
                with open(str(self.dir + "/" + file_cls + file_ex), "a", encoding="UTF-8") as f:
                    for line in self.classes[cls]:
                        Tags = ""
                        for tag in line[0]:
                            Tags += tag + ","
                        text = line[1]
                        f.write(Tags + "\t" + text + '\n')
            except IOError:
                res = 0
                print("[!]文件【{0}】写入失败，请检查代码和文件名".format(cls))
                break
        if res == 1:
            self.classes = None


if __name__ == '__main__':
    c = classifier()
    while 1:
        c.menu()
        choice = input("\n请输入：")

        if choice == '1':
            c.data_file_loader()
        elif choice == '2':
            c.pattern_file_loader()
        elif choice == '3':
            c.classifier("manual")
        elif choice == '4':
            c.classifier("auto_1")
        elif choice == '5':
            c.classifier("auto_2")
        elif choice == '6':
            c.save_to_file()
        elif choice == '0':
            c.classifier_closer()
        else:
            print("[!]不能识别的指令")
