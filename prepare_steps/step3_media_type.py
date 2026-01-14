import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import EXCLUDED_DOMAINS,sparql_exe
import json


def get_all_types_count():
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
    num_example=10
    types_count = get_all_types_count()
    named_types_count = get_all_named_types_count()
    with open('../jsons/type_relation.json', 'r', encoding='utf-8') as f:
        type_relations = json.load(f)
    media_type = []
    for i,type_ in enumerate(type_relations.keys()):
        big = types_count.get(type_,0)
        small = named_types_count.get(type_,0)
        if small==0 or big/small > 1.5:
            media_type.append(type_)
    output_file = '../jsons/media_type.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(media_type, f, ensure_ascii=False, indent=2)





