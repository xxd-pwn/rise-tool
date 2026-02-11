import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time

from adaptiveparser import parse_sql_by_pg
from applyrule import apply_rule
from llmtranslator import translate_query
from queryreduction import get_simplified_query, simplify_sqlbyLLM
from rulegen import extract_rule, abstract_rule
from utils.LLMSetting import LLMSetting
from utils.Rule import Rule
from utils.astoperation import copy_mytree, myast2sql
from utils.common import read_from_tpcds
from utils.db import verify

#override
def init(tree, s_db, t_db):
    # TODO: Add correct new rules below.
    rules = """
        """

    rulesList = rules.split('\n')
    ruleset = []
    for rule in rulesList:
        if rule != '' and len(rule.split('#TO#')) == 2:
            source_pattern, target_pattern = rule.split('#TO#')
            # print(f'rule: {source_pattern}->{target_pattern}')
            rule = Rule(source_pattern, target_pattern)
            ruleset.append(rule)
    sql = tree.print_query()

    # print(f"TEST:{len(ruleset)}")
    for rule in ruleset:
        copy_tree = copy_mytree(tree)
        copy_tree = apply_rule(rule, copy_tree, s_db, t_db)
        copy_query = myast2sql(copy_tree)
        judge, info = verify(s_db, sql, t_db, copy_query)
        newmsg = info
        # print(f'Result: {judge}, errmsg: {newmsg}')
        if judge:
            tree = apply_rule(rule, tree, s_db, t_db)
            break
        elif '1054 (42S22)' in newmsg:
            continue
        else:
            tree = apply_rule(rule, tree, s_db, t_db)

    return tree


if __name__ == '__main__':
    sourcedb = 'PostgreSQL'
    targetdb = 'MySQL'
    llm_engine = 'gpt-4o-2024-05-13'
    # llm_engine = 'DeepSeek-V3'
    start_time = time.time()
    sql = read_from_tpcds(12, 'TPC-DS-PostgreSQL')
    judge, info = verify(sourcedb, sql, targetdb, sql)
    if judge == True:
        print(f'Original SQL do not need new rules:\n{sql}')
    else:
        original_tree = parse_sql_by_pg(sql)
        original_tree = init(original_tree, sourcedb, targetdb)
        converted_sql = myast2sql(original_tree)
        judge, info = verify(sourcedb, sql, targetdb, converted_sql)
        if judge == True:
            print(f'Original SQL do not need new rules:\n{converted_sql}')
        else:
            print(f'Original SQL has SQL dialects. errmsg:{info}')
            print(f'Original SQL:\n{sql}')
            print(f'After apply the rules in the ruleset: \n{converted_sql}')
            print(f'Original SQL AST:\n{original_tree.get_parentheses_with_TREE()}')
            simplified_tree = get_simplified_query(converted_sql, sourcedb, targetdb)
            simplified_sql = myast2sql(simplified_tree)

            print(f'Simplified SQL from random delete:\n{simplified_sql}')
            simplify_llm = LLMSetting('openai', llm_engine, 0.7, 1.0, 2048, '')
            simplified_sql = simplify_sqlbyLLM(simplified_sql, targetdb, sourcedb, simplify_llm)
            print(f'Simplified SQL from LLM:\n{simplified_sql}')

            llm_analysis = LLMSetting('openai', llm_engine, 0, 1.0, 2048, '')
            llm_translation = LLMSetting('openai', llm_engine, 0.7, 1.0, 2048, '')
            converted_sql, summary = translate_query(simplified_sql, sourcedb, targetdb, llm_analysis, llm_translation)
            print(summary)
            print(converted_sql)
            simplified_tree = parse_sql_by_pg(simplified_sql)
            target_tree = parse_sql_by_pg(converted_sql)

            rule_addsemicolon = Rule('( Stmtmulti&& ( TREE_1_Stmt&& ) )',
                                     '( Stmtmulti&& ( TREE_1_Stmt&& ) ( ; ) )')
            target_tree = apply_rule(rule_addsemicolon, target_tree, sourcedb, targetdb)

            bestNode1, bestNode2 = extract_rule(simplified_tree, target_tree, simplified_tree, target_tree)
            # Visualization.print_tree(target_tree)
            print('original rule')
            print(f'source pattern:{bestNode1.get_parentheses()}')
            print(f'target pattern:{bestNode2.get_parentheses()}')
            abstract_rule(bestNode1, bestNode2)
            print('processed rule')
            print(f'source pattern:{bestNode1.get_parentheses_with_TREE()}')
            print(f's_pattern_str:{bestNode1.print_query()}')
            print(f'target pattern:{bestNode2.get_parentheses_with_TREE()}')
            print(f't_pattern_str:{bestNode2.print_query()}')
            print(f'new rule:\n{bestNode1.get_parentheses_with_TREE()} #TO# {bestNode2.get_parentheses_with_TREE()}\n')
            newRule = Rule(bestNode1.get_parentheses_with_TREE(), bestNode2.get_parentheses_with_TREE())
            target_tree = apply_rule(newRule, original_tree, sourcedb, targetdb)
            print(f'Apply the rule to the source query')
            print(f'The final query:\n{myast2sql(target_tree)}')
            print(f'Query AST:\n{target_tree.get_parentheses_with_TREE()}')
            judge, info = verify(sourcedb, sql, targetdb, myast2sql(target_tree))
            print(f'Result: {judge}, errmsg: {info}')
    end_time = time.time()
    print(f'Time cost: {end_time - start_time}')