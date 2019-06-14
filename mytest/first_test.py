# coding=utf-8

import pandas as pd
import re

input_file = '../data/3150_news.xls'
output = '../output_tmp/3150_news.xls'

lst1 = ['a1', 'a2', 'a3']
lst2 = ['b1', 'b2', 'b3']
print('~~~~~~~~~~~~~)
df = pd.DataFrame()  #
df2 = pd.DataFrame()  #
citys = ['c1', 'c2', 'c3']
df.insert(0, 'city', citys)  # 在第0列，加上column名称为city，值为citys的数值。
jobs = ['student', 'AI', 'teacher']
df['job'] = jobs  # 默认在df最后一列加上column名称为job，值为jobs的数据。
df.loc[:, 'salary'] = ['1k', '2k', '3k']  # 在df最后一列加上column名称为salary，值为等号右边数据

# df = pd.read_excel(input_file, header=0)
print(df.columns)
#
# for index, row in df.iterrows():
#     row['标题'] = str(index)
# print(row['标题'])

df2['city'] = df['city']
df2['job'] = df['job']

df2.to_excel(output)


# 文件处理程序，bert 与 新闻与处理都需要调用相同的函数,保持一致
def read_xls_data(input_file):
    # 读取指定列
    df = pd.read_excel(input_file, header=0, index=0, usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    # print(df.columns)
    df.columns = ['website', 'channel', 'category', 'title', 'nation', 'province', 'city', 'county', 'reason', 'text']
    # 增加原文src_text列，为以后就错unk字符用
    df['src_text'] = 'null'
    # 输出制行，列
    # print(df.ix[[1, 5], ['title', 'province']])
    # print(df.ix[1:5, ['title', 'province', 'city']])
    # 处理缺省值，填充NaN为指定的值,必须要加上inplace，否则不会保存填充的结果
    df.fillna('', inplace=True)

    for index, row in df.iterrows():
        # title加到正文
        # df['text'] = df['title'] + '。' + df['text']

        # 都加入标题子段
        txt_tmp = str(row['text']).strip()
        # if not txt_tmp.startswith('原标题'):
        txt_tmp = row['title'] + '。' + txt_tm
        # print(row)

    return df
