import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (ask_LLM, load_prompt, generate_kg_doc,get_all_domains_str)
    
    

all_domains_str = get_all_domains_str(path='../jsons')
domains = all_domains_str.split(',')
doc_list = []
for i,domain in enumerate(domains):
    kg_doc = generate_kg_doc([domain],path='../jsons')
    prompt = load_prompt('get_domain_desc',path="./").format(kg_doc=kg_doc)
    desc, token_used = ask_LLM(prompt)
    doc = f'domain <{domain}>:'+desc
    doc_list.append(doc)
    print(f'{i+1}/{len(domains)}')
    
doc_total = '\n'.join(doc_list)
with open('domain_description.txt', 'w') as f:
    f.write(doc_total)





