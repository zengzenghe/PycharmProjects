import os
import pandas as pd


def record_result(news, lst):
    lst.append('id\t' + str(news.id))
    lst.append('token\t' + '||'.join(news.text))

    tmp_lst = []
    for v in news.labels:
        tmp_lst.append(' '.join(v))
    lst.append('lables\t' + '||'.join(tmp_lst))

    lst.append('place\tnation(国家):' + news.nation + '\tprovince(省):'
               + news.province + '\tcity(市):' + news.city
               + '\tcounty(县):' + news.county)
    lst.append('nerloc\t' + ' '.join(news.nerloc))
    lst.append('nerorg\t' + ' '.join(news.nerorg))
    lst.append('predict_place\tnation(国家):null\tprovince(省):' + news.predict_place['province']
               + '\tcity(市):' + news.predict_place['city']
               + '\tcounty(县):' + news.predict_place['county'])
    lst.append('\n')


def record_error(news, lst):
    lst.append('id\t' + str(news.id))
    lst.append('website\t' + news.website)
    lst.append('channel\t' + news.channel)
    lst.append('category\t' + news.category)
    lst.append('reason\t' + news.reason)
    lst.append('title\t' + news.title)
    lst.append('token\t' + '||'.join(news.text))

    tmp_lst = []
    for v in news.labels:
        tmp_lst.append(' '.join(v))
    lst.append('lables\t' + '||'.join(tmp_lst))

    lst.append('place\tnation(国家):' + news.nation + '\tprovince(省):'
               + news.province + '\tcity(市):' + news.city
               + '\tcounty(县):' + news.county)
    lst.append('nerloc\t' + ' '.join(news.nerloc))
    lst.append('nerloc_index\t' + ' '.join(news.nerloc_index))
    lst.append('nerorg\t' + ' '.join(news.nerorg))
    lst.append('nerorg_index\t' + ' '.join(news.nerorg_index))
    lst.append('predict_place\tnation(国家):null\tprovince(省):' + news.predict_place['province']
               + '\tcity(市):' + news.predict_place['city']
               + '\tcounty(县):' + news.predict_place['county'])
    lst.append('\n')


# 评估算法的结果
def result_evaluate(news_lst):
    rows = len(news_lst)
    cnt_p = 0  # 计算省accuracy
    cnt_p_c = 0  # 计算省市的accuracy用
    cnt_samples = 0  # 样本中的信息条数
    cnt_predict_p = 0  # 提取出的信息条数
    tp_p = 0  # 提取出且省正确数
    tp_p_c = 0  # 提取出且省市正确数

    result_place_tree_lst = []  # 把地名打印出来

    # error
    error_tp_p = []
    error_fn_p = []
    bad_case = []
    bad_cities = []
    for news in news_lst:
        # if new.id == '139':
        #     print('note')
        province = news.province.strip()
        city = news.city.strip()
        predict_province = news.predict_place['province']
        predict_city = news.predict_place['city']

        if province == predict_province:
            cnt_p += 1

        if province == predict_province and city == predict_city:
            cnt_p_c += 1

        if province != '':
            cnt_samples += 1
            record_result(news, result_place_tree_lst)

        if predict_province != '':
            cnt_predict_p += 1

        if predict_province == province and predict_province != '':
            tp_p += 1

        if province == predict_province and city == predict_city and predict_province != '':
            tp_p_c += 1

        # 记录错误 --begin
        if predict_province != province and predict_province != '':
            record_error(news, error_tp_p)

        if predict_province != province and predict_province == '':
            record_error(news, error_fn_p)

        if predict_province != province and province != '':
            record_error(news, bad_case)

        if province == predict_province and city != predict_city and predict_province != '':
            record_error(news, bad_cities)
            # 记录错误 --end
    precision_p = tp_p / cnt_predict_p
    recall_p = tp_p / cnt_samples
    f1_p = (1 + 1 * 1) * precision_p * recall_p / (1 * 1 * precision_p + recall_p)
    f05_p = (1 + 0.5 * 0.5) * precision_p * recall_p / (0.5 * 0.5 * precision_p + recall_p)

    precision_p_c = tp_p_c / cnt_predict_p
    recall_p_c = tp_p_c / cnt_samples
    f1_p_c = (1 + 1 * 1) * precision_p_c * recall_p_c / (1 * 1 * precision_p_c + recall_p_c)
    f05_p_c = (1 + 0.5 * 0.5) * precision_p_c * recall_p_c / (0.5 * 0.5 * precision_p_c + recall_p_c)

    print('rows', rows)
    print('cnt_predict', cnt_predict_p)
    print('cnt_samples', cnt_samples)
    print('tp_p', tp_p)
    print('tp_p_c', tp_p_c)

    print('\n')

    print('precision_p', round(precision_p, 4))
    print('recall_p', round(recall_p, 4))
    print('f0.5_p', round(f05_p, 4))
    print('f1_p', round(f1_p, 4))

    print('\n')
    print('precision_p_c', round(precision_p_c, 4))
    print('recall_p_c', round(recall_p_c, 4))
    print('f0.5_p_c', round(f05_p_c, 4))
    print('f1_p_c', round(f1_p_c, 4))

    print('\n')
    accuracy_p = cnt_p / rows
    print('accuracy_p', round(accuracy_p, 4))
    accuracy_p_c = cnt_p_c / rows
    print('accuracy_p_c', round(accuracy_p_c, 4))

    # with open('result_place_tree.txt', 'w') as f:
    #     f.write('\n'.join(result_place_tree_lst))

    with open('result/badcase.txt', 'w') as f:
        f.write('\n'.join(bad_case))

    with open('result/error_tp_p', 'w') as f:
        f.write('\n'.join(error_tp_p))

    with open('result/error_fn_p', 'w') as f:
        f.write('\n'.join(error_fn_p))

    with open('result/bad_cities.txt', 'w') as f:
        f.write('\n'.join(bad_cities))


def save2excel(news_lst):
    save_path = '../tmp/tmp.xls'
    if os.path.exists(save_path):
        os.remove(save_path)
    lst_province = []
    lst_city = []
    lst_county = []
    for news in news_lst:
        if news.predict_place['province'] != '':
            lst_province.append(news.predict_place['province'])
        else:
            lst_province.append('')

        if news.predict_place['city'] != '':
            lst_city.append(news.predict_place['city'])
        else:
            lst_city.append('')

        if news.predict_place['county'] != '':
            lst_county.append(news.predict_place['county'])
        else:
            lst_county.append('')

    print(lst_province[0:10])
    print(lst_city[0:10])
    print(lst_county[0:10])

    df = pd.DataFrame()
    df['province'] = lst_province
    df['city'] = lst_city
    df['county'] = lst_county
    df.to_excel(save_path)
