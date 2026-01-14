#%% dataset cwq  webqsp graliqa simpleqa webquestions
import json
import re
import time
from openai import OpenAI
from SPARQLWrapper import SPARQLWrapper, JSON
import pathlib
import graphviz
from beautifultable import BeautifulTable
from typing import Dict, Any, Optional
SPARQLPATH = "http://localhost:8890/sparql"  
EXCLUDED_DOMAINS = {"common", "base", "user", "freebase", "type", "pipeline"}
def prepare_dataset(dataset_name,root='./data'):
    if dataset_name == 'cwq':
        with open(f'{root}/cwq.json',encoding='utf-8') as f:
            datas = json.load(f)
        qa_list = []
        for qa in datas:
            question = qa['question']
            answer = qa['answer']
            topic_entity = qa['topic_entity']
            qa_list.append((question,answer,topic_entity))
    elif dataset_name == 'webqsp':
        with open(f'{root}/WebQSP.json',encoding='utf-8') as f:
            datas = json.load(f)
        qa_list = []
        for qa in datas:
            question = qa['RawQuestion']
            topic_entity = qa['topic_entity']
            answers = qa["Parses"][0]["Answers"]
            answer = ','.join([f'{a["EntityName"]}' for a in answers])
            qa_list.append((question,answer,topic_entity))
    elif dataset_name == 'graliqa':
        with open(f'{root}/graliqa.json',encoding='utf-8') as f:
            datas = json.load(f)
        qa_list = []
        for qa in datas:
            question = qa['question']
            topic_entity = qa['topic_entity']
            answers = qa["answer"]
            answer = ','.join([f'{a["entity_name"]}' if 'entity_name' in a else f'{a["answer_argument"]}' for a in answers])
            qa_list.append((question,answer,topic_entity))
    elif dataset_name == 'simpleqa':
        with open(f'{root}/SimpleQA.json',encoding='utf-8') as f:
            datas = json.load(f)    
        qa_list = []
        for qa in datas:
            question = qa['question']
            topic_entity = qa['topic_entity']
            answer = qa["answer"]
            qa_list.append((question,answer,topic_entity))
    elif dataset_name == 'webquestions':
        with open(f'{root}/WebQuestions.json',encoding='utf-8') as f:
            datas = json.load(f)
        qa_list = []
        for qa in datas:
            question = qa['question']
            topic_entity = qa['topic_entity']
            answers = qa["answers"]
            answer = ','.join(answers)
            qa_list.append((question,answer,topic_entity))
    else:
        raise('not correct QAdataset')
    return qa_list

#%% llm

def ask_LLM(prompt, LLM_name='deepseek-reasoner', file=None):
    LLM_dict = {
        'deepseek-reasoner': {
            'api_key': 'sk-5f313ee8bc974f98996f21c729eb4414',
            'base_url': 'https://api.deepseek.com'
        },
        'qwen-plus': {
            'api_key': 'sk-f41a19cea42e4c80bcf2af95c0bb332f',
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        }
    }
    max_retries = 3
    retry_delay = 10  # seconds
    attempt = 0
    
    while attempt <= max_retries:
        try:
            client = OpenAI(
                api_key=LLM_dict[LLM_name]['api_key'],
                base_url=LLM_dict[LLM_name]['base_url']
            )
            completion = client.chat.completions.create(
                model=LLM_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content,completion.usage.total_tokens
            
        except Exception as e:
            if attempt < max_retries:
                print(f"请求失败: {str(e)}。{retry_delay}秒后重试... (尝试 {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                attempt += 1
            else:
                raise Exception(f"API请求失败，已达最大重试次数。最后错误: {str(e)}")
def sparql_exe(sparql_query):
    """执行SPARQL查询并返回JSON格式结果"""
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()
def get_relations_by_mid(mid):
    sparql_query = '''
    PREFIX fb: <http://rdf.freebase.com/ns/>
    SELECT DISTINCT ?rel ?rel_verse
    WHERE {
      
      fb:%s ?rel ?some.
      ?some2 ?rel_verse fb:%s.
    }
    ''' % (mid,mid)# fb:%s fb:type.object.type ?type .
    results = sparql_exe(sparql_query)
    rels_pos = set()
    rels_neg = set()
    # 提取关系并去掉前缀
    for rel_result in results["results"]["bindings"]:
        rel_uri = rel_result["rel"]["value"]
        rel_name = rel_uri.replace("http://rdf.freebase.com/ns/", "")
        if rel_name.split('.')[0] not in EXCLUDED_DOMAINS:
            rels_pos.add(rel_name)
        rel_uri = rel_result["rel_verse"]["value"]
        rel_name = rel_uri.replace("http://rdf.freebase.com/ns/", "")
        if rel_name.split('.')[0] not in EXCLUDED_DOMAINS:
            rels_neg.add(rel_name)
    # 添加到字典
    return rels_pos,rels_neg
def get_topic_info(topic_entity):
    topic_info = ''
    for topic_mid,topic_name in topic_entity.items():
        rels_pos,rels_neg = get_relations_by_mid(topic_mid)
        topic_info += f"Topic entity {topic_name} has relations: {','.join(sorted(rels_pos))}\n"
        topic_info += f"Relations target to topic entity {topic_name}: {','.join(sorted(rels_neg))}\n"
    return topic_info
def load_frame_dicts(path='./jsons'):
    with open(f'{path}/domain_type.json', 'r', encoding='utf-8') as f:
        domain_types = json.load(f)
    with open(f'{path}/relation_examples.json', 'r', encoding='utf-8') as f:
        relation_examples = json.load(f)
    with open(f'{path}/type_relation.json', 'r', encoding='utf-8') as f:
        type_relations = json.load(f)
    with open(f'{path}/relation_targettype.json', 'r', encoding='utf-8') as f:
        relation_targettype = json.load(f)
    with open(f'{path}/media_type.json', 'r', encoding='utf-8') as f:
        media_type = json.load(f)
    with open(f'{path}/type_father.json', 'r', encoding='utf-8') as f:
        type_father = json.load(f)
    with open(f'{path}/confusing_in_domains.json', 'r', encoding='utf-8') as f:
        confusing_in_domains = json.load(f)
    return domain_types,relation_examples,type_relations, relation_targettype, media_type,type_father,confusing_in_domains
def get_all_domains_str(path='./jsons'):
    domain_types,_,_,_,_,_,_ = load_frame_dicts(path=path)
    return ','.join(sorted(set(domain_types.keys())))
def get_all_relations(path='./jsons'):
    _,_,type_relations,_,_,_,_ = load_frame_dicts(path=path)
    all_relations = [rel for relations in type_relations.values() for rel in relations]
    return sorted(set(all_relations))
def get_related_type_relations(domain_list, path='./jsons'):
    domain_types,_,type_relations,_,_,_,_ = load_frame_dicts(path=path)
    related_type_relations = {}
    for domain in domain_list:
        types = domain_types[domain]
        for type_ in types:
            related_type_relations[type_] = type_relations[type_]
    return related_type_relations
def generate_kg_doc(related_domains, num_example=5, path='./jsons'):
    domain_types,relation_examples,type_relations, relation_targettype,media_type,type_father,confusing_in_domains = load_frame_dicts(path=path)
    media_type = set(media_type)
    related_type_list = [type_ for domain in related_domains for type_ in domain_types[domain]]
    
    kg_doc = ""
    for type_name in related_type_list:
        relations = type_relations.get(type_name, [])
        if len(relations)==0:
            continue
        if type_name in media_type:
            continue
        father_list = type_father.get(type_name,[])
        if len(father_list)>0:
            father_display = ','.join([f'<{father}>' for father in father_list])
            kg_doc +=  f"Type <{type_name}> can use the relations of its father types {father_display}.\n"
        kg_doc += f"Type <{type_name}> has relations:\n"
        for idx, relation in enumerate(relations):
            headname_list, tailname_list = relation_examples.get(relation, ([],[]))
            headname_list = [item for item in headname_list if item is not None]
            tailname_list = [item for item in tailname_list if item is not None]
            head_display = f"{', '.join(headname_list[:num_example])}"
            tail_display = f"{', '.join(tailname_list[:num_example])}"
            target_type = relation_targettype.get(relation, "unknow")
            if target_type not in media_type:
                example_display = f'head examples:{head_display};tail examples:{tail_display}'
                kg_doc += f" {idx+1}：{relation}-->{target_type}; {example_display}.\n"
            else:
                info_rels = type_relations.get(target_type, [])
                if not info_rels:
                    info = " None"
                else:
                    info = []
                    for rel in info_rels:
                        info.append(f'{rel}-->{relation_targettype.get(rel, "unknow")}')
                    info = ', '.join(info)
                example_display = f'head examples:{head_display};tail is CVT'
                kg_doc += f" {idx+1}：{relation}-->{target_type}(CVT infomations:{info}); {example_display}.\n"
        kg_doc += "\n"
    for domain in related_domains:
        kg_doc += f'Domain {domain} has fallowing confusing items:\n'
        if domain in confusing_in_domains:
            confusing = confusing_in_domains[domain]
            i = 1
            for k,v in confusing.items():
                kg_doc += f' {i}. {k}:{v}\n'
                i += 1
    return kg_doc
def load_prompt(prompt_name: str, path="./prompts") -> str:
    """
    从 ./prompts/{prompt_name}.txt 加载Prompt模板
    """
    file_path = pathlib.Path(path) / f"{prompt_name}.txt"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt文件不存在: {file_path.absolute()}")
    return file_path.read_text(encoding='utf-8')
def visualize_query_scheme(related_relations: str, output_dir: str = "./visualizations") -> str:
    dot_prompt = load_prompt("visualize_scheme").format(related_relations=related_relations)
    print('Getting visualization dot.')
    dot_code = ask_LLM(dot_prompt).strip()
    dot_code = re.sub(r'^```dot\s*|^```\s*|```$', '', dot_code, flags=re.MULTILINE).strip()
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = str(pathlib.Path(output_dir) / "query_scheme.png")
    graph = graphviz.Source(dot_code)
    graph.render(filename=output_path.rsplit('.', 1)[0], format='png', cleanup=True)
def sparql_results_to_beautiful_table(
    sparql_json: Dict[str, Any], 
    max_rows: Optional[int] = None,
    column_width: Optional[int] = 10
) -> BeautifulTable:
    table = BeautifulTable()
    headers = sparql_json.get('head', {}).get('vars', [])
    table.columns.header = headers
    bindings = sparql_json.get('results', {}).get('bindings', [])
    if max_rows is not None:
        bindings = bindings[:max_rows]
    for binding in bindings:
        row = []
        for var in headers:
            var_data = binding.get(var, {})
            value = var_data.get('value', '') if isinstance(var_data, dict) else str(var_data)
            row.append(value)
        table.rows.append(row)
    table.set_style(BeautifulTable.STYLE_BOX)  # 使用BOX样式
    if column_width is not None:
        for i in range(len(headers)):
            table.columns.width[i] = column_width
    return table





















