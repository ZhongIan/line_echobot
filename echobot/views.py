from django.shortcuts import render

# TEST
import requests
from django.http import HttpResponse

def index(request):
    # 顏文字
    r = requests.get('http://httpbin.org/status/418')
    print(r.text)
    return HttpResponse('<pre>' + r.text + '</pre>')


# @Initial
from line_echobot import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from django.views.decorators.csrf import csrf_exempt

# @ line API
from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ButtonsTemplate, MessageTemplateAction,
    URIAction
)

line_bot_api = LineBotApi(settings.YOUR_CHANNEL_ACCESS_TOKEN)

# Define Receiver 
handler = WebhookHandler(settings.YOUR_CHANNEL_SECRET)

from bs4 import BeautifulSoup
from ast import literal_eval

import pandas as pd
import sqlite3

# 股票代號
conn = sqlite3.connect("db.sqlite3")
df1 = pd.read_sql('SELECT * FROM stock', conn, index_col=['id'])
# 內容
#df1['stock'].values

# 油價資訊 
def oil_price():
    url = 'https://gas.goodlife.tw/'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    # 最後更新時間
    main = soup.select('#main')[0].text.replace('\n', '').split('(')[0]
    # 調整
    gas_price = soup.select('#gas-price')[0].text.replace('\n\n\n', '').replace(' ', '')
    # 油價
    cpc = soup.select('#cpc')[0].text.replace(' ', '').split('\n')

    cpc_title = cpc[1] # 今日中油油價
    cpc_92 = cpc[5]
    cpc_95 = cpc[8]
    cpc_98 = cpc[11]
    cpc_柴油 = cpc[14]

    content = f'{main}\n{gas_price}\n\n' + \
        f'{cpc_title}\n 92汽油:{cpc_92}\n 95汽油:{cpc_95}\n 98汽油:{cpc_98}\n 柴油:{cpc_柴油}'

    return content

# 股價資訊
def stock_info(stock_name='2330'):
    # 新聞網址 news_target為相對網址，需要 domain_url
    domain_url = 'https://www.wantgoo.com/'
    stock_url = 'https://www.wantgoo.com/stock/' + stock_name
    # response
    res = requests.get(stock_url)
    # 解析
    soup = BeautifulSoup(res.text, 'html.parser')
    # 目標: 新聞
    news_target = soup.find_all('ul', class_='ell lists')[0].find_all('a')
    news_content = ''
    # 只取 5筆
    if len(news_target)>5:
        num = 5
    else :
        num = len(news_target)
    for i in range(num):
        news_content += f"{news_target[i].text} \n " + \
            f"{domain_url + news_target[i].get('href')} \n\n"
    
    # 即時股價資訊，需要 headers 進行訪問
    head = {
        'referer': stock_url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
    }

    realtime_url = 'https://www.wantgoo.com/stock/astock/realtimechartupdatedata?StockNo=' + stock_name
    res = requests.get(realtime_url,headers=head)
    
    # eval() :str -> 轉成程式碼 ; res.json()['returnValues'] 回傳文字
    # https://stackoverflow.com/questions/30109030/how-does-strlist-work
    realtime_stock_info = literal_eval(
        res.json()['returnValues'].replace('null','"nan"') # 更換空值 null -> nan
    )['_01_基本股價資訊']

    stock_info_content = ''
    for i in ['更新時間','StockNo','Name','開','高','低','收','成交量']:
        stock_info_content += f'{i}: {realtime_stock_info[i]} \n'
    
    content = '相關新聞:\n' + news_content + '即時股價資訊:\n' + stock_info_content
    return content

# 文字訊息處理器
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

    if event.message.text == "開始":
        buttons_template = TemplateSendMessage(
            alt_text='開始 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='油價查詢',
                        text='油價查詢'
                    ),
                    MessageTemplateAction(
                        label='股價資訊',
                        text='股價資訊'
                    ),
                    URIAction(
                        label='分享 bot',
                        ## @kgo9924i https://line.me/R/ti/p/%40kgo9924i
                        uri='https://line.me/R/nv/recommendOA/@kgo9924i'
                    )
                ]
            )
        )

        line_bot_api.reply_message(event.reply_token, buttons_template)

        return 0

    if event.message.text == "油價查詢":
        content = oil_price()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    
    if event.message.text == "股價資訊":
        content = '請輸入股票代號 \n 如: 2330'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    # 判斷是否為股票代號
    if event.message.text in df1['stock'].values:
        content = stock_info(stock_name=event.message.text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    # 重複接收的訊息
    """ line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    ) """

# 一般訊息處理器 e.g. 貼圖 圖片 i.e. 除已定義的處理器外
@handler.default()
def default(event):
    print(event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Currently Not Support None Text Message \n' + '不支持此格式'
        )
    )

# @csrf_exempt 放棄 djaogo 的 csrf 認證
@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        # 處理訊息 Handler when receiver Line Message 
        try:
            handler.handle(body, signature)
        # 如果request不是從Line Server來的，丟出InvalidSignatureError其他使用錯誤，
        except InvalidSignatureError:
            return HttpResponseForbidden()
        # Line Server的問題會是丟出LineBotApiError    
        except LineBotApiError:
            return HttpResponseBadRequest()
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


# 風險值
from .VaR import VaR
import json

def out_VaR(request):

    name=str(request.GET.get('name', 2330))
    year=2015
    alpha=float(request.GET.get('alpha', 0.05))
    method=str(request.GET.get('method', 'sample'))

    a = VaR(name=name,year=year,alpha=alpha,method=method)
    
    # '歷史模擬法' # '變異數_共變異數法' # '蒙地卡羅法'
    # hist = a.main(method_name='歷史模擬法')
    # (data_result, dis_VaR, dis_CVaR)

    method_dict = [ a.main(method_name=i) for i in ['歷史模擬法','變異數_共變異數法','蒙地卡羅法']]
    hist_data = json.dumps(method_dict[0][0].to_dict('list'))
    hist_dis_VaR = method_dict[0][1]
    hist_dis_CVaR = method_dict[0][2]

    cm_data = json.dumps(method_dict[1][0].to_dict('list'))
    cm_dis_VaR = method_dict[1][1]
    cm_dis_CVaR = method_dict[1][2]

    mote_data = json.dumps(method_dict[2][0].to_dict('list'))
    mote_dis_VaR = method_dict[2][1]
    mote_dis_CVaR = method_dict[2][2]

    return render(
        request, 
        'Test_VaR.html', 
        locals()
    )
