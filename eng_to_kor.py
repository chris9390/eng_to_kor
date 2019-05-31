'''

네이버 기사 수집된 것을 DB에서 가져오는 예제 코드

@author: Jeongpil Lee (koreanfeel@gmail.com)
@created at : 2019. 05. 31.

'''

import pymysql
from bs4 import BeautifulSoup
from my_news_normalizer import my_news_normalizer
import re

eng_kor_dict = {'a' : '에이', 'b' : '비', 'c' : '씨', 'd' : '디', 'e' : '이',
                'f' : '에프','g' : '쥐' ,'h' : '에이치' ,'i' : '아이' ,'j' : '제이',
                'k' : '케이', 'l' : '엘', 'm' : '엠', 'n' : '엔', 'o' : '오',
                'p' : '피', 'q' : '큐', 'r' : '알', 's' : '에스', 't' : '티',
                'u' : '유',  'v' : '브이', 'w' : '더블유', 'x' : '엑스', 'y' : '와이', 'z' : '지'}


# 영어 패턴
eng_pattern = re.compile(r'([a-zA-Z]+)')



conn = pymysql.connect(host='163.239.28.23',
                       port=3306,
                       user='s20131533',
                       passwd='s20131533',
                       db='django_dms',
                       charset='utf8',
                       cursorclass=pymysql.cursors.DictCursor)


c = conn.cursor()

sql = "SELECT * from core_article LIMIT 10, 20"

c.execute(sql)
rows = c.fetchall()

for row in rows:
    print('\n{} - {} - {}'.format(row['article_uploaded_at'], row['article_title'], row['article_url']))
    print('=========================================================================================================')


    article_raw = row['article_raw']

    html_obj = BeautifulSoup(article_raw, "html.parser")
    content_text = html_obj.text
    divided_text = my_news_normalizer(content_text)

    for sentence in divided_text:
        #print(sentence)

        eng = eng_pattern.findall(sentence)
        if eng:
            print(sentence)

    print('=========================================================================================================\n')


c.close()

