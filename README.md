# 基于投融资事件的问答系统
基于规则的关于企业信息和投融资事件的问答系统，由于时间原因，没有实现算法抽取，都是用的AC自动机，所以对于部分问题会出bug

## 使用要求
### 安装
    pyahocorasick: v1.4.0
    elasticsearch: v7.1.0
    Elastic Search: v7.5.1
    ik-analyzer: v7.5.1

### 运行
    cd financial_qa
    python answer.py --question=问题
