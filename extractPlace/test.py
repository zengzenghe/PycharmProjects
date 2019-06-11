# coding=utf-8
import re
import pandas as pd


lst = []
a = ' '.join(lst)
print(len(a))

a = [0,1,2,3,4,5,6]
print(a[3:6])

a = set()
a.add(1)
a.clear()
print(a)

b = set()
b.add(2)
a | b
# df = pd.DataFrame(columns=['A', 'B'], data = [[1,2],[3,4]])
# df['C'] = 'null'
# print(df)


a = '1 2 3444'
l = list(a)
print(l)
l_str = ' '.join(l)
print(l_str)

a = [1]
b = [2]
a.extend(b)
print(a)
a = set()
a.add(1)
a.add(1)
print(a)
# p = '中国|美国|英国'
# s = '我爱我的中国，美国资本主义，英国帝王'
# m = re.search(p, s)
# print(m.group(0))
# m = re.findall(p, s)
# print(m)

a = set()
a.add(1)
a.add(2)

print(set(a))
