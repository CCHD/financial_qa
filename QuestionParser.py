import re
from extract import entity_extract, attribute_extract, attr_value_extract, financial_factor_extract
from typing import List, Dict, Tuple

class QuestionParser:
    def __init__(self):
        super().__init__()
        self.cmp_dir = {
            "小于":"lt",
            "少于":"lt",
            "低于":"lt",
            "不多于":"lte",
            "不大于":"lte",
            "不超过":"lte",
            "不高于":"lte",
            "超出":"gt",
            "超过":"gt",
            "大于":"gt",
            "多于":"gt",
            "高于":"gt",
            "不少于":"gte",
            "不小于":"gte",
            "不低于":"gte",
        }
    
    def _is_date(self, financial_factor_list: Dict) -> bool:
        if len(financial_factor_list) == 1:
            if '年' in list(financial_factor_list)[0] or '月' in list(financial_factor_list)[0] \
                 or '日' in list(financial_factor_list)[0] or '号' in list(financial_factor_list)[0]:
                return True
        return False

    def _question_classification(self, question: str, entity_list: Dict) -> (bool, Dict):
        financial_factor_list = financial_factor_extract(question, entity_list)
        # financial_factor_list = {}说明没有抽取出投融资事件的关键词，所以是属性问句，而非事件问句
        if not financial_factor_list or (len(financial_factor_list)==1 and self._is_date(financial_factor_list)):
            return (False, None)
        return (True, financial_factor_list)

    def question2sql(self, question: str) -> Tuple:
        question_no_w = re.sub(r'哪里|哪些|什么|哪一个|哪一种|哪类|哪一类|哪个|哪种', '', question.lower())
        entity_list = entity_extract(question=question_no_w)
        attribute_list = attribute_extract(question=question_no_w)
        attribute_list = attr_value_extract(question=question_no_w, attr_list=attribute_list)
        entity_list = self._clear_attribute(entity_list, attribute_list)
        classification = self._question_classification(question=question_no_w, entity_list=entity_list)
        factor_pattern = ""
        for entity in entity_list:
            factor_pattern += entity + '|'
        query_type = None
        query = None
        must_match = []
        msg = "success"
        # 事件问句
        if classification[0]:
            entity_list = self._clear_financial_factor(entity_list, classification[1])
            for factor in classification[1]:
                factor_pattern += factor + '|'
                if '轮' in factor:
                    must_match.append({"match":{"轮次": factor}})
                elif factor not in ['投资', '融资']:
                    must_match.append({"match":{"融资时间": self._trans2date(factor)}})
            factor_pattern = factor_pattern[:-1]
            question_no_factor = re.sub(factor_pattern, '', question.lower())
            if len(entity_list) == 1:
                # [投资方]在[轮次/时间]投资了哪些公司？，[被投资方]在[轮次/时间]被哪些公司投资了？
                if '公司' in question_no_factor or '企业' in question_no_factor:
                    if '被' in question_no_factor:
                        must_match.append({"match":{"融资方":list(entity_list)[0]}})
                        query_type = '投资方列表'
                    else:
                        must_match.append({"match":{"投资方":list(entity_list)[0]}})
                        query_type = '融资方列表'
                # [被投资方]在[轮次/时间]获得融资多少？
                elif '多少' in question_no_factor:
                    must_match.append({"match":{"融资方":list(entity_list)[0]}})
                    query_type = '融资金额'
                # [被投资方]在[时间]进行哪轮融资？
                elif '轮' in question_no_factor:
                    must_match.append({"match":{"融资方":list(entity_list)[0]}})
                    query_type = '轮次'
                # [被投资方]的[轮次]融资发生在什么时间？
                else:
                    must_match.append({"match":{"融资方":list(entity_list)[0]}})
                    query_type = '融资时间'
            else:
                if '被' in question_no_factor:
                    must_match.extend([{"match":{"融资方": list(entity_list)[0]}}, {"match":{"投资方": list(entity_list)[1]}}])
                else:
                    must_match.extend([{"match":{"融资方": list(entity_list)[1]}}, {"match":{"投资方": list(entity_list)[0]}}])
                # [投资方]在哪个轮次投资了[被投资方]？=[被投资方]在哪个轮次被[被投资方]投资了
                if '轮' in question_no_factor:
                    query_type = '轮次'
                # [投资方]在[A轮/时间]投资了[被投资方]多少钱？=[被投资方]在[A轮/时间]被[投资方]投资了多少？
                elif '多少' in question_no_factor:
                    # 无时间或轮次信息
                    if len(must_match) == 2:
                        query_type = '融资金额列表'
                    else:
                        query_type = '融资金额'
                # [投资方]在什么时候投资了[被投资方]？=[被投资方]在什么时候被[被投资方]投资了
                else:
                    query_type = '融资时间'

            query = {"query":{"bool":{"must": must_match}}}
        # 属性问句
        else:
            # [公司]的[法人]是谁
            if len(entity_list) == 1 and not self._has_attr_value(attribute_list):
                query_type = list(attribute_list)
                if len(query_type) == 0:
                    query_type = '企业介绍'
                must_match.append({"match":{"企业名称": list(entity_list)[0]}})
                query = {"query":{"bool":{"must": must_match}}}
            elif len(entity_list) == 0 or self._has_attr_value(attribute_list):
                query_type = '企业列表'
                # 遍历属性名值列表
                find_or_pos = 0
                attribute_should_query = []
                range_query = {'bool': {'must':[]}}
                is_or_find = False
                for attribute in attribute_list:
                    # 这个属性没有对应的查询范围
                    if len(attribute_list[attribute]['adverb']) == 0:
                        msg = "Error: 部分属性对应的查询范围缺失，请检查问句是否完整！！！"
                        return query_type, None, msg
                    else:
                        # 将或者和或替换为x，并不改变问题长度
                        question_no_or = re.sub(r'或者', 'xx', question_no_w)
                        question_no_or = re.sub(r'或', 'x', question_no_or)
                        for adverb in attribute_list[attribute]['adverb']:
                            if adverb['value'] == '没有对应属性值':
                                msg = "Error: 部分属性值缺失，请检查问句是否完整！！！"
                                return query_type, None, msg
                            adverb_value = self._trans2date(adverb['value']) if self._is_date_pattern(adverb['value']) else adverb['value']
                            if not is_or_find:
                                find_or_pos = question_no_or.find('x', find_or_pos)
                            # 找到or或没有or了
                            if find_or_pos > adverb['pos'] or find_or_pos < 0:
                                is_or_find = True
                                if adverb['adverb'] not in self.cmp_dir:
                                    range_query['bool']['must'].append({'match': {attribute: adverb_value}})
                                else:
                                    range_query['bool']['must'].append({'range': {attribute: {self.cmp_dir[adverb['adverb']]: adverb_value}}})
                            else:
                                is_or_find = False
                                find_or_pos += 2
                                attribute_should_query.append(range_query)
                                range_query = {'bool': {'must':[]}}
                                if adverb['adverb'] not in self.cmp_dir:
                                    range_query['bool']['must'].append({'match': {attribute: adverb_value}})
                                else:
                                    range_query['bool']['must'].append({'range': {attribute: {self.cmp_dir[adverb['adverb']]: adverb_value}}})
                attribute_should_query.append(range_query)
                query = {'query':{'bool': {'should':attribute_should_query}}}
        return query_type, query, msg
    
    # 抽取出来的实体可能与属性名或属性值重叠
    def _clear_attribute(self, entity_list: Dict, attribute_list: Dict) -> Dict:
        new_entity_list = {}
        for entity in entity_list:
            is_cover = False
            for attribute in attribute_list:
                if is_cover:
                    break
                if (entity_list[entity][0] >= attribute_list[attribute]['start_index'] and entity_list[entity][0] <= attribute_list[attribute]['end_index'])\
                    or (entity_list[entity][0] <= attribute_list[attribute]['start_index'] and entity_list[entity][1] >= attribute_list[attribute]['start_index']):
                    is_cover = True
                    break
                for adverb in attribute_list[attribute]['adverb']:
                    if (entity_list[entity][0] >= adverb['pos'] and entity_list[entity][0] <= adverb['end_pos'])\
                        or (entity_list[entity][0] <= adverb['pos'] and entity_list[entity][1] >= adverb['end_pos']):
                        is_cover = True
                        break
            if not is_cover:
                new_entity_list[entity] = entity_list[entity]
        return new_entity_list

    # 抽取出来的实体可能与事件元素重叠
    def _clear_financial_factor(self, entity_list: Dict, financial_factor_list: Dict) -> Dict:
        new_entity_list = {}
        for entity in entity_list:
            is_cover = False
            for factor in financial_factor_list:
                if (entity_list[entity][0] >= financial_factor_list[factor][0] and entity_list[entity][0] <= financial_factor_list[factor][1])\
                    or (entity_list[entity][0] <= financial_factor_list[factor][0] and entity_list[entity][1] >= financial_factor_list[factor][0]):
                    is_cover = True
                    break
            if not is_cover:
                new_entity_list[entity] = entity_list[entity]
        return new_entity_list

    def _is_date_pattern(self, date_string: str) -> bool:
        if '年' in date_string or '月' in date_string or '日' in date_string or '号' in date_string:
            return True
        return False
        
    def _trans2date(self, value: str, format: str = None) -> str:
        date = '-'.join(re.split(r'年|月|日|号', value))[:-1]
        if '年' not in value:
            date = '2019-' + date
        if '月' not in value:
            if format == 'M':
                date += '-02'
            else:
                date += '-01'
        if '日' not in value:
            date += '-01'
        
        if format == 'y':
            date = '2020-01-01'
        parts = date.split('-')
        if len(parts[0]) == 2:
            parts[0] = '20' + parts[0]
        if len(parts[1]) == 1:
            parts[1] = '0' + parts[1]
        if len(parts[2]) == 1:
            parts[2] = '0' + parts[2]
        
        date = '-'.join(parts)
        return date
        

    def _has_attr_value(self, attribute_list: Dict) -> bool:
        for attribute in attribute_list:
            if len(attribute_list[attribute]['adverb']):
                return True
        return False

if __name__ == '__main__':
    question = '邦盛科技的简介'
    question_parser = QuestionParser()
    print(question_parser.question2sql(question))