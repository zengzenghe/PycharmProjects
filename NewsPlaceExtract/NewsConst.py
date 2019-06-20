# coding=utf-8


# 常量文件
# 创建正则表达式，主要用于包含字符串查询
def create_world_city_reg(file_path, min_length):
    names_dic = dict()
    with open(file_path, 'r', encoding='utf-8') as f:
        for name in f:
            name = name.strip()
            l = len(name)
            if l < min_length:
                continue
            if l not in names_dic.keys():
                name_set = set()
                name_set.add(name)
                names_dic[l] = name_set
            else:
                names_dic[l].add(name)

    # 必须按照key降序
    names_sorted = sorted(names_dic.items(), key=lambda x: x[0], reverse=True)

    lst_names = []
    for tp in names_sorted:
        lst_names.extend(list(tp[1]))
    # 国外国家名的正则表达式
    reg_str = '|'.join(lst_names)

    return reg_str


# 创建正则表达式，主要用于城市包含字符串查询
def create_place_reg(dic, min_length):
    names_dic = dict()
    for name in dic.keys():
        l = len(name)
        if l < min_length:
            continue
        if l not in names_dic.keys():
            name_set = set()
            name_set.add(name)
            names_dic[l] = name_set
        else:
            names_dic[l].add(name)

    # 必须按照key降序
    names_sorted = sorted(names_dic.items(), key=lambda x: x[0], reverse=True)

    lst_names = []
    for tp in names_sorted:
        lst_names.extend(list(tp[1]))

    reg_str = '|'.join(lst_names)

    return reg_str


filter = {u'地区': 0, u'比如': 0, u'市区': 0, u'南部': 0, u'东南': 0, u'城市': 0, u'行政': 0, u'城区': 0,
          u'都市': 0, u'公安': 0, u'县市': 0, u'花园': 0, u'五大': 0, u'通道': 0, u'平安': 0, u'联合': 0,
          u'长寿': 0, u'上街': 0, u'海林': 0, u'保安': 0, u'富裕': 0, u'永年': 0, u'五家': 0, u'建华': 0,
          u'合作': 0, u'新建': 0, u'港口': 0, u'延长': 0, u'连平': 0, u'草坪': 0, u'阿里': 0, u'方正': 0,
          u'平原': 0, u'林浩': 0, u'东风': 0, u'三元': 0, u'罗斯': 0, u'石龙': 0, u'凤凰': 0, u'复兴': 0,
          u'灯塔': 0, u'和平': 0, u'长子': 0, u'军区': 0, u'长顺': 0, u'黎平': 0, u'双江': 0, u'招远': 0,
          u'集市': 0, u'祥云': 0, u'石桥': 0, u'太子': 0, u'惠安': 0, u'石柱': 0, u'张家': 0,
          u'公主': 0, u'天桥': 0, u'大通': 0, u'巧家': 0, u'鸭': 0, u'中国': 0}

place_code_path = 'conf/place.code'
code2city = dict()
city2code = dict()
with open(place_code_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        lst = line.split('\t')
        code = int(lst[0])
        city = lst[-1]
        # 去掉 500200 县
        if len(city) == 1:
            continue

        code2city[code] = city
        if city not in city2code.keys():
            code_lst = [int(code)]
            city2code[city] = code_lst
        else:
            city2code[city].append(code)

reg_city2code_place = create_place_reg(city2code, min_length=2)

# 省简称，channel参考可使用
province_abbreviation_dic = dict()
province_abbreviation_path = 'conf/provinceAbbreviation.txt'
with open(province_abbreviation_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        arr = line.split('\t')
        province_abbreviation_dic[arr[0]] = arr[1]

# 城市简称 映射 城市全称,一个简称可能对应多个
standard_place_dic = dict()
std_place_dic_path = 'conf/standard_place_dic.txt'
with open(std_place_dic_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        arr = line.split('\t')
        palces = list(set(arr[1].split(' ')))  # 可能地名相同，所以要set
        standard_place_dic[arr[0]] = palces

# include_place_dic.txt  是在standard_place_dic.txt基础上修改的
include_place_dic = dict()
include_place_dic_path = 'conf/include_place_dic.txt'
with open(include_place_dic_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        arr = line.split('\t')
        palces = list(set(arr[1].split(' ')))  # 可能地名相同，所以要set
        include_place_dic[arr[0]] = palces

reg_include_place = create_place_reg(include_place_dic, min_length=2)

# load 除我国意外的国家以及城市,国外国家名的正则表达式
world_nation_path = 'conf/worldNation_dic.txt'
reg_world_nation = create_world_city_reg(world_nation_path, min_length=2)

# 国外国家名的正则表达式
world_city_path = 'conf/worldCity_dic.txt'
reg_world_city = create_world_city_reg(world_city_path, min_length=4)

# 其他国家部分简称
world_nation_abbreviation = dict()
world_nation_abbreviation_path = 'conf/worldNationAbbreviation.txt'
with open(world_nation_abbreviation_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        arr = line.split('\t')
        world_nation_abbreviation[arr[0]] = arr[1]

# 国家主要部委
major_department_set = set()
major_department_path = 'conf/nationMajorDepartment.txt'
with open(major_department_path, 'r', encoding='utf-8') as f:
    major_department_set = set([name.strip() for name in f])

# 对直辖市的处理
municipality_names = ['北京市', '上海市', '重庆市', '天津市']
municipality_codes = [110000, 310000, 500000, 120000]

if __name__ == '__main__':
    file_path = 'conf/worldCity_dic.txt'
    create_world_city_reg(file_path, 4)
