# coding=utf-8
import pandas as pd
import re
import os
from collections import OrderedDict
from extractPlace import NewsConst
from extractPlace import FileTools

global_char_cnt = 0
sample_size = 0

provinceMap = dict()  # 省份简称 ---》 省份全称
p_map_path = 'conf/provinceMap.txt'
with open(p_map_path, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f.readlines()]
    for line in lines:
        arr = line.split('\t')
        provinceMap[arr[0]] = arr[1]


# 纠正[UNK]单词
def correct_unk_word(lines, ner_tokens):
    correct_tokens = []
    for i in range(len(lines)):
        tokens = ['[CLS]']
        for word in list(lines[i]):
            tokens.append(word)
        tokens.append('[SEP]')
        correct_tokens.extend(tokens)

    assert len(correct_tokens) == len(ner_tokens)
    return correct_tokens


def merge_result():
    input_file = '../data/1000_news.xls'
    input_file = '../data//1050_news.xls'
    input_file = '../data//3150_news.xls'
    output_file = 'input/merge.txt'
    if os.path.exists(output_file):
        os.remove(output_file)

    df = FileTools.read_xls_data(input_file)
    global sample_size
    sample_size = df.shape[0]
    # 去掉 留言信息等非新闻文本
    clean = []
    if input_file == '../data/1000_news.xls':
        clean = [981, 982, 984, 985, 986, 987, 988, 989, 990, 992, 993, 994, 995, 936, 938, 797, 798, 799, 800, 801,
                 802, 803, 106, 108, 109, 110, 121, 126, 142, 143, 149, 151, 159, 177, 182, 190, 191, 196, 198, 201,
                 206, 212, 250, 255, 262, 269, 293, 295, 300, 302, 305, 308, 337, 340, 352, 362, 368, 375, 391, 399,
                 402, 403, 405, 416, 470, 471, 479, 487, 505]

    for index, row in df.iterrows():
        if index in clean:
            continue
        print(index)

        # count char--begin
        word_cnt = 0
        news_rows = row['src_text']
        for line in news_rows:
            word_cnt += len(line)
        global global_char_cnt
        global_char_cnt += word_cnt
        # count char--end

        # if index <18:
        #     continue
        # 清楚空字符的影响
        website = row['website'].strip()
        channel = row['channel'].strip()
        category = row['category'].strip()

        title = row['title'].strip()
        nation = row['nation'].strip()
        province = row['province'].strip()
        province = provinceMap.get(province, province)
        # 标准映射
        city = row['city'].strip()
        if city in NewsConst.standard_place_dic.keys() and len(NewsConst.standard_place_dic[city]) == 1:
            city = NewsConst.standard_place_dic[city][0]

        # 标准映射
        county = row['county'].strip()
        if county in NewsConst.standard_place_dic.keys() and len(NewsConst.standard_place_dic[county]) == 1:
            county = NewsConst.standard_place_dic[county][0]

        row['nation'] = nation
        row['province'] = province
        row['city'] = city
        row['county'] = county

        if nation == '' or nation == '未知':
            row['nation'] = 'null'
        if province == '' or province == '未知':
            row['province'] = 'null'
        if city == '' or city == '未知':
            row['city'] = 'null'
        if county == '' or county == '未知':
            row['county'] = 'null'

        token_path = '../output/predict_dir/news_tokens/token_test' + '_' + str(index) + '.txt'
        ner_tokens = readfile(token_path)

        # 由于dictionary汉字不全，需要纠错,还原ner_tokens的[UNK]字符
        if '[UNK]' in ner_tokens:
            correct_tokens = correct_unk_word(row['src_text'], ner_tokens)
        else:
            correct_tokens = ner_tokens

        # print('label_test' + '_' + str(index) + '.txt')

        output_predict_file = '../output/predict_dir/news_labels/label_test' + '_' + str(index) + '.txt'
        predict_lst = readfile(output_predict_file)

        place = 'nation(国家):' + row['nation'] + '\tprovince(省):' + row['province'] \
                + '\tcity(市):' + row['city'] + '\tcounty(县):' + row['county']

        # ner_pers = extract_ner(tokens_lst, predict_lst, 'B-PER', 'PER')
        # pers_set = set(ner_pers)
        # pers_count = {k: ner_pers.count(k) for k in pers_set}
        # pers_sorted = sorted(pers_count.items(), key=lambda x: x[1], reverse=True)

        ner_locs = extract_ner(correct_tokens, predict_lst, 'B-LOC', 'LOC')
        ner_locs_index = extract_ner_index(correct_tokens, predict_lst, 'B-LOC', 'LOC')
        locs_set = set(ner_locs)
        locs_count = {k: ner_locs.count(k) for k in locs_set}
        locs_sorted = sorted(locs_count.items(), key=lambda x: x[1], reverse=True)

        ner_orgs = extract_ner(correct_tokens, predict_lst, 'B-ORG', 'ORG')
        ner_orgs_index = extract_ner_index(correct_tokens, predict_lst, 'B-ORG', 'ORG')
        orgs_set = set(ner_orgs)
        orgs_count = {k: ner_orgs.count(k) for k in orgs_set}
        orgs_sorted = sorted(orgs_count.items(), key=lambda x: x[1], reverse=True)

        txt = 'id\t' + str(index)
        txt = txt + '\nwebsite\t' + website
        txt = txt + '\nchannel\t' + channel
        txt = txt + '\ncategory\t' + category
        txt = txt + '\ntitle\t' + title
        txt = txt + '\ntoken\t' + ' '.join(correct_tokens)
        txt = txt + '\nlabels\t' + ' '.join(predict_lst)
        txt = txt + '\nplace\t' + place
        # txt = txt + '\nnerper\t' + ' '.join(ner_pers)
        # txt = txt + '\nnerper_sorted\t' + str(pers_sorted)
        txt = txt + '\nnerloc\t' + ' '.join(ner_locs)
        txt = txt + '\nnerloc_index\t' + ' '.join(ner_locs_index)
        txt = txt + '\nnerloc_sorted\t' + str(locs_sorted)
        txt = txt + '\nnerorg\t' + ' '.join(ner_orgs)
        txt = txt + '\nnerorg_index\t' + ' '.join(ner_orgs_index)
        txt = txt + '\nnerorg_sorted\t' + str(orgs_sorted)
        txt = txt + '\n\n\n'
        write_file(output_file, txt)


def write_file(output_file, txt):
    with open(output_file, 'a') as f:
        f.write(txt)


# 从txt_predict中找出loc，带word 索引，句子索引
def extract_ner_index(token_lst, predict_lst, begin_str, end_str):
    # 记录句子的位置
    sentence_index = 0  # 保存句子的索引
    word_index = 0  # 保存字符的索引
    sentence_index_tmp = 1
    locs = []
    loc = ''
    index = 0
    for i in range(len(token_lst)):
        if predict_lst[i] == '[SEP]':
            # print('sep' + str(i))
            sentence_index_tmp += 1

        if predict_lst[i] == begin_str:
            if loc != '':
                # 句子索引是 sentence_index 而不是 sentence_index_tmp
                locs.append(loc + ':' + str(word_index) + ':' + str(sentence_index))
            sentence_index = sentence_index_tmp
            word_index = i
            loc = token_lst[i]
            index = i

            # print(predict_lst[i])
            # print(token_lst[i])
        elif predict_lst[i].endswith(end_str) and index == i - 1:
            loc = loc + token_lst[i]
            index = i
            # print(predict_lst[i])
            # print(token_lst[i])
    # 最后一个loc
    # if loc != '' and len(loc) > 1:
    if loc != '':
        locs.append(loc + ':' + str(word_index) + ':' + str(sentence_index))

    return locs


# 从txt_predict中找出loc
def extract_ner(token_lst, predict_lst, begin_str, end_str):
    # 记录句子的位置
    # sentence_index = 0  # 保存句子的索引
    # sentence_index_tmp = 1
    locs = []
    loc = ''
    index = 0
    for i in range(len(token_lst)):
        # if predict_lst[i] == '[SEP]':
        # print('sep' + str(i))
        # sentence_index_tmp += 1
        if predict_lst[i] == begin_str:
            # if loc != '' and len(loc) > 1:
            if loc != '':
                # 句子索引是 sentence_index 而不是 sentence_index_tmp
                # locs.append(loc + ':' + str(sentence_index))
                locs.append(loc)
            # sentence_index = sentence_index_tmp
            loc = token_lst[i]
            index = i
            # print(predict_lst[i])
            # print(token_lst[i])
        elif predict_lst[i].endswith(end_str) and index == i - 1:
            loc = loc + token_lst[i]
            index = i
            # print(predict_lst[i])
            # print(token_lst[i])
    # 最后一个loc
    # if loc != '' and len(loc) > 1:
    if loc != '':
        # locs.append(loc + ':' + str(sentence_index_tmp))
        locs.append(loc)

    return locs


def readfile(path):
    with open(path, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    return lines


# 创建标准的词典
def create_standard_dic_step1():
    input_file = 'conf/place.code'
    dic = OrderedDict()
    dic['京'] = ['北京市']
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    lst_zizhi = []
    for line in lines:
        _, name = line.split('\t')
        if '自治' not in name and '特别行政区' not in name:
            if name.endswith('省') or name.endswith('市') or name.endswith('区') or name.endswith('县'):
                key = name[0:-1]
                if key.strip() == '' or name == '':
                    continue
                if key not in dic.keys():
                    dic[key] = [name]
                elif name not in dic[key]:
                    dic[key].append(name)
        else:
            # 自治区/县，有150来个，必须人工创建
            lst_zizhi.append(name + '\t' + name)

    with open('tmp/zizhiqu.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lst_zizhi))

    # 对省、直辖市、自治区特殊处理
    with open('conf/provinceMap.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            arr = line.split('\t')
            dic[arr[0]] = [arr[1]]  # 必须list，后面会判断长度
    dic['台'] = ['台湾省']
    # 对省份简称的处理。注意：增加简称效果更差
    # with open('conf/resource/province_abbreviation.txt', 'r', encoding='utf-8') as f:
    #     for line in f:
    #         line = line.strip()
    #         arr = line.split('\t')
    #         dic[arr[0]] = [arr[1]]  # 必须list，后面会判断长度

    ret = []
    for k, v in dic.items():
        if len(v) == 1:
            ret.append(k + '\t' + v[0])
        else:
            ret.append(k + '\t' + ' '.join(v))

    with open('tmp/standard_place_dic_tmp.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(ret))


# 根据临时词典+人工字典，组成标准词典
def create_standard_dic_step2():
    dic = OrderedDict()
    with open('tmp/standard_place_dic_tmp.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            arr = line.split('\t')
            key = arr[0]
            values = list(set(arr[-1].split(' ')))
            dic[key] = values
    with open('conf/resource/zizhiqu_bak.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            arr = line.split('\t')
            key = arr[0]
            value = arr[1]
            if key not in dic.keys():
                dic[key] = [value]
            elif value not in dic[key]:
                dic[key].append(value)
    lst = []
    for k, v in dic.items():
        lst.append(k + '\t' + ' '.join(v))
    with open('tmp/standard_place_dic.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lst))


def create_include_dic():
    input = 'conf/standard_place_dic.txt'
    output = 'conf/include_place_dic.txt'
    lst = []
    with open(input, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            key = line.split('\t')[0]
            if (line.endswith('省') or line.endswith('市')) and len(key) > 1:
                lst.append(line)

    # 添加5个自治区，2个特别行政区
    lst.append('广西\t广西壮族自治区')
    lst.append('内蒙古\t内蒙古自治区')
    lst.append('宁夏\t宁夏回族自治区')
    lst.append('新疆\t新疆维吾尔自治区')
    lst.append('西藏\t西藏自治区')
    lst.append('香港\t香港特别行政区')
    lst.append('澳门\t澳门特别行政区')

    with open(output, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lst))


def main():
    # txt = '11;22；33！44!55'
    # clean_text(txt)
    # 创建标准的词典,统一词典
    # create_standard_dic_step1()
    # create_standard_dic_step2()

    # 创建一个包含的词典
    # create_include_dic()

    # 合并模型预测结果
    # 合并中带word_index,sentence_index
    merge_result()


    # print('merge end!')

    global global_char_cnt
    print('sample_size', sample_size)
    print('total chars', global_char_cnt)
    print('average chars', global_char_cnt // sample_size)
    print('end')


if __name__ == "__main__":
    main()
