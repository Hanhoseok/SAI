import os
import sys
import requests
from pprint import pprint

client_id = "v5sUIgVX8kgdL8dH6zsD"
client_secret = "iUvWd3Pjn1"

def get_translate(text, source, lan):
    data = {'text' : text,
            'source' : source,
            'target': lan}

    url = "https://openapi.naver.com/v1/papago/n2mt"

    header = {"X-Naver-Client-Id":client_id,
              "X-Naver-Client-Secret":client_secret}

    response = requests.post(url, headers=header, data=data)
    rescode = response.status_code
    if(rescode==200):
        t_data = response.json()
        text_i = t_data['message']['result']['translatedText']
        return text_i
    return ""
if __name__ == '__main__':
    while True:
        text = input("텍스트 : ")
        source = input("번역 전 언어")
        lan = input("번역 후 언어 (영어 : en, 일어 : ja) :")
        t_text = get_translate(text, source, lan)
        print(t_text)

