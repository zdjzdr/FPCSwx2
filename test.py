ds = [[('产品名称', '轴承壳'), ('产品图号', '11517329152'), ('产品型号', 'TCR18'), ('产品材质', 'GGG40')], [('产品名称', '轴承体毛坯'), ('产品图号', '11517689064'), ('产品型号', 'TCR18'), ('产品材质', 'GGG40')]]
ls=[]
import collections
for d in ds:
	dic1=collections.OrderedDict()
	for d2 in d:
		dic1[d2[0]] = d2[1]

	ls.append(dic1)

print(ls[0]['产品型号'])