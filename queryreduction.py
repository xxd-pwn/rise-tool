import re
from itertools import combinations

import pyodbc
from Levenshtein import ratio as levenshtein_ratio

from adaptiveparser import *
from applyrule import apply_rule
from utils import db, llm
from utils.LLMSetting import LLMSetting
from utils.Rule import Rule
from utils.astoperation import *
from utils.db import execute_plsql, execute_plpgsql


# TPC-DS
def delete_random_visit(node, errmsg, conn_t, conn_s):
    if node is None:
        return
    else:
        root_node = node.getRoot()
        mid_query = root_node.print_query_except(node)
        # print(f'mid_query:{mid_query}')
        canbedel = True
        try:
            db.SQLExecuteWithRollback(conn_t, mid_query)
            canbedel = False
        except Exception as e:
            new_errmsg = str(e)
            if new_errmsg != errmsg:
                canbedel = False
            else:
                try:
                    db.SQLExecuteWithRollback(conn_s, mid_query)
                except Exception as e:
                    canbedel = False
                    # judge, msg = compile_sql_by_pg(mid_query)
                    # if judge == False:
                    #     canbedel = False
                    # else:
                    #     canbedel = True
        if canbedel:
            node.deleteSelf()
        else:
            for child in node.getChildren():
                delete_random_visit(child, errmsg, conn_t, conn_s)
    return

def delete_all_visit(node):
    if node is None:
        return None
    children = [delete_all_visit(child) for child in node.getChildren()]
    node.setChildren(children)
    if node.getNodeType() == 'Non-terminalNode' and len(node.getChildren()) == 1:
        newChild = node.getChildren()[0]
        parent = node.getParent()
        if parent is not None:
            parent.replaceChild(node, newChild)
            return newChild
        else:
            return newChild
    return node

def run_delete_random(tree, target_db, source_db):
    conn_t = db.getConnbyName(target_db)
    conn_s = db.getConnbyName(source_db)
    old_query = myast2sql(tree)
    try:
        db.SQLExecuteWithRollback(conn_t, old_query)
        return
    except Exception as e:
        errmsg = str(e)
        judge = True
        while judge:
            delete_random_visit(tree, errmsg, conn_t, conn_s)
            new_query = myast2sql(tree)
            if new_query == old_query:
                judge = False
            else:
                old_query = new_query

def run_delete_random_two(tree, target_db, source_db):
    conn_t = db.getConnbyName(target_db)
    conn_s = db.getConnbyName(source_db)
    old_query = myast2sql(tree)
    try:
        db.SQLExecuteWithRollback(conn_t, old_query)
        return
    except Exception as e:
        errmsg = str(e)
        judge = True
        while judge:
            oldNodeNum = tree.count_nodes()
            # print(f'old SQL:{tree.print_query()}')
            _help_delete_random_two(tree.find_all_nodes(), errmsg, conn_t, conn_s)
            newNodeNum = tree.count_nodes()
            # print(f'new SQL:{tree.print_query()}')
            if newNodeNum == oldNodeNum:
                judge = False

def _help_delete_random_two(nodelist, errmsg, conn_t, conn_s):
    root_node = nodelist[0].getRoot()
    # print(f'node num:{len(nodelist)}')
    # idx = 0
    for node1, node2 in combinations(nodelist, 2):
        # idx += 1
        # print(f'idx:{idx}')
        mid_query = root_node.print_query_except_two(node1, node2)
        # print(f'mid_query:{mid_query}')
        canbedel = True
        try:
            db.SQLExecuteWithRollback(conn_t, mid_query)
            canbedel = False
        except Exception as e:
            # print(f'new_errmsg for {idx}:{str(e)}')
            new_errmsg = str(e)
            if new_errmsg != errmsg:
                canbedel = False
            else:
                try:
                    db.SQLExecuteWithRollback(conn_s, mid_query)
                except Exception as e:
                    # print(f'new_errmsg2 for {idx}:{str(e)}')
                    canbedel = False
                    # judge, msg = compile_sql_by_pg(mid_query)
                    # if judge == False:
                    #     canbedel = False
                    # else:
                    #     canbedel = True

        if canbedel:
            node1.deleteSelf()
            node2.deleteSelf()

def simplify(sql, source_db, target_db):
    query = sql
    mytree = parse_sql_by_pg(query)
    print(f"Original tree lens:{mytree.count_nodes()}")
    delete_all_visit(mytree)
    print(f"Simplified tree1 lens:{mytree.count_nodes()}")
    run_delete_random(mytree, target_db, source_db)
    print(f"Simplified tree2 lens:{mytree.count_nodes()}")
    # print(f'Simplified SQL1:{myast2sql(mytree)}')
    run_delete_random_two(mytree, target_db, source_db)
    print(f"Simplified tree3 lens:{mytree.count_nodes()}")
    # print(f'Simplified SQL2:{myast2sql(mytree)}')
    return mytree

def get_simplified_query(sql, source_db, target_db):
    simplified_tree = simplify(sql, source_db, target_db)
    s_sql = simplified_tree.print_query()
    tree = parse_sql_by_pg(s_sql)
    rule_addsemicolon = Rule('( Stmtmulti&& ( TREE_1_Stmt&& ) )',
                             '( Stmtmulti&& ( TREE_1_Stmt&& ) ( ; ) )')
    tree = apply_rule(rule_addsemicolon, tree, source_db, target_db)
    rule_addSelectTarget = Rule('( Simple_select_pramary&& ( select ) )',
                                '( Simple_select_pramary&& ( select ) ( Target_list_&& ( Target_list&& ( Target_label&& ( A_expr&& ( A_expr_qual&& ( A_expr_lessless&& ( A_expr_or&& ( A_expr_and&& ( A_expr_between&& ( A_expr_in&& ( A_expr_unary_not&& ( A_expr_isnull&& ( A_expr_is_not&& ( A_expr_compare&& ( A_expr_like&& ( A_expr_qual_op&& ( A_expr_unary_qualop&& ( A_expr_add&& ( A_expr_mul&& ( A_expr_caret&& ( A_expr_unary_sign&& ( A_expr_at_time_zone&& ( A_expr_collate&& ( A_expr_typecast&& ( C_expr_expr&& ( Aexprconst&& ( Iconst&& ( 1 ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) )')
    tree = apply_rule(rule_addSelectTarget, tree, source_db, target_db)
    return tree

def simplify_sqlbyLLM(sql, target_db, source_db, simplify_llm):
    print(f'Simplify the SQL:\n{sql}\n')
    conn = db.getConnbyName(target_db)
    conn_s = db.getConnbyName(source_db)
    original_error = ''
    try:
        db.SQLExecuteWithRollback(conn, sql)
    except Exception as e:
        original_error = str(e)
    simplify_prompt = f"""
    I want to migrate the following query from {source_db} to {target_db}.
    After executing the following query in {target_db}, the error message '{original_error}' is produced. Please help simplify this query to retain only the statements necessary to trigger this error message.\n
    Query: {sql}\n
    First, locate the specific position of the error, then analyze the cause of the error, and finally remove as much content irrelevant to the error as possible.\n
    The simplified SQL statement should be as short as possible. 
    Try to use the table names and column names that exist in the original statement, and do not generate new identifiers yourself to avoid introducing additional errors. The statement you provide should end with a semicolon.
    Delete the query CTE expression, redundant aliases, and column names, if possible. Note that, the simplified query you provided should compile correctly on {source_db}. 
    So that, The column you select and its corresponding table correspond to the original query, and if you cannot tell which table the column comes from, you should add all possible tables in the original query.
    Here is a base query. If possible, use the least cost to add dialect points to the base query and return it.\n
    Note that the dialect part needs to be preserved intact.\n
    Base query: select 1 from (select 1);\n
    Please return in the following format:```sql the simplified query here ```
    """

    simplified_sql = ''
    bestScore = 0
    shortest_len = 1000000000

    state = True

    answer_in_round = ""
    tryTime = 0
    while state and tryTime < 6:
        tryTime += 1
        simplify_sqls = llm.invoke(simplify_prompt, simplify_llm.getTemp(), simplify_llm.getMax_tokens(),
                                   simplify_llm.getTop_P(), simplify_llm.getApi(), simplify_llm.getModel(),
                                   simplify_llm.getSys_prompt(), n=5)
        print(f"Prompt:{simplify_prompt}")

        for sql in simplify_sqls:
            similarity = 0
            answer_in_round += f"Answer:\n##################################\n{sql}\n"
            print(f"Answer:\n##################################\n{sql}")
            print()
            try:
                sql_content = re.search(r'```sql([\s\S]*?)```', sql).group(1)
                try:
                    db.SQLExecuteWithRollback(conn, sql_content)
                    answer_in_round += f"The {target_db} do npt report any error.\n"
                    print(f"The {target_db} do not report any error.")
                except Exception as e:
                    new_error_info = str(e)
                    try:
                        db.SQLExecuteWithRollback(conn_s, sql_content)

                        answer_in_round += f"The {target_db} return:{new_error_info}\n"
                        similarity = calculate_similarity(original_error, new_error_info)
                        print(f"Similarity:{similarity}")
                        # 'ERROR 1054 (42S22)' ———— Unknown xxxx
                        if similarity > bestScore and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                            bestScore = similarity
                            simplified_sql = sql_content
                            shortest_len = len(sql_content)
                            state = False
                        elif similarity == bestScore and len(
                                sql_content) < shortest_len and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                            simplified_sql = sql_content
                            shortest_len = len(sql_content)
                            state = False

                    except Exception as e:
                        judge, msg = compile_sql_by_pg(sql_content)
                        if judge == False:
                            answer_in_round += f"This query cannot compile correctly on {source_db}. {source_db} return:{str(e)}\n"
                            print(f"This query cannot compile correctly on {source_db}. {source_db} return:{str(e)}")
                        else:
                            answer_in_round += f"The {target_db} return:{new_error_info}\n"
                            similarity = calculate_similarity(original_error, new_error_info)
                            print(f"Similarity:{similarity}")
                            # 'ERROR 1054 (42S22)' ———— Unknown xxxx
                            if similarity > bestScore and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                                bestScore = similarity
                                simplified_sql = sql_content
                                shortest_len = len(sql_content)
                                state = False
                            elif similarity == bestScore and len(
                                    sql_content) < shortest_len and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                                simplified_sql = sql_content
                                shortest_len = len(sql_content)
                                state = False

                    finally:
                        if similarity > bestScore:
                            simplified_sql = sql_content

            except Exception as e:
                print(f'Exception:{e} --No match found in simplify_sqls!')

        answer_in_round += 'All of these answers cannot trigger the original bug!'
        simplify_prompt += f"You have provide these simplified queries before, however none of them could trigger the original bug.\n{answer_in_round}"

    print(f'Returned simplify_sql:\n{simplified_sql}\nIts score: {bestScore}\n')

    return simplified_sql

def calculate_similarity(str1, str2):
    similarity = levenshtein_ratio(str1, str2)
    return similarity

# PLSQL
def get_simplified_query_pl(sql, source_db, target_db):
    simplified_tree = simplify_pl(sql, source_db, target_db)
    s_sql = simplified_tree.print_query()
    tree = parse_sql_by_pg(s_sql)
    rule_addsemicolon = Rule('( Root&& ( Stmtblock&& ( Stmtmulti&& ( TREE_1 ) ) ) ( <EOF> ) )',
                             '( Root&& ( Stmtblock&& ( Stmtmulti&& ( TREE_1 ) ( ; ) ) ) ( <EOF> ) )')
    tree = apply_rule(rule_addsemicolon, tree, source_db, target_db)
    rule_addSelectTarget = Rule('( Simple_select_pramary&& ( select ) )',
                                '( Simple_select_pramary&& ( select ) ( Target_list_&& ( Target_list&& ( Target_label&& ( A_expr&& ( A_expr_qual&& ( A_expr_lessless&& ( A_expr_or&& ( A_expr_and&& ( A_expr_between&& ( A_expr_in&& ( A_expr_unary_not&& ( A_expr_isnull&& ( A_expr_is_not&& ( A_expr_compare&& ( A_expr_like&& ( A_expr_qual_op&& ( A_expr_unary_qualop&& ( A_expr_add&& ( A_expr_mul&& ( A_expr_caret&& ( A_expr_unary_sign&& ( A_expr_at_time_zone&& ( A_expr_collate&& ( A_expr_typecast&& ( C_expr_expr&& ( Aexprconst&& ( Iconst&& ( 1 ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) ) )')
    tree = apply_rule(rule_addSelectTarget, tree, source_db, target_db)
    return tree

def simplify_pl(sql, source_db, target_db):
    query = sql
    mytree = parse_sql_by_pg(query)
    print(f"Original tree lens:{mytree.count_nodes()}")
    delete_all_visit(mytree)
    print(f"Simplified tree1 lens:{mytree.count_nodes()}")
    run_delete_random_pl(mytree, target_db, source_db)
    print(f"Simplified tree2 lens:{mytree.count_nodes()}")
    # print(f'Simplified SQL1:{myast2sql(mytree)}')
    run_delete_random_two_pl(mytree, target_db, source_db)
    print(f"Simplified tree3 lens:{mytree.count_nodes()}")
    # print(f'Simplified SQL2:{myast2sql(mytree)}')
    return mytree

def run_delete_random_pl(tree, target_db, source_db):
    old_query = myast2sql(tree)
    if target_db.lower() == 'oracle':
        judge, errmsg = execute_plsql(old_query)
    else:
        judge, errmsg = execute_plpgsql(old_query)
    if judge:
        return
    else:
        LoopCondition = True
        while LoopCondition:
            __delete_random_visit_pl(tree, errmsg, target_db, source_db)
            new_query = myast2sql(tree)
            if new_query == old_query:
                LoopCondition = False
            else:
                old_query = new_query

def __delete_random_visit_pl(node, old_errmsg, target_db, source_db):
    if node is None:
        return
    else:
        root_node = node.getRoot()
        mid_query = root_node.print_query_except(node)
        # print(f'mid_query:{mid_query}')

        if target_db.lower() == 'oracle':
            judge, new_errmsg = execute_plsql(mid_query)
        else:
            judge, new_errmsg = execute_plpgsql(mid_query)

        if judge:
            canbedel = False
        else:
            if new_errmsg != old_errmsg:
                canbedel = False
            else:
                if source_db.lower() == 'oracle':
                    canBeCompiled, msg = execute_plsql(mid_query)
                else:
                    canBeCompiled, msg = execute_plpgsql(mid_query)

                canbedel = canBeCompiled
                if not canBeCompiled:
                    judge, msg = compile_sql_by_pg(mid_query)
                    if judge == False:
                        canbedel = False
                    else:
                        canbedel = True

        if canbedel:
            node.deleteSelf()
        else:
            for child in node.getChildren():
                __delete_random_visit_pl(child, old_errmsg, target_db, source_db)
    return

def run_delete_random_two_pl(tree, target_db, source_db):
    old_query = myast2sql(tree)
    if target_db.lower() == 'oracle':
        judge, errmsg = execute_plsql(old_query)
    else:
        judge, errmsg = execute_plpgsql(old_query)
    if judge:
        return
    else:
        LoopCondition = True
        while LoopCondition:
            oldNodeNum = tree.count_nodes()
            _help_delete_random_two_pl(tree.find_all_nodes(), errmsg, target_db, source_db)
            newNodeNum = tree.count_nodes()
            if newNodeNum == oldNodeNum:
                LoopCondition = False

def _help_delete_random_two_pl(nodelist, old_errmsg, target_db, source_db):
    root_node = nodelist[0].getRoot()
    for node1, node2 in combinations(nodelist, 2):
        mid_query = root_node.print_query_except_two(node1, node2)

        if target_db.lower() == 'oracle':
            judge, new_errmsg = execute_plsql(mid_query)
        else:
            judge, new_errmsg = execute_plpgsql(mid_query)
        if judge:
            canbedel = False
        else:
            if new_errmsg != old_errmsg:
                canbedel = False
            else:
                if source_db.lower() == 'oracle':
                    canBeCompiled, msg = execute_plsql(mid_query)
                else:
                    canBeCompiled, msg = execute_plpgsql(mid_query)
                canbedel = canBeCompiled
                if not canBeCompiled:
                    judge, msg = compile_sql_by_pg(mid_query)
                    if judge == False:
                        canbedel = False
                    else:
                        canbedel = True

        if canbedel:
            node1.deleteSelf()
            node2.deleteSelf()

def simplify_plbyLLM(sql, target_db, source_db, simplify_llm):
    print(f'Simplify the SQL:\n{sql}\n')

    if target_db.lower() == 'oracle':
        judge, original_error = execute_plsql(sql)
    else:
        judge, original_error = execute_plpgsql(sql)

    simplify_prompt = f"""
    I want to migrate the following query from {source_db} to {target_db}.
    After executing the following query in {target_db}, the error message '{original_error}' is produced. Please help simplify this query to retain only the statements necessary to trigger this error message.\n
    Query: {sql}\n
    First, locate the specific position of the error, then analyze the cause of the error, and finally remove as much content irrelevant to the error as possible.\n
    Please make sure that the answers you provide meet my requirements below, otherwise my computer will explode!\n
    1: The simplified SQL statement should be as short as possible.\n
    2: Try to use the table names and column names that exist in the original statement, and do not generate new identifiers yourself to avoid introducing additional errors. The statement you provide should end with a semicolon.\n
    3: The simplified query you provided should compile correctly on {source_db}.\n
    4: The dialect part needs to be preserved intact.\n
    Please return in the following format:```sql the simplified query here ```
    """

    simplified_sql = sql
    bestScore = 0
    shortest_len = 1000000000

    state = True

    answer_in_round = ""
    tryTime = 0
    while state and tryTime < 6:
        tryTime += 1
        simplify_sqls = llm.invoke(simplify_prompt, simplify_llm.getTemp(), simplify_llm.getMax_tokens(),
                                   simplify_llm.getTop_P(), simplify_llm.getApi(), simplify_llm.getModel(),
                                   simplify_llm.getSys_prompt(), n=5)
        print(f"Prompt:{simplify_prompt}")

        for sql in simplify_sqls:
            answer_in_round += f"Answer:\n##################################\n{sql}\n"
            print(f"Answer:\n##################################\n{sql}")
            print()
            try:
                sql_content = re.search(r'```sql([\s\S]*?)```', sql).group(1)
                if target_db.lower() == 'oracle':
                    status, new_error_info = execute_plsql(sql_content)
                else:
                    status, new_error_info = execute_plpgsql(sql_content)
                if status:
                    answer_in_round += f"The {target_db} do npt report any error.\n"
                    print(f"The {target_db} do not report any error.")
                else:
                    if source_db.lower() == 'oracle':
                        status, unexpected_error_info = execute_plsql(sql_content)
                    else:
                        status, unexpected_error_info = execute_plpgsql(sql_content)

                    if status:
                        answer_in_round += f"The {target_db} return:{new_error_info}\n"
                        similarity = calculate_similarity(original_error, new_error_info)
                        print(f"Similarity:{similarity}")
                        # 'ERROR 1054 (42S22)' ———— Unknown xxxx
                        if similarity > bestScore and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                            bestScore = similarity
                            simplified_sql = sql_content
                            shortest_len = len(sql_content)
                            state = False
                        elif similarity == bestScore and len(
                                sql_content) < shortest_len and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                            simplified_sql = sql_content
                            shortest_len = len(sql_content)
                            state = False

                    else:
                        judge, msg = compile_sql_by_pg(sql_content)
                        if judge == False:
                            answer_in_round += f"This query cannot compile correctly on {source_db}. {source_db} return:{msg}\n"
                            print(f"This query cannot compile correctly on {source_db}. {source_db} return:{msg}")
                        else:
                            answer_in_round += f"The {target_db} return:{new_error_info}\n"
                            similarity = calculate_similarity(original_error, new_error_info)
                            print(f"Similarity:{similarity}")
                            # 'ERROR 1054 (42S22)' ———— Unknown xxxx
                            if similarity > bestScore and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                                bestScore = similarity
                                simplified_sql = sql_content
                                shortest_len = len(sql_content)
                                state = False
                            elif similarity == bestScore and len(
                                    sql_content) < shortest_len and similarity > 0.8 and '1054 (42S22)' not in new_error_info:
                                simplified_sql = sql_content
                                shortest_len = len(sql_content)
                                state = False

            except Exception as e:
                print(f'Exception:{e} --No match found in simplify_sqls!')

        answer_in_round += 'All of these answers cannot trigger the original bug!'
        simplify_prompt += f"You have provide these simplified queries before, however none of them could trigger the original bug.\n{answer_in_round}"

    print(f'Returned simplify_sql:\n{simplified_sql}\nIts score: {bestScore}\n')

    return simplified_sql