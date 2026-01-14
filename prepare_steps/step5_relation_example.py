import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import EXCLUDED_DOMAINS,sparql_exe

def get_relation_examples(relation):
    """
    分析关系指向的目标类型分布
    返回: (type_counter, literal_count)
    """
    query = '''
    PREFIX ns: <http://rdf.freebase.com/ns/>

    SELECT DISTINCT ?headname ?tailname
    WHERE {
      ?head ns:%s ?tail .
      
      ?head ns:type.object.name ?headname .
      
      OPTIONAL {
        ?tail ns:type.object.name ?tailname .
      }
    }
    LIMIT 5
    '''
    results = sparql_exe(query % relation)
    headname_list = []
    tailname_list = []
    for binding in results.get("results", {}).get("bindings", []):
        headname = binding.get("headname", {}).get("value") 
        headname_list.append(headname)
        tailname = binding.get("tailname", {}).get("value") 
        tailname_list.append(tailname)
    return headname_list, tailname_list


if __name__ == "__main__":
    # 读取关系列表
    with open('../jsons/type_relation.json', 'r', encoding='utf-8') as f:
        type_relation = json.load(f)
    all_relations = [item for sublist in type_relation.values() for item in sublist]
    with open('../jsons/media_type.json', 'r', encoding='utf-8') as f:
        media_type = set(json.load(f))
    relation_examples = {}
    
    i = 1
    for type_, relations in type_relation.items():
        if type_ not in media_type:
            j = 1
            for rel in relations:
                headname_list, tailname_list = get_relation_examples(rel)
                relation_examples[rel] = (headname_list, tailname_list)
                print(f'{i}/{len(type_relation)}---{j}/{len(relations)}')
                j+=1
        i+=1
    
    # 保存结果
    output_file = '../jsons/relation_examples.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(relation_examples, f, ensure_ascii=False, indent=2)
    
