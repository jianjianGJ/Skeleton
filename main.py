import argparse
import time
import os
from loguru import logger
from utils import (ask_LLM, sparql_exe, prepare_dataset,
                   load_prompt, generate_kg_doc,
                   sparql_results_to_beautiful_table, get_topic_info)

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='KGQA处理脚本')
    parser.add_argument('--dataset', type=str, default='webqsp', 
                       choices=['cwq', 'webqsp', 'graliqa', 'simpleqa', 'webquestions'],
                       help='要处理的数据集名称')
    parser.add_argument('--start_id', type=int, default=0, 
                       help='起始问题ID（包含）')
    parser.add_argument('--end_id', type=int, default=1, 
                       help='结束问题ID（不包含）')
    parser.add_argument('--log_dir', type=str, default='logs',
                       help='日志文件保存目录')
    
    args = parser.parse_args()
    
    # 设置日志目录
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 配置日志
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), 
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
               level="INFO")
    logger.add(f"{args.log_dir}/{args.dataset}_processing_{{time:YYYY-MM-DD_HH-mm-ss}}.log", 
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | q{extra[question_id]} | {message}",
               rotation="500 MB", 
               retention="10 days", 
               level="DEBUG")
    logger.add(f"{args.log_dir}/{args.dataset}_processing_latest.log", 
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | q{extra[question_id]} | {message}",
               rotation="500 MB", 
               retention="1 day", 
               level="DEBUG",
               mode="w")
    logger.configure(extra={"question_id": "N/A"})
    
    # 准备数据集
    dataset = args.dataset
    qa_list = prepare_dataset(dataset)
    
    # 检查索引范围
    if args.start_id < 0 or args.end_id > len(qa_list) or args.start_id >= args.end_id:
        logger.error(f"无效的索引范围: start_id={args.start_id}, end_id={args.end_id}, 数据集大小={len(qa_list)}")
        return
    
    logger.info(f"开始处理数据集: {dataset}, 共 {len(qa_list)} 条数据")
    logger.info(f"处理范围: {args.start_id} 到 {args.end_id-1} (共 {args.end_id-args.start_id} 条)")
    
    # 统计信息
    total_tokens = {"domain": 0, "skeleton": 0, "sparql": 0}
    total_times = {"domain": 0, "skeleton": 0, "sparql": 0, "total": 0}
    
    for i in range(args.start_id, args.end_id):
        q_logger = logger.bind(question_id=i)
        start_time = time.time()  # 记录问题开始时间
        
        q_logger.info(f"{'=' * 50}")
        q_logger.info("开始处理问题")
        
        ############################################# STEP 0 load question and construct topic_info
        question, answer, topic_entity = qa_list[i]
        question_with_calibration = question + f"(Topic entity name calibration: {','.join(topic_entity.values())})"
        topic_info = get_topic_info(topic_entity)
        
        # 记录问题核心信息
        q_logger.info(f"问题: {question_with_calibration}")
        q_logger.info(f"标准答案: {answer}")
        q_logger.debug(f"基础问题文本: {question}")
        q_logger.debug(f"主题实体: {topic_entity}")
        
        ############################################# STEP 1 get related domain
        domain_start = time.time()
        prompt = load_prompt('get_related_domains').format(question=question_with_calibration)
        related_domain_answer, domain_token_used = ask_LLM(prompt)
        domain_time = time.time() - domain_start
        
        total_tokens["domain"] += domain_token_used
        total_times["domain"] += domain_time
        
        # 记录领域相关信息
        q_logger.info(f"相关领域: {related_domain_answer}")
        q_logger.info(f"领域分析 - Token: {domain_token_used}, 耗时: {domain_time:.2f}秒")
        
        ############################################# STEP 2 construct kg_doc
        kg_doc_start = time.time()
        kg_doc = generate_kg_doc(related_domain_answer.split(',')[:10]) + '='*20 + '\n' + topic_info + '\n'
        kg_doc_time = time.time() - kg_doc_start
        
        q_logger.debug(f"KG文档生成耗时: {kg_doc_time:.2f}秒")
        
        ############################################# STEP 3 get kg skeleton
        skeleton_start = time.time()
        prompt = load_prompt('get_skeleton_from_kgdoc').format(kg_doc=kg_doc, question=question_with_calibration)
        skeleton, skeleton_token_used = ask_LLM(prompt)
        skeleton_time = time.time() - skeleton_start
        
        total_tokens["skeleton"] += skeleton_token_used
        total_times["skeleton"] += skeleton_time
        
        # 记录骨架信息
        q_logger.info(f"KG骨架: \n{skeleton}")
        q_logger.info(f"骨架生成 - Token: {skeleton_token_used}, 耗时: {skeleton_time:.2f}秒")
        
        ############################################# STEP 4 get sparql
        sparql_gen_start = time.time()
        prompt = load_prompt('get_query_from_skeleton').format(skeleton=skeleton, question=question_with_calibration)
        query, sparql_token_used = ask_LLM(prompt)
        sparql_gen_time = time.time() - sparql_gen_start
        
        total_tokens["sparql"] += sparql_token_used
        total_times["sparql"] += sparql_gen_time
        
        # 记录查询信息
        q_logger.info(f"SPARQL查询: \n{query}")
        q_logger.info(f"查询生成 - Token: {sparql_token_used}, 耗时: {sparql_gen_time:.2f}秒")
        
        ############################################# STEP 5 exe sparql
        sparql_exe_start = time.time()
        try:
            result = sparql_exe(query)
            result_table = sparql_results_to_beautiful_table(result)
        except Exception:
            result_table = 'SPARQL执行失败'
        sparql_exe_time = time.time() - sparql_exe_start
        
        # 记录执行结果
        q_logger.info(f"查询结果: \n{result_table}")
        q_logger.info(f"SPARQL执行耗时: {sparql_exe_time:.2f}秒")
        
        # 记录该问题的总处理时间
        total_time = time.time() - start_time
        total_times["total"] += total_time
        q_logger.info(f"问题总处理时间: {total_time:.2f}秒")
        
        # 可选：每条问题处理后输出进度
        progress = i - args.start_id + 1
        total = args.end_id - args.start_id
        logger.info(f"进度: {progress}/{total} ({progress/total*100:.1f}%)")
    
    # 记录最终统计
    logger.info("=" * 50)
    logger.info("所有问题处理完成")
    logger.info(f"处理范围: {args.start_id} 到 {args.end_id-1}")
    logger.info(f"Token使用统计: 领域={total_tokens['domain']}, 骨架={total_tokens['skeleton']}, SPARQL={total_tokens['sparql']}")
    logger.info(f"总Token消耗: {sum(total_tokens.values())}，预计消耗{sum(total_tokens.values())/1000000*2:.2f}元")
    logger.info(f"时间统计 - 领域分析: {total_times['domain']:.2f}秒, 骨架生成: {total_times['skeleton']:.2f}秒, 查询生成: {total_times['sparql']:.2f}秒")
    logger.info(f"总处理时间: {total_times['total']:.2f}秒, 平均每条: {total_times['total']/(args.end_id-args.start_id):.2f}秒")

if __name__ == "__main__":
    main()