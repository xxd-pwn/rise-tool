import os
import re
from loguru import logger

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from applyrule import apply_rule
from utils.Rule import Rule
from utils.astoperation import copy_mytree, myast2sql
from utils.db import verify


def getSummary(response: str):
    summary = re.search(r'```summary([\s\S]*?)```', response)
    try:
        summary = summary.group(1)
        return summary
    except Exception as e:
        logger.error(f'Exception:{e} --No match found!')
        return ''

def init(tree, s_db, t_db, ruleset):
    sql = tree.print_query()
    for rule in ruleset:
        copy_tree = copy_mytree(tree)
        copy_tree = apply_rule(rule, copy_tree, s_db, t_db)
        copy_query = myast2sql(copy_tree)
        judge, info = verify(s_db, sql, t_db, copy_query)
        newmsg = info
        if judge:
            tree = apply_rule(rule, tree, s_db, t_db)
            break
        elif '1054 (42S22)' in newmsg:
            continue
        else:
            tree = apply_rule(rule, tree, s_db, t_db)
    return tree

def get_project_root(project_name):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    while True:
        dir_name = os.path.basename(current_dir)
        if dir_name == project_name:
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError(f"Fail to find: '{project_name}'")
        current_dir = parent_dir

def getTPC_DS_basedaddr(dataset):
    root = ''
    try:
        root = get_project_root('rise-tool')
    except FileNotFoundError as e:
        print(e)
    baseAddr = os.path.join(root, f'dataset\\TPC-DS\\{dataset}\\')
    return baseAddr

def read_from_tpcds(i, dataset):
    baseaddr = getTPC_DS_basedaddr(dataset)
    query_addr = baseaddr + f'query{i}.sql'
    with open(query_addr, 'r', encoding='ISO-8859-1') as file:
        query_content = file.read()
    query_content = query_content.split(';')[0] + ';'
    pattern = r"--.*?(?=\n)"
    matches = re.findall(pattern, query_content, re.MULTILINE)
    for match in matches:
        query_content = query_content.replace(match, '')
    query_content = query_content.replace('\n', ' ')
    while '  ' in query_content:
        query_content = query_content.replace('  ', ' ')
    return query_content

def getPLSQL_basedaddr(dataset):
    root = ''
    try:
        root = get_project_root('rise-tool')
    except FileNotFoundError as e:
        print(e)
    baseAddr = os.path.join(root, f'dataset\\Stored-Procedures\\{dataset}\\')
    return baseAddr

def read_from_plsql(i, dataset):
    baseaddr = getPLSQL_basedaddr(dataset)
    query_addr = baseaddr + f'proc{i}.sql'
    with open(query_addr, 'r', encoding='ISO-8859-1') as file:
        query_content = file.read()
    pattern = r"--.*?(?=\n)"
    matches = re.findall(pattern, query_content, re.MULTILINE)
    for match in matches:
        query_content = query_content.replace(match, '')
    while '  ' in query_content:
        query_content = query_content.replace('  ', ' ')
    return query_content + '\n'


def init_pl(tree, s_db, t_db):
    # #
    # PL/SQL
    rules = """
    """
    rulesList = rules.split('\n')
    ruleset = []
    for rule in rulesList:
        if rule != '' and len(rule.split('#TO#')) == 2:
            source_pattern, target_pattern = rule.split('#TO#')
            rule = Rule(source_pattern, target_pattern)
            ruleset.append(rule)
    sql = tree.print_query()
    for rule in ruleset:
        copy_tree = copy_mytree(tree)
        copy_tree = apply_rule(rule, copy_tree, s_db, t_db)
        copy_query = myast2sql(copy_tree)
        judge, info = verify(s_db, sql, t_db, copy_query)
        newmsg = info
        if judge:
            tree = apply_rule(rule, tree, s_db, t_db)
        elif '1054 (42S22)' in newmsg:
            continue
        else:
            tree = apply_rule(rule, tree, s_db, t_db)

    return tree
