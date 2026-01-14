import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import EXCLUDED_DOMAINS,sparql_exe


def get_all_types():
    sparql_types_query = '''
    PREFIX ns: <http://rdf.freebase.com/ns/>

    SELECT ?type (COUNT(?instance) AS ?instance_count)
    WHERE {
      ?instance ns:type.object.type ?type.
    }
    GROUP BY ?type
    ORDER BY DESC(?instance_count)
    '''
    print("正在查询Freebase类型...")
    results = sparql_exe(sparql_types_query)
    
    types_list = []
    for binding in results["results"]["bindings"]:
        type_uri = binding["type"]["value"]
        
        # 提取类型标识符（如 "music.composition"）
        type_id = type_uri.replace("http://rdf.freebase.com/ns/", "")
        
        # 提取并检查域名
        domain = type_id.split('.')[0]
        if domain not in EXCLUDED_DOMAINS:
            types_list.append(type_id)
    return types_list


if __name__ == "__main__":
    print("正在查询类型列表...")
    all_types = get_all_types()
    # 初始化字典
    type_relation = {}
    sparql_relation_query = '''
    PREFIX ns: <http://rdf.freebase.com/ns/>

    SELECT DISTINCT ?relation
    WHERE {
      ?instance ns:type.object.type ns:%s.
      ?instance ?relation ?something .
    }
    LIMIT 5000
    '''
    # 处理类型查询结果
    for i, type_name in enumerate(all_types):
        # 执行关系查询
        relation_results = sparql_exe(sparql_relation_query % (type_name))
        relations = set()
        # 提取关系并去掉前缀
        for rel_result in relation_results["results"]["bindings"]:
            rel_uri = rel_result["relation"]["value"]
            rel_name = rel_uri.replace("http://rdf.freebase.com/ns/", "")
            if '.'.join(rel_name.split('.')[:2]) == type_name:
                relations.add(rel_name)
        # 添加到字典
        type_relation[type_name] = relations
        print(f"  找到 {len(relations)} 个关系")
        break
    # 保存到文件（可选）
    save_dict = {k: list(v) for k, v in type_relation.items()}
    with open("../jsons/type_relation.json", "w", encoding="utf-8") as f:
        json.dump(save_dict, f, indent=2, ensure_ascii=False)
    
    print("字典已保存到 type_relation.json")
