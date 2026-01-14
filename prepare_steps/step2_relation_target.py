import json
from collections import Counter
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import EXCLUDED_DOMAINS,sparql_exe

def extract_domain(relation):
    """从关系字符串中提取域（如'music.release_track' -> 'music'）"""
    if '.' in relation:
        return relation.split('.')[0]
    return ""

def analyze_target_types(relation, sample_size=5000):
    """
    分析关系指向的目标类型分布
    返回: (type_counter, literal_count)
    """
    query = f'''
    PREFIX ns: <http://rdf.freebase.com/ns/>

    SELECT ?target ?targettype
    WHERE {{
      ?instance ns:{relation} ?target .
      OPTIONAL {{
        ?target ns:type.object.type ?targettype .
      }}
    }}
    LIMIT {sample_size}
    '''
    domain = extract_domain(relation)
    results = sparql_exe(query)
    if not results:
        return Counter(), 0
    
    type_counter = Counter()
    literal_count = 0
    
    for binding in results.get("results", {}).get("bindings", []):
        target_info = binding.get("target", {})
        target_type = target_info.get("type")  # 可能是: uri, literal, typed-literal
        
        targettype_value = binding.get("targettype", {}).get("value", "")
        
        # 判断目标是否为字面量
        if target_type in ["literal", "typed-literal"]:
            literal_count += 1
        elif target_type == "uri" and targettype_value:
            # 提取类型名称（去掉命名空间前缀）
            if targettype_value.startswith("http://rdf.freebase.com/ns/"):
                type_short = targettype_value.replace("http://rdf.freebase.com/ns/", "")
                # if type_short.startswith(f"{domain}."):
                #     type_counter[type_short] += 1
                domain = extract_domain(type_short)
                if domain not in EXCLUDED_DOMAINS:
                    type_counter[type_short] += 1
    
    return type_counter, literal_count

def select_target_type(type_counter, literal_count):
    """
    根据统计结果选择最合适的类型：
    1. 如果字面量占主导，返回"literal"
    2. 优先选择与关系同域的类型（出现次数最多的）
    3. 否则选择所有类型中出现次数最多的
    4. 如果没有任何类型，返回"unknown"
    """
    # 如果主要是字面量（数量超过任何实体类型）
    if literal_count > 0 and (not type_counter or literal_count > max(type_counter.values())):
        return "literal"
    # 选择类型
    if type_counter:
        # 所有类型中选择出现次数最多的
        return max(type_counter, key=type_counter.get)
    else:
        # 没有找到任何类型
        return "unknown"

def get_relation_target_type(relation):
    """主函数：获取关系的目标类型"""
    type_counter, literal_count = analyze_target_types(relation)
    return select_target_type(type_counter, literal_count)


if __name__ == "__main__":
    # 读取关系列表
    with open('../jsons/type_relation.json', 'r', encoding='utf-8') as f:
        type_relation = json.load(f)
    all_relations = [item for sublist in type_relation.values() for item in sublist]
    
    print(f"待处理关系总数: {len(all_relations)}")
    
    # 处理每个关系
    relation_target_map = {}
    for i, relation in enumerate(all_relations, 1):
        target_type = get_relation_target_type(relation)
        relation_target_map[relation] = target_type
        print(f"[{i}/{len(all_relations)}] {relation} -> {target_type}")
    
    # 保存结果
    output_file = '../jsons/relation_targettype.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(relation_target_map, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理完成！结果已保存到 {output_file}")
