# 網路來源

http://lee-w-blog.logdown.com/posts/1148021-deploy-linebot-on-heroku

# 目錄

- [Heroku](#heroku)    
    - [Create App](#create-app)    
    - [Deploy](#deploy)        
        - [Add Remote](#add-remote)    

    - [Environment Variables](#environment-variables)    
    - [Python Envrionments](#python-envrionments)     
        - [requirements.txt](#requirementstxt)        
        - [runtime.txt](#runtimetxt)        
        - [Deploy Settings - Procfile](#deploy-settings---procfile)    
    - [push 至 heroku](#push-至-heroku)    
    - [開啟/關閉功能](#開啟關閉功能)

**Deploy LineBot on Heroku**

# Heroku

## Create App

先上Heroku辦個帳號

到個人的dashboard
New -> Create New App選一個名字，就創好App了

## Deploy

### Add Remote

在部署之前要先安裝[Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

再來我們要到原本line-echobot，將heroku加入這個專案的remote

```sh
heroku login
heroku git:remote -a {Create App Name}
```

## Environment Variables

首先是我們原先設定的環境變數Heroku是透過這個指令來做設定

```sh
heroku config:set "env key":"env value"
```

或者也能到dashboard的Settings -> Config Variables -> Reveal Config Vars做設定

## Python Envrionments

因為Heroku支援多種不同的語言所以要讓Heroku知道我們使用的是Python

### requirements.txt

Heroku可過專案中是否有requirements.txt來判斷這個專案是否為Python專案並且安裝requirements.txt內的函式庫
名稱如果打錯，可能會讓Heroku不知道這是Python專案，導致部署失敗

### runtime.txt

另外可以透過runtime.txt來指定Python的版本

### Deploy Settings - Procfile

再來必須要讓Heroku知道我們執行專案的指令是什麼
這個指令就是寫在Profile中

這裡使用的部署套件是gunicorn
先在requirements.txt加入gunicorn==19.0.0
再來創一個Profile，內容是

```txt
web: gunicorn line_echobot.wsgi --log-file -
```

須注意settings.py部分
```py
# line_echobot\line_echobot\settings.py


import django_heroku

...

SECRET_KEY = "CHANGE_ME!!!! (P.S. the SECRET_KEY environment variable will be used, if set, instead)."

...

django_heroku.settings(locals())


```

## push 至 heroku

```cmd
git init

heroku git:remote -a "YOUR heroku APP NAME "

git add .

git commit -m "Add code"

git push heroku master
```

## 開啟/關閉功能

```cmd
heroku ps:scale web=1

heroku open

heroku ps:scale web=0
```



