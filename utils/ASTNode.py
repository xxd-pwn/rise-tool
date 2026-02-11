import re


class ASTNode:
    def __init__(self, nodeType, content):
        self.__nodeType = nodeType
        self.__content = content
        self.__children = []
        self.__parent = None

    def addChild(self, child):
        child.__parent = self
        self.__children.append(child)

    def getChildren(self):
        return self.__children

    def getParent(self):
        return self.__parent

    def getNodeType(self):
        return self.__nodeType

    def getContent(self):
        return self.__content

    def setContent(self, content):
        self.__content = content

    def setNodeType(self, nodeType):
        self.__nodeType = nodeType

    def setParent(self, parent):
        self.__parent = parent

    def setChildren(self, children):
        self.deleteChildren()
        for child in children:
            child.__parent = self
        self.__children = children

    def replaceChild(self, oldchild, newchild):
        for i, child in enumerate(self.__children):
            if child == oldchild:
                self.__children[i] = newchild
                newchild.__parent = self
                oldchild.__parent = None

    def deleteChild(self, child):
        self.__children.remove(child)
        child.__parent = None

    def deleteChildren(self):
        for child in self.__children:
            child.__parent = None
        self.__children = []

    def deleteParent(self):
        self.__parent = None

    def deleteSelf(self):
        if self.__parent is not None:
            self.__parent.deleteChild(self)

    def getRoot(self):
        if self.__parent is None:
            return self
        else:
            return self.__parent.getRoot()

    def visit(self, query):
        if self.__nodeType == 'TerminalNode':
            query.append(self.__content)
        for child in self.__children:
            child.visit(query)

    def get_parentheses(self):
        return self.tree_to_parentheses_visit(self)

    def tree_to_parentheses_visit(self, root):
        if not root:
            return ""

        result = [f"( {root.__content}"]

        for child in root.getChildren():
            child_result = self.tree_to_parentheses_visit(child)
            if child_result:
                result.append(child_result)

        result.append(")")

        return " ".join(result)

    def get_parentheses_with_TREE(self):
        return self.tree_to_parentheses_with_TREE_visit(self)

    def tree_to_parentheses_with_TREE_visit(self, root):
        if not root:
            return ""
        if root.__content == '(':
            result = [f"( left_bracket"]
        elif root.__content == ')':
            result = [f"( right_bracket"]
        else:
            result = [f"( {root.__content}"]

        if 'TREE' not in root.__content:
            for child in root.getChildren():
                child_result = self.tree_to_parentheses_with_TREE_visit(child)
                if child_result:
                    result.append(child_result)

        result.append(")")

        return " ".join(result)

    def simplify_tree(self, node):
        if not node or not node.getChildren():
            return node

        children = [self.simplify_tree(child) for child in node.getChildren()]
        node.setChildren(children)

        while (len(node.getChildren()) == 1 and
               len(node.getChildren()[0].getChildren()) == 1 and
               not node.getChildren()[0].getNodeType() == 'TerminalNode' and
               len(node.getChildren()[0].getChildren()[0].getChildren()) == 1 and
               not node.getChildren()[0].getChildren()[0].getNodeType() == 'TerminalNode'):
            node.setChildren(node.getChildren()[0].getChildren()[0].getChildren())

        return node

    def find_root(self):
        if self.getParent() is None:
            return self
        else:
            return self.getParent().find_root()

    def count_nodes(self):
        count = 1

        for child in self.getChildren():
            count += child.count_nodes()

        return count

    def find_all_nodes(self):
        collector = []
        self._find_all_nodes_helper(collector)
        return collector

    def _find_all_nodes_helper(self, collector):
        collector.append(self)
        for child in self.getChildren():
            child._find_all_nodes_helper(collector)

    def find_all_nodes_exceptTREE(self):
        collector = []
        self._find_all_nodes_except_helper( collector)
        return collector

    def _find_all_nodes_except_helper(self, collector):
        if 'TREE' not in self.getContent():
            collector.append(self)
            for child in self.getChildren():
                child._find_all_nodes_except_helper(collector)

    def print_query(self):
        query = []
        new_declare_item = ''
        self.visit(query)
        print_str = " ".join(query).replace(' <EOF>', '').replace('left_bracket', '(').replace('right_bracket', ')').replace(' (', '(')
        new_variables_list = self.__extract_new_variables(print_str)
        for item in new_variables_list:
            print_str = print_str.replace(item, '')
            declare_item = item.replace('@new&&', '').replace('&&', ' ') + ';'
            if declare_item not in new_declare_item:
                new_declare_item += declare_item
        print_str = re.sub(r'begin', new_declare_item + 'begin', print_str, flags=re.IGNORECASE)
        return print_str

    def print_query_except(self, subtree):
        query = []
        new_declare_item = ''
        self.print_partial_visit(subtree, query)
        print_str = " ".join(query).replace(' <EOF>', '').replace('left_bracket', '(').replace('right_bracket',
                                                                                               ')').replace(' (', '(')
        new_variables_list = self.__extract_new_variables(print_str)
        for item in new_variables_list:
            print_str = print_str.replace(item, '')
            declare_item = item.replace('@new&&', '').replace('&&', ' ') + ';'
            if declare_item not in new_declare_item:
                new_declare_item += declare_item
        print_str = re.sub(r'begin', new_declare_item + 'begin', print_str, flags=re.IGNORECASE)
        return print_str

    def print_partial_visit(self, subtree, query):
        if self != subtree:
            if self.__nodeType == 'TerminalNode':
                query.append(self.__content)
            for child in self.__children:
                child.print_partial_visit(subtree, query)

    def print_query_except_two(self, subtree1, subtree2):
        query = []
        new_declare_item = ''
        self.print_partial_visit_two(subtree1, subtree2, query)
        print_str = " ".join(query).replace(' <EOF>', '').replace('left_bracket', '(').replace('right_bracket',
                                                                                               ')').replace(' (', '(')
        new_variables_list = self.__extract_new_variables(print_str)
        for item in new_variables_list:
            print_str = print_str.replace(item, '')
            declare_item = item.replace('@new&&', '').replace('&&', ' ') + ';'
            if declare_item not in new_declare_item:
                new_declare_item += declare_item
        print_str = re.sub(r'begin', new_declare_item + 'begin', print_str, flags=re.IGNORECASE)
        return print_str

    def print_partial_visit_two(self, subtree1, subtree2, query):
        if self != subtree1 and self != subtree2:
            if self.__nodeType == 'TerminalNode':
                query.append(self.__content)
            for child in self.__children:
                child.print_partial_visit_two(subtree1, subtree2, query)

    def gen_reserved_tree(self):
        self.setContent(f'RESERVED_{self.__content}')
        # for child in self.__children:
        #     child.gen_reserved_tree()

    def remove_reserved(self):
        self.setContent(self.__content.replace('RESERVED_', ''))
        for child in self.__children:
            child.remove_reserved()

    def __extract_new_variables(self, input_string: str):
        pattern = r'@new&&[a-zA-Z_][a-zA-Z0-9_&]*'
        matches = re.findall(pattern, input_string)
        return matches

    def isequal(self, node2):
        if self.getContent() == node2.getContent() and self.getNodeType() == node2.getNodeType():
            return True
        else:
            return False

