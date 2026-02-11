import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llmtranslator import translate_query, VerifyByLLMs, translate_query_SingleLLM
from utils.LLMSetting import LLMSetting
from utils.Logs import logs_init
from utils.common import read_from_tpcds
from utils.db import verify

if __name__ == '__main__':
    sourcedb = 'PostgreSQL'
    targetdb = 'MySQL'
    llm_engine2 = 'DeepSeek-V3'
    # llm_engine = 'gpt-4o-2024-05-13'
    llm_engine = 'DeepSeek-V3'
    # start_Time = time.time()
    logger = logs_init(f'{sourcedb}--{targetdb}--{llm_engine}--EmpiricalStudy--SingleLLM.log')
    num = 0
    wq = {}
    for i in range(1, 100):
        # i = 54
        sql = read_from_tpcds(i, f'TPC-DS-{sourcedb}')
        # sql = read_from_plsql(44)
        print(f'SQL: {sql}')
        logger.info(f'SQL{i}: {sql}')

        llm_analysis = LLMSetting('openai', llm_engine, 0, 1.0, 2048, '')
        llm_translation = LLMSetting('openai', llm_engine, 0.7, 1.0, 4096, '')
        final_answer, summary = translate_query_SingleLLM(sql, sourcedb, targetdb, llm_analysis, llm_translation)
        print(summary)
        logger.debug(f"Summary:\n{summary}")
        print(final_answer)
        logger.debug(f"Translated SQL:\n{final_answer}")
        judge, info = verify(sourcedb, sql, targetdb, final_answer)
        print(f'Result: {judge}, errmsg: {info}')
        logger.debug(f"Verification Result: {judge}, errmsg: {info}")

        if not judge:
            num += 1
            wq[i] = {'sql': sql, '\nfinal_answer': final_answer, '\nmsg': info}

        else:

            llm_verifier = LLMSetting('openai', llm_engine2, 0, 1.0, 3000, '')
            res = VerifyByLLMs(sourcedb, sql, targetdb, final_answer, llm_verifier)
            print(res)
            logger.debug(f"Verification Result(LLM): {res}")

            if 'verify EQUIVALENT' not in res:
                num += 1
                wq[i] = {'sql': sql, '\nfinal_answer': final_answer, '\nmsg': res}

        break


    print(f'Total number of failed queries: {num}')
    for i in wq:
        print(f'query {i}: {wq[i]}')

            # else:
            #     print(f'Result: {judge}, errmsg: {info}')
            # end_time = time.time()
            # print(f'Time cost: {end_time - start_Time}')