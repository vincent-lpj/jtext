import re
import MeCab        # Notice the capitalized M and C
import pandas as pd
from collections import Counter
import requests
import os
import json
# note unidic should be installed before use

class JText:
    def __init__(self, text: str) -> None:
        """Create an instance of JText class.
        """
        if text.endswith(".csv"):
            self.sections, self.clean_text, self.wakati = self.parse_annual_csv(text)
        else:
            text += "。" if not text.endswith("。") else  ""            # add a period if there is no period at the end
            self.sections = None
            self.clean_text = self.preprocess_text(text)                # remove whitespace, etc.
            self.wakati = self.parse_text(self.clean_text)              # save parsed words in a list, each list consists of its feature

    def parse_annual_csv(self, text) -> tuple[list,str,list]: 
        """Parse annual report in csv format. 
        """
        df = pd.read_csv(text,encoding='utf-16',on_bad_lines='skip', sep = "\t")
        df = df.loc[-df["値"].str.isdigit()]
        df = df.loc[df['要素ID'].str.contains("TextBlock")]
        df = df.drop_duplicates(subset = "項目名")
        raw_text_list = df["値"].to_list()

        sections = []
        clean_text = ""
        wakati = []
        for item in raw_text_list:
            sub_clean_text = self.preprocess_text(item)
            sub_wakati = self.parse_text(sub_clean_text)[1:-2]          # slice the list by [1:-2] to get rid of BOS/EOS
            if len(sub_wakati) > 100:                                   # include only textblock that exceeds 100 words
                wakati += sub_wakati
                # add period to each textblock 
                if sub_clean_text.endswith("。"):
                    clean_text += sub_clean_text
                    sections.append(sub_clean_text)
                else:
                    clean_text = clean_text + sub_clean_text + "。"
                    sections.append(sub_clean_text + "。")
            else:
                pass

        return sections, clean_text, wakati                             # return list(of textblocks), str, list(of words features)

    def preprocess_text(self, raw_text) -> str:
        clean_text = re.sub(r'\s','',raw_text)                          # remove all whitespace characters
        clean_text = re.sub(r'<.*?>','',clean_text)                     # remove all HTML or XML-like tags 
        clean_text = re.sub(r"[\r\n]", "", clean_text)                  # remove newline characters
        clean_text = re.sub(r"[\u3000 \t \xa0]", " ", clean_text)
        return clean_text                                               # return str
    
    @staticmethod
    def parse_text(clean_text) -> list:
        wakati = []
        tagger = MeCab.Tagger()
        nodes = tagger.parseToNode(clean_text)                          # can not save as self.nodes, do not know why
        while nodes:
            segment = nodes.feature.split(",")                          # segment is list of word features
            wakati.append(segment)
            nodes = nodes.next
        return wakati

    
    def get_length(self) -> int:
        length = 0
        for feature in self.wakati:
            # count with conditions, the first (index 0) element in the feature list is the target. see pos1 in https://pypi.org/project/unidic/
            if feature[0] not in ["BOS/EOS", "補助記号"]:               
                length += 1
            else: 
                pass
        return length                                                   # return interger
    
    def get_readability(self, print_detail: bool = False) -> float:
        """This follows the formula in Li(2006):
         readability = number of words per sentence * -0.056 + proportion of kango * -0.126 + proportion of wago * -0.042 + proportion of verbs * -0.145 + proportion of auxiliaries * -0.044 + 11.724
        """
        word_count = 0
        sent_count = 0
        kan_count = 0
        wa_count = 0
        verb_count = 0
        adverb_count = 0

        for feature in self.wakati:
            if feature[0] not in ["BOS/EOS","補助記号"]:                # remove BOS/EOS, and periods, etc.
                word_count += 1                                         # add one to total length
                word_class = feature[0]
                if word_class == "動詞": verb_count += 1                # add one if it is verb
                if word_class == "助詞": adverb_count += 1              # add one if it is adverb
                try:
                    word_origin = feature[12]
                except IndexError:
                    pass
                else:                                                   # proceed only it has features columns of No. 13 (the 12nd in the list)
                    if word_origin == "漢": kan_count += 1              # add one if it is Chinese character(kango)
                    if word_origin == "和": wa_count += 1               # add one if it is from wago

            else:
                if feature[0] == "補助記号" and feature[1] == "句点" : 
                    sent_count += 1                                     # add the sentence count if there is a period
                else:
                    pass

        sent_count += 1 if sent_count == 0 else 0                       # set sentence count as 1 if no periods

        # the ratio is multiplied by 100 here, not sure if it is in line with Li(2016)
        avg_len = word_count/sent_count
        verb_ratio = (verb_count/word_count) * 100 
        adverb_ratio = (adverb_count/word_count)   * 100 
        kan_ratio = (kan_count/word_count)  * 100 
        wa_ratio = (wa_count/word_count)  * 100 
        # Li(2016)
        readability = (-0.056*avg_len) + (-0.126*kan_ratio)+ (-0.042* wa_ratio)+ (-0.145*verb_ratio) + (-0.044*adverb_ratio) + 11.724

        # Show details if needed 
        if print_detail == True:
            detail_list = []
            for feature in self.wakati:
                if feature[0] == "BOS/EOS": 
                    pass
                else:
                    if len(feature) >= 8:                               # get rid of mainly ['名詞', '数詞', '*', '*', '*', '*'], ['名詞', '普通名詞', '一般', '*', '*', '*'], ['補助記号', '一般', '*', '*', '*', '*'], 
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
    
    def get_ngram(self, words_per_phrase:int = 8) -> list[str]:
        n_gram_list = []
        wakati_list = self.wakati[1:-1]
        for k in range(len(wakati_list)):
            if len(wakati_list[k]) < 9 or wakati_list[k][0] == "補助記号":
                pass
            else:
                phrase = ""
                for i in range(words_per_phrase):
                    try:
                        phrase += wakati_list[k+i][8]                # the 9th (index 8) element of a feature list contains orth:  the word as it appears in text, this appears to be identical to the surface.
                    except IndexError:
                        phrase = ""
                        break
                    except:
                        pass
                    else:
                        pass
                if phrase != "":
                    n_gram_list.append(phrase)
                else:
                    pass
        return n_gram_list

    def get_redundancy(self, words_per_pharse: int = 8, print_detail: bool = False, detail_section: int = 0) -> float:
        tagger = MeCab.Tagger()
        n_gram = []
        count = 0
        # loop textblocks saved in self.sections and get word features lists
        if self.sections == None:
            return 0
        else:
            pass
        
        for section in self.sections:
            count += 1
            sub_wakati = []
            nodes = tagger.parseToNode(section)                         # can not save as self.nodes, do not know why
            while nodes:
                segment = nodes.feature.split(",")
                sub_wakati.append(segment)
                nodes = nodes.next
            sub_wakati = sub_wakati[1:-2]

            sub_n_gram_list = []
            for k in range(len(sub_wakati) - words_per_pharse + 1):
                if len(sub_wakati[k]) < 9:
                    pass
                else:
                    phrase = ""
                    for i in range(words_per_pharse):
                        try:
                            phrase += sub_wakati[k+i][8]                # the 9th (index 8) element of a feature list contains orth:  the word as it appears in text, this appears to be identical to the surface.
                        except IndexError:
                            phrase = ""
                            break
                        except:
                            pass
                        else:
                            pass
                    if phrase != "":
                        sub_n_gram_list.append(phrase)

            sub_n_gram = Counter(sub_n_gram_list)
            n_gram.append(sub_n_gram)

            if print_detail == True:
                if detail_section == count:
                    print("\n")
                    print(f"The original text: \n{section}")
                    print("\n")
                    print(f"{words_per_pharse}-gram phrases list: \n{sub_n_gram_list}")
                    print("\n")
                    print(f"The unique {words_per_pharse}-gram phrases are: \n{sub_n_gram}")
            else:
                pass
        
        common_n_gram = Counter()

        for sub_n_gram in n_gram:
            common_n_gram.update(sub_n_gram)
            total_n_gram = common_n_gram.total()

        for sub_n_gram in n_gram:
            for key in sub_n_gram.keys():
                if key in common_n_gram and common_n_gram[key] ==  sub_n_gram[key]:
                    common_n_gram.pop(key)
            redundant_n_gram = common_n_gram.total()
        if print_detail == True:
            print("\n")
            print(f"The redundant count is as follows: \n{common_n_gram}")

        redundant_ratio = redundant_n_gram/total_n_gram

        return redundant_ratio

    @staticmethod
    def download_ner(download: bool = True) -> list[str]:
        ner_url = "https://raw.githubusercontent.com/stockmarkteam/ner-wikipedia-dataset/refs/heads/main/ner.json"
        cdir = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(cdir, 'ner.json')
        if os.path.exists(fname):
            with open (fname,"r", encoding = "utf-16") as f:
                data = json.load(f)
        else:
            try:
                # Download the JSON file
                response = requests.get(ner_url)
                response.raise_for_status()  # Check for errors in the request

                # Load the JSON data
                data = response.json()
            except:
                data = dict()
            else:
                if response.status_code == 200 and download == True:
                    with open(fname, "w", encoding = "utf-16") as f:
                        json.dump(data,f)
                else:
                    pass
            
        # Extract all "name" fields from "entities"
        entities_list = []
        for item in data:
            for entity in item.get("entities", []):
                entities_list.append(entity["name"])
                
        return entities_list
        

    def get_specificity(self, entities_list: list[str] = None) -> float:
        if entities_list == None:
            entities_list = self.download_ner()
        else:
            pass
            
        ner_dict = {}
        for entity in entities_list:
            count = 0
            start = 0
            while True:
                start = self.clean_text.find(entity, start)
                if start == -1:
                    break
                else:
                    pass
                count += 1
                start += 1
            if count > 0:
                ner_dict[entity] = count
            else:
                pass
        
        # drop sub-phrases, such as "京" in "東京都千代田区"
        sorted_keys = sorted(list(ner_dict.keys()), key = len, reverse = True)
        filered_keys = []
        for key in sorted_keys:
            if not any(key in longer_word for longer_word in filered_keys):
                filered_keys.append(key)
        for key in list(ner_dict.keys()):
            if key not in filered_keys:
                del ner_dict[key]

        # calculate specificity ratio
        specificity = 0
        try:
            for key in ner_dict.keys():
                specificity += len(key) * ner_dict[key]             
        except:
            pass
        finally:
            length = len(self.clean_text)                                   # use simple text length, instead of wakati numbers
            specific_ratio = specificity/length

        return specific_ratio
   