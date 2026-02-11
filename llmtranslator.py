from utils import llm
from utils.LLMSetting import LLMSetting
from utils.common import *
from utils.db import *

def translate_query(s_sql: str, s_db: str, t_db: str, s_gpt: LLMSetting, m_gpt: LLMSetting):
    status, info = verify(s_db, s_sql, t_db, s_sql)
    status = False
    if status:
        return '```sql ' + s_sql + ' ```', 'NO SUMMARY'
    else:
        prompt1 = f"Please summarize the database features contained in the SQL of {s_db} database.\n" \
                  f"Step by step, analyze all the features and conditional expressions included.\n" \
                  f"The sql statement is: {s_sql}\n" \
                  f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
                  f"1: Make sure your answer includes all the features in the SQL.\n" \
                  f"2: Make sure that the summary you provide matches the description of the corresponding database document.\n" \
                  f"3: If the SQL query contains complex expressions, provide semantically equivalent simplified forms.\n" \
                  f"4: Make sure your answers are concise and don't provide too much explanatory information.\n" \
                  f"You need to summarize these features as succinctly as possible and return in the format: ```summary your summary here ```"
        sys_prompt1 = (f'You are an expert in {s_db} and {t_db} database field. '
                       f'Please provide me with the correct answer according to my requirements.') if s_gpt.getSys_prompt() == '' else s_gpt.getSys_prompt()
        summary = llm.invoke(prompt1, s_gpt.getTemp(), s_gpt.getMax_tokens(), s_gpt.getTop_P(), s_gpt.getApi(),
                             s_gpt.getModel(), sys_prompt1)
        summary = getSummary(summary)

        prompt2 = f"The source sql on {s_db}: {s_sql} cannot compile on {t_db}. This is the error message: {info}\n" \
                  f"Please check whether the above error information can be resolved. The following is a summary of the features in the source SQL: {summary} \n" \
                  f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
                  f"1: Make sure you only resolve errors without changing the semantic information of the statement.\n" \
                  f"2: If the error cannot be resolved or the semantics of the original SQL must be changed to resolve it, output the reason.\n" \
                  f"3: SQL semantic unchanged specifically refers to the execution logic unchanged, alias change does not affect the execution logic, can be regardless." \
                  f"If only the syntax is different but the execution logic behind it is the same, it is considered semantically equivalent. One exception is that if different operations are used to simulate an unsupported operation, we consider this semantically equivalent as long as both return the same result and database state in any case.\n" \
                  f"You should carefully check if there are other operations that can be used to simulate an unsupported operation and return the same result and database state in any case. If so, please provide the corresponding SQL statement.\n" \
                  f"4: Just return what I need in the format below, without any explanatory information.\n" \
                  f"5: If you need to generate a new identifier, use the following fixed noun -- ANYVALUE.\n" \
                  f"6: If there is no AS before the alias, do not add it automatically. In contrast, if the alias is preceded by AS, do not delete it automatically.\n" \
                  f"The return format: ```sql your SQL here ```\n" \
                  f"Else please provide the reason.\n" \
                  f"The return format: ```impossible your reason here ```"
        sys_prompt2 = (f'You are an expert in {s_db} and {t_db} database field. '
                       f'Please provide me with the correct answer according to my requirements.') if m_gpt.getSys_prompt() == '' else m_gpt.getSys_prompt()
        convertedTestCase = llm.invoke(prompt2, m_gpt.getTemp(), m_gpt.getMax_tokens(), m_gpt.getTop_P(),
                                       m_gpt.getApi(),
                                       m_gpt.getModel(), sys_prompt2, n = 3)
        print(convertedTestCase)
        final_answer = ''
        for answer in convertedTestCase:
            impossiblereason, translated_q = '', ''
            if 'impossible' in answer:
                try:
                    impossiblereason = re.search(r'```impossible([\s\S]*?)```', answer).group(1)
                except Exception as e:
                    print(f'Exception:{e} --No match found! Rerunning.')
            else:
                try:
                    translated_q = re.search(r'```sql([\s\S]*?)```', answer).group(1)
                except Exception as e:
                    print(f'Exception:{e} --No match found! Rerunning.')
            if translated_q != "":
                status, info = verify(s_db, s_sql, t_db, translated_q)
                if status:
                    final_answer = translated_q
                    break
                else:
                    final_answer = translated_q
            elif impossiblereason != "":
                final_answer = f'```impossible {impossiblereason}```'

    return final_answer, summary

def translate_query_SingleLLM(s_sql: str, s_db: str, t_db: str, s_gpt: LLMSetting, m_gpt: LLMSetting):
    prompt2 = f"The source sql on {s_db}: {s_sql} cannot compile on {t_db}.\n" \
              f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
              f"1: Make sure you only resolve errors without changing the semantic information of the statement.\n" \
              f"2: If the error cannot be resolved or the semantics of the original SQL must be changed to resolve it, output the reason.\n" \
              f"3: SQL semantic unchanged specifically refers to the execution logic unchanged, alias change does not affect the execution logic, can be regardless." \
              f"If only the syntax is different but the execution logic behind it is the same, it is considered semantically equivalent. One exception is that if different operations are used to simulate an unsupported operation, we consider this semantically equivalent as long as both return the same result and database state in any case.\n" \
              f"You should carefully check if there are other operations that can be used to simulate an unsupported operation and return the same result and database state in any case. If so, please provide the corresponding SQL statement.\n" \
              f"4: Just return what I need in the format below, without any explanatory information.\n" \
              f"5: If you need to generate a new identifier, use the following fixed noun -- ANYVALUE.\n" \
              f"6: If there is no AS before the alias, do not add it automatically. In contrast, if the alias is preceded by AS, do not delete it automatically.\n" \
              f"The return format: ```sql your SQL here ```\n" \
              f"Else please provide the reason.\n" \
              f"The return format: ```impossible your reason here ```"
    sys_prompt2 = (f'You are an expert in {s_db} and {t_db} database field. '
                   f'Please provide me with the correct answer according to my requirements.') if m_gpt.getSys_prompt() == '' else m_gpt.getSys_prompt()
    convertedTestCase = llm.invoke(prompt2, m_gpt.getTemp(), m_gpt.getMax_tokens(), m_gpt.getTop_P(),
                                   m_gpt.getApi(),
                                   m_gpt.getModel(), sys_prompt2, n = 3)
    print(convertedTestCase)
    final_answer = ''
    for answer in convertedTestCase:
        impossiblereason, translated_q = '', ''
        if 'impossible' in answer:
            try:
                impossiblereason = re.search(r'```impossible([\s\S]*?)```', answer).group(1)
            except Exception as e:
                print(f'Exception:{e} --No match found! Rerunning.')
        else:
            try:
                translated_q = re.search(r'```sql([\s\S]*?)```', answer).group(1)
            except Exception as e:
                print(f'Exception:{e} --No match found! Rerunning.')
        if translated_q != "":
            status, info = verify(s_db, s_sql, t_db, translated_q)
            if status:
                final_answer = translated_q
                break
            else:
                final_answer = translated_q
        elif impossiblereason != "":
            final_answer = f'```impossible {impossiblereason}```'

    return final_answer, 'NULL'

def translate_pl(s_sql: str, s_db: str, t_db: str, s_gpt: LLMSetting, m_gpt: LLMSetting):
    if t_db.lower() == 'oracle':
        status, info = execute_plsql(s_sql)
    else:
        status, info = execute_plpgsql(s_sql)
    status = False
    if status:
        return '```sql ' + s_sql + ' ```', 'NO SUMMARY'
    else:
        prompt1 = f"Please summarize the database features contained in the SQL of {s_db} database.\n" \
                  f"Step by step, analyze all the features and conditional expressions included.\n" \
                  f"The sql statement is: {s_sql}\n" \
                  f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
                  f"1: Make sure your answer includes all the features in the SQL.\n" \
                  f"2: Make sure that the summary you provide matches the description of the corresponding database document.\n" \
                  f"3: If the SQL query contains complex expressions, provide semantically equivalent simplified forms.\n" \
                  f"4: Make sure your answers are concise and don't provide too much explanatory information.\n" \
                  f"You need to summarize these features as succinctly as possible and return in the format: ```summary your summary here ```"
        sys_prompt1 = (f'You are an expert in {s_db} and {t_db} database field. '
                       f'Please provide me with the correct answer according to my requirements.') if s_gpt.getSys_prompt() == '' else s_gpt.getSys_prompt()
        summary = llm.invoke(prompt1, s_gpt.getTemp(), s_gpt.getMax_tokens(), s_gpt.getTop_P(), s_gpt.getApi(),
                             s_gpt.getModel(), sys_prompt1)
        summary = getSummary(summary)

        prompt2 = f"The source sql on {s_db}: {s_sql} cannot compile on {t_db}. This is the error message: {info}\n" \
                  f"Please check whether the above error information can be resolved. The following is a summary of the features in the source SQL: {summary} \n" \
                  f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
                  f"1: Translate the query from {s_db} to {t_db}. Do not add anything unless it is necessary. Please note that you must ensure that the SQL after translation is equivalent to the original SQL before translation.\n" \
                  f"2: Use a procedure instead to achieve similar functionality. You should ensure that the semantics of the SQL remain consistent before and after translation. Each modification should only address the SQL related to the error message. Even if there are other errors in the SQL, you should not fix them all at once.\n" \
                  f"3: Note that, the parameters of the procedure should remain consistent with those of the function, without arbitrarily adding or removing parameters! If it is not necessary, do not change the 'in out' attribute of the parameter arbitrarily. If the parameter does not have the IN OUT attribute declared, do not arbitrarily add the IN attribute.\n" \
                  f"4: If there is no content between BEGIN and END, you should not add anything (except NULL) inside unless it resolves the current error messages.\n" \
                  f"5: There is no need to add the / symbol at the end. Do not use 'IF EXISTS( SELECT 1 FROM t1 )' to replace 'IF EXISTS( SELECT * FROM t1 )', although they are the same. Because this kind of modification is not necessary, be careful not to make any unnecessary modifications!\n" \
                  f"6: Just return what I need in the format below, without any explanatory information.\n" \
                  f"7: If you need to generate a new identifier, use the following fixed noun -- ANYVALUE.\n" \
                  f"8: Carefully consider the knowledge I provided last.\n" \
                  f"9: Ensure that your modification is the one with the minimal cost. Although there may be multiple feasible solutions, you need to choose the one that requires the least amount of change. For example, consider the following case:In PostgreSQL, the statement 'OPEN c1 FOR SELECT web_loss + cat_loss INTO total_loss;' can be translated into Oracle in two ways: 'OPEN c1 FOR SELECT web_loss + cat_loss INTO total_loss from dual;' and 'total_loss := web_loss + cat_loss; OPEN c1 FOR SELECT total_loss FROM dual;'. However, you should choose the first modification because it has the smallest cost.\n" \
                  f"The return format: ```sql your SQL here ```\n" \
                  f"Else please provide the reason.\n" \
                  f"The return format: ```impossible your reason here ```\n" \
                  f"Here is some knowledge that you may find useful: \n" \
                  f"1. In Oracle Database, you can use the dbms_sql.return_result() method to return a sys_refcursor value. For example: CREATE or replace PROCEDURE procName (st char) AS c1 sys_refcursor; BEGIN dbms_sql.return_result(c1); END; Note that, the absence of the dbms_sql.return_result(c1); statement will not cause an error in Oracle. If the PostgreSQL query does not include a RETURN c1; statement, please do not add it!\n" \
                  f"2. In Oracle, FETCH FIRST n ROWS is equivalent to LIMIT n.\n" \
                  f"3. Oracle uses `raise_application_error` to raise custom exceptions with an error number -20111.\n" \
                  f"4. In the definition of an Oracle procedure, if you need to declare a new variable (Variable that do not appear between AS and BEGIN), please add @new&&identifier name&&type before where you use it and do not alter the content of the declaration section. I will handle them manually. Below is an example. This is an SQL statement that needs to be translated into Oracle:CREATE OR REPLACE PROCEDURE getStoreByManager(manager VARCHAR2) AS BEGIN if not exists (select * from store where s_manager= manager) then raise_application_error (-20111, 'No stores operated by this manager'); end if; END; However, Oracle does not support the IF EXISTS syntax. Therefore, a new variable v_count needs to be declared to store the result of the conditional query for evaluation. Below is the equivalent SQL in Oracle:CREATE OR REPLACE PROCEDURE getStoreByManager(manager VARCHAR2) AS BEGIN @new&&v_count&&number SELECT COUNT(*) INTO v_count FROM store WHERE s_manager = manager; IF v_count = 0 THEN raise_application_error(-20111, 'No stores operated by this manager'); END IF; END; Note that if the current dialect issue can be resolved without adding new variables, then no new variables should be added, as this would increase my workload. However, if the issue cannot be resolved without adding variables, as in the example I provided, you may use the symbol to declare a new variable and utilize it to address the problem.\n"
        sys_prompt2 = (f'You are an expert in {s_db} and {t_db} database field. '
                       f'Please provide me with the correct answer according to my requirements.') if m_gpt.getSys_prompt() == '' else m_gpt.getSys_prompt()
        convertedTestCase = llm.invoke(prompt2, m_gpt.getTemp(), m_gpt.getMax_tokens(), m_gpt.getTop_P(),
                                       m_gpt.getApi(),
                                       m_gpt.getModel(), sys_prompt2, n = 3)
        print(convertedTestCase)
        final_answer = ''
        for answer in convertedTestCase:
            impossiblereason, translated_q = '', ''
            if 'impossible' in answer:
                try:
                    impossiblereason = re.search(r'```impossible([\s\S]*?)```', answer).group(1)
                except Exception as e:
                    print(f'Exception:{e} --No match found! Rerunning.')
            else:
                try:
                    translated_q = re.search(r'```sql([\s\S]*?)```', answer).group(1)
                except Exception as e:
                    print(f'Exception:{e} --No match found! Rerunning.')
            if translated_q != "":
                if t_db.lower() == 'oracle':
                    status, info = execute_plsql(s_sql)
                else:
                    status, info = execute_plpgsql(s_sql)
                if status:
                    final_answer = translated_q
                    break
                else:
                    final_answer = translated_q
            elif impossiblereason != "":
                final_answer = f'```impossible {impossiblereason}```'

    return final_answer, summary

def llmtranslator_pl(s_sql: str, s_db: str, t_db: str, s_gpt: LLMSetting, m_gpt: LLMSetting):
    if t_db.lower() == 'oracle':
        status, info = execute_plsql(s_sql)
    else:
        status, info = execute_plpgsql(s_sql)
    status = False
    if status:
        return '```sql ' + s_sql + ' ```', 'NO SUMMARY'
    else:
        prompt1 = f"Please summarize the database features contained in the SQL of {s_db} database.\n" \
                  f"Step by step, analyze all the features and conditional expressions included.\n" \
                  f"The sql statement is: {s_sql}\n" \
                  f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
                  f"1: Make sure your answer includes all the features in the SQL.\n" \
                  f"2: Make sure that the summary you provide matches the description of the corresponding database document.\n" \
                  f"3: If the SQL query contains complex expressions, provide semantically equivalent simplified forms.\n" \
                  f"4: Make sure your answers are concise and don't provide too much explanatory information.\n" \
                  f"You need to summarize these features as succinctly as possible and return in the format: ```summary your summary here ```"
        sys_prompt1 = (f'You are an expert in {s_db} and {t_db} database field. '
                       f'Please provide me with the correct answer according to my requirements.') if s_gpt.getSys_prompt() == '' else s_gpt.getSys_prompt()
        summary = llm.invoke(prompt1, s_gpt.getTemp(), s_gpt.getMax_tokens(), s_gpt.getTop_P(), s_gpt.getApi(),
                             s_gpt.getModel(), sys_prompt1)
        summary = getSummary(summary)

        prompt2 = f"The source sql on {s_db}: {s_sql} cannot compile on {t_db}. This is the error message: {info}\n" \
                  f"Please check whether the above error information can be resolved. The following is a summary of the features in the source SQL: {summary} \n" \
                  f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
                  f"1: Translate the query from {s_db} to {t_db}. Do not add anything unless it is necessary.\n" \
                  f"2: Use a procedure or function instead to achieve similar functionality\n" \
                  f"3: The parameters of the procedure should remain consistent with those of the function, without arbitrarily adding or removing parameters.\n" \
                  f"4: Just return what I need in the format below, without any explanatory information.\n" \
                  f"The return format: ```sql your SQL here ```\n" \
                  f"Else please provide the reason.\n" \
                  f"The return format: ```impossible your reason here ```"
        sys_prompt2 = (f'You are an expert in {s_db} and {t_db} database field. '
                       f'Please provide me with the correct answer according to my requirements.') if m_gpt.getSys_prompt() == '' else m_gpt.getSys_prompt()
        convertedTestCase = llm.invoke(prompt2, m_gpt.getTemp(), m_gpt.getMax_tokens(), m_gpt.getTop_P(),
                                       m_gpt.getApi(),
                                       m_gpt.getModel(), sys_prompt2, n = 3)
        print(convertedTestCase)
        final_answer = ''
        for answer in convertedTestCase:
            impossiblereason, translated_q = '', ''
            if 'impossible' in answer:
                try:
                    impossiblereason = re.search(r'```impossible([\s\S]*?)```', answer).group(1)
                except Exception as e:
                    print(f'Exception:{e} --No match found! Rerunning.')
            else:
                try:
                    translated_q = re.search(r'```sql([\s\S]*?)```', answer).group(1)
                except Exception as e:
                    print(f'Exception:{e} --No match found! Rerunning.')
            if translated_q != "":
                if t_db.lower() == 'oracle':
                    status, info = execute_plsql(s_sql)
                else:
                    status, info = execute_plpgsql(s_sql)
                if status:
                    final_answer = translated_q
                    break
                else:
                    final_answer = translated_q
            elif impossiblereason != "":
                final_answer = f'```impossible {impossiblereason}```'

    return final_answer, summary

def llmtranslator_pl_SingleLLM(s_sql: str, s_db: str, t_db: str, s_gpt: LLMSetting, m_gpt: LLMSetting):
    prompt2 = f"The source sql on {s_db}: {s_sql} cannot compile on {t_db}.\n" \
              f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
              f"1: Translate the query from {s_db} to {t_db}. Do not add anything unless it is necessary.\n" \
              f"2: Use a procedure or function instead to achieve similar functionality\n" \
              f"3: The parameters of the procedure should remain consistent with those of the function, without arbitrarily adding or removing parameters.\n" \
              f"4: Just return what I need in the format below, without any explanatory information.\n" \
              f"The return format: ```sql your SQL here ```\n" \
              f"Else please provide the reason.\n" \
              f"The return format: ```impossible your reason here ```"
    sys_prompt2 = (f'You are an expert in {s_db} and {t_db} database field. '
                   f'Please provide me with the correct answer according to my requirements.') if m_gpt.getSys_prompt() == '' else m_gpt.getSys_prompt()
    convertedTestCase = llm.invoke(prompt2, m_gpt.getTemp(), m_gpt.getMax_tokens(), m_gpt.getTop_P(),
                                   m_gpt.getApi(),
                                   m_gpt.getModel(), sys_prompt2, n = 3)
    print(convertedTestCase)
    final_answer = ''
    for answer in convertedTestCase:
        impossiblereason, translated_q = '', ''
        if 'impossible' in answer:
            try:
                impossiblereason = re.search(r'```impossible([\s\S]*?)```', answer).group(1)
            except Exception as e:
                print(f'Exception:{e} --No match found! Rerunning.')
        else:
            try:
                translated_q = re.search(r'```sql([\s\S]*?)```', answer).group(1)
            except Exception as e:
                print(f'Exception:{e} --No match found! Rerunning.')
        if translated_q != "":
            if t_db.lower() == 'oracle':
                status, info = execute_plsql(s_sql)
            else:
                status, info = execute_plpgsql(s_sql)
            if status:
                final_answer = translated_q
                break
            else:
                final_answer = translated_q
        elif impossiblereason != "":
            final_answer = f'```impossible {impossiblereason}```'

    return final_answer, 'NULL'

def VerifyByLLMs(s_db: str, s_sql: str, t_db: str, t_sql: str, v_llm: LLMSetting):
    prompt1 = f"The following is the source SQL statement on {s_db}: {s_sql}\n" \
              f"The source SQL statement is translated to {t_db}: {t_sql}\n" \
              f"Step by step, first determine what SQL features the source SQL contains and whether those features have been successfully translated, then determine whether the translated SQL has the same semantics on {t_db} as the source SQL on {s_db}.\n" \
              f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
              f"1: If these two SQL are semantic equivalent, please return in the following format: ```verify EQUIVALENT ```\n" \
              f"2: Else, return in the following format: ```verify NON-EQUIVALENT your reason here ```"
    sys_prompt1 = (f'You are an expert in {s_db} and {t_db}. '
                   f'Please provide me with the correct answer according to my requirements.') if v_llm.getSys_prompt() == '' else v_llm.getSys_prompt()
    res = llm.invoke(prompt1, v_llm.getTemp(), v_llm.getMax_tokens(), v_llm.getTop_P(), v_llm.getApi(), v_llm.getModel(), sys_prompt1, n = 1)
    return res

def VerifyPLByLLMs(s_db: str, s_sql: str, t_db: str, t_sql: str, v_llm: LLMSetting, idx: int):
    right_ans = ''
    if s_db.lower() == 'postgresql':
        right_ans = read_from_plsql(idx, 'SQLProBench-Oracle')
    elif s_db.lower() == 'oracle':
        right_ans = read_from_plsql(idx, 'SQLProBench-PostgreSQL')

    prompt1 = f"The following is the source SQL statement on {s_db}: {s_sql}\n" \
              f"The source SQL statement is translated to {t_db}: {t_sql}\n" \
              f"Step by step, first determine what SQL features the source SQL contains and whether those features have been successfully translated, then determine whether the translated SQL has the same semantics on {t_db} as the source SQL on {s_db}.\n" \
              f"Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n" \
              f"1: If these two SQL are semantic equivalent, please return in the following format: ```verify EQUIVALENT ```\n" \
              f"2: Else, return in the following format: ```verify NON-EQUIVALENT your reason here ```" \
              f"Here is the equivalent query on {t_db}, which can serve as a reference for you to judge whether the translation is accurate: \n{right_ans}"
    sys_prompt1 = (f'You are an expert in {s_db} and {t_db}. '
                   f'Please provide me with the correct answer according to my requirements.') if v_llm.getSys_prompt() == '' else v_llm.getSys_prompt()
    print(f"Verify Prompt:{prompt1}")
    res = llm.invoke(prompt1, v_llm.getTemp(), v_llm.getMax_tokens(), v_llm.getTop_P(), v_llm.getApi(), v_llm.getModel(), sys_prompt1, n = 1)
    return res