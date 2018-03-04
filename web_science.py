from urllib import parse
import os
import nltk
import re
import gender_guesser.detector as gender
from datetime import date
import datetime
import calendar as cal


dg = {"female": "she her", "male": "he his", "unknown":"he she his her", "mostly_male": "he his", "mostly_female": "she her", "andy": "he she his her"}
gg = {"female": "she", "male": "he", "unknown":"", "mostly_male": "he", "mostly_female": "she", "andy": "he she"}

genders = {}
genders_person = {}


def get_dict_of_entities():
    entities = {}
    g = gender.Detector()

    with open('./TD/entity_list.txt') as f:
        for line in f:
           tmp = parse.urlparse(line).path.split('/')[-1].strip().replace('_',' ')
           try:
               ind = tmp.index("(")
               tmp = tmp[:ind]
           except:
               pass
           entities[tmp] = line.strip()
           genders[tmp] = dg[g.get_gender(tmp.split()[0])]
           genders_person[tmp] = gg[g.get_gender(tmp.split()[0])]
   
    return entities


def check_if_available(text, entity):
    text = re.sub(r'[^\w\s]', '', text)
    spl = set(text.split())
    ent = set(entity.split())
    gend = set(genders[entity].split() + [x.title() for x in genders[entity].split()])
    if spl.intersection(ent) == ent or spl.intersection(gend) != set():
            return True
    return False


def check_if_valid(text, entity):
    text = re.sub(r'[^\w\s]', '', text)
    spl = set(text.split()[:20])
    ent = set(entity.split())
    if spl.intersection(ent) == ent:
            return True
    return False
 

class Annotator:
    def __init__(self, path='./TD/Wikipedia_corpus'):
        self.path = path
        self.entities = get_dict_of_entities()
        self.knowledge = []

    def get_list_of_files(self):
        return os.listdir(self.path)


    def annotate(self, file_name):
        with open('./TD/Annotations/' + file_name.replace('.txt','_ant.txt'), 'w') as fw:
            with open(self.path + '/' + file_name) as fr:
                text = fr.read()
                for item in self.entities:
                    if check_if_valid(text, item): 
                        self.knowledge.append(self.extract_birth_day(text, item))
                        self.knowledge.append(self.extract_type(text, item))
                        self.knowledge.append(self.extract_pattern(text, item))
                        self.knowledge.append(self.extract_marriage(text, item))
                        self.knowledge.append(self.extract_pattern(text, item, pattern="appeared in"))

                        tmp = item.split(' ')
                        name = tmp[0].strip()
                        g = gender.Detector()
                        pronouns = genders_person[item].split() 
                        pros = pronouns + [x.title() for x in pronouns]
                        regex = "(" + item + "|" + tmp[-1].strip() + "| " + " |".join(pros)  + " )"
                        text = re.sub(regex, r'<entity name="'+self.entities[item]+'">\\1</entity>', text)
            fw.write(text)

    def annotate_files(self):
        files = self.get_list_of_files()
        for f in files:
            self.annotate(f)
        with open("knowledge.xml","w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<data>')
            f.write('\n'.join(list(filter(lambda x: x != "", self.knowledge))))
            f.write("</data>")

    def extract_birth_day(self, text, entity):

        regex = r"(?P<person>(?:[A-Z][a-z]+\s){2})(?:.){0,60}?(?:\(?born )?(?:\(?born (?P<year>\d\d\d\d)\)?|(?:(?P<day_base>\d\d?) (?P<month_base>[A-Z][a-z]*) (?P<year_base>\d\d\d\d)\)?))"
        extract = ""
        tmp = re.findall(regex, text)
        if tmp:
            year = 1000
            month = 1
            day = 1
            if tmp[0][1] != "":
                year = int(tmp[0][1])
                dat = date(year, month, day).strftime("%Y") 
    
            else:
                year = int(tmp[0][4])
                day = int(tmp[0][2])
                month = list(cal.month_name).index(tmp[0][3])
                dat = date(year, month, day).strftime("%Y-%m-%d") 
    
            print(dat)
            extract = '<entity link="' + self.entities[entity] + '" hasDate= "' + dat + '"/>'
        return extract

    def extract_type(self, text, entity):
        det = ""
        regex = r"(.*?)(?:is|are|was|were) (?:a|the|an) (.*)"
        tmp = re.findall(regex, text)
        for i in tmp:
            if check_if_valid(i[0], entity):
                words = nltk.word_tokenize(i[1])
                tokens = nltk.pos_tag(words)
                detected_type = entity.title()
                for tok in tokens:
                    if "NN" in tok[1]:
                        det += " " + tok[0]
                    elif "JJ" in tok[1]:
                        det += " " + tok[0]
                    elif "VBG" in tok[1]:
                        det += " " + tok[0]
                    elif "," in tok[1]:                        
                        det += "" 
                    elif "CC" in tok[1]:
                         det += ""  
                    else:
                        break
                detected_type += " is " + det
                print(detected_type)
            break
        extract = '<entity link="' + self.entities[entity] + '" type="' + det + '"/>'
        return extract

    def extract_pattern(self, text, entity, pattern="painted"):
        det = ""
        extract = ""
        regex = r"(.*?)(?:" + pattern + ") (.*)"
        tmp = re.findall(regex, text)
        for i in tmp:
            if check_if_available(i[0], entity): 
                words = nltk.word_tokenize(i[1])
                tokens = nltk.pos_tag(words)
                detected_type = entity.title()
                for tok in tokens:
                    if "NN" in tok[1]:
                        det += " " + tok[0]
                    elif "JJ" in tok[1]:
                        det += " " + tok[0]
                    elif "VBG" in tok[1]:
                        det += " " + tok[0]
                    elif "," in tok[1]:                        
                        det += "" 
                    elif "CC" in tok[1]:
                         det += ""  
                    elif "DT" in tok[1]:
                         det += ""  
                    else:
                        break
                if det != "":
                    detected_type += " " + pattern + " " + det
                    print(detected_type)
                    if det in self.entities:
                        extract = '<entity link="' + self.entities[entity] + '" ' + "_".join(pattern.lower().split()) + '= "' + self.entities[det] + '"/>'
                    else:
                        extract = '<entity link="' + self.entities[entity] + '" ' + "_".join(pattern.lower().split()) + '="' + det + '"/>'

        return extract

    def extract_marriage(self, text, entity):
        det = ""
        extract = ""
        regex = r"(.*?)(?: is|are|was|were|(?:has been))? (?:married|marriage to) (.*)"
        tmp = re.findall(regex, text)
        for i in tmp:
            if check_if_available(i[0], entity): 
                words = nltk.word_tokenize(i[1])
                tokens = nltk.pos_tag(words)
                detected_type = entity.title()
                
                for tok in tokens:
                    if "NN" in tok[1]:
                        det += " " + tok[0]
                    elif "JJ" in tok[1]:
                        det += " " + tok[0]
                    elif "VBG" in tok[1]:
                        det += " " + tok[0]
                    elif "," in tok[1]:                        
                        det += "" 
                    elif "CC" in tok[1]:
                         det += ""  
                    else:
                        break
                if det != "":
                    detected_type += " is/was married to " + det
                    print(detected_type)
                    if det in self.entities:
                        extract = '<entity link="' + self.entities[entity] + '" ' + "married_to" + '="' + self.entities[det] + '"/>'
                    else:
                        extract = '<entity link="' + self.entities[entity] + '" ' + "married_to" + '="' + det + '"/>'

            break

        return extract


ant = Annotator()
ant.annotate_files()
