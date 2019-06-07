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


read_like_this = {'kist' : '키스트', 'sars' : '사스', 'kaist' : '카이스트', 'kal' : '칼', 'naver' : '네이버', 'posco' : '포스코',
                  'koica' : '코이카', 'lifeplus' : '라이프플러스', 'korea' : '코리아', 'etri' : '에트리', 'opec' : '오펙'}

# R&D, M&A
eng_n_eng_pattern = re.compile(r'([a-zA-Z]+\s*\&\s*[a-zA-Z]+)')

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

sql = "SELECT * from core_article LIMIT 0, 1000"

c.execute(sql)
rows = c.fetchall()



for row in rows:
    #print('\n{} - {} - {}'.format(row['article_uploaded_at'], row['article_title'], row['article_url']))
    #print('=========================================================================================================')


    article_raw = row['article_raw']

    html_obj = BeautifulSoup(article_raw, "html.parser")
    content_text = html_obj.text
    divided_text = my_news_normalizer(content_text)

    # 기사 내에 영어가 있는 경우만 출력
    if eng_pattern.findall(' '.join(divided_text)):
        print('\n{} - {} - {}'.format(row['article_uploaded_at'], row['article_title'], row['article_url']))
        print('=========================================================================================================')

        for sentence in divided_text:

            # 알파벳 소문자로 변환
            sentence = sentence.lower()

            # 각 문장에 영어가 있는 경우
            eng = eng_pattern.findall(sentence)
            if eng:
                # 변경 전
                print(sentence)

                # 읽는 방법이 있는 영어인 경우 미리 저장해놓은 딕셔너리를 통해 변경
                for each in read_like_this:
                    if each in sentence:
                        sentence = sentence.replace(each, '<<' + read_like_this[each] + '>>')


                # R&D -> R앤D
                eng_n_eng = eng_n_eng_pattern.findall(sentence)
                if eng_n_eng:
                    for each in eng_n_eng:
                        temp = each.replace('&', '앤')
                        sentence = sentence.replace(each, temp)


                # 나머지 모든 알파벳 각각 읽기 방식으로 변경
                #  a -> 에이 / b -> 비
                for each in eng_kor_dict:
                    if each in sentence:
                        sentence = sentence.replace(each, eng_kor_dict[each])


                # 영어 표기 색칠
                '''
                for each in eng:
                    sentence = sentence.replace(each, '\033[1m\033[31m' + each + '\033[0m')
                '''

                # 변경 후
                print(sentence )
                print('\n')


        print('=========================================================================================================\n')


c.close()

