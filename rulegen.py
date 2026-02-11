from adaptiveparser import *
from applyrule import apply_rule
from utils.ASTNode import ASTNode
from utils.Rule import Rule
from utils.common import read_from_tpcds


def extract_rule(source_tree: ASTNode, target_tree: ASTNode, source_tree_p: ASTNode, target_tree_p: ASTNode):
    if equal_except_subtrees(source_tree, target_tree, source_tree_p, target_tree_p):
        for childNode_s in source_tree_p.getChildren():
            childNode_t = None
            for childNode2 in target_tree_p.getChildren():
                if childNode_s.isequal(childNode2):
                    childNode_t = childNode2
                    break
            if childNode_t is None:
                continue
            else:
                rule_root1, rule_root2 = extract_rule(source_tree, target_tree, childNode_s, childNode_t)
                if rule_root1 is not None and rule_root2 is not None:
                    return rule_root1, rule_root2
        return source_tree_p, target_tree_p
    else:
        return None, None

def abstract_rule(node1: ASTNode, node2: ASTNode):
    nodeList1 = node1.find_all_nodes()
    nodeList2 = node2.find_all_nodes()
    num = 1
    for node_1 in nodeList1:
        for node_2 in nodeList2:
            if node_1.getParent() is not None and node_2.getParent() is not None:
                if node_1.getParent().getContent() == 'Iconst&&' and node_2.getParent().getContent() == 'Iconst&&' and node_1.getContent() == node_2.getContent() and '$' not in node_1.getContent():
                    content = node_1.getContent()
                    for node_1_tmp in nodeList1:
                        if node_1_tmp.getContent() == content:
                            node_1_tmp.setContent(f'${num}')
                    for node_2_tmp in nodeList2:
                        if node_2_tmp.getContent() == content:
                            node_2_tmp.setContent(f'${num}')
                    num += 1
                elif node_1.getParent().getContent() == 'Identifier&&' and node_2.getParent().getContent() == 'Identifier&&' and node_1.getContent() == node_2.getContent() and '$' not in node_1.getContent():
                    content = node_1.getContent()
                    for node_1_tmp in nodeList1:
                        if node_1_tmp.getContent() == content:
                            node_1_tmp.setContent(f'${num}')
                    for node_2_tmp in nodeList2:
                        if node_2_tmp.getContent() == content:
                            node_2_tmp.setContent(f'${num}')
                    num += 1
                elif node_1.getParent().getContent() == 'Anysconst&&' and node_2.getParent().getContent() == 'Anysconst&&' and node_1.getContent() == node_2.getContent() and '$' not in node_1.getContent():
                    content = node_1.getContent()
                    for node_1_tmp in nodeList1:
                        if node_1_tmp.getContent() == content:
                            node_1_tmp.setContent(f'${num}')
                    for node_2_tmp in nodeList2:
                        if node_2_tmp.getContent() == content:
                            node_2_tmp.setContent(f'${num}')
                    num += 1
    judge = True
    num = 1
    while judge:
        judge = _abstract_rule_visit(node1, node2, num)
        num += 1

def equal_tree(treeA: ASTNode, treeB: ASTNode):
    if treeA is None and treeB is None:
        return True
    if treeA is None or treeB is None:
        return False
    if (treeA.getNodeType() != treeB.getNodeType() or
            (treeA.getContent().lower() != treeB.getContent().lower() and 'TREE_' not in treeA.getContent() and 'TREE_' not in treeB.getContent())):
        return False
    childrenA = treeA.getChildren()
    childrenB = treeB.getChildren()
    if len(childrenA) != len(childrenB):
        return False
    for childA, childB in zip(childrenA, childrenB):
        if not equal_tree(childA, childB):
            return False
    return True

# Determine whether two trees are exactly the same except for a certain subtree
def equal_except_subtrees(treeA: ASTNode, treeB: ASTNode, subtreeA: ASTNode, subtreeB: ASTNode):
    def equal_tree_with_subtree_handling(treeA: ASTNode, treeB: ASTNode) -> bool:
        if treeA is None and treeB is None:
            return True
        if treeA is None:
            return treeB is subtreeB
        if treeB is None:
            return treeA is subtreeA
        if treeA is subtreeA and treeB is subtreeB:
            return True
        if treeA is subtreeA or treeB is subtreeB:
            return False

        if (treeA.getNodeType() != treeB.getNodeType() or
                (treeA.getContent().lower() != treeB.getContent().lower() and
                 'TREE_' not in treeA.getContent() and 'TREE_' not in treeB.getContent())):
            return False

        childrenA = treeA.getChildren()
        childrenB = treeB.getChildren()

        lenA = sum(1 for child in childrenA if child is not subtreeA)
        lenB = sum(1 for child in childrenB if child is not subtreeB)

        if lenA != lenB:
            return False

        iterA = [child for child in childrenA if child is not subtreeA]
        iterB = [child for child in childrenB if child is not subtreeB]

        for childA, childB in zip(iterA, iterB):
            if not equal_tree_with_subtree_handling(childA, childB):
                return False

        return True

    return equal_tree_with_subtree_handling(treeA, treeB)

def _abstract_rule_visit(node1: ASTNode, node2: ASTNode, num):
    nodeList1 = node1.find_all_nodes_exceptTREE()
    nodeList2 = node2.find_all_nodes_exceptTREE()

    for node_1 in nodeList1:
        for node_2 in nodeList2:
            if node_1.count_nodes() > 1 and node_2.count_nodes() > 1 and equal_tree(node_1, node_2):
                copy_tmp_tree = copy_mytree(node_1)
                for node_1_tmp in nodeList1:
                    if equal_tree(node_1_tmp, copy_tmp_tree):
                        node_1_tmp.setContent(f'TREE_{num}_{copy_tmp_tree.getContent()}')
                for node_2_tmp in nodeList2:
                    if equal_tree(node_2_tmp, copy_tmp_tree):
                        node_2_tmp.setContent(f'TREE_{num}_{copy_tmp_tree.getContent()}')
                return True
    return False

# Looser checking rules provide higher generality, but sometimes the rules may be incorrectly applied, leading to unexpected results
def _looser_abstract_rule_visit(node1: ASTNode, node2: ASTNode, num):
    nodeList1 = node1.find_all_nodes_exceptTREE()
    nodeList2 = node2.find_all_nodes_exceptTREE()

    for node_1 in nodeList1:
        for node_2 in nodeList2:
            if node_1.count_nodes() > 1 and node_2.count_nodes() > 1 and equal_tree(node_1, node_2):
                for node_1_tmp in nodeList1:
                    if equal_tree(node_1_tmp, node_1):
                        node_1_tmp.setContent(f'TREE_{num}')
                for node_2_tmp in nodeList2:
                    if equal_tree(node_2_tmp, node_2):
                        node_2_tmp.setContent(f'TREE_{num}')
                return True
    return False