import pickle
import re
from collections import OrderedDict
from NewsPlaceExtract import NewsConst
from NewsPlaceExtract.Evaluate import result_evaluate, save2excel
import os

from NewsPlaceExtract import FileTools
from NewsPlaceExtract.News import createNews
from datetime import datetime


def load_model(file_name):
    """用于加载模型"""
    with open(file_name, "rb") as f:
        model = pickle.load(f)
    return model


model_path = 'model/crf.pkl'
model_crf = load_model(model_path)


# 对省份进行筛选，参数需要传（addList:[地点名]，city2code，code2city，pValue：阈值默认0.2）
def get_threshold_province(std_locs, pValue=0.2):  # addList为匹配后的地名list,pValue:大于阈值返回list，包含地名
    error = []
    threshold_province = []
    provinceList = []
    try:
        # provinceList = [code2city[j[:2]+'0000'] for i in addList if i in city2code for j in city2code[i] else i]
        for loc in std_locs:
            if loc in NewsConst.city2code:
                # print(add)
                midPro = [NewsConst.code2city[i // 10000 * 10000] for i in NewsConst.city2code[loc]]
                # print(midPro)
                provinceList.extend(midPro)
            else:
                provinceList.append(loc)
        lenpro = len(provinceList)

        # print(provinceList)
        for pro in list(set(provinceList)):
            midValue = provinceList.count(pro) / lenpro
            # if midValue >= pValue and pro not in NewsConst.filter:
            if midValue >= pValue:
                threshold_province.append((pro, midValue))
            else:
                pass
    except Exception as e:
        print(str(e))
        error.append((std_locs, e))
        # print(error)

    return threshold_province  # return 的是（省名，省名所占比例）


def dictSort_bak(input_dict):
    return sorted(input_dict.items(), key=lambda x: x[1], reverse=True)


# 排序，如果次数相同，则按照顺序排列
def dictSort(input_dict):
    ret = dict()
    for code, cnt in input_dict.items():
        if cnt not in ret.keys():
            lst = []
            lst.append(code)
            ret[cnt] = lst
        else:
            ret[cnt].append(code)
    return sorted(ret.items(), key=lambda x: x[0], reverse=True)


def get_list(txt):
    pattern = '\(.*?\)'
    lst = re.findall(pattern, txt)
    return lst


def extract_place_from_org(news, max_length=5, max_sent_index=10, max_character_index=250):
    # 只取前面5个地名，待优化
    orgs = []
    for i in range(len(news.nerorg_index)):
        if ':' not in news.nerorg_index[i]:
            continue
        lst = news.nerorg_index[i].split(':')
        if len(lst) != 4:
            break
        name = lst[0]
        character_index = int(lst[3])
        sent_index = int(lst[1])
        if i >= max_length or sent_index > max_sent_index or character_index > max_character_index:
            break
        orgs.append(name)

    code_count = OrderedDict()
    for word in orgs:
        # word = '北京市海淀区广西医院'
        # 标准匹配
        include_words = set(re.findall(NewsConst.reg_city2code_place, word))
        # 包含匹配
        names = re.findall(NewsConst.reg_include_place, word)

        for name in names:
            # 映射后再并集
            include_words = include_words | set(NewsConst.include_place_dic[name])

        for include_word in include_words:
            include_codes = NewsConst.city2code[include_word]
            for include_code in include_codes:
                code_count[include_code] = code_count.get(include_code, 0) + 1

    if len(code_count) == 0:
        return [], [], []

    p_count = OrderedDict()  # 省级
    city_count = OrderedDict()  # 市级
    county_count = OrderedDict()  # 县级
    for code, count in code_count.items():
        p_code = code // 10000 * 10000  # 去掉后4位上的编号，映射成省级
        p_count[p_code] = p_count.get(p_code, 0) + count

        if code % 10000 == 0:  # 只有省级信息没有市级信息
            continue
        city_code = code // 100 * 100  # 去掉后2位上的编号，映射成市级
        if city_code in NewsConst.code2city:  # 110100 市辖区,这种编码去掉，海淀区110108这种编码处理之后得到的市级编码不存在
            city_count[city_code] = city_count.get(city_code, 0) + count

        if code % 100 == 0:
            continue
        county_code = code
        if county_code in NewsConst.code2city:
            county_count[county_code] = county_count.get(county_code, 0) + count

    # 次数：[省]
    sorted_p_count = dictSort(p_count)
    # print(sorted_p_count[0][1][0])
    # 次数：[市]
    sorted_city_count = dictSort(city_count)
    # 次数：[县/区]
    sorted_county_count = dictSort(county_count)
    return sorted_p_count, sorted_city_count, sorted_county_count


# 获取标准的locs
def get_std_locs(news):
    loc_lst = []
    for loc in news.nerloc:
        names = NewsConst.standard_place_dic.get(loc, [loc])
        loc_lst.extend(names)
    return loc_lst


# 获取标准地名,max_length:最多取的地名数   max_sent_index：最大句子索引
def get_place_from_loc(news, max_length=100, max_sent_index=50):
    locs = []
    for i in range(len(news.nerloc_index)):
        if ':' not in news.nerloc_index[i]:
            continue

        arr = news.nerloc_index[i].split(':')
        if len(arr) != 4:
            continue
        sent_index = int(arr[1])
        if i >= max_length or sent_index > max_sent_index:
            break
        locs.append(arr[0])

    loc_lst = []
    for loc in locs:
        names = NewsConst.standard_place_dic.get(loc, [loc])
        loc_lst.extend(names)

    # 包含
    ret = []
    for loc in loc_lst:
        tmp = set()
        if loc in NewsConst.city2code.keys():
            tmp.add(loc)
        # 包含
        if len(tmp) == 0:
            tmp = set(re.findall(NewsConst.reg_city2code_place, loc))
            # 一个地名中可能存在多个子地名
            # if len(tmp) == 0:
            # 正则取代循环
            # for k, v in include_place_dic.items():
            #     if k in loc and len(k) > 1:
            #         tmp = include_place_dic[k]
            #         break
            names = re.findall(NewsConst.reg_include_place, loc)
            if names:
                for name in names:
                    # 求并集
                    tmp = tmp | set(NewsConst.include_place_dic[name])
        if tmp:
            ret.extend(list(tmp))
        else:
            ret.append(loc)
    return ret


# 获取标准地名
def get_place_from_org(news, max_length=100, max_sent_index=50):
    orgs = []
    for i in range(len(news.nerorg_index)):
        if ':' not in news.nerorg_index[i]:
            continue

        arr = news.nerorg_index[i].split(':')
        if len(arr) != 4:
            continue

        sent_index = int(arr[1])
        if i >= max_length or sent_index > max_sent_index:
            break
        orgs.append(arr[0])

    ret = []
    for org in orgs:
        tmp = set()
        #  可能出现： 无锡锡山区政协党组
        # for k, v in NewsConst.city2code.items():
        #     if k in org and len(k) > 1:
        #         tmp.add(k)
        tmp = set(re.findall(NewsConst.reg_city2code_place, org))
        # if len(tmp) == 0:
        #  可能出现： 无锡锡山区政协党组，这里匹配无锡
        names = re.findall(NewsConst.reg_include_place, org)
        if names:
            for name in names:
                tmp = tmp | set(NewsConst.include_place_dic[name])
        if tmp:
            ret.extend(list(tmp))
    return ret


# 从地名中抽取
def extract_place_from_loc(news, max_length=5, max_sent_index=10, max_character_index=250):
    # 只取前面5个地名，待优化
    locs = []
    for i in range(len(news.nerloc_index)):
        if ':' not in news.nerloc_index[i]:
            continue
        lst = news.nerloc_index[i].split(':')
        if len(lst) != 4:
            break
        name = lst[0]
        character_index = int(lst[3])
        sent_index = int(lst[1])
        if i >= max_length or sent_index > max_sent_index or character_index > max_character_index:
            break
        locs.append(name)

    # if len(new.nerloc) > max_length:
    #     locs = new.nerloc[0:max_length]
    # else:
    #     locs = new.nerloc
    loc_lst = []
    for loc in locs:
        names = NewsConst.standard_place_dic.get(loc, [loc])
        loc_lst.extend(names)

    # 这里能用set，set 无序，前面出现的地名为新闻地名概率更大，去掉重复的地址
    # loc_clean = []
    # for loc in loc_lst:
    #     if loc not in loc_clean:
    #         loc_clean.append(loc)

    # word_count = {k: loc_lst.count(k) for k in word_set}

    code_count = OrderedDict()
    for word in loc_lst:
        if word.strip() in NewsConst.filter:
            continue
        if word not in NewsConst.city2code.keys():
            codes = []
        else:
            codes = NewsConst.city2code[word]

        # 注意，对于一个word对应多个 code的，我们权重暂时看为一样
        for code in codes:
            code_count[code] = code_count.get(code, 0) + 1

        ###############loc 包含 --begin##############
        # 运用包含规则，ner地名中包含简称，且简称长度必须大于2
        else:
            include_words = set()
            # for k, v in city2code.items():
            #     if k in word and len(k) > 1:
            #         include_words.append(k)
            include_words = set(re.findall(NewsConst.reg_city2code_place, word))

            # if len(include_words) == 0:
            # for k, v in include_place_dic.items():
            #     if k in word and len(k) > 1:
            #         include_words.extend(include_place_dic[k])
            names = re.findall(NewsConst.reg_include_place, word)
            for name in names:
                include_words = include_words | set(NewsConst.include_place_dic[name])

            for include_word in include_words:
                include_codes = NewsConst.city2code[include_word]
                for include_code in include_codes:
                    code_count[include_code] = code_count.get(include_code, 0) + 1
                    ###############loc 包含 --end##############

    if len(code_count) == 0:
        return [], [], []

    # 没必要排序
    # sorted_codeCount = dictSort(code_count)  ######[(110000, 3), (130000, 1),...]
    p_dict = OrderedDict()  # 省级
    city_count = OrderedDict()  # 市级
    county_count = OrderedDict()  # 县级
    for code, count in code_count.items():
        p_code = code // 10000 * 10000  # 去掉后4位上的编号，映射成省级
        p_dict[p_code] = p_dict.get(p_code, 0) + count

        if code % 10000 == 0:  # 只有省级信息没有市级信息
            continue
        city_code = code // 100 * 100  # 去掉后2位上的编号，映射成市级
        if city_code in NewsConst.code2city:  # 110100 市辖区,这种编码去掉，海淀区110108这种编码处理之后得到的市级编码不存在
            city_count[city_code] = city_count.get(city_code, 0) + count

        if code % 100 == 0:
            continue
        county_code = code
        if county_code in NewsConst.code2city:
            county_count[county_code] = county_count.get(county_code, 0) + count

    # 次数：[省]
    sorted_p_count = dictSort(p_dict)
    # print(sorted_p_count[0][1][0])
    # 次数：[市]
    sorted_city_count = dictSort(city_count)
    # 次数：[县/区]
    sorted_county_count = dictSort(county_count)
    return sorted_p_count, sorted_city_count, sorted_county_count


# 权重，地名权重为1，机构中的权重为0.5
def get_code_score(loc_dic, org_dic, loc_weight=1, org_weight=1):
    dic = OrderedDict()
    for score_codes in loc_dic:
        score = score_codes[0] * loc_weight
        codes = score_codes[1]
        for code in codes:
            dic[code] = dic.get(code, 0) + score

    for score_codes in org_dic:
        score = score_codes[0] * org_weight
        codes = score_codes[1]
        for code in codes:
            dic[code] = dic.get(code, 0) + score
    ret = dictSort(dic)
    return ret


def get_abandon_province(std_locs, news):
    province_count = dict()
    county_count = dict()
    abandon_p_code = set()
    for loc in std_locs:
        if loc not in NewsConst.city2code.keys():
            continue
        codes = NewsConst.city2code[loc]
        for code in codes:
            p_code = code // 10000 * 10000
            province_count[p_code] = province_count.get(p_code, 0) + 1

            if code % 100 != 0:
                c_code = code // 100 * 100
                # c_code not in code2city.keys() 表示直辖市
                if c_code in NewsConst.code2city.keys():
                    county_count[code] = county_count.get(code, 0) + 1

    for code, cnt in county_count.items():
        p_code = code // 10000 * 10000
        # 当区/县 对应 的省出现次数 等于 该省的次数:当出现一个县或区，但是没有出现该城市的市或者省，则丢弃此省份
        if province_count[p_code] == cnt:
            abandon_p_code.add(p_code)

    # 参考频道
    channel_province_code = get_channel_province(news)
    for code in abandon_p_code:
        if code == channel_province_code:
            abandon_p_code.remove(code)
            break

    return abandon_p_code


# 返回空预测的新闻
def get_null_predict(predict_place, nation=None):
    if nation:
        predict_place['nation'] = nation
        predict_place['province'] = ''
        predict_place['city'] = ''
        predict_place['county'] = ''
    else:
        predict_place['province'] = ''
        predict_place['city'] = ''
        predict_place['county'] = ''

    return predict_place


# 国际新闻处理
def is_international_news(news):
    flag = False
    m = re.search(NewsConst.reg_world_nation, news.title)
    if m:
        flag = True
    else:
        # 部分国家简称，如果前两句地点包含此简称，判断为国际新闻
        max_sent_index = 2
        for loc_index in news.nerloc_index:
            arr = loc_index.split(':')

            if len(arr) != 4 or int(arr[1]) > max_sent_index:
                break
            if arr[0] in NewsConst.world_nation_abbreviation.keys():
                flag = True
                break

    return flag


# 是否存在新闻地名
def is_exist_place(std_locs):
    flag = True
    # 规则1: 地点或者省太多则判断没有地点--begin
    province_set = set()
    loc_set = set()
    max_province = 9
    max_loc = 18
    for loc in std_locs:
        if loc in NewsConst.city2code.keys():
            loc_set.add(loc)
            codes = NewsConst.city2code[loc]
            for code in codes:
                province_set.add(code // 10000 * 10000)

    if len(province_set) > max_province or len(loc_set) > max_loc:
        flag = False
    #  地点或者省太多则判断没有地点---end

    # 规则2：对省份进行筛选，占比最大的省必须>=pValue,才表示存在地点。
    threshold_province_1 = get_threshold_province(std_locs, pValue=0.2)
    threshold_province_2 = []
    # 规则3：规则2可能太严格，我们需要判断前10个，阈值设置为0.4
    max_length = 10
    if len(std_locs) > max_length:
        threshold_province_2 = get_threshold_province(std_locs[:max_length], pValue=0.4)
    if len(threshold_province_1) == 0 and len(threshold_province_2) == 0:
        flag = False

    return flag


# 判断是否国家各大部委发布的新闻，这种新闻没有地名
def is_major_department_news(new, persent=0.5):
    flag = False
    if len(new.nerorg) == 0:
        return flag
    cnt = 0
    for org in new.nerorg:
        if org in NewsConst.major_department_set:
            cnt += 1
    # 如果部委在机构中占比>= persent，判定此新闻为部委发布，新闻没有地点
    if cnt / len(new.nerorg) >= persent:
        flag = True

    return flag


# 在+地名
def strong_rule(news, max_sent_index=1, max_character_index=200):
    code = 0
    for i in range(len(news.nerloc_index)):
        if ':' not in news.nerloc_index[i]:
            continue
        arr = news.nerloc_index[i].split(':')
        if len(arr) != 4:
            break
        name = arr[0]
        sent_index = int(arr[1])
        word_index_of_sentence = int(arr[2])
        word_index_of_content = int(arr[3])

        if sent_index > max_sent_index or word_index_of_content > max_character_index:
            break
        # print(new_tokens[character_index - 1])
        # 在+地名+后面rule_words单词，则符合强规则
        rule_words = ['启动', '举行', '开幕', '发布', '召开', '举办', '实施']
        # rule_words = ['启动']
        # after_words_start_index = character_index + len(name)

        # after_words = ''.join(new_tokens[after_words_start_index:after_words_start_index + 2])
        # if new_tokens[character_index - 1] == '在' and after_words in rule_words:
        if word_index_of_sentence > 0:
            pre_character = news.text[sent_index][word_index_of_sentence - 1]
            if pre_character == '在':
                # print(new.id)
                # print(''.join(after_words))
                loc_lst = []
                if name in NewsConst.city2code.keys():
                    loc_lst = [name]
                if len(loc_lst) == 0:
                    loc_lst = NewsConst.standard_place_dic.get(name, [])
                #  如果存在多个地名，不作判断
                if len(loc_lst) == 1:
                    code = NewsConst.city2code[loc_lst[0]][0]
                    break

    rule_province_code = 0
    rule_city_code = 0
    rule_county_code = 0
    if code != 0:
        # is province?
        rule_province_code = code // 10000 * 10000
        province_name = NewsConst.code2city[rule_province_code]
        # 直辖市
        if province_name in NewsConst.municipality:
            rule_city_code = rule_province_code

        if code % 10000 != 0 and rule_city_code == 0:
            rule_city_code = code // 100 * 100
        if code % 100 != 0:
            rule_county_code = code

    return rule_province_code, rule_city_code, rule_county_code

    # 根据loc 与地点 的份加权


# 用规则清洗一些地名
def clean_locs(news):
    # 1 去掉句式：5月23日电/讯
    reg_str = '\d{1,2}月\d{1,2}日[电讯]'
    pattern = re.compile(reg_str)  # 将正则表达式编译成Pattern对象
    index_remove = []  # 记录被删除的索引
    for i in range(len(news.nerloc_index)):
        arr = news.nerloc_index[i].split(':')
        if len(arr) != 4:
            break
        loc = arr[0]
        sentence_index = int(arr[1])
        word_index_of_sentence = int(arr[2])
        if sentence_index > 3:
            break
        txt = news.text[sentence_index]
        # 使用Pattern匹配文本，获得匹配结果，无法匹配时将返回None，必须用search
        match = pattern.search(txt)
        if match:
            start = match.start()
            if word_index_of_sentence + len(loc) == start:
                index_remove.append(i)

    if index_remove:
        update_nerloc = []
        update_nerloc_index = []
        # 注意，当len(index_remove) > 1，不能根据索引删除list元素
        for i in range(len(news.nerloc_index)):
            if i not in index_remove:
                update_nerloc.append(news.nerloc[i])
                update_nerloc_index.append(news.nerloc_index[i])

        news.nerloc = update_nerloc
        news.nerloc_index = update_nerloc_index


# 根据频道的省市区，获取对应预测
def get_channel_predict(news):
    include_words = re.findall(NewsConst.reg_city2code_place, news.channel)
    if include_words:
        for include_word in include_words:
            include_codes = NewsConst.city2code[include_word]
            if len(include_codes) == 1:
                p_code = include_codes[0] // 10000 * 10000
                return p_code
            else:
                for include_code in include_codes:
                    if include_code % 10000 == 0:
                        return include_code

    # 包含匹配
    names = re.findall(NewsConst.reg_include_place, news.channel)

    for name in names:
        include_words.extend(NewsConst.include_place_dic[name])

    channel_province_codes = []
    for include_word in include_words:
        include_codes = NewsConst.city2code[include_word]
        for include_code in include_codes:
            p_code = include_code // 10000 * 10000
            channel_province_codes.append(p_code)
    # 计算排名最高的
    channel_province_codes.sort(reverse=True)
    if channel_province_codes:
        return channel_province_codes[0]
    else:
        return 0


# 根据频道获取省份,注意，频道对应的省份一定是唯一的
def get_channel_province(news):
    include_words = re.findall(NewsConst.reg_city2code_place, news.channel)
    if include_words:
        for include_word in include_words:
            include_codes = NewsConst.city2code[include_word]
            if len(include_codes) == 1:
                p_code = include_codes[0] // 10000 * 10000
                return p_code
            else:
                for include_code in include_codes:
                    if include_code % 10000 == 0:
                        return include_code

    # 包含匹配
    names = re.findall(NewsConst.reg_include_place, news.channel)

    for name in names:
        include_words.extend(NewsConst.include_place_dic[name])

    channel_province_codes = []
    for include_word in include_words:
        include_codes = NewsConst.city2code[include_word]
        for include_code in include_codes:
            p_code = include_code // 10000 * 10000
            channel_province_codes.append(p_code)
    # 计算排名最高的
    channel_province_codes.sort(reverse=True)
    if channel_province_codes:
        return channel_province_codes[0]
    else:
        return 0


# 如果新闻中没有地点，则考虑匹配我市|市委|全市，匹配成功则提取站点或频道中的地点
# 存在问题，需要考虑 一个市区对应多个市
def get_local_place(news):
    p_code = 0
    city_code = 0
    county_code = 0

    pattern = '我省|本省|全省|省委|我市|本市|全市|市委|我区|本区|全区|区委|我县|本县|全县|县委|主城区'
    pattern = '我省|本省|我市|本市|我县|本县|主城区'
    m = re.search(pattern, str(news.text))
    if m:
        name = []
        if len(name) == 0:
            name = re.findall(NewsConst.reg_include_place, news.website)
        if len(name) == 0:
            name = re.findall(NewsConst.reg_include_place, news.channel)
        if len(name) != 0:
            # 需要优化，考虑多个地址
            include_code = NewsConst.city2code[NewsConst.standard_place_dic[name[0]][0]]
            p_code = include_code[0] // 10000 * 10000  # 去掉后4位上的编号，映射成省级
            if include_code[0] % 10000 != 0:
                city_code = include_code[0] // 100 * 100  # 去掉后2位上的编号，映射成市级
                if include_code[0] % 100 != 0:
                    county_code = include_code

    return p_code, city_code, county_code


def extract_place(news):
    predict_place = dict()
    predict_place['province'] = ''
    predict_place['city'] = ''
    predict_place['county'] = ''

    # if new.id != '1704':
    #     return

    # ------规则1: 判断是否国际新闻
    if is_international_news(news):
        # lst = ['欧洲', '美洲', '非洲']
        # predict_place = get_null_predict(predict_place)
        return predict_place

    # ------规则2:判断是否国家各大部委发布的新闻,persent为组织机构占的百分比
    if is_major_department_news(news, persent=0.8):
        # predict_place = get_null_predict(news)
        return predict_place

    # 用规则清洗一些地名
    clean_locs(news)

    # ------规则3:强规则，就是 ：在+地名--begin
    # rule_province_code, rule_city_code, rule_county_code = strong_rule(news, max_sent_index=2, max_character_index=200)
    # ------规则3.2：# 如果新闻中没有地点，则考虑匹配我市|本市|市委|全市，匹配成功则提取站点或频道中的地点----begin
    rule_province_code, rule_city_code, rule_county_code = get_local_place(news)
    # rule_province_code = 0
    # rule_city_code = 0
    # rule_county_code = 0

    # rule_province_code, rule_city_code, rule_county_code = 0, 0, 0
    # if rule_county_code != 0:
    #     predict_place['province'] = NewsConst.code2city[rule_province_code]
    #     predict_place['city'] = NewsConst.code2city[rule_city_code]
    #     predict_place['county'] = NewsConst.code2city[rule_county_code]
    #     return predict_place
    # ------规则3:强规则，就是 ：在+地名--end

    # ------规则4:判断新闻是否存在地名---begin
    # 求映射的标准地名standard loc
    std_locs = get_place_from_loc(news, 100, 50)
    std_org_locs = get_place_from_org(news, 100, 50)
    std_locs.extend(std_org_locs)
    # print(new_locs)precision_p

    # 强规则优先处理，对省份进行筛选,比例最高的省份需要大于pValue=0.2
    if rule_province_code == 0:
        if not is_exist_place(std_locs):
            # predict_place = get_null_predict(news)
            return predict_place
    # ------规则4:判断新闻是否存在地名---end



    # ------规则5：# 如果新闻中没有地点，则考虑匹配我市|本市|市委|全市，匹配成功则提取站点或频道中的地点----end

    # ------规则6:如果区/县对应的市或者省没有出现，则区/县则被过滤掉(排除直辖市)
    # 注意：如果新闻中只有一个省，那么不能丢弃；如果丢弃的地点属于XX频道，属于xx，则不丢弃
    abandon_p_code = get_abandon_province(std_locs, news)

    # 字符索引作影响不是很大
    loc_sorted_p_count, loc_sorted_city_count, loc_sorted_county_count = extract_place_from_loc(news, 10, 6, 300)
    org_sorted_p_count, org_sorted_city_count, org_sorted_county_count = extract_place_from_org(news, 10, 6, 300)

    # 对地名与机构打分。权重，地名权重为1，机构中的权重为0.5
    loc_weight = 1
    org_weight = 0.8
    sorted_p_score = get_code_score(loc_sorted_p_count, org_sorted_p_count, loc_weight, org_weight)
    sorted_city_score = get_code_score(loc_sorted_city_count, org_sorted_city_count, loc_weight, org_weight)
    sorted_county_score = get_code_score(loc_sorted_county_count, org_sorted_county_count, loc_weight, org_weight)

    # print(sorted_p_count)
    # [(3.5, [350000]), (2, [360000])]

    # 注意：如果新闻中只有一个省，那么不能丢弃--begin
    p_code_set = set()
    for score_codes in sorted_p_score:
        for code in score_codes[1]:
            p_code_set.add(code)
    if len(p_code_set) == 1:
        abandon_p_code.clear()

    # 注意：如果新闻中只有一个省，那么不能丢弃--end
    province_name = ''
    if len(abandon_p_code) == 0:
        province_name = NewsConst.code2city[sorted_p_score[0][1][0]] if len(sorted_p_score) > 0 else ''
    else:
        for score_codes in sorted_p_score:
            if province_name != '':
                break
            for p_code in score_codes[1]:
                if p_code not in abandon_p_code:
                    province_name = NewsConst.code2city[p_code]
                    break

    # 强规则优先----设置省--begin
    if rule_province_code != 0:
        province_name = NewsConst.code2city[rule_province_code]
    # 强规则优先----设置省--end

    city_name = ''
    county_name = ''
    city_code = 0
    #  找省下面的市、区县
    if province_name != '':
        province_code = NewsConst.city2code[province_name][0]
        for city_tuple in sorted_city_score:
            if city_code != 0:
                break
            city_codes = city_tuple[1]
            for code in city_codes:
                if code // 10000 * 10000 == province_code:
                    city_name = NewsConst.code2city[code]
                    city_code = code
                    break

        # 判断直辖市
        if province_name in NewsConst.municipality:
            city_name = province_name
            city_code = NewsConst.city2code[city_name][0]

        # 强规则优先----设置市---begin
        if rule_city_code != 0:
            city_name = NewsConst.code2city[rule_city_code]
            city_code = rule_city_code
        # 强规则优先----设置市---end

        if city_code != 0:
            for county_tuple in sorted_county_score:
                if county_name != '':
                    break
                county_codes = county_tuple[1]
                for code in county_codes:
                    my_p_name = NewsConst.code2city[code // 10000 * 10000]
                    # 直辖市特殊处理
                    if my_p_name == province_name and province_name in NewsConst.municipality:
                        county_name = NewsConst.code2city[code]
                        break
                    elif code // 100 * 100 == city_code:
                        county_name = NewsConst.code2city[code]
                        break

        # 强规则优先----设置区县---begin
        if rule_county_code != 0:
            county_name = NewsConst.code2city[rule_county_code]
        # 强规则优先----设置区县---end

    expect_province = ['台湾省', '香港特别行政区', '澳门特别行政区']
    if province_name in expect_province:
        city_name = ''
        county_name = ''

    predict_place['province'] = province_name
    predict_place['city'] = city_name
    predict_place['county'] = county_name
    return predict_place


def main():
    time_begin = datetime.now()
    input_file = '../data/News-merge_news1_news2-20190523.xls'
    input_file = '../data/News-weibo-20190523.xls'
    # input_file = '../data/1000_news.xls'
    # input_file = '../data/News-稿件导出wechat-20190523.xls'

    # 去掉 留言信息等非新闻文本
    clean = []
    if input_file == '../data/1000_news.xls':
        clean = [981, 982, 984, 985, 986, 987, 988, 989, 990, 992, 993, 994, 995, 936, 938, 797, 798, 799, 800, 801,
                 802, 803, 106, 108, 109, 110, 121, 126, 142, 143, 149, 151, 159, 177, 182, 190, 191, 196, 198, 201,
                 206, 212, 250, 255, 262, 269, 293, 295, 300, 302, 305, 308, 337, 340, 352, 362, 368, 375, 391, 399,
                 402, 403, 405, 416, 470, 471, 479, 487, 505]

    df = FileTools.read_xls_data(input_file)
    news_lst = []
    for index, row in df.iterrows():
        print('index: ' + str(index))
        # if index != 293:
        #     continue

        if index in clean:
            continue

        lst = []
        for v in row['text']:
            lst.append(list(v))
        pred_tags = model_crf.test(lst)
        news = createNews(index, row, pred_tags)
        news.predict_place = extract_place(news)
        news_lst.append(news)

    result_evaluate(news_lst)

    is_save2excel = True
    if is_save2excel:
        save2excel(news_lst)

    print('program run time: ' + str(datetime.now() - time_begin))


if __name__ == '__main__':
    main()
