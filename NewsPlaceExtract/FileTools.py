# coding=utf-8

import pandas as pd
import re


# 文件处理程序，bert 与 新闻与处理都需要调用相同的函数,保持一致
def read_xls_data(input_file):
    # 读取指定列
    df = pd.read_excel(input_file, header=0, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    # df = pd.read_excel(input_file, header=0, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
    # when add pubdate, row['text']的值无法修改，由于pubdate格式与其它列不统一
    # df = pd.read_excel(input_file, header=0, usecols=[0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13])
    # print(df.columns)
    df.columns = ['website', 'channel', 'category', 'title', 'nation', 'province', 'city', 'county', 'reason', 'text']
    # df.columns = ['website', 'channel', 'category', 'title', 'pubdate', 'nation', 'province', 'city', 'county',
    #               'predictProvince', 'predictCity', 'predictCounty', 'reason', 'text']

    # df.columns = ['website', 'channel', 'category', 'title', 'nation', 'province', 'city', 'county',
    #               'predictProvince', 'predictCity', 'predictCounty', 'reason', 'text']
    # # 增加原文src_text列，为以后就错unk字符用
    # df['src_text'] = 'null'
    # 输出制行，列
    # print(df.ix[[1, 5], ['title', 'province']])
    # print(df.ix[1:5, ['title', 'province', 'city']])
    # 处理缺省值，填充NaN为指定的值,必须要加上inplace，否则不会保存填充的结果
    df.fillna('', inplace=True)
    # print(df.ix[1:5, ['title', 'province', 'city']])

    for index, row in df.iterrows():
        # title加到正文
        # df['text'] = df['title'] + '。' + df['text']

        # 都加入标题子段
        txt_tmp = str(row['text']).strip()
        # if not txt_tmp.startswith('原标题'):
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
        # bert vocab.txt中没有中文的引号，需要修改文英文，否则token结果为UNK
        sent = sent.replace('“', '"').replace('”', '"')
        sent = re.sub('\\s+', '', sent)
        sent = re.sub(reg_str, '', sent)
        if len(sent) > 1:
            lines.append(sent)
    return lines
