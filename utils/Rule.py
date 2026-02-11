class Rule:
    def __init__(self, source_pattern, target_pattern):
        self.__source_pattern = source_pattern
        self.__target_pattern = target_pattern

    def get_source_pattern(self):
        return self.__source_pattern

    def get_target_pattern(self):
        return self.__target_pattern