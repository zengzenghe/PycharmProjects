# coding=utf-8

import pandas as pd
import re


# 文件处理程序，bert 与 新闻与处理都需要调用相同的函数,保持一致
def read_xls_data(input_file):
    # 读取指定列
    # df = pd.read_excel(input_file, header=0, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    # df = pd.read_excel(input_file, header=0, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
    # when add pubdate, row['text']的值无法修改，由于pubdate格式与其它列不统一
    df = pd.read_excel(input_file, header=0, usecols=[0, 1, 2, 3, 5, 6, 7, 8, 16, 17, 18])
    # print(df.columns)
    # df.columns = ['website', 'channel', 'category', 'title', 'nation', 'province', 'city', 'county', 'reason', 'text']
    # df.columns = ['website', 'channel', 'category', 'title', 'pubdate', 'nation', 'province', 'city', 'county',
    #               'predictProvince', 'predictCity', 'predictCounty', 'reason', 'text']
    #
    # df.columns = ['website', 'channel', 'category', 'title', 'nation', 'province', 'city', 'county',
    #               'predictProvince', 'predictCity', 'predictCounty', 'reason', 'text']

    df.columns = ['website', 'channel', 'category', 'title', 'nation', 'province', 'city', 'county',
                  'checkDetails', 'reason', 'text']
    # # 增加原文src_text列，为以后就错unk字符用
    # df['src_text'] = 'null'
    # 输出制行，列
    # print(df.ix[[1, 5], ['title', 'province']])
    # print(df.ix[1:5, ['title', 'province', 'city']])
    # 处理缺省值，填充NaN为指定的值,必须要加上inplace，否则不会保存填充的结果
    df.fillna('', inplace=True)
    # print(df.ix[1:5, ['title', 'province', 'city']])
    #
    for index, row in df.iterrows():
        print('loading index: ' + str(index))
        # if index == 829:
        #     print('note')
        # title加到正文
        # df['text'] = df['title'] + '。' + df['text']

        # 都加入标题子段,微博数据很特殊，标题和正文基本一样
        txt_tmp = str(row['text']).strip()
        if '微博' in row['website']:
            # row['text'] = clean_text_weibo(txt_tmp)
            row['text'] = clean_text_weibo(txt_tmp)
        else:
            txt_tmp = row['title'] + '。' + txt_tmp
            row['text'] = clean_text(txt_tmp)

        # print('next...')
        # print(row)
    return df


def clean_text(txt):
    # 保存原文，为了以后就错unk字符用
    src_txt_lines = []
    reg_str = '<.*?>'
    pattern = '[。|！|!|？|?|\\n|；|;]'
    sents = re.split(pattern, txt)
    lines = []
    for sent in sents:
        # 微博数据存在很多#
        # sent = sent.replace('#', '')
        sent = sent.replace('“', '"').replace('”', '"')
        sent = re.sub('\\s+', '', sent)
        sent = re.sub(reg_str, '', sent)
        if len(sent) > 1:
            lines.append(sent)
    return lines


# 微薄数据清洗
def clean_text_weibo(txt):
    # 存在句式：
    # 1  #铜仁身边事# 【打卡铜仁！[照相机][照相机]全网征集铜】
    # 2 【#数学不好的人学不了法语#】
    # 3 【“勿动！插管去了！”#一张写在餐巾纸上的留言# 走红[中国赞]】
    # 4  #小编说天气  # 未来几天以晴或多云天气为主，
    reg_str = '<.*?>'
    pattern = '[。|！|!|？|?|\\n|；|;]'
    sents = re.split(pattern, txt)
    lines = []
    pattern_url = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')  # 匹配模式

    # 清楚特别字符，变为逗号
    # pattern_1 = re.compile(r'#')  # 将正则表达式编译成Pattern对象
    # pattern_2 = re.compile(r'#】')  # 将正则表达式编译成Pattern对象

    for i in range(len(sents)):
        sent = sents[i]
        # 微博数据存在很多#
        # sent = sent.replace('#', '')
        sent = sent.replace('“', '"').replace('”', '"')
        sent = re.sub('\\s+', '', sent)
        sent = re.sub(reg_str, '', sent)
        sent = re.sub(pattern_url, '', sent)

        # if i == 0:
        #     # 之看内容，从#后开始才是正文
        #     index = sent.find('】')
        #     if index != -1:
        #         if index < len(sent) - 1:
        #             sent = sent[index + 1:]
        #         else:
        #             sent = ''

        if i == 0:
            if sent.startswith('#'):
                sent = sent[1:]
                index = sent.find('#')
                if index != -1:
                    if index < len(sent) - 1:
                        sent = sent[0:index] + ',' + sent[index + 1:]
                    else:
                        sent = sent[0:index]

            elif sent.startswith('【#'):
                sent = sent[2:]
                index = sent.find('#】')
                if index != -1:
                    if index < len(sent) - 2:
                        sent = sent[0:index] + ',' + sent[index + 2:]
                    else:
                        sent = sent[0:index]
        # print(sent)

        if len(sent) > 1:
            lines.append(sent)

    return lines
