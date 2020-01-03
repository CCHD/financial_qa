from elasticsearch import Elasticsearch
from datetime import datetime
import json
import re

def create_es_connection():
    es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

    if es.ping():
        print('成功连接到ES服务器')
    else:
        print('请检查ES服务是否打开')
    
    return es

def create_index(es):
    company_info_setting = {
        "settings": {
            "analysis": {
                "normalizer": {
                    "my_normalizer": {
                        "type": "custom",
                        "char_filter": [],
                        "filter": ["lowercase", "asciifolding"]
                        }
                }
            }
        },
        "mappings": {
            "properties": {
                "企业名称": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "法定代表人": {
                    "type": "keyword"
                },
                "纳税人识别号": {
                    "type": "keyword"
                },
                "经营状态": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "统一社会信用代码": {
                    "type": "keyword"
                },
                "组织机构代码": {
                    "type": "keyword"
                },
                "注册号": {
                    "type": "keyword"
                },
                "企业类型": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "所属行业": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "核准日期": {
                    "type": "date",
                    "format": "yyyy-MM-dd"
                },
                "成立日期": {
                    "type": "date",
                    "format": "yyyy-MM-dd"
                },
                "注册资本": {
                    "type": "float"
                },
                "所属地区": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "曾用名": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "人员规模": {
                    "type": "keyword"
                },
                "企业地址": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "经营范围": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "登记机关": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_max_word",
                },
                "英文名": {
                    "type": "keyword",
                    "normalizer": "my_normalizer"
                },
                "参保人数": {
                    "type": "integer"
                },
                "营业期限": {
                    "type": "keyword"
                },
                "实缴资本": {
                    "type": "float"
                }
            }
        }
    }
    financial_event_setting = {
        "settings": {
            "analysis": {
                "normalizer": {
                    "my_normalizer": {
                        "type": "custom",
                        "char_filter": [],
                        "filter": ["lowercase", "asciifolding"]
                        }
                }
            }
        },
        "mappings": {
            "properties": {
                "融资方": {
                    "type": "keyword",
                },
                "投资方": {
                    "type": "keyword",
                },
                "轮次": {
                    "type": "keyword",
                    "normalizer": "my_normalizer"
                },
                "融资时间": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "融资金额": {
                    "type": "keyword"
                }
            }           
        }
    }
    if not es.indices.exists(index='company_info'):
        res = es.indices.create(index='company_info', body=company_info_setting)
        if res['acknowledged']:
            print("成功建立索引companyand_info")
        else:
            print("建立索引失败，请检查ES是否正常！！！")
    else:
        print('索引company_info已存在！')
    if not es.indices.exists(index='financial_event'):
        res = es.indices.create(index='financial_event', body=financial_event_setting)
        if res['acknowledged']:
            print("成功建立索引financial_event")
        else:
            print("建立索引失败，请检查ES是否正常！！！")
    else:
        print('索引financial_event已存在！')

def trans2date(value: str, format: str = None) -> str:
    if value == '未披露':
        return value
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
    return date

def insert_company_info(es, company_info_file):
    count = 1
    with open(company_info_file, 'r', encoding='utf-8') as f:
        all_data = json.load(f, encoding='utf-8')
    data = {}
    for company in all_data:
        data['企业名称'] = company
        for attr in all_data[company]:
            if all_data[company][attr] == '-':
                pass
            else:    
                data[attr] = all_data[company][attr]
        try:
            es.index(index='company_info', id=count, body=data)
            count += 1
            data = {}
        except:
            data = {}
            pass

def insert_financial_event(es, financial_event_file):
    count = 1
    with open(financial_event_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                line = json.loads(line)
                line['融资时间'] = trans2date(line['融资时间'])
                es.index(index='financial_event', id=count, body=line)
                count += 1
            except:
                pass

if __name__ == '__main__':
    es = create_es_connection()
    es.indices.delete(index="company_info", ignore=[400, 404])
    es.indices.delete(index="financial_event", ignore=[400, 404])
    create_index(es)
    insert_financial_event(es, './financial_event.txt')
    insert_company_info(es, './company_info.json')
    # print(es.search(index='company_info', body ={'query': {'bool': {'must': [{'match': {'企业名称': '邦盛科技'}}]}}}))
    # print(es.search(index='financial_event', body={'query': {'bool': {'must': [{'match': {'融资时间': '2019-01-01'}}, {'match': {'融资方': '学堂在线'}}]}}}))