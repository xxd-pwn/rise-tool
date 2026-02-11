import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adaptiveparser import parse_sql_by_pg
from applyrule import apply_rule
from llmtranslator import translate_query, translate_pl
from queryreduction import get_simplified_query, simplify_sqlbyLLM, get_simplified_query_pl, simplify_pl, \
    simplify_plbyLLM
from rulegen import extract_rule, abstract_rule
from utils.LLMSetting import LLMSetting
from utils.Rule import Rule
from utils.astoperation import copy_mytree, myast2sql
from utils.common import read_from_plsql
from utils.db import execute_plsql, execute_plpgsql


#override
def init_pl(tree, s_db, t_db):
    # #
    # PL/SQL PostgreSQL->Oracle
    rules = """
    ( Createfunctionstmt&& ( CREATE ) ( TREE_1 ) ( function ) ( TREE_2 ) ( TREE_3 ) ( returns ) ( Func_return&& ( Func_type&& ( Typename&& ( Simpletypename&& ( Generictype&& ( Type_function_name&& ( Identifier&& ( refcursor ) ) ) ) ) ( Opt_array_bounds&& ) ) ) ) ( Createfunc_opt_list&& ( Createfunc_opt_item&& ( AS ) ( Func_as&& ( Plsql_block&& ( $$ ) ( Declare_section&& ( declare ) ( TREE_4 ) ) ( TREE_5 ) ( ; ) ( $$ ) ( language ) ( plpgsql ) ) ) ) ) ) #TO# ( Createfunctionstmt&& ( CREATE ) ( TREE_1 ) ( PROCEDURE ) ( TREE_2 ) ( TREE_3 ) ( Createfunc_opt_list&& ( Createfunc_opt_item&& ( AS ) ( Func_as&& ( Plsql_block&& ( Declare_section&& ( TREE_4 ) ) ( TREE_5 ) ) ) ) ) )\n
    ( Createfunc_opt_item&& ( language ) ( plpgsql ) ( as ) ( Func_as&& ( Plsql_block&& ( $$ ) ( Declare_section&& ( declare ) ( TREE_1 ) ) ( TREE_2 ) ( ; ) ( $$ ) ) ) ) #TO# ( Createfunc_opt_item&& ( as ) ( Func_as&& ( Plsql_block&& ( Declare_section&& ( TREE_1 ) ) ( TREE_2 ) ) ) )\n
    ( Createfunc_opt_item&& ( language ) ( plpgsql ) ( as ) ( Func_as&& ( Plsql_block&& ( $$ ) ( TREE_1 ) ( TREE_2 ) ( ; ) ( $$ ) ) ) ) #TO# ( Createfunc_opt_item&& ( as ) ( Func_as&& ( Plsql_block&& ( TREE_1 ) ( TREE_2 ) ) ) )\n

    """

    # PL/SQL Oracle->PostgreSQL
    rules = """
    ( Createfunctionstmt&& ( CREATE ) ( Or_replace_&& ( or ) ( replace ) ) ( PROCEDURE ) ( Func_name&& ( TREE_1 ) ) ( Createfunc_opt_list&& ( TREE_2 ) ) ) #TO# ( Createfunctionstmt&& ( CREATE ) ( Or_replace_&& ( or ) ( replace ) ) ( PROCEDURE ) ( Func_name&& ( TREE_1 ) ) ( Func_args_with_defaults&& ( left_bracket ) ( right_bracket ) ) ( Createfunc_opt_list&& ( TREE_2 ) ) )\n
    
    ( Declare_item&& ( TREE_1 ) ( Type_spec&& ( SYS_REFCURSOR ) ) ( ; ) ) #TO# ( Declare_item&& ( TREE_1 ) ( Type_spec&& ( Func_type&& ( Typename&& ( Simpletypename&& ( Generictype&& ( Type_function_name&& ( Identifier&& ( refcursor ) ) ) ) ) ( Opt_array_bounds&& ) ) ) ) ( := ) ( A_expr&& ( A_expr_qual&& ( A_expr_lessless&& ( A_expr_or&& ( A_expr_and&& ( A_expr_between&& ( A_expr_in&& ( A_expr_unary_not&& ( A_expr_isnull&& ( A_expr_is_not&& ( A_expr_compare&& ( A_expr_like&& ( A_expr_qual_op&& ( A_expr_unary_qualop&& ( A_expr_add&& ( A_expr_mul&& ( A_expr_caret&& ( A_expr_unary_sign&& ( A_expr_at_time_zone&& ( A_expr_collate&& ( A_expr_typecast&& ( C_expr_expr&& ( Aexprconst&& ( Sconst&& ( Anysconst&& ( 'mycursor' ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ( ; ) )\n

    ( Pl_stmt&& ( dbms_sql ) ( . ) ( return_result ) ( left_bracket ) ( TREE_1 ) ( right_bracket ) ( ; ) ) #TO# ( Pl_stmt&& ( return ) ( A_expr&& ( A_expr_qual&& ( A_expr_lessless&& ( A_expr_or&& ( A_expr_and&& ( A_expr_between&& ( A_expr_in&& ( A_expr_unary_not&& ( A_expr_isnull&& ( A_expr_is_not&& ( A_expr_compare&& ( A_expr_like&& ( A_expr_qual_op&& ( A_expr_unary_qualop&& ( A_expr_add&& ( A_expr_mul&& ( A_expr_caret&& ( A_expr_unary_sign&& ( A_expr_at_time_zone&& ( A_expr_collate&& ( A_expr_typecast&& ( C_expr_expr&& ( Columnref&& ( Colid&& ( TREE_1 ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ( ; ) )\n
    
    """

    rulesList = rules.split('\n')
    ruleset = []
    for rule in rulesList:
        if rule != '' and len(rule.split('#TO#')) == 2:
            source_pattern, target_pattern = rule.split('#TO#')
            rule = Rule(source_pattern, target_pattern)
            ruleset.append(rule)
    sql = tree.print_query()

    # print(f"TEST:{len(ruleset)}")
    for rule in ruleset:
        copy_tree = copy_mytree(tree)
        copy_tree = apply_rule(rule, copy_tree, s_db, t_db)
        copy_query = myast2sql(copy_tree)
        if t_db.lower() == 'oracle':
            judge, info = execute_plsql(copy_query)
        else:
            judge, info = execute_plpgsql(copy_query)
            if rule.get_source_pattern() == '    ( Createfunctionstmt&& ( CREATE ) ( TREE_1 ) ( PROCEDURE ) ( TREE_2 ) ( TREE_3 ) ( Createfunc_opt_list&& ( Createfunc_opt_item&& ( AS ) ( Func_as&& ( Plsql_block&& ( Declare_section&& ( TREE_4 ) ) ( TREE_5 ) ) ) ) ) ) ' and 'sys_refcursor' not in sql.lower():
                continue
        newmsg = info
        # print(f'Result: {judge}, errmsg: {newmsg}')
        if judge:
            tree = apply_rule(rule, tree, s_db, t_db)
        elif '1054 (42S22)' in newmsg:
            continue
        else:
            tree = apply_rule(rule, tree, s_db, t_db)

    return tree

if __name__ == '__main__':
    sourcedb = 'PostgreSQL'
    targetdb = 'Oracle'
    llm_engine = 'gpt-4o-2024-05-13'
    # llm_engine = 'DeepSeek-V3'

    sql = read_from_plsql(44, 'SQLProBench-PostgreSQL')
    if targetdb.lower() == 'oracle':
        judge, info = execute_plsql(sql)
    else:
        judge, info = execute_plpgsql(sql)
    if judge:
        print(f'Original SQL do not need new rules:\n{sql}')
    else:
        original_tree = parse_sql_by_pg(sql)
        original_tree = init_pl(original_tree, sourcedb, targetdb)
        converted_sql = myast2sql(original_tree)
        if targetdb.lower() == 'oracle':
            judge, info = execute_plsql(converted_sql)
        else:
            judge, info = execute_plpgsql(converted_sql)
        if judge:
            print(f'Original SQL do not need new rules:\n{converted_sql}')
        else:
            print(f'Original SQL has SQL dialects. errmsg:{info}')
            print(f'Original SQL:\n{sql}')
            print(f'After apply the rules in the ruleset: \n{converted_sql}')
            print(f'Original SQL AST:\n{original_tree.get_parentheses_with_TREE()}')
            simplified_tree = get_simplified_query_pl(converted_sql, sourcedb, targetdb)
            simplified_sql = myast2sql(simplified_tree)

            # Visualization.print_tree(source_tree)

            print(f'Simplified SQL from random delete:\n{simplified_sql}')
            simplify_llm = LLMSetting('openai', llm_engine, 0.7, 1.0, 2048, '')
            simplified_sql = simplify_plbyLLM(simplified_sql, targetdb, sourcedb, simplify_llm)
            print(f'Simplified SQL from LLM:\n{simplified_sql}')

            llm_analysis = LLMSetting('openai', llm_engine, 0, 1.0, 2048, '')
            llm_translation = LLMSetting('openai', llm_engine, 0.7, 1.0, 2048, '')
            converted_sql, summary = translate_pl(simplified_sql, sourcedb, targetdb, llm_analysis, llm_translation)
            converted_sql = converted_sql.replace('NULL;',"")
            converted_sql = converted_sql.replace('null;', "")
            print(summary)
            print(converted_sql)
            simplified_tree = parse_sql_by_pg(simplified_sql)
            target_tree = parse_sql_by_pg(converted_sql)
            print(f'Node num:{target_tree.count_nodes()}')
            # if target_tree.count_nodes() >= 1146:
            #     print('Timeout!')
            #     exit(-1)

            rule_addsemicolon = Rule('( Root&& ( Stmtblock&& ( Stmtmulti&& ( TREE_1 ) ) ) ( <EOF> ) )',
                                     '( Root&& ( Stmtblock&& ( Stmtmulti&& ( TREE_1 ) ( ; ) ) ) ( <EOF> ) )')
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
            if targetdb.lower() == 'oracle':
                judge, info = execute_plsql(myast2sql(target_tree))
            else:
                judge, info = execute_plpgsql(myast2sql(target_tree))
            print(f'Result: {judge}, errmsg: {info}')
