from django.shortcuts import render

# Create your views here.
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

# 文字訊息處理器
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

    if event.message.text == "開始玩":
        buttons_template = TemplateSendMessage(
            alt_text='開始玩 template',
            template=ButtonsTemplate(
                title='選擇服務',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/xQF5dZT.jpg',
                actions=[
                    MessageTemplateAction(
                        label='油價查詢',
                        text='油價查詢'
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
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

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



