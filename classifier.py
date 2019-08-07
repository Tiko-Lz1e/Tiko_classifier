import re
import sys
import os
import csv
from tqdm import trange


def classifier_closer():
    os.system('cls')
    sys.exit()


def get_file_encoding(file):
    """
    辨别文件是否为GB2312或UTF-8编码
    :param file: 文件路径
    :return: 文件编码方式
    """
    try:
        with open(file, "r", encoding="GB2312") as f:
            f.readline()
            encoding = "GB2312"
    except UnicodeDecodeError:
        try:
            with open(file, "r", encoding="utf-8") as f:
                f.readline()
                encoding = 'UTF-8'
        except UnicodeDecodeError:
            encoding = "尚不支持的编码方式"
    return encoding


def menu():
    print("\n输入数字并回车进入相应功能")
    print("1: 加载数据文件(tsv)")
    print("2: 加载正则表达式文件(tsv)")
    print("3: 开始进行手动分类")
    print("4: 开始进行自动分类(显示分类信息)")
    print("5: 开始进行自动分类(不显示分类信息)")
    print("6: 将已分类数据保存至文件(tsv)")
    print("0: 退出系统")


def data_file_loader():
    """
    将数据读取到list中，需要为tsv格式，headers会被当成数据
    :return: dict(info=文件信息组成的dict，list=格式化处理后的数据)
    """
    data = {"info": {}}
    file_path = input("请输入本地文件路径：")
    print()
    print("【正在获取文件信息，请稍候...】")
    info = get_file_info(file_path)
    data['info'] = info
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
            data['list'] = f_list
        if info['encoding'] == "UTF-8" or "GB2312":
            print("【文件读取完毕，可以开始进行分类】")
        else:
            print("【文件已读取完毕，但编码方式未知，分类过程中可能会出现乱码】")
    else:
        print("[!]文件不存在，请检查文件路径")
        return None
    return data


def get_file_info(file):
    """
        获取文件信息
        :param file: 文件路径
        :return: 包含文件信息的dict
    """
    file_dir = os.path.dirname(file)
    file_name_full = os.path.basename(file)
    (file_name, file_ex) = os.path.splitext(file_name_full)
    h_file_path = file_dir + "\\" + file_name + "\\history.txt"

    info = {"found": os.path.exists(file), 'file_dir': file_dir, 'file_name': file_name, 'file_ex': file_ex, 'h_file_path': h_file_path}
    # 判断文件是否存在并获取文件编码方式
    if info['found']:
        info['encoding'] = get_file_encoding(file)

        # 判断是否存在历史分类信息
        try:
            f = open(h_file_path, "r", encoding="UTF-8")
            info['history'] = int(f.read())
            f.close()
        except FileNotFoundError:
            info["history"] = 0
    return info


def pattern_file_loader():
    """
    读取tab分割的正则表达式储存文件，每行为一类，第一项为类名
    :return: [包含所有类名的list， dict(类名=[正则表达式list])]
    """
    file = input("请输入本地文件路径：")
    pattern_list = []
    tags = []
    if os.path.exists(file):
        encoding = get_file_encoding(file)
        with open(file, "r", encoding=encoding) as f:
            f_lines = f.readlines()
            for line in f_lines:
                line_cuted = line.split('\t')
                tag = line_cuted[0]
                patterns = line_cuted[1:]
                pattern_list.append(patterns)
                tags.append(tag)
        tag_pattern = {tags[i]: pattern_list[i] for i in range(len(f_lines))}
        pattern_dict = [tags, tag_pattern]
        print("\n[+]已读取{}条tag\n".format(len(f_lines)))
    else:
        print("[!]文件不存在，请检查文件路径")
        return None
    return pattern_dict


def classifier(data, p, patterns=None):
    """
    完成分类前的准备工作，比如建立文件夹和读取历史记录信息
    :param data: 包含有文件信息和数据的dict
    :param p: 分类方式标记
    :param patterns: 分类规则，当分类模式为manual时不需要所以默认为None
    :return: 返回分类好的数据
    """
    global i
    os.system('cls')
    dir_path = data['info']['file_dir'] + "\\" + data['info']['file_name']
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    i = data['info']['history']
    if os.path.exists(data['info']['h_file_path']):
        with open(data['info']['h_file_path']) as f:
            i = int(f.read())
    classes = {}
    length = len(data['list'])
    if p == "manual":
        classes = classifier_m(data, i, length)
    elif p == "auto_1":
        classes = classifier_auto(data, patterns, i, length)
    elif p == "auto_2":
        classes = classifier_auto(data, patterns, i, length, log=False)
    return classes


def classifier_m(data, i, length):
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

            os.system("cls")
    except KeyboardInterrupt:
        os.system('cls')
        with open(data['info']['h_file_path'], "w", encoding="UTF-8") as f:
            f.write(str(i))
        return classes
    return classes


def classifier_auto(data, patterns, i, length, log=True):
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
                if text[len(text) - 1] == '\n':
                    text[len(text) - 1] = '\0'
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
                    input()                                       # 自动化运行时，注释掉这一句
                try:
                    # if line not in classes[c]:
                    classes[c].append(line)
                except KeyError:
                    classes[c] = [line]
                if log:
                    os.system("cls")
        t.close()

    except KeyboardInterrupt:
        t.close()
        os.system('cls')
        with open(data['info']['h_file_path'], "w", encoding="UTF-8") as f:
            f.write(str(i))
        return classes
    t.close()
    return classes


def save_to_file(classes, file_dir, file_ex):
    """
    将数据保存至文件中
    :param classes: 将被保存的数据
    :param file_dir: 文件所在地址
    :param file_ex: 文件保存格式
    :return: 返回成功1 否0
    """
    res = 1
    for cls in classes:
        print("[+]正在将 {0} 条数据储存至 {1} ".format(str(len(classes[cls])), str(file_dir + "\\" + cls + file_ex)))
        try:
            with open(str(file_dir + "\\" + cls + file_ex), "a", encoding="UTF-8") as f:
                for line in classes[cls]:
                    Tags = ""
                    for tag in line[0]:
                        Tags += tag + ","
                    text = line[1]
                    f.write(Tags + "\t" + text + '\n')
        except IOError:
            res = 0
            print("[!]文件写入失败，请检查代码和文件")
            break

    return res


if __name__ == '__main__':
    os.system('cls')
    print("\n【欢迎来到Tiko分类器 v1.2.0】\n")
    input("\n--->按下回车键开始--->")
    os.system('cls')
    data = {}
    pattern = []
    classes = {}
    while 1:
        menu()
        choice = input("\n请输入：")
        print()
        if choice == '1':
            data = data_file_loader()
        elif choice == '2':
            pattern = pattern_file_loader()
        elif choice == '3':
            if data:
                classes = classifier(data, "manual")
            else:
                print("[!]缺少必要数据，无法进行手动分类，请先完成数据加载")
        elif choice == '4':
            if data and pattern:
                classes = classifier(data, "auto_1", patterns=pattern)
            else:
                print("[!]缺少必要数据，无法进行自动分类，请先完成数据和规则加载")
        elif choice == '5':
            if data and pattern:
                classes = classifier(data, "auto_2", patterns=pattern)
            else:
                print("[!]缺少必要数据，无法进行自动分类，请先完成数据和规则加载")
        elif choice == '6':
            if classes:
                save_to_file(classes, data['info']['file_dir'] + "\\" + data['info']['file_name'], data['info']['file_ex'])
                classes = None
            else:
                print("[!]无数据，请先进行至少一条数据分类")
        elif choice == '0':
            if classes:
                c = input("\n[!]还有数据尚未保存，是否确认退出?[Y|N]\n")
                if c == "Y" or c == "y":
                    print("\n【退出Tiko分类器】")
                    sys.exit()
            else:
                print("\n【退出Tiko分类器】")
                sys.exit()
        else:
            print("[!]不能识别的指令")
