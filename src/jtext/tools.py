import re
import MeCab   # Notice the capitalized M and C
import pandas as pd
from collections import Counter

class JText:
    def __init__(self, text: str) -> None:
        if text.endswith(".csv"):
            self.clean_text, self.wakati = self.parse_annual_csv(text)
        else:
            text += "。" if not text.endswith("。") else  ""
            self.clean_text = self.preprocess_text(text)       # remove whitespace, etc.
            self.wakati = self.parse_text(self.clean_text)              # save parsed words in a list, each list consists of its feature

    def parse_annual_csv(self, text): 
        df = pd.read_csv(text,encoding='utf-16',on_bad_lines='skip', sep = "\t")
        df = df.loc[-df["値"].str.isdigit()]
        df = df.loc[df['要素ID'].str.contains("TextBlock")]
        df = df.drop_duplicates(subset = "項目名")
        raw_text_list = df["値"].to_list()

        clean_text = ""
        wakati = []
        for item in raw_text_list:
            sub_clean_text = self.preprocess_text(item)
            sub_wakati = self.parse_text(sub_clean_text)[1:-2]
            if len(sub_wakati) > 100:
                wakati += sub_wakati
                if sub_clean_text.endswith("。"):
                    clean_text += sub_clean_text
                else:
                    clean_text = clean_text + sub_clean_text + "。"
            else:
                pass

        return clean_text, wakati

    def preprocess_text(self, raw_text):
        clean_text = re.sub(r'\s','',raw_text)     # remove all whitespace characters
        clean_text = re.sub(r'<.*?>','',clean_text)     # remove all HTML or XML-like tags 
        clean_text = re.sub(r"[\r\n]", "", clean_text)  # remove newline characters
        clean_text = re.sub(r"[\u3000 \t \xa0]", " ", clean_text)
        return clean_text
    
    def parse_text(self, clean_text):
        watati = []
        tagger = MeCab.Tagger()
        nodes = tagger.parseToNode(clean_text)           # can not save as self.nodes, do not know why
        while nodes:
            segment = nodes.feature.split(",")
            watati.append(segment)
            nodes = nodes.next
        return watati

    
    def get_length(self):
        length = 0
        for feature in self.wakati:
            if feature[0] not in ["BOS/EOS", "補助記号"]:
                length += 1
            else: 
                pass
        return length
    
    def get_readability(self, print_detail: bool = False):
        word_count = 0
        sent_count = 0
        kan_count = 0
        wa_count = 0
        verb_count = 0
        adverb_count = 0

        for feature in self.wakati:
            if feature[0] not in ["BOS/EOS","補助記号"]:     # remove BOS/EOS, and periods, etc.
                word_count += 1                             # add one to total length
                word_class = feature[0]
                if word_class == "動詞": verb_count += 1        # add one if it is verb
                if word_class == "助詞": adverb_count += 1      # add one if it is adverb
                try:
                    word_origin = feature[12]
                except IndexError:
                    pass
                else:       # proceed only it has features columns of No. 13 (the 12nd in the list)
                    if word_origin == "漢": kan_count += 1          # add one if it is Chinese character
                    if word_origin == "和": wa_count += 1           # add one if it is from wago

            else:
                if feature[0] == "補助記号" and feature[1] == "句点" : 
                    sent_count += 1                     # add the sentence count if there is a period
                else:
                    pass

        sent_count += 1 if sent_count == 0 else 0       # set sentence count as 1 if no periods

        # the ratio is multiplied by 100 here, not sure if it is in line with Li(2016)
        avg_len = word_count/sent_count
        verb_ratio = (verb_count/word_count) * 100 
        adverb_ratio = (adverb_count/word_count)   * 100 
        kan_ratio = (kan_count/word_count)  * 100 
        wa_ratio = (wa_count/word_count)  * 100 
        # Li(2016)
        readability = (-0.056*avg_len) + (-0.126*kan_ratio)+ (-0.042* wa_ratio)+ (-0.145*verb_ratio) + (-0.044*adverb_ratio) + 11.724

        if print_detail == True:
            detail_list = []
            for feature in self.wakati:
                if feature[0] == "BOS/EOS": 
                    pass
                else:
                    if len(feature) >= 8:       # get rid of mainly ['名詞', '数詞', '*', '*', '*', '*'], ['名詞', '普通名詞', '一般', '*', '*', '*'], ['補助記号', '一般', '*', '*', '*', '*'], 
                        sub_detail_turple = (feature[7], feature[6], f"{feature[0]}-{feature[1]}-{feature[2]}-{feature[3]}")
                        detail_list.append(sub_detail_turple)
                    else:
                        pass
            detail_counter = Counter(detail_list)
            for key in detail_counter:
                print(key, detail_counter[key])
            print("\n")
            print(f"Total Sentences: {sent_count}\nTotal Words: {word_count} \nAverage Words per Sentence: {avg_len} \nVerb Count: {verb_count} \nAdverb Count: {adverb_count} \nKan-go Count: {kan_count} \nWa-go Count: {wa_count}")
            print("\n")
            print(f"Formula: - 0.056 * {avg_len} - 0.126 * {kan_ratio} - 0.042 * {wa_ratio} - 0.145 * {verb_ratio} - 0.044 * {adverb_ratio} + 11.724")
            print("\n")
        else:
            pass

        return readability

