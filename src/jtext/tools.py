import re
import MeCab   # Notice the capitalized M and C

class Jtext:
    def __init__(self, text: str) -> None:
        self.raw_text = text
        self.text = self.clean_text()

    def clean_text(self):
        clean_text = re.sub(r'\s','',self.raw_text)         # remove all whitespace characters
        clean_text = re.sub(r'<.*?>','',clean_text)         # remove all HTML or XML-like tags 
        clean_text = re.sub(r"[\r\n]", "", clean_text)      # remove newline characters
        clean_text = re.sub(r"[\u3000 \t \xa0]", " ", clean_text)
        return clean_text
    
    def get_length(self):
        length = 0
        tagger = MeCab.Tagger()
        nodes = tagger.parseToNode(self.text)               # can not save as self.nodes, do not know why
        while nodes:
            feature = nodes.feature.split(",")
            if feature[0] not in ["BOS/EOS", '補助記号']:
                length += 1
            else: 
                pass
            nodes = nodes.next              # Do not forget to add this line
        return length

