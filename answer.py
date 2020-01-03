from typing import List, Dict
from es_process import create_es_connection
from QuestionParser import QuestionParser
import argparse

class EsAnswer:
    def __init__(self):
        super().__init__()
        self.es = create_es_connection()

    def answer(self, question: str) -> Dict:
        parser = QuestionParser()
        query_type, query, msg = parser.question2sql(question=question)
        if query_type is None:
            return {'status': 'ErrNo[0]: 目前的系统无法回答您所问的问题，请谅解。'}
        elif msg != 'success':
            return {'status': 'ErrNo[0]: '+msg}
        else:
            final_answer = {}
            # 属性问题
            if isinstance(query_type, list) or query_type == '企业列表' or query_type == '企业介绍':
                result = self.es.search(index='company_info', body=query, size=10000)
                if result['hits']['total']['value'] == 0:
                    return {'status': '问题解析成功', 'answer': '系统暂时没有搜索到任何相关知识。'}
                if query_type == '企业列表':
                    final_answer['company_name'] = []
                    final_answer['total_num'] = result['hits']['total']['value']
                    for company in result['hits']['hits']:
                        final_answer['company_name'].append(company['_source']['企业名称'])
                elif query_type == '企业介绍':
                    final_answer['企业介绍'] = result['hits']['hits'][0]['_source']
                    # final_answer['企业介绍'] = []
                    # final_answer['total_num'] = result['hits']['total']['value']
                    # for company in result['hits']['hits']:
                    #     final_answer['企业介绍'].append(company['_source'])
                else:
                    for attribute in query_type:
                        if attribute not in result['hits']['hits'][0]['_source']:
                            final_answer['属性缺失项'] = attribute
                        else:
                            final_answer[attribute] = result['hits']['hits'][0]['_source'][attribute]
            else:
                result = self.es.search(index='financial_event', body=query, size=10000)
                if result['hits']['total']['value'] == 0:
                    return {'status': '问题解析成功', 'answer': '系统暂时没有搜索到任何相关知识。'}
                if query_type == '融资金额列表':
                    final_answer['total_num'] = result['hits']['total']['value']
                    final_answer['financial_event'] = []
                    for event in result['hits']['hits']:
                        final_answer['financial_event'].append(event['_source'])
                elif query_type == '融资方列表' or query_type == '投资方列表':
                    final_answer['total_num'] = result['hits']['total']['value']
                    final_answer[query_type] = []
                    for event in result['hits']['hits']:
                        final_answer[query_type].extend(event['_source'][query_type[:3]])
                else:
                    final_answer[query_type] = result['hits']['hits'][0]['_source'][query_type]
            return {'status': '问题解析成功', 'answer': final_answer}

parser = argparse.ArgumentParser(description='请用中文输入你想问的关于投融资事件或企业信息的问题。')
parser.add_argument('--question', type=str, help='关于投融资事件或企业信息的问题')
args = parser.parse_args()

if __name__ == '__main__':
    question = args.question
    # question = '学堂在线在哪轮被慕华资本投资了'
    Answer = EsAnswer()
    print(Answer.answer(question))