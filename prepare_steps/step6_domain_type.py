import json


def create_domain_type_dict(type_relation):
    """
    将type_relation字典转换为domain_type字典
    
    参数:
    type_relation: 键为类，值为关系列表的字典
    
    返回:
    domain_type: 键为域，值为类列表的字典
    """
    domain_type = {}
    
    for class_name in type_relation.keys():
        # 从类名中提取域（第一个点之前的部分）
        if '.' in class_name:
            domain = class_name.split('.')[0]
            
            # 如果域不存在，创建空列表
            if domain not in domain_type:
                domain_type[domain] = []
            
            # 将类添加到对应域的列表中（避免重复）
            if class_name not in domain_type[domain]:
                domain_type[domain].append(class_name)
    
    return domain_type

if __name__ == "__main__":
    # 读取关系列表
    with open('../jsons/type_relation.json', 'r', encoding='utf-8') as f:
        type_relation = json.load(f)
    domain_type = create_domain_type_dict(type_relation)
    
    output_file = '../jsons/domain_type.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(domain_type, f, ensure_ascii=False, indent=2)
    
    print(f"\n处理完成！结果已保存到 {output_file}")
