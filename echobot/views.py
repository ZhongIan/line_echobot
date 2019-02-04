from django.shortcuts import render

# Create your views here.
# @Initial
from line_echobot import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from django.views.decorators.csrf import csrf_exempt

# @ line API
from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi(settings.YOUR_CHANNEL_ACCESS_TOKEN)

# Define Receiver 
handler = WebhookHandler(settings.YOUR_CHANNEL_SECRET)

# 文字訊息處理器
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
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
        TextSendMessage(text='Currently Not Support None Text Message')
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



