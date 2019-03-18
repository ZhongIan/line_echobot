
# 網路來源

http://lee-w-blog.logdown.com/posts/1134898-line-echo-bot-on-django

參考後實際操作

# 目錄

- [Create a line_echobot project](#create-a-line_echobot-project)
- [Create an echobot app](#create-an-echobot-app)
- [Setup Line Secrets](#setup-line-secrets)
- [Setup Line Webhook URL](#setup-line-webhook-url)
- [Implement Callback Funtion](#implement-callback-funtion)    
    - [Validate Signature](#validate-signature)    
    - [Handle Recevied Message](#handle-recevied-message)        
        - [WEBHOOKPARSER](#webhookparser)        
        - [WEBHOOKHANDLER](#webhookhandler)    
- [FULL CODE](#full-code)        
    - [WebhookParser](#webhookparser)        
    - [WebhookHandler](#webhookhandler)
- [啟動時注意 by ngrok](#啟動時注意-by-ngrok)

# Create a line_echobot project

django-admin startproject line_echobot

# Create an echobot app

python manage.py startapp echobot

# Setup Line Secrets

接著設定Line Bot的Channel Secret, Channel Access Token

```bash
export SECRET_KEY='Your django secret key'
export LINE_CHANNEL_ACCESS_TOKEN='Your line channel access token'
export LINE_CHANNEL_SECRET='Your line channel secret'
```

執行時，讓設定檔先去讀取這些環境變數
下面的 get_env_variable 函式是用來取得環境變數
只要有少設定，就會丟出 **ImproperlyConfigured** 的例外事件中斷執行


```py
# line_echobot/settings.py


......

def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = 'Set the {} environment variable'.format(var_name)
        raise ImproperlyConfigured(error_msg)
        
SECRET_KEY = get_env_variable('SECRET_KEY')
LINE_CHANNEL_ACCESS_TOKEN = get_env_variable('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = get_env_variable('LINE_CHANNEL_SECRET')

......

INSTALLED_APPS = [
     ......,
    'echobot'
]

```

不過如果只是單純測試用，這些值也可以直接寫死在settings.py中

另外也不要忘了在INSTLLED_APPS加入echobot

一般來說，django產生project時settings.py裡面就會有secret key

這裡的做法是把預設的secret key刪掉設定到環境變數中，避免被git記錄下來

# Setup Line Webhook URL

再來要設定一個Webhook URL讓Line可以把Bot收到的訊息傳給我們

先在project的urls.py設定讓project可以找到echobot這個app的urls.py

```py
# line_echobot/urls.py

......

import echobot

urlpatterns = [
    ......,
    url(r'^echobot/', include('echobot.urls')),
]

......
```

接著在echobot內，創一個urls.py並將url再導到callback，呼叫views.py裡面的callback函式(接下來才會實作)

```py
# echobot/urls.py

from django.conf.urls import url

from . import views

urlpatterns = [
    url('^callback/', views.callback),
]
```

# Implement Callback Funtion

```py
echobot/views.py

# @Initial
from line_echobot import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

from django.views.decorators.csrf import csrf_exempt

# @ line API
from linebot import LineBotApi, WebhookParser, WebhookHanlder
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)


# TODO: Define Receiver


# @csrf_exempt 放棄 djaogo 的 csrf 認證
@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        
        # TODO: Handler when receiver Line Message


        return HttpResponse()
    else:
        return HttpResponseBadRequest()

```

## Validate Signature

處理訊息之前先確認這個request是不是真的是從Line Server傳來的要確認這件事，需要

+ request的body
+ request header中的X-Line-Signature

也就是上面的

```py
signature = request.META['HTTP_X_LINE_SIGNATURE']
body = request.body.decode('utf-8')
```

## Handle Recevied Message

取得body跟signature後Line Bot API會在處理訊息的同時，確認這個訊息是否來自Line;而處理Line傳過來給我們的訊息，有兩種不同的做法

+ WEBHOOKPARSER
+ WEBHOOKHANDLER

### WEBHOOKPARSER

WebhookParser會Parse這個訊息的所有欄位讓我們針對各種不同型別的訊息做個別的處理e.g.

+ UserID
+ Event Type
+ Message Content
+ and etc.

在[這裡](https://github.com/line/line-bot-sdk-python#webhook-event-object)可以找到有哪些欄位


```py
# TODO: Define Receiver
arser = WebhookParser(settings.LINE_CHANNEL_SECRET)

```

parser會parse所有的event跟各個event中的所有欄位如果request不是從Line Server來的，就會丟出InvalidSignatureError其他使用錯誤，或Line Server的問題都會是丟出LineBotApiError

```py
# TODO: Handler when receiver Line Message

try:
    events = parser.parse(body, signature)
except InvalidSignatureError:
    return HttpResponseForbidden()
except LineBotApiError:
    return HttpResponseBadRequest()

```

再來要判斷收到的事件是什麼事件這個Bot只需要echo純文字訊息所以先判斷這個事件是不是訊息事件，而這個訊息是不是文字訊息

```py
for event in events:
    if isinstance(event, MessageEvent):
        if isinstance(event.message, TextMessage):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.message.text)
            )

# isinstance 判斷是否為同一類別

```

最後的reply_message函式，讓我們傳訊息給Line Server第一個參數是要回傳要用的reply_token，可以從事件中取得 （event.reply_token）使用這個reply_token做回覆，是不用收費的不過同一個reply_token只能使用一次，而且在一定的時間內就會失效

第二個參數是這次要回傳的訊息

[這裡](https://github.com/line/line-bot-sdk-python#send-message-object)有所有能回傳的訊息也可以傳一個都是訊息的list或tuple不過一次最多只能傳5個
只要超過就會有LineBotApiError

### WEBHOOKHANDLER

WebhookHandler是針對每一種不同的訊息型態註冊一個處理器只要收到這樣的訊息，就會丟給對應的處理器如果確定每一類訊息，在任何情況下都會有相似的處理方式，就很適合這樣的設計

```py
# TODO: Define Receiver
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
```

先為handler加入，TextMessage的處理器參數是接收到的event
這裡做的也是讀取到原本event中的文字，並回傳回去


```py

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

```

因為沒有要處理其他訊息如果收到其他訊息(e.g. 貼圖, 照片)或訊息以外的事件使用default來回傳"Currently Not Support None Text Message"的文字訊息

```py

@handler.default()
def default(event):
    print(event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Currently Not Support None Text Message')
    )
```

```py
# TODO: Handler when receiver Line Message

try:
    handler.handle(body, signature)
except InvalidSignatureError:
    return HttpResponseForbidden()
except LineBotApiError:
    return HttpResponseBadRequest()

```

## FULL CODE

由於上面的code說明比較分散這裡附上兩個版本各自的完整版

### WebhookParser

```py
# line_echobot/echobot/views.py

# WebhookParser version


from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=event.message.text)
                    )

        return HttpResponse()
    else:
        return HttpResponseBadRequest()
```

### WebhookHandler

```py
# line_echobot/echobot/views.py

# WebhookHandler version


from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, TextMessage

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


@handler.default()
def default(event):
    print(event)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Currently Not Support None Text Message')
    )


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

```

如果你發現除了echo訊息外，還有其他的訊息可能就是沒有把Atuo Reply Message關掉這時候就可以去Line Bot的LINE@ MangerSettings -> Bot Settings把它關掉或者到Messages -> Auto Reply Message做修改訊息內容


# 啟動時注意 by ngrok

```py
# settings.py

# 出错信息
DEBUG = False
# 允許所有人訪問
ALLOWED_HOSTS = ['*']

# 預設文字 繁中
LANGUAGE_CODE = 'zh-hant'
# 時區 台北
TIME_ZONE = 'Asia/Taipei'
```


