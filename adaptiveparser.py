from antlr4 import *
from antlr4.error.ErrorStrategy import DefaultErrorStrategy

from utils.antlr.MyErrorListener import MyErrorListener
from utils.antlr.PostgreSQLLexer import PostgreSQLLexer
from utils.antlr.PostgreSQLParser import PostgreSQLParser
from utils.astoperation import *

def parse_sql_by_pg(sql: str):
    input_stream = InputStream(sql)
    lexer = PostgreSQLLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = PostgreSQLParser(stream)
    tree = parser.root()
    mytree = copy_tree(tree)
    return mytree

def compile_sql_by_pg(sql: str):
    input_stream = InputStream(sql)
    lexer = PostgreSQLLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = PostgreSQLParser(stream)
    parser.removeErrorListeners()
    myerrorlistener = MyErrorListener()
    parser.addErrorListener(myerrorlistener)
    parser._errHandler = DefaultErrorStrategy()
    parser.root()

    if myerrorlistener.getErrors():
        errmsg = "SQL syntax error: "
        for error in myerrorlistener.getErrors():
            errmsg += error
        return False, errmsg

    else:
        return True, None
