import os
from collections import OrderedDict
from NewsPlaceExtract import NewsConst
from NewsPlaceExtract import FileTools

provinceMap = dict()  # 省份简称 ---》 省份全称
p_map_path = 'conf/provinceMap.txt'
with open(p_map_path, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f.readlines()]
    for line in lines:
        arr = line.split('\t')
        provinceMap[arr[0]] = arr[1]


class News(object):
    def __init__(self, id, website, channel, category, title,
                 nation, province, city, county,
                 reason, text, labels,
                 nerloc, nerloc_index, nerorg, nerorg_index,
                 checkDetails):
        self.id = id
        self.website = website
        self.channel = channel
        self.category = category
        self.title = title

        self.nation = nation
        self.province = province
        self.city = city
        self.county = county

        self.reason = reason
        self.text = text
        self.labels = labels

        self.nerloc = nerloc
        self.nerloc_index = nerloc_index
        self.nerorg = nerorg
        self.nerorg_index = nerorg_index

        # 算法预测的结果，省/市/区
        self.predict_place = {}

        # test用
        self.checkDetails = checkDetails

    # 从txt_predict中找出loc


def extract_entity(token_lst, predict_lst, begin_str, end_str):
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


# 从txt_predict中找出loc，带word 索引，句子索引
def extract_entity_index(sents, predict_lst, begin_str, end_str):
    # 记录句子的位置
    word_index = -1  # 保存字符的索引
    word_index_of_content = 0  # loc的开始字符索引

    word_index_of_sentence = 0  # loc在句的开始索引
    index = 0  # 记录loc中前一个字符的位置

    entities_index = []
    entities = []

    for i in range(len(sents)):
        # 组成loc的字符
        entity_character = ''
        sentence_index = i
        words = list(sents[i])
        # if predict_lst[i].count('B-ORG') > 1 and begin_str == 'B-ORG':
        #     print('note')
        for j in range(len(words)):
            word_index += 1
            if predict_lst[i][j] == begin_str:
                if entity_character != '':
                    # 地狱名:句子索引:当前句子字符索引：全文字符索引
                    entities_index.append(entity_character + ':' + str(sentence_index) + ':'
                                      + str(word_index_of_sentence) + ':' + str(word_index_of_content))
                    entities.append(entity_character)
                entity_character = words[j]
                word_index_of_content = word_index
                word_index_of_sentence = j
                index = j

            elif predict_lst[i][j].endswith(end_str) and index == j - 1:
                entity_character = entity_character + words[j]
                index = j

        if entity_character != '':
            # 地狱名:句子索引:当前句子字符索引：全文字符索引
            entities_index.append(entity_character + ':' + str(sentence_index) + ':'
                              + str(word_index_of_sentence) + ':' + str(word_index_of_content))
            entities.append(entity_character)

    return entities, entities_index


def extract_ner_index2(token_lst, predict_lst, begin_str, end_str):
    # 记录句子的位置
    sentence_index = 0  # 保存句子的索引
    word_index = 0  # 保存字符的索引
    sentence_index_tmp = 1
    locs_index = []
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
                locs_index.append(loc + ':' + str(word_index) + ':' + str(sentence_index))
                locs.append(loc)
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
        locs_index.append(loc + ':' + str(word_index) + ':' + str(sentence_index))
        locs.append(loc)

    return locs_index


def createNews(index, row, pred_tags):
    # 清楚空字符的影响
    website = row['website'].strip()
    channel = row['channel'].strip()
    category = row['category'].strip()
    reason = row['reason'].strip()
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

    if nation == '未知':
        nation = ''

    if province == '未知':
        province = ''
    if city == '未知':
        city = ''
    if county == '未知':
        county = ''

    ner_locs, ner_locs_index = extract_entity_index(row['text'], pred_tags, 'B-LOC', 'LOC')
    ner_orgs, ner_orgs_index = extract_entity_index(row['text'], pred_tags, 'B-ORG', 'ORG')

    for str_org in ner_orgs_index:
        ner_orgs.append(str_org.split(':')[0])

    # 测试专用
    checkDetails = row['checkDetails'].strip()
    news = News(index, website, channel, category, title,
                nation, province, city, county,
                reason, row['text'], pred_tags,
                ner_locs, ner_locs_index, ner_orgs, ner_orgs_index,
                checkDetails)

    return news
