from typing import List, Dict
import ahocorasick
import os
import pickle
import re

entity_file = './Entity_File.txt'
attribute_file = './Attribute_File.txt'
attribute_value_file = './Attribute_Value_File.txt'
financial_factor_file = './Financial_Factor.txt'
entity_automation_file = './Entity_Automation.pkl'
attribute_automation_file = './Atrribute_Automation.pkl'
attribute_value_automation_file = './Attribute_Value_Automation.pkl'
financial_factor_automation_file = './Financial_Factor_Automation.pkl'

def build_entity_automation(entity_file: str, entity_automation_file: str):
    entity_automation = ahocorasick.Automaton()
    with open(entity_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lower()
            entity_automation.add_word(line, line)
    entity_automation.make_automaton()
    with open(entity_automation_file, 'wb') as f:
        pickle.dump(entity_automation, f)

def entity_extract(question: str) -> Dict:
    # question_no_w = re.sub(r'哪里|哪些|什么|哪一个|哪一种|哪类|哪一类|哪个|哪种', '', question.lower())
    # 加载实体名AC自动机
    if not os.path.exists(entity_automation_file):
        build_entity_automation(entity_file, entity_automation_file)
    with open(entity_automation_file, 'rb') as f:
        entity_automation = pickle.load(f)
    entity_info = []
    entity_name = []
    for end_index, entity in entity_automation.iter(question):
        if entity not in entity_name:
            entity_name.append(entity)
            entity_info.append({'start_index': end_index - len(entity) + 1, 'end_index': end_index, 'entity': entity})
    # 去掉包含关系的实体名
    entity_info.sort(key=lambda entity:len(entity['entity']))
    for i in range(0, len(entity_info)-1):
        for j in range(i+1, len(entity_info)):
            if entity_info[i]['start_index'] < entity_info[j]['start_index']:
                continue
            if entity_info[i]['end_index'] <= entity_info[j]['end_index']:
                entity_name.remove(entity_info[i]['entity'])
                break

    # entity_list返回的内容包含实体名entity、起始位置start_index、结束位置end_index,
    # 以Dict存储，entity为key，(start_index, end_index)为value
    entity_list = {}
    new_list = {}
    for entity in entity_info:
        if entity['entity'] not in entity_name:
            continue
        new_list[entity['entity']] = (entity['start_index'], entity['end_index'])
    for k in sorted(new_list.items(),key = lambda x:x[1][0]):
        entity_list[k[0]] = k[1]
    del entity_info
    del entity_name
    del new_list
    return entity_list

def build_atrribute_automation(attribute_file: str, attribute_automation_file: str):
    attribute_automation = ahocorasick.Automaton()
    with open(attribute_file, 'r', encoding='utf-8') as f:
        for line in f:
            attributes = line.strip().lower().split(' ')
            for attribute in attributes:
                attribute_automation.add_word(attribute, (attribute, attributes[0]))
    attribute_automation.make_automaton()
    with open(attribute_automation_file, 'wb') as f:
        pickle.dump(attribute_automation, f)

def attribute_extract(question: str) -> Dict:
    # 加载属性名AC自动机
    if not os.path.exists(attribute_automation_file):
        build_atrribute_automation(attribute_file, attribute_automation_file)
    with open(attribute_automation_file, 'rb') as f:
        attribute_automation = pickle.load(f)
    # 将问题去掉如哪里、什么、哪个这些问题词
    # 如question: 阿里巴巴所属哪个行业
    # question_no_w = re.sub(r'哪里|哪些|什么|哪一个|哪一种|哪类|哪一类|哪个|哪种', '', question.lower())
    # attribute_list返回的内容包含属性名attribute、起始位置start_index、结束位置end_index,
    # 以Dict存储，attribute为key，{start_index, end_index}为value
    attribute_list = {}
    for end_index, (attribute_alias, attribute) in attribute_automation.iter(question):
        if attribute not in attribute_list.keys():
            attribute_list[attribute] = {'start_index': end_index - len(attribute_alias) + 1, 'end_index': end_index, 'adverb': []}
    return attribute_list

def build_atrribute_value_automation(attribute_value_file: str, attribute_value_automation_file: str):
    attribute_value_automation = ahocorasick.Automaton()
    with open(attribute_value_file, 'r', encoding='utf-8') as f:
        for line in f:
            value = line.strip()
            attribute_value_automation.add_word(value, value)
    attribute_value_automation.make_automaton()
    with open(attribute_value_automation_file, 'wb') as f:
        pickle.dump(attribute_value_automation, f)

# 假设每个属性都有对应的属性值
def attr_value_extract(question: str, attr_list: Dict) -> Dict:
    if not os.path.exists(attribute_value_automation_file):
        build_atrribute_value_automation(attribute_value_file, attribute_value_automation_file)
    with open(attribute_value_automation_file, 'rb') as f:
        attribute_value_automation = pickle.load(f)
    # question_no_w = re.sub(r'哪里|哪些|什么|哪一个|哪一种|哪类|哪一类|哪个|哪种', '', question.lower())
    adverb_pattern = re.compile(r'超出|超过|大于|小于|等于|少于|不少于|不多于|不大于|不小于|不超过|低于|不低于|多于|在|为|不高于|高于')
    result = adverb_pattern.findall(question)
    attribute_name_list = list(attr_list)
    search_adverb_pos = 0
    for adverb in result:
        pos = question.find(adverb, search_adverb_pos)
        search_adverb_pos = pos + 1
        use_automation = False
        is_money = False
        for i in range(len(attribute_name_list)):
            if pos > attr_list[attribute_name_list[i]]['end_index']:
                if i == len(attribute_name_list) - 1 or pos < attr_list[attribute_name_list[i+1]]['start_index']:
                    if attribute_name_list[i] in ['核准日期', '成立日期']:
                        value_pattern = re.compile(r'((\d{2,4}年){1}(\d{1,2}月){0,1}(\d{1,2}[日号]){0,1})')
                    elif attribute_name_list[i] in ['注册资本', '实缴资本']:
                        value_pattern = re.compile(r'((\d+)万(人民币){0,1})')
                        is_money = True
                    else:
                        use_automation = True
                    endpos = attr_list[attribute_name_list[i+1]]['start_index'] if i < len(attribute_name_list) - 1 else len(question)
                    value = "没有对应属性值"
                    if use_automation:
                        for (endindex, match) in attribute_value_automation.iter(question, pos, endpos):
                            if value == "没有对应属性值":
                                value = match
                            elif len(match) > len(value):
                                value = match
                    else:
                        value_list = value_pattern.findall(question, pos, endpos)
                        if len(value_list):
                            if not is_money:
                                value = value_list[0][0]
                            else:
                                value = value_list[0][1]
                    attr_list[attribute_name_list[i]]['adverb'].append({'adverb': adverb, 'pos': pos, 'end_pos':pos+len(adverb)-1, 'value': value})
    return attr_list

def build_financial_factor_automation(financial_factor_file: str, financial_factor_automation_file: str):
    financial_factor_automation = ahocorasick.Automaton()
    with open(financial_factor_file, 'r', encoding='utf-8') as f:
        for line in f:
            value = line.strip()
            financial_factor_automation.add_word(value, value)
    financial_factor_automation.make_automaton()
    with open(financial_factor_automation_file, 'wb') as f:
        pickle.dump(financial_factor_automation, f)

def financial_factor_extract(question: str, entity_list: Dict) -> Dict:
    if not os.path.exists(financial_factor_automation_file):
        build_financial_factor_automation(financial_factor_file, financial_factor_automation_file)
    with open(financial_factor_automation_file, 'rb') as f:
        financial_factor_automation = pickle.load(f)

    # question_no_w = re.sub(r'哪里|哪些|什么|哪一个|哪一种|哪类|哪一类|哪个|哪种', '', question.lower())
    financial_factor_list = {}
    time_pattern = re.compile(r'((\d{2,4}年){1}(\d{1,2}月){0,1}(\d{1,2}[日号]){0,1})')
    time_value = time_pattern.findall(question)
    if len(time_value):
        financial_factor_list[time_value[0][0]] = (question.find(time_value[0][0]), question.find(time_value[0][0])+len(time_value[0][0])-1)
    for end_index, value in financial_factor_automation.iter(question):
        entity_contains = False
        for entity in entity_list:
            if end_index >= entity_list[entity][0] and end_index <= entity_list[entity][1]:
                entity_contains = True
                break
        if entity_contains:
            continue
        financial_factor_list[value] = (end_index - len(value) + 1, end_index)
    return financial_factor_list

if __name__ == '__main__':
    question = '浙江邦盛科技有限公司的法人是谁'.lower()
    print(entity_extract(question))