# coding:utf-8
import re
from collections import OrderedDict
from extractPlace import NewsConst
import os


class New(object):
    def __init__(self, id, website, channel, category, reason, title, token, labels, place, nerper, nerper_sorted, nerloc,
                 nerloc_index, nerloc_sorted, nerorg, nerorg_index, nerorg_sorted):
        self.id = id
        self.website = website
        self.channel = channel
        self.category = category
        self.reason = reason
        self.title = title
        self.token = token
        self.labels = labels
        self.place = place
        self.nerper = nerper
        self.nerper_sorted = nerper_sorted
        self.nerloc = nerloc
        self.nerloc_index = nerloc_index
        self.nerloc_sorted = nerloc_sorted
        self.nerorg = nerorg
        self.nerorg_index = nerorg_index
        self.nerorg_sorted = nerorg_sorted

        # 算法预测的结果，省/市/区
        self.predict_place = {}
        self.place_tree_str = ''
        self.place_tree_dic = dict()


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


def parse_merge_file(inpurt_file):
    with open(inpurt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    news = []
    id = ''
    website = ''
    channel = ''
    category = ''
    reason = ''
    title = ''
    token = ''
    labels = ''
    place = {}
    nerper = []
    nerper_sorted = []
    nerloc = []
    nerloc_index = []
    nerloc_sorted = []
    nerorg = []
    nerorg_index = []
    nerorg_sorted = []

    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith('id'):
            if i != 0:
                new = New(id, website, channel, category, reason, title, token, labels, place, nerper, nerper_sorted,
                          nerloc, nerloc_index, nerloc_sorted, nerorg, nerorg_index, nerorg_sorted)
                news.append(new)
            id = line[3:]

        elif line.startswith('website'):
            website = line[8:]
        elif line.startswith('channel'):
            channel = line[8:]
        elif line.startswith('category'):
            category = line[9:]
        elif line.startswith('reason'):
            reason = line[7:]
        elif line.startswith('title'):
            title = line[6:]
        elif line.startswith('token'):
            token = line[6:]
        elif line.startswith('labels'):
            labels = line[7:]
        elif line.startswith('place'):
            lst = line.split('\t')
            place = {}
            place['nation'] = lst[1].split(':')[-1]
            place['province'] = lst[2].split(':')[-1]
            place['city'] = lst[3].split(':')[-1]
            place['county'] = lst[4].split(':')[-1]
        elif line.startswith('nerper_sorted'):
            nerper_sorted = get_list(line[14:])
        elif line.startswith('nerper'):
            nerper = line[7:].split(' ')
        elif line.startswith('nerloc_index'):
            nerloc_index = line[13:].split(' ')
        elif line.startswith('nerloc_sorted'):
            nerloc_sorted = get_list(line[14:])
        elif line.startswith('nerloc'):
            nerloc = line[7:].split(' ')
        elif line.startswith('nerorg_index'):
            nerorg_index = line[13:].split(' ')
        elif line.startswith('nerorg_sorted'):
            nerorg_sorted = get_list(line[14:])
        elif line.startswith('nerorg'):
            nerorg = line[7:].split(' ')

    # last one
    new = New(id, website, channel, category, reason, title, token, labels, place, nerper,
              nerper_sorted, nerloc, nerloc_index, nerloc_sorted, nerorg,
              nerorg_index, nerorg_sorted)
    news.append(new)
    return news


def extract_place_from_org(new, max_length=5, max_sent_index=10, max_character_index=250):
    # 只取前面5个地名，待优化
    orgs = []
    for i in range(len(new.nerorg_index)):
        if ':' not in new.nerorg_index[i]:
            continue
        lst = new.nerorg_index[i].split(':')
        if len(lst) != 3:
            break
        name = lst[0]
        character_index = int(lst[1])
        sent_index = int(lst[2])
        if i >= max_length or sent_index > max_sent_index or character_index > max_character_index:
            break
        orgs.append(name)

    code_count = OrderedDict()
    for word in orgs:
        include_words = set(re.findall(NewsConst.reg_city2code_place, word))
        names = re.findall(NewsConst.reg_include_place, word)

        for name in names:
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
def get_std_locs(new):
    loc_lst = []
    for loc in new.nerloc:
        names = NewsConst.standard_place_dic.get(loc, [loc])
        loc_lst.extend(names)
    return loc_lst


# 获取标准地名,max_length:最多取的地名数   max_sent_index：最大句子索引
def get_place_from_loc(new, max_length=100, max_sent_index=50):
    locs = []
    for i in range(len(new.nerloc_index)):
        if ':' not in new.nerloc_index[i]:
            continue
        sent_index = int(new.nerloc_index[i].split(':')[-1])
        if i >= max_length or sent_index > max_sent_index:
            break
        locs.append(new.nerloc_index[i].split(':')[0])

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
def get_place_from_org(new, max_length=100, max_sent_index=50):
    orgs = []
    for i in range(len(new.nerorg_index)):
        if ':' not in new.nerorg_index[i]:
            continue
        sent_index = int(new.nerorg_index[i].split(':')[-1])
        if i >= max_length or sent_index > max_sent_index:
            break
        orgs.append(new.nerorg_index[i].split(':')[0])

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
def extract_place_from_loc(new, max_length=5, max_sent_index=10, max_character_index=250):
    # 只取前面5个地名，待优化
    locs = []
    for i in range(len(new.nerloc_index)):
        if ':' not in new.nerloc_index[i]:
            continue
        lst = new.nerloc_index[i].split(':')
        if len(lst) != 3:
            break
        name = lst[0]
        character_index = int(lst[1])
        sent_index = int(lst[2])
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


def get_abandon_province(std_locs):
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

    return abandon_p_code


# 返回空预测的新闻
def set_null_predict(new, nation=None):
    if nation:
        new.predict_place['nation'] = nation
        new.predict_place['province'] = 'null'
        new.predict_place['city'] = 'null'
        new.predict_place['county'] = 'null'
    else:
        new.predict_place['province'] = 'null'
        new.predict_place['city'] = 'null'
        new.predict_place['county'] = 'null'


# 国际新闻处理
def is_international_news(new):
    flag = False
    m = re.search(NewsConst.reg_world_nation, new.title)
    nation = ''
    if m:
        nation = m.group(0)
        flag = True
    else:
        # 部分国家简称，如果前两句地点包含此简称，判断为国际新闻
        max_sent_index = 2
        for loc_index in new.nerloc_index:
            arr = loc_index.split(':')

            if len(arr) != 3 or int(arr[-1]) > max_sent_index:
                break
            if arr[0] in NewsConst.world_nation_abbreviation.keys():
                nation = NewsConst.world_nation_abbreviation[arr[0]]
                flag = True
                break
    lst = ['欧洲', '美洲', '非洲']
    if flag:
        # set_null_predict(new, nation)
        if nation not in lst:
            set_null_predict(new, nation)
        else:
            set_null_predict(new)

    return flag


# 是否存在新闻地名
def is_exist_place(new, std_locs):
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
        set_null_predict(new)
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
        set_null_predict(new)
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

    if flag:
        set_null_predict(new)

    return flag


# 在+地名
def strong_rule(new, max_sent_index=1, max_character_index=200):
    code = 0
    new_tokens = str(new.token).split(' ')
    for i in range(len(new.nerloc_index)):
        if ':' not in new.nerloc_index[i]:
            continue
        arr = new.nerloc_index[i].split(':')
        if len(arr) != 3:
            break
        name = arr[0]
        character_index = int(arr[1])
        sent_index = int(arr[2])
        if sent_index > max_sent_index or i > max_character_index:
            break
        # print(new_tokens[character_index - 1])
        # 在+地名+后面rule_words单词，则符合强规则
        rule_words = ['启动', '举行', '开幕', '发布', '召开', '举办', '实施']
        # rule_words = ['启动']
        after_words_start_index = character_index + len(name)
        after_words = ''.join(new_tokens[after_words_start_index:after_words_start_index + 2])
        # if new_tokens[character_index - 1] == '在' and after_words in rule_words:
        if new_tokens[character_index - 1] == '在':
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
        rule_province_code = code // 10000 * 10000
        province_name = NewsConst.code2city[rule_province_code]
        # 直辖市
        if province_name in NewsConst.municipality:
            rule_city_code = rule_province_code
            if code % 100 != 0:
                rule_county_code = code
        else:
            rule_city_code = code // 100 * 100
            if code % 100 != 0:
                rule_county_code = code

    # if rule_province_code != 0 and new.place['province'] != NewsConst.code2city[rule_province_code]:
    #     print(new.id)
    #     print('label\t' + new.place['province'])
    #     print('predict\t' + NewsConst.code2city[rule_province_code])

    return rule_province_code, rule_city_code, rule_county_code

    # 根据loc 与地点 的份加权


def extract_place(new):
    print(new.id)
    # if new.id != '33':
    #     return

    # ------规则1: 判断是否国际新闻
    if is_international_news(new):
        return
    # ------规则2:判断是否国家各大部委发布的新闻,persent为组织机构占的百分比
    if is_major_department_news(new, persent=0.8):
        return

    # ------规则3:强规则，就是 ：在+地名--begin
    rule_province_code, rule_city_code, rule_county_code = strong_rule(new, max_sent_index=3, max_character_index=200)
    # rule_province_code, rule_city_code, rule_county_code = 0, 0, 0
    if rule_county_code != 0:
        new.predict_place['province'] = NewsConst.code2city[rule_province_code]
        new.predict_place['city'] = NewsConst.code2city[rule_city_code]
        new.predict_place['county'] = NewsConst.code2city[rule_county_code]
        return
    # ------规则3:强规则，就是 ：在+地名--end

    # ------规则4:判断新闻是否存在地名---begin
    # 求映射的标准地名standard loc
    std_locs = get_place_from_loc(new, 100, 50)
    std_org_locs = get_place_from_org(new, 100, 50)
    std_locs.extend(std_org_locs)
    # print(new_locs)precision_p

    if len(std_locs) == 0:
        set_null_predict(new)
        return

    # 强规则优先处理，对省份进行筛选,比例最高的省份需要大于pValue=0.2
    if rule_province_code == 0:
        if not is_exist_place(new, std_locs):
            return
    # ------规则4:判断新闻是否存在地名---end

    # ------规则5:如果区/县对应的市或者省没有出现，则区/县则被过滤掉(排除直辖市)
    # 注意：如果新闻中只有一个省，那么不能丢弃
    abandon_p_code = get_abandon_province(std_locs)

    # 字符索引作影响不是很大
    loc_sorted_p_count, loc_sorted_city_count, loc_sorted_county_count = extract_place_from_loc(new, 10, 7, 300)
    org_sorted_p_count, org_sorted_city_count, org_sorted_county_count = extract_place_from_org(new, 10, 7, 300)

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
    province_name = 'null'
    if len(abandon_p_code) == 0:
        province_name = NewsConst.code2city[sorted_p_score[0][1][0]] if len(sorted_p_score) > 0 else 'null'
    else:
        for score_codes in sorted_p_score:
            if province_name != 'null':
                break
            for p_code in score_codes[1]:
                if p_code not in abandon_p_code:
                    province_name = NewsConst.code2city[p_code]
                    break

    # 强规则优先----设置省--begin
    if rule_province_code != 0:
        province_name = NewsConst.code2city[rule_province_code]
    # 强规则优先----设置省--end

    city_name = 'null'
    county_name = 'null'
    city_code = 0
    #  找省下面的市、区县
    if province_name != 'null':
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
                if county_name != 'null':
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
        city_name = 'null'
        county_name = 'null'

    new.predict_place['province'] = province_name
    new.predict_place['city'] = city_name
    new.predict_place['county'] = county_name


def record_result(new, lst):
    lst.append('id\t' + new.id)
    lst.append('token\t' + new.token)
    lst.append('lables\t' + new.labels)
    lst.append('place\tnation(国家):' + new.place['nation'] + '\tprovince(省):'
               + new.place['province'] + '\tcity(市):' + new.place['city']
               + '\tcounty(县):' + new.place['county'])
    lst.append('nerloc\t' + ' '.join(new.nerloc))
    lst.append('nerloc_sorted\t' + ' '.join(new.nerloc_sorted))
    lst.append('nerorg\t' + ' '.join(new.nerorg))
    lst.append('nerorg_sorted\t' + ' '.join(new.nerorg_sorted))
    lst.append('predict_place\tnation(国家):null\tprovince(省):' + new.predict_place['province']
               + '\tcity(市):' + new.predict_place['city']
               + '\tcounty(县):' + new.predict_place['county'])
    lst.append('predict_place_tree\t' + new.place_tree_str)
    lst.append('\n')


def record_error(new, lst):
    lst.append('id\t' + new.id)
    lst.append('website\t' + new.website)
    lst.append('channel\t' + new.channel)
    lst.append('category\t' + new.category)
    lst.append('reason\t' + new.reason)
    lst.append('title\t' + new.title)
    lst.append('token\t' + new.token)
    lst.append('lables\t' + new.labels)
    lst.append('place\tnation(国家):' + new.place['nation'] + '\tprovince(省):'
               + new.place['province'] + '\tcity(市):' + new.place['city']
               + '\tcounty(县):' + new.place['county'])
    lst.append('nerloc\t' + ' '.join(new.nerloc))
    lst.append('nerloc_index\t' + ' '.join(new.nerloc_index))
    lst.append('nerloc_sorted\t' + ' '.join(new.nerloc_sorted))
    lst.append('nerorg\t' + ' '.join(new.nerorg))
    lst.append('nerorg_index\t' + ' '.join(new.nerorg_index))
    lst.append('nerorg_sorted\t' + ' '.join(new.nerorg_sorted))
    lst.append('predict_place\tnation(国家):null\tprovince(省):' + new.predict_place['province']
               + '\tcity(市):' + new.predict_place['city']
               + '\tcounty(县):' + new.predict_place['county'])
    lst.append('\n')


# 评估算法的结果
def result_evaluate(news):
    rows = len(news)
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
    for new in news:
        # if new.id == '139':
        #     print('note')
        province = new.place['province']
        city = new.place['city'].strip()
        predict_province = new.predict_place['province']
        predict_city = new.predict_place['city']

        if province == predict_province:
            cnt_p += 1

        if province == predict_province and city == predict_city:
            cnt_p_c += 1

        if province != 'null':
            cnt_samples += 1
            record_result(new, result_place_tree_lst)

        if predict_province != 'null':
            cnt_predict_p += 1

        if predict_province == province and predict_province != 'null':
            tp_p += 1

        if province == predict_province and city == predict_city and predict_province != 'null':
            tp_p_c += 1

        # 记录错误 --begin
        if predict_province != province and predict_province != 'null':
            record_error(new, error_tp_p)

        if predict_province != province and predict_province == 'null':
            record_error(new, error_fn_p)

        if predict_province != province and province != 'null':
            record_error(new, bad_case)

        if province == predict_province and city != predict_city and predict_province != 'null':
            record_error(new, bad_cities)
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


def main():
    # inpurt_file = 'conf/merge_before.txt'
    merge_file = 'input/merge.txt'
    news = parse_merge_file(merge_file)
    for new in news:
        # 方法2：运用打分制
        extract_place(new)

    result_evaluate(news)
    print('\t')


if __name__ == '__main__':
    main()
