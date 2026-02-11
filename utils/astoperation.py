import random
import secrets
import string

from antlr4.tree.Tree import *
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ASTNode import *


def copy_tree(ctx):
    if isinstance(ctx, TerminalNodeImpl):
        cont = ctx.getText()
        cont = cont.replace('\n', ' ')
        while '  ' in cont:
            cont = cont.replace('  ', ' ')
        node = ASTNode(nodeType='TerminalNode', content=cont)
        return node
    else:
        node = ASTNode(nodeType='Non-terminalNode', content=type(ctx).__name__.replace("Context", "") + '&&')

    for child in ctx.getChildren():
        child_node = copy_tree(child)
        if child_node is not None:
            node.addChild(child_node)

    return node

def copy_mytree(root):
    if root.getNodeType() == 'TerminalNode':
        cont = root.getContent().replace('\n', ' ')
        while '  ' in cont:
            cont = cont.replace('  ', ' ')
        node = ASTNode(nodeType='TerminalNode', content=cont)
        return node
    else:
        cont = root.getContent().replace('\n', ' ')
        while '  ' in cont:
            cont = cont.replace('  ', ' ')
        node = ASTNode(nodeType='Non-terminalNode', content=cont)

    for child in root.getChildren():
        child_node = copy_mytree(child)
        if child_node is not None:
            node.addChild(child_node)

    return node

def myast2sql(newTree):
    return newTree.print_query()

def read_str(inputstr):
    inputstr = inputstr.replace('\n', ' ')
    inputstr = inputstr.replace('\t', ' ')
    inputstr = inputstr.replace(';', ' ; ')
    inputstr = inputstr.replace('(', ' ( ').replace(')', ' ) ')
    while '  ' in inputstr:
        inputstr = inputstr.replace('  ', ' ')
    temp = inputstr.split(' ')
    list = []
    stringrec = ""
    for item in temp:
        if item != '' and "'" not in item and stringrec == "" and '"' not in item:
            list.append(item)
        elif item != '' and item.startswith("'") and item.endswith("'") and stringrec == "":
            list.append(item)
        elif item != '' and item.startswith('"') and item.endswith('"') and stringrec == "":
            list.append(item)
        elif item != '' and "'" in item:
            if stringrec == "":
                stringrec = item
            else:
                stringrec = stringrec + " " + item
                list.append(stringrec)
                stringrec = ""
        elif item != '' and '"' in item:
            if stringrec == "":
                stringrec = item
            else:
                stringrec = stringrec + " " + item
                list.append(stringrec)
                stringrec = ""
        elif item != '' and "'" not in item and stringrec != "":
            stringrec = stringrec + " " + item
        elif item != '' and '"' not in item and stringrec != "":
            stringrec = stringrec + " " + item
    return list

# Determine whether strA contains strB based on the expression in parentheses
def contains_subtree(treeA: str, treeB: str, AST_root = None):
    listA = read_str(treeA)
    listB = read_str(treeB)
    const = {}
    i = 0
    j = 0
    while i < len(listA):
        old_i = i
        j = 0
        while j < len(listB):
            # print(f'i = {i};j = {j}')
            # print(f'listA: {listA[i]};listB: {listB[j]}')
            if '$' in listB[j]:
                const[listB[j]] = listA[i]
                i = i + 1
                if j == len(listB) - 1:
                    return True, const
                if i == len(listA):
                    return False, {}
            elif j + 1 < len(listB) and 'TREE_' in listB[j + 1] and listB[j] == '(':
                if listA[i] != '(':
                    break
                if i + 1 >= len(listA):
                    break
                if i + 1 < len(listA) and listA[i + 1] not in listB[j + 1]:
                    break
                stack = []
                tree = ''
                judge_completeTree = False
                while i < len(listA):
                    if listA[i] == '(':
                        judge_completeTree = True
                        stack.append(listA[i])
                    elif listA[i] == ')' and len(stack) > 0:
                        stack.pop()
                    tree += listA[i] + ' '
                    i += 1
                    if len(stack) == 0 and judge_completeTree == True:
                        break
                copy_tree = tree
                const[' '.join(listB[j:j+3])] = copy_tree
                j = j + 2
                if j == len(listB) - 1:
                    return True, const
                if i == len(listA):
                    return False, {}

            elif listB[j].lower() != listA[i].lower():
                const = {}
                i = old_i
                break

            elif listB[j].lower() == listA[i].lower():
                if j == len(listB) - 1:
                    return True, const
                else:
                    i = i + 1
                    if i == len(listA):
                        return False, {}

            j += 1
            if j == len(listB) and i < len(listA):
                return True, const

        i += 1

    return False, {}

# Determine whether two trees are equivalent, consider the abstract symbols
def equal_tree(treeA: str, treeB: str):
    listA = read_str(treeA)
    listB = read_str(treeB)

    i = 0
    j = 0
    while i < len(listA):
        while j < len(listB):

            if '$' in listB[j]:
                if j == len(listB) - 1 and i == len(listA) - 1:
                    return True
                i = i + 1
                if i >= len(listA):
                    return False

            elif j + 1 < len(listB) and 'TREE_' in listB[j + 1] and listB[j] == '(':
                if listA[i] != '(':
                    break
                if i + 1 >= len(listA):
                    break
                if i + 1 < len(listA) and listA[i + 1] not in listB[j + 1]:
                    break
                stack = []
                tree = ''
                judge_completeTree = False
                while i < len(listA):
                    if listA[i] == '(':
                        judge_completeTree = True
                        stack.append(listA[i])
                    elif listA[i] == ')' and len(stack) > 0:
                        stack.pop()
                    tree += listA[i] + ' '
                    i += 1
                    if len(stack) == 0 and judge_completeTree == True:
                        break
                j = j + 2
                if j == len(listB) - 1 and i == len(listA):
                    return True
                if i == len(listA):
                    return False

            elif 'TREE_' in listB[j]:
                if listA[i] not in listB[j]:
                    return False
                stack = []
                tree = ''
                judge_completeTree = False
                while i < len(listA):
                    if listA[i] == '(':
                        judge_completeTree = True
                        stack.append(listA[i])
                    elif listA[i] == ')' and len(stack) > 0:
                        stack.pop()
                    tree += listA[i] + ' '
                    i += 1
                    if len(stack) == 0 and judge_completeTree == True:
                        break

                if j == len(listB) - 1 and i == len(listA):
                    return True
                if i == len(listA):
                    return False

            elif listB[j].lower() != listA[i].lower():
                return False
            elif listB[j].lower() == listA[i].lower():
                if j == len(listB) - 1 and i == len(listA) - 1:
                    return True
                else:
                    i = i + 1
                    if i >= len(listA):
                        return False

            j += 1
            if j == len(listB) and i < len(listA):
                return False

        i += 1

    return False

# From the perspective of the tree, determine whether there is a subtree that matches the source template of the rule
# (The efficiency will be slower than directly judging from contains_subtree. And the matching part of contains_subtree is not definitely a tree.)
def find_rootOfPattern(root, pattern: str):#, parser, myroot):
    judge = equal_tree(root.get_parentheses_with_TREE(), pattern)
    if judge:
        return root

    for child in root.getChildren():
        result = find_rootOfPattern(child, pattern)
        if result is not None:
            return result

    return None

def generate_secure_random_string() -> str:
    random_integer = random.randint(5, 10)
    characters = string.ascii_letters
    secure_random_string = ''.join(secrets.choice(characters) for _ in range(random_integer))
    return secure_random_string
