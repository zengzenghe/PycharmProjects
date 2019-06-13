def AddWorldCity(input_file):
    #绝对路径
    #output_file1 = r'D:\PycharmProjects\newsPlaceExtract_20190422\conf\worldNation_dic.txt'
    #相对代码同级目录的相对路径
    output_file1 = 'conf/worldNation_dic.txt'
    #output_file2 = r'D:\PycharmProjects\newsPlaceExtract_20190422\conf\worldCity_dic.txt'
    output_file2 = 'conf/worldCity_dic.txt'
    #清除已存在文件
    if os.path.exists(output_file1):
        os.remove(output_file1)

    if os.path.exists(output_file2):
        os.remove(output_file2)

    # 读取指定列
    df = pd.read_excel(input_file, header=0, index=0, usecols=[0, 2])
    # 输出读取行列的具体情况
    #print(df.columns)
    df.columns = ['nationOrcity', 'code']
    # 处理缺省值，填充NaN为指定的值,必须要加上inplace，否则不会保存填充的结果
    df.fillna('', inplace=True)
    place_code_path = 'conf/place.code'
    place_code = dict()
    provinceMap_path = 'conf/provinceMap.txt'
    provinceMap = dict()
    standard_place_dic_path = 'conf/standard_place_dic.txt'
    standard_place_dic = dict()

    #创建place_code字典，用于去重
    with open(place_code_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            lst = line.split(' ')
            code = lst[-1]
            city = int(lst[0])
            #code为键，city为值
            place_code[code] = city

    #创建place_code字典，用于去重
    with open(provinceMap_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            lst = line.split('	')
            samplename = lst[-1]
            wholename = lst[0]
            provinceMap[wholename] = samplename

    #创建place_code字典，用于去重
    with open(standard_place_dic_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            lst = line.split('	')
            standardsamplename = lst[-1]
            standardwholecname = lst[0]
            standard_place_dic[standardwholecname] = standardsamplename

    #按行遍历读取出的excel表格
    for index, row in df.iterrows():
        # 将与place_code、provinceMap.txt、standard_place_dic.txt文件不重复的外国名称写入worldNation_dic.txt
        # row['code']本身是个字符串，不需要再用str()函数进行转换了
        if row['code'] == 0 and row['nationOrcity'] != '中国':
            if row['nationOrcity'] not in place_code.keys() and row['nationOrcity'] not in provinceMap.keys() and row['nationOrcity'] not in standard_place_dic.keys():
                txt =  str(row['nationOrcity']) + '\n'
                #write_file(output_file1, txt)
                with open(output_file1, 'a') as f:
                    f.write(txt)
        # 将与place_code、provinceMap.txt、standard_place_dic.txt文件不重复的外国城市名写入worldCity_dic.txt
        if row['code'] != 0 and row['nationOrcity'] not in place_code.keys() and row['nationOrcity'] not in provinceMap.keys() and row['nationOrcity'] not in standard_place_dic.keys():
            txt = str(row['nationOrcity']) + '\n'
            #write_file(output_file2, txt)
            with open(output_file2, 'a') as f:
                f.write(txt)
