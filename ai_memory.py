from utility import StringUtility, PrintColor


class AiMemory:
    MAX_HISTORY_LENGTH = 3000

    def __init__(self):
        # could've just use string and split by \n but will break if \n is in the text
        self.history = dict[int, list[str]]()

    def add_history(self, text: str, role, conversation_id) -> str:
        if conversation_id not in self.history:
            self.history[conversation_id] = []
        self.history[conversation_id].append(f'{role}: {text}')

        # remove old messages
        len = StringUtility.WordCount(text)
        over_max = False
        for i, text in reversed(list(enumerate(self.history[conversation_id]))):
            if over_max:
                self.history[conversation_id].pop(i)
            else:
                len += StringUtility.WordCount(text)
                if len > self.MAX_HISTORY_LENGTH:
                    over_max = True
                    self.history[conversation_id].pop(i)

        print(
            f'{PrintColor.OKBLUE}history: {self.history[conversation_id]}{PrintColor.ENDC}')
        return '\n'.join(self.history[conversation_id])

    def remove_history(self, conversation_id):
        if conversation_id in self.history:
            self.history.pop(conversation_id)
