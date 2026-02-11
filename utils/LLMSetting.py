class LLMSetting:
    def __init__(self, api, model, temp, top_P, max_tokens, sys_prompt):
        self.__api = api
        self.__model = model
        self.__temp = temp
        self.__top_P = top_P
        self.__max_tokens = max_tokens
        self.__sys_prompt = sys_prompt

    def getApi(self):
        return self.__api

    def getModel(self):
        return self.__model

    def getTemp(self):
        return self.__temp

    def getTop_P(self):
        return self.__top_P

    def getMax_tokens(self):
        return self.__max_tokens

    def getSys_prompt(self):
        return self.__sys_prompt
