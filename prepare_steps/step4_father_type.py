import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import EXCLUDED_DOMAINS,sparql_exe
def get_all_named_types_count():
    sparql_types_query = '''
    PREFIX ns: <http://rdf.freebase.com/ns/>

    SELECT ?type (COUNT(?instance) AS ?instance_count)
    WHERE {
      ?instance ns:type.object.type ?type.
      ?instance ns:type.object.name ?name.
    }
    GROUP BY ?type
    ORDER BY DESC(?instance_count)
    '''
    print("正在查询Freebase类型...")
    results = sparql_exe(sparql_types_query)
    
    types_count = {}
    for binding in results["results"]["bindings"]:
        type_uri = binding["type"]["value"]
        type_count = binding["instance_count"]["value"]
        # 提取类型标识符（如 "music.composition"）
        type_id = type_uri.replace("http://rdf.freebase.com/ns/", "")
        
        # 提取并检查域名
        domain = type_id.split('.')[0]
        if domain not in EXCLUDED_DOMAINS:
            types_count[type_id] = int(type_count)
    
    return types_count


if __name__ == "__main__":
    print("正在查询类型列表...")
    types_count = get_all_named_types_count()
    # 初始化字典
    type_father = {}
    sparql_father_query = '''
    PREFIX ns: <http://rdf.freebase.com/ns/>

    SELECT DISTINCT ?father (COUNT(?instance) AS ?instance_count)
    WHERE {
      ?instance ns:type.object.type ns:%s.
      ?instance ns:type.object.name ?name.
      ?instance ns:type.object.type ?father.
    }
    GROUP BY ?father
    ORDER BY DESC(?instance_count)
    LIMIT 30
    '''
    # 处理类型查询结果
    i = 0
    for type_name, count in types_count.items():
        # 执行关系查询
        father_results = sparql_exe(sparql_father_query % (type_name))
        # 提取关系并去掉前缀
        type_father[type_name] = []
        for father in father_results["results"]["bindings"]:
            father_uri = father["father"]["value"]
            father_name = father_uri.replace("http://rdf.freebase.com/ns/", "")
            father_count = int(father["instance_count"]["value"])
            if father_name.split('.')[0] not in EXCLUDED_DOMAINS and father_name!=type_name  and father_count/count>0.5:
                type_father[type_name].append(father_name)
        # 添加到字典
        i+=1
        print(f"{(i+1)}/{len(types_count)}")
    
    with open("../jsons/type_father.json", "w", encoding="utf-8") as f:
        json.dump(type_father, f, indent=2, ensure_ascii=False)
    
        
        
        
        
        
        
        