# 问答系统
## 1 系统概述
        根据构建出来的知识图谱，其包括企业信息与企业投融资事件信息，通过分析一般用户可能会询问问句，将问句根据特征进行简单的语义分析，实现关于企业投融资的问答系统。
## 2 使用工具
Elastic Search: v7.5.1  
ik分词工具: v7.5.1，安装过程请详见[ik分析器github地址](https://github.com/medcl/elasticsearch-analysis-ik)  
python: v3.7.5  
python主要使用的第三方软件库：  
pyahocorasick: v1.4.0  
elasticsearch: v7.
## 3 系统实现流程
        首先对问题进行分类，主要通过判断问句中是否出现关于投融资事件元素，简单分为投融资事件问句与企业信息问句。比较典型的投融资事件元素如轮次信息，如A轮、天使轮等。
        然后对问句抽取企业实体，根据实体个数进行进一步的语义分析。语义解析过程如下图。
![问答系统语义解析.png](https://i.loli.net/2020/01/02/cxL7bGHSTfZIu4r.png)  
***
        如上图所示，分为事件问句（投融资事件）与属性问句（企业信息问句）后，根据实体个数，分析出问题意图。
* #### 对于事件问句  
        如果有两个实体，则认为这两个实体分别为投资方和被投资方（即融资方），则在这种情况下，问句的询问意图可能有投资金额、投资时间、投资轮次。
        如果只有一个实体，需要先判断出是投资方还是被投资方。通过将问句中所有抽取出来的实体信息、投融资事件元素删去后，观察是否出现'被'或'融资'来判断抽取出来的实体是否为被投资方，否则为投资方。之后根据删减过后的问句中出现的意图词，如'多少'代表投资金额，'什么'代表投资时间，'轮'代表投资轮次，来决定查询内容。
* #### 对于属性问句  
    * **没有实体**  
        &emsp;&emsp;在本问答系统中我们认为则是询问所有企业属性符合条件的企业。 需要抽取出询问的属性与对应属性值，以及比较符（包括大于、小于、不超过等等）。  
        &emsp;&emsp;由于问题中的属性条件可能比较复杂，会出现或、且等关系，因此对抽取出来的结果进行'或'的语义分析，将复杂的属性比较条件分解为由'或'断开的多个或条件比较语句组合而成的查询语句。
    * **只有一个实体**  
        &emsp;&emsp;只有一个实体我们认为是询问关于这个企业实体的属性信息。考虑到用户可能只输入公司从而希望得到该公司的信息，所以将询问公司属性信息的情况也分为两种可能，即是否抽取到想要询问的属性名。  
        * 没有抽取到属性名  
        &emsp;&emsp;这种情况属于输入一个公司名，希望获得该公司所有属性信息。
        * 抽取到属性名  
        &emsp;&emsp;将输出所有询问的该公司的属性对应属性值。
## 4 系统使用
* ### 如何使用问答系统  
1. 进入问答系统项目目录
```shell
cd 项目目录financial_qa/
```
2. 启动Elastic Search服务
```shell
进入Elastic Search安装目录后
Windows系统下运行：.\bin\elasticsearch.bat
Mac/Linux系统下运行: ./bin/elasticsearch
```
3. 向ElasticSearch中导入数据
```python
python es_process.py
```
4. 运行问答系统
```python
python answer.py --question=问题
```

## 5 使用示例
1. 询问公司
```python
python answer.py --question=阿里巴巴  
```
### 输出:  
> 成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'企业介绍': {'企业名称': '阿里体育有限公司', '法定代表人': '戴玮', '注册资本': 26143.7909, '经营状态': '存续（在营、开业、在册）', '成立日期': '2015-09-08', '统一社会信用代码': '913101103507613521', '纳税人识别号': '913101103507613521', '注册号': '310110000763636', '组织机构代码': '35076135-2', 
'企业类型': '有限责任公司(自然人投资或控股)', '所属行业': '文化、体育和娱乐业', '核准日期': '2015-09-08', '登记机关': '杨浦区市场监管局', '所属地区': '上海市', '曾用名
': '阿里体育（上海）有限公司\xa0\xa0', '参保人数': 157, '人员规模': '100-499人', '营业期限': '2015-09-08 至 无固定期限', '企业地址': '上海市杨浦区军工路1436号64幢一层J181室\n                 查看地图  附近企业', '经营范围': '计算机硬件、网络技术领域内的技术开发、技术服务、技术转让、技术咨询,体育产业开发,体育赛事、电子竞技的组织、策 
划,体育场馆开发与运营,知识产权服务,多媒体制作,电子商务(不得从事增值电信、金融业务),演出经纪,文化经纪,体育经纪,计算机软件的设计、开发和制作、销售,商务信息咨询,企业营销 
策划咨询,会展服务,平面设计,电脑图文设计,广告设计、制作、代理、发布,旅游咨询,计算机软硬件开发与销售,办公设备、文教用品、服装、工艺礼品的销售,从事货物及技术的进出口业务,自有设备租赁,企业营销策划,文化艺术交流活动策划,数据处理,会务服务,体育赛事活动策划,票务代理,旅行社业务 ,广播电视节目制作 ,电信业务 。【依法须经批准的项目,经相关部门批准
后方可开展经营活动】'}}}

2. 询问公司的某些属性
```python
python answer.py --question=阿里体育的成立时间和注册资金是多少
```
### 输出：
>成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'成立日期': '2015-09-08', '注册资本': 26143.7909}}  

3. 询问符合条件的公司
```python
python answer.py --question=注册时间超过2018年12月的公司
```
### 输出:
> 成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'company_name': ['浙江国通星驿付信息技术有限公司', '杭州皮克皮克科技有限公司', '南京不止少年网络科技有限公司', '安徽中科昊音科技
股份有限公司', '深圳云一文化传媒有限公司', '上海攀达人力资源有限公司', '桂林凤凰文投置业有限公司', '内蒙古阿嘎日科技有限公司', '上海集氪科技有限公司', '广州虚拟影业有 
限公司', '上海贺弥医药有限公司', '南京昕瑞再生医药科技有限公司', '济南兴瑞商业运营有限公司', '河南堂学格筑教育科技有限公司', '深圳博华网络科技有限公司', '重庆起飞线信 
息技术有限公司', '福建宁德智享无限科技有限公司', '瑞福艺佳（北京）餐饮管理有限公司', '辽宁神州万峰新材料科技有限公司', '上海满电未来智能科技有限公司', '上海铼锶信息技 
术有限公司', '成都海博为药业有限公司', '和其瑞医药（南京）有限公司', '天津汇禾海河智能物流产业基金合伙企业（有限合伙）', '西安高新金融控股有限公司', '福州北控禹阳股权 
投资合伙企业（有限合伙）', '长春卓燊创景科技有限公司', '北京无线创和科技有限公司', '鼎晖投资（天津）有限公司', '镇江市悦禾企业管理咨询合伙企业（有限合伙）', '深圳华岩 
资本有限公司', '宁波复星锐正创业投资合伙企业（有限合伙）', '河南创投酒店管理有限公司', '上海掌租企业管理中心（有限合伙）', '中以（酒泉）绿色生态产业园有限公司', '欧瑞 
泽（上海）投资管理有限公司', '厦门亿远医药科技有限公司', '深圳市神驼物流科技有限公司', '杭州基本起源信息科技有限公司', '北京国欢文化传播有限公司', '牛创科技（广州）有 
限公司', '陕西当老师教育科技有限公司', '深圳市碧桂园创新投资有限公司', '宁波齐安信息科技有限公司', '隐木（上海）科技有限公司', '平潭骏晨金投资有限公司', '北京云真信科 
技有限公司', '北京国信云控科技股权投资合伙企业（有限合伙）', '天津汇禾资本管理有限公司', '吉药柜（天津）医疗科技有限公司', '和度生物医药（苏州）有限公司', '南京大鱼半 
导体有限公司', '武汉都印科技有限公司', '约策信息科技有限公司', '苏州绿科连接科技有限公司', '泉州市中禾金属有限公司', '快麟融网络科技（上海）有限公司', '北京中关村发展 
启航创新投资基金（有限合伙）', '北京中关村发展前沿企业投资基金（有限合伙）', '杭州嗨宝贝科技有限公司', '深圳市基础设施投资基金合伙企业（有限合伙）', '北京维妥科技有限 
公司', '杭州鲸鱼轻烟网络科技有限公司', '交银科创股权投资基金（上海）合伙企业（有限合伙）', '宇新（厦门）大数据股权投资基金合伙企业（有限合伙）', '家庭管家（上海）科技 
有限公司', '杭州主理网络科技有限公司', '沈阳潵绿餐饮服务有限公司', '浪潮（滨州）大数据有限公司', '镜头作家（深圳）咨询管理有限公司', '维塔科技（北京）有限公司', '北京 
宁矩科技有限公司', '北京积加科技有限公司', '北京鑫润一期股权投资合伙企业（有限合伙）', '福建固定科技有限公司', '上海近屿智能科技有限公司', '西安市未央区搞的各个商贸店', '广西芝根芝地生物科技有限公司', '广州欣旎科技有限公司', '杭州蔚来供应链科技有限公司', '广州六一教育科技有限公司', '上海非弘科技发展有限公司'], 'total_num': 82}}

```python
python answer.py --question=注册时间超过2018年12月且注册资金大于100万人民币的公司
```
### 输出:
> 成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'company_name': ['浙江国通星驿付信息技术有限公司', '南京不止少年网络科技有限公司', '安徽中科昊音科技股份有限公司', '深圳云一文化
传媒有限公司', '上海攀达人力资源有限公司', '桂林凤凰文投置业有限公司', '上海贺弥医药有限公司', '南京昕瑞再生医药科技有限公司', '济南兴瑞商业运营有限公司', '重庆起飞线 
信息技术有限公司', '福建宁德智享无限科技有限公司', '瑞福艺佳（北京）餐饮管理有限公司', '辽宁神州万峰新材料科技有限公司', '上海满电未来智能科技有限公司', '上海铼锶信息 
技术有限公司', '成都海博为药业有限公司', '和其瑞医药（南京）有限公司', '天津汇禾海河智能物流产业基金合伙企业（有限合伙）', '西安高新金融控股有限公司', '福州北控禹阳股 
权投资合伙企业（有限合伙）', '长春卓燊创景科技有限公司', '北京无线创和科技有限公司', '鼎晖投资（天津）有限公司', '深圳华岩资本有限公司', '河南创投酒店管理有限公司', ' 
上海掌租企业管理中心（有限合伙）', '中以（酒泉）绿色生态产业园有限公司', '欧瑞泽（上海）投资管理有限公司', '厦门亿远医药科技有限公司', '深圳市神驼物流科技有限公司', ' 
北京国欢文化传播有限公司', '陕西当老师教育科技有限公司', '深圳市碧桂园创新投资有限公司', '宁波齐安信息科技有限公司', '隐木（上海）科技有限公司', '北京云真信科技有限公 
司', '北京国信云控科技股权投资合伙企业（有限合伙）', '天津汇禾资本管理有限公司', '吉药柜（天津）医疗科技有限公司', '和度生物医药（苏州）有限公司', '南京大鱼半导体有限 
公司', '约策信息科技有限公司', '泉州市中禾金属有限公司', '快麟融网络科技（上海）有限公司', '北京中关村发展启航创新投资基金（有限合伙）', '深圳市基础设施投资基金合伙企 
业（有限合伙）', '北京维妥科技有限公司', '杭州鲸鱼轻烟网络科技有限公司', '交银科创股权投资基金（上海）合伙企业（有限合伙）', '宇新（厦门）大数据股权投资基金合伙企业（ 
有限合伙）', '杭州主理网络科技有限公司', '沈阳潵绿餐饮服务有限公司', '浪潮（滨州）大数据有限公司', '维塔科技（北京）有限公司', '北京宁矩科技有限公司', '北京积加科技有 
限公司', '北京鑫润一期股权投资合伙企业（有限合伙）', '福建固定科技有限公司', '广西芝根芝地生物科技有限公司', '广州欣旎科技有限公司', '广州六一教育科技有限公司', '上海 
非弘科技发展有限公司'], 'total_num': 62}}

4. 询问投融资事件
```python
python answer.py --question=学堂在线被哪些公司投资了
```
### 输出:
>成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'total_num': 1, '投资方列表': ['慕华资本', '高榕资本', '红点中国\n']}}

```python
python answer.py --question=学堂在线在哪轮被慕华资本投资了
```
### 输出:
> 成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'轮次': 'B轮'}}

```python
python answer.py --question=学堂在线在什么时候被慕华资本投资了
```
### 输出:
> 成功连接到ES服务器  
{'status': '问题解析成功', 'answer': {'融资时间': '2019-12-12'}}