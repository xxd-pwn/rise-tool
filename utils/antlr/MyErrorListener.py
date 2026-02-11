from antlr4.error.ErrorListener import ErrorListener

class MyErrorListener(ErrorListener):
    def __init__(self):
        super(MyErrorListener, self).__init__()
        self.errors = []
        self.first_error_pos = -1

    def getErrors(self):
        return self.errors

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        error_msg = f"Syntax error at line {line}, column {column}: {msg}"
        # print(error_msg)
        self.errors.append(error_msg)
        if offendingSymbol and self.first_error_pos == -1:
            self.first_error_pos = offendingSymbol.start
