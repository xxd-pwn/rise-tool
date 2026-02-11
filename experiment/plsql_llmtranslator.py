import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llmtranslator import llmtranslator_pl, VerifyPLByLLMs
from utils.LLMSetting import LLMSetting
from utils.Logs import logs_init
from utils.common import read_from_plsql
from utils.db import execute_plsql, verify, execute_plpgsql

if __name__ == '__main__':
    sourcedb = 'PostgreSQL'
    targetdb = 'Oracle'
    llm_engine2 = 'DeepSeek-V3'
    # llm_engine = 'gpt-4o-2024-05-13'
    llm_engine = 'DeepSeek-V3'
    logger = logs_init(f'{sourcedb}--{targetdb}--{llm_engine}--EmpiricalStudy--SingleLLM.log')
    # start_Time = time.time()
    num = 0
    wq = {}
    for i in range(1, 45):
        # i = 28
        sql = read_from_plsql(i, f'SQLProBench-{sourcedb}')
        print(f'SQL: {sql}')
        logger.info(f'SQL{i}: {sql}')

        llm_analysis = LLMSetting('openai', llm_engine, 0, 1.0, 2048, '')
        llm_translation = LLMSetting('openai', llm_engine, 0.7, 1.0, 4096, '')
        final_answer, summary = llmtranslator_pl(sql, sourcedb, targetdb, llm_analysis, llm_translation)
        print(summary)
        logger.debug(f"Summary:\n{summary}")
        print(final_answer)
        logger.debug(f"Translated SQL:\n{final_answer}")
        if targetdb.lower() == 'oracle':
            judge, info = execute_plsql(final_answer)
        else:
            judge, info = execute_plpgsql(final_answer)
        print(f'Result: {judge}, errmsg: {info}')
        logger.debug(f"Verification Result: {judge}, errmsg: {info}")

        if not judge:
            num += 1
            wq[i] = {'sql': sql, '\nfinal_answer': final_answer, '\nmsg': info}

        else:

            llm_verifier = LLMSetting('openai', llm_engine2, 0, 1.0, 3000, '')
            res = VerifyPLByLLMs(sourcedb, sql, targetdb, final_answer, llm_verifier, i)
            print(res)
            logger.debug(f"Verification Result(LLM): {res}")

            if 'verify EQUIVALENT' not in res:
                num += 1
                wq[i] = {'sql': sql, '\nfinal_answer': final_answer, '\nmsg': res}
        # break


    print(f'Total number of failed queries: {num}')
    for i in wq:
        print(f'query {i}: {wq[i]}')