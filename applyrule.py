from utils.Rule import Rule
from utils.astoperation import *
from utils.db import getConnbyName, SQLExecuteWithRollback

# Perform the SQL dialect conversion by applying the rule
def apply_rule(rule: Rule, source_tree: ASTNode, source_db, target_db):
    source_parentheses = source_tree.get_parentheses_with_TREE()
    judge, const = contains_subtree(source_parentheses, rule.get_source_pattern())
    # print(f'AST:{source_parentheses}\nRule:{rule.get_source_pattern()}')
    # print(f'judge:{judge};const:{const}')
    while judge:
        ruleRoot = find_rootOfPattern(source_tree, rule.get_source_pattern())
        target_content = rule_instantiation(rule.get_target_pattern(), const)
        try:
            new_subtree = parentheses_ast(target_content) # Construct a tree based on the expression in parentheses
        except Exception as e:
            print(f'Error: {e}')
            return source_tree

        # Copy the tree and roll back the current modifications
        copy_tree = copy_mytree(source_tree)
        copy_ruleRoot = find_rootOfPattern(copy_tree, rule.get_source_pattern())
        copy_ruleRoot.gen_reserved_tree()

        if ruleRoot.getContent() != 'Root&&':
            ruleRoot.getParent().replaceChild(ruleRoot, new_subtree)
        else:
            source_tree = new_subtree

        converted_sql = source_tree.print_query()
        conn1 = getConnbyName(target_db)
        try:
            SQLExecuteWithRollback(conn1, converted_sql)
        except Exception as e:
            if '1054 (42S22)' in str(e): # The error message is caused by the use of a non-existent column
                source_tree = copy_tree

        source_parentheses = source_tree.get_parentheses_with_TREE()
        judge, const = contains_subtree(source_parentheses, rule.get_source_pattern())

    source_tree.remove_reserved()

    return source_tree

def rule_instantiation(target_pattern, const):
    target_pattern_list = target_pattern.split(' ')
    target_content = ''
    for item in target_pattern_list:
        if item == 'ANYVALUE':
            item = generate_secure_random_string()
        target_content += item + ' '
    for key in const:
        target_content = replace_constValue(target_content, key, const[key])
        if '$' not in key:
            target_content = target_content.replace(key, const[key]) # replace TREE_N
    return target_content

# replace $N
def replace_constValue(target_pattern, key, value):
    list = target_pattern.split(' ')
    for i in range(len(list)):
        if list[i] == key:
            list[i] = value
    return ' '.join(list)

def parentheses_ast(parentheses: str):
    tokens = parentheses.replace('(', ' ( ').replace(')', ' ) ').split()
    stack = []
    root = None
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == '(':
            i += 1
            if i >= len(tokens):
                raise ValueError("Unexpected end of input after '('")
            if tokens[i].startswith("\'") and tokens[i].endswith("\'"):
                name = tokens[i]
            elif tokens[i].startswith("\"") and tokens[i].endswith("\""):
                name = tokens[i]
            elif "\'" in tokens[i] or "\"" in tokens[i]:
                name = tokens[i]
                while i < len(tokens):
                    i += 1
                    name += ' ' + tokens[i]
                    if "\'" in tokens[i] or "\"" in tokens[i]:
                        break
            else:
                name = tokens[i]
            node = ASTNode('TerminalNode', name)
            if stack:
                stack[-1].addChild(node)
            else:
                root = node
            stack.append(node)
            i += 1
        elif token == ')':
            if not stack:
                raise ValueError("Unexpected ')'")
            current_node = stack.pop()
            if len(current_node.getChildren()) == 0 and '&&' not in current_node.getContent() and current_node.getContent() != 'Opt_array_bounds':
                current_node.setNodeType('TerminalNode')
            elif '@new&&' in current_node.getContent():
                current_node.setNodeType('TerminalNode')
            else:
                current_node.setNodeType('Non-terminalNode')
            i += 1
        else:
            raise ValueError(f"Unexpected token: {token}")
    if stack:
        raise ValueError("Unclosed parentheses in input")
    return root