import re
import os
import requests
from bs4 import BeautifulSoup
from urllib import parse

import queue
# 문장 내 문장 처리에 사용될 큐
q = queue.Queue()

# 따옴표 패턴
quoted_pattern = re.compile(r'[“\"\'\‘].*?[”\"\'\’]')

#fp_read = open('/home/public_data/news_corpus/2015/100/output_20150101_20151231_100_264.txt','r')
#fp_write = open('result.txt', 'w')

#articles_before = fp_read.readlines()
articles_after = []
result = []

remove_count = 0

# 개행 문자
line_sep = os.linesep

#for article in articles_before:
def my_news_normalizer(article, limit_len=400):
    article = preprocess_text(article)
    article = get_content_before_endpoint(article)

    #article_original = article
    remove_count = 0


    # 기사 내용과 관계없는 문구 제거
    pattern_trash = re.compile(r'(© AFP=뉴스1)|(© News1)|(뉴스1)|(포토공용\s*기자)|(본문\s*이미지\s*영역)|(청와대\s*사진기자단)|(청와대\s*제공\.)')
    if pattern_trash.findall(article):
        article = pattern_trash.sub('', article)


    # Copyright부분 제거
    pattern_copyright = re.compile(r'[(<\[]?(Copyright|ⓒ)s?.*[)>\]]?')
    if pattern_copyright.findall(article):
        article = pattern_copyright.sub('', article)


    # 기사 끝부분에 기자 이메일 포함 뒷부분 제거
    # pattern_email = re.compile(r'[(\[<]?[a-z0-9_+.-]+@([a-z0-9-]+[.])+[a-z0-9]{2,4}[)\]>]?')
    # if pattern_email.findall(article):
    #     article = pattern_email.sub(line_sep, article)
    #     article = article.split(line_sep)[0]


    # 오른쪽 화살표 뒷부분 제거
    pattern_right_arrow = re.compile(r'▶|☞')
    if pattern_right_arrow.findall(article):
        article = pattern_right_arrow.sub(line_sep, article)
        article = article.split(line_sep)[0]


    # 기사 본문 제일 앞에 "기자 =" 또는 "특파원 =" 앞부분 제거
    pattern_reporter = re.compile(r'(?<=(특파원))\s*[=]|(?<=(기자))\s*[=]')
    if pattern_reporter.findall(article):
        article = pattern_reporter.sub(line_sep, article)
        article = article.split(line_sep)[1]


    # 여러 종류의 괄호로 묶인 내용 제거
    pattern_parentheses = re.compile(r'\(.*?\)|\[.*?\]|\<.*?\>|\【.*?\】|\＜.*?\＞')
    if pattern_parentheses.findall(article):
        article = pattern_parentheses.sub('', article)

    # 큐 초기화
    q.__init__()

    # 인용문 처리 (1차 치환)
    # 따옴표로 들어간 인용문 부분은 개행되지 않도록 별도 패턴으로 치환
    quoted = quoted_pattern.findall(article)
    if quoted:
        for idx, matched in enumerate(quoted):
            # 매칭된 패턴 Enqueue
            q.put(matched)
            # 나중에 다시 바꿔주기 위해 #(숫자)# 라고 표시
            article = article.replace(matched, '#' + str(idx) + '#')


    # ================================================================================================================

    article = article.replace('#br#', '\n')
    article = article.replace('#p#', '\n')


    '''
    article_original = article_original.replace('#br#', '\n')
    article_original = article_original.replace('#p#', '\n')

    pattern_LF = re.compile(r'(?<=[겠|니|한|했|이|하]다)(\s*[^가-힣\w]*)(?!이|가|고|라|며|면|는|거나|하|만)(?=[가-힣]|\w)|((?<!\d)(\.|\?)\s*(?=[^\w]))|((?<=[가-힣])(\.|\?)(?=[가-힣]))|((?<=\s)(\.|\?)(?=[가-힣]))|((?<=[가-힣])(\.|\?)(?=\w))')
    '''


    # 문장 단위로 나누는 패턴
    pattern_LF = re.compile(r'(?<=다)\s*([.]|[!]|[,])\s*(?!가|고|라|며|면|는|거나|만)')
    article = pattern_LF.sub('\n', article)

    # 인용문 처리 (후처리)
    # 문장 내 문장(인용 문장) 원위치
    idx = 0
    while q.qsize():
        article = article.replace('#' + str(idx) + '#', q.get())
        idx += 1

    # 광고 및 기사 사진에 대한 설명같이 매우 짧은 기사는 생략
    if limit_len:
        if len(article) < limit_len:
            return None

    sentences = article.split('\n')
    #sentences = article.split(line_sep)
    sentences_temp = []

    # ================================================================================================================


    # 문장들의 좌우 공백 제거 및 단어간 이중 띄어쓰기 제거
    for sentence in sentences:
        sentence = sentence.strip()
        sentence = ' '.join(sentence.split())

        if len(sentence) > 0:
            sentences_temp.append(sentence)

    sentences = sentences_temp


    # 한글이 포함되지 않은 문장패턴
    pattern_no_kor = re.compile(r'[^가-힣]*$')


    # remove를 수행하기 위한 sentences의 복사본
    sentences_temp = sentences


    # 문장단위로 보면서 한번 더 필터링
    for sentence in sentences:

        if len(sentence) < 15 and ('입니다' in sentence or '기자' in sentence or '특파원' in sentence) and sentence in sentences_temp:
            sentences_temp.remove(sentence)
            remove_count += 1


        # 문장 길이가 10글자 미만이면 제거
        if len(sentence) < 10 and sentence in sentences_temp:
            sentences_temp.remove(sentence)
            remove_count += 1


        if '공식 SNS 계정' in sentence and sentence in sentences_temp:
            sentences_temp.remove(sentence)
            remove_count += 1


        # 한글이 포함되지 않은 문장이면 제거
        if pattern_no_kor.findall(sentence) != [''] and sentence in sentences_temp:
            sentences_temp.remove(sentence)
            remove_count += 1


        # '다'로 끝나지 않는('다'가 포함되지 않은) 문장 제거
        if '다' not in sentence and sentence in sentences_temp:
            sentences_temp.remove(sentence)
            remove_count += 1


    sentences = sentences_temp

    '''
    print('\n===============================================================')
    print(article_original + '\n')
    print('\n===============================================================')
    for i in sentences:
        print(i + '\n')
    print('===============================================================\n')
    '''

    # 리스트 타입으로 리턴
    return sentences


def preprocess_text(text):
    text = text.replace('// flash 오류를 우회하기 위한 함수 추가', '')
    text = text.replace('function _flash_removeCallback() {}', '')
    text = text.strip()
    return text


class NewsArticle():
    title = None
    content = None
    summary = None
    content_raw = None
    uploaded_date = None
    updated_date = None
    url = None
    aid = None
    sid1 = None
    sid2 = None

    def __init__(self):
        pass

    def normalize(self):
        if self.content_raw:
            html_obj = BeautifulSoup(self.content_raw, "html.parser")
            content_text = html_obj.text
            divided_text = my_news_normalizer(content_text)

            # 텍스트 normalization 후에 남은 텍스트가 없는 경우에는 None을 리턴
            if divided_text == None or len(divided_text) == 0:
                return None

            self.content = divided_text

            return self.content
        else:
            return None


def get_article(article_url):

    news_article = NewsArticle()

    #
    # URL에서 querystring 추출작업
    #
    url = parse.urlparse(article_url)
    news_article.aid = parse.parse_qs(url.query)['aid'][0]
    news_article.sid1 = parse.parse_qs(url.query)['sid1'][0]
    news_article.sid2 = parse.parse_qs(url.query)['sid2'][0]

    main_content_after_opening_link = requests.get(article_url)
    plain_text__after_opening_link = main_content_after_opening_link.text
    plain_text__after_opening_link = plain_text__after_opening_link.replace('<br><br>', '#p#')
    plain_text__after_opening_link = plain_text__after_opening_link.replace('<br>', '#br#')

    soup_after_opening_link = BeautifulSoup(plain_text__after_opening_link, "html.parser")

    def parse_uploaded_date(soup_after_opening_link):
        """
        기사입력 날짜를 뽑아오는 함수

        :param soup_after_opening_link:
        :return:
        """

        #
        # 기사 형식에 따라 날짜를 뽑아옴.
        #
        if soup_after_opening_link.findAll('span', {'class': 't11'}): # 일반 기사
            date_temp = soup_after_opening_link.findAll('span', {'class': 't11'})[0].text

        elif soup_after_opening_link.select_one('div.news_headline > div.info span'): # 스포츠 기사
            date_temp = soup_after_opening_link.select_one('div.news_headline > div.info span').text

        # 그 이외 case
        elif soup_after_opening_link.select_one('div.article_info > span.author > em'): # 연예 기사
            date_temp = soup_after_opening_link.select_one('div.article_info > span.author > em').text

        else:
            raise Exception('No uploaded date.')

        date_pattern = r'(\d{4})[/.-](\d{2})[/.-](\d{2})[/.-]'
        time_pattern = r'(\d{1,2})[:](\d{2})'

        result = re.findall(date_pattern, date_temp)
        date = None

        if len(result) > 0:
            find_result = result[0]
            date = find_result[0] + '-' + find_result[1] + '-' + find_result[2]

        has_pm = False

        if '오후' in date_temp:
            has_pm = True

        result = re.findall(time_pattern, date_temp)
        time = None
        if len(result) > 0:
            find_result = result[0]
            hour = find_result[0]
            min = find_result[1]

            plus_time = 0
            if has_pm and hour != '12': # 오후 12시인 경우에는 12를 더하지 않음.
                plus_time = 12

            time = '{}:{}'.format(int(hour) + plus_time, min)

        if not date or not time:
            raise Exception('date or time not recognized.')

        date_temp = date + ' ' + time

        return date_temp

    def parse_content_body(soup_after_opening_link):
        """
        기사 본문을 뽑아오는 함수

        :param soup_after_opening_link:
        :return:
        """

        #
        # 기사 형식에 따라 본문을 뽑아옴.
        #
        content = None
        article_raw = None
        summary = None
        cleaned_summary = None

        if soup_after_opening_link.find('div', {'id': 'articleBodyContents'}):  # 일반 기사
            if soup_after_opening_link.find('div', {'class': 'news_content'}):
                content = soup_after_opening_link.find('div', {'class': 'news_content'}) # news_content가 있는 경우엔 기자 이메일 주소가 news_content 바깥에 존재함.

            else:
                content = soup_after_opening_link.find('div', {'id': 'articleBodyContents'})

        elif soup_after_opening_link.find('div', {'id': 'newsEndContents'}):  # 스포츠 기사
            content = soup_after_opening_link.find('div', {'id': 'newsEndContents'})

        elif soup_after_opening_link.find('div', {'id': 'articeBody'}):  # 연예 기사
            content = soup_after_opening_link.find('div', {'id': 'articeBody'})

        else:
            raise Exception('No content body.')

        # 기사 상단에 있는 요약 텍스트를 제거 (media_end_summary)
        if soup_after_opening_link.find('strong', {'class': 'media_end_summary'}):
            summary = soup_after_opening_link.find('strong', {'class': 'media_end_summary'}).extract().text # 이 라인 이후 전체 트리에서 자동으로 빠짐
        elif soup_after_opening_link.select('font > strong'):
            summary = soup_after_opening_link.select_one('font > strong').extract().text
        elif soup_after_opening_link.select('div#articleBodyContents > b'):
            summary = soup_after_opening_link.select_one('div#articleBodyContents > b').extract().text
        elif soup_after_opening_link.select('div#articleBodyContents > font > b'):
            summary_list = soup_after_opening_link.select('div#articleBodyContents > font > b')

            summaries = []
            for elem in summary_list:
                summaries.append(elem.extract().text)

            summary = '#br#'.join(summaries)

        # 요약텍스트를 라인별로 잘라 리스트 형태로 변환
        if summary:
            summary = line_split(summary)

            cleaned_summary = []
            for elem in summary:
                non_word_pattern = re.compile(r'^[^a-zA-Z0-9_가-힣]') # 특수문자인지 판단을 위한 패턴
                elem = non_word_pattern.sub('', elem)
                cleaned_summary.append(elem.strip())


        article_raw = str(content)

        return article_raw, cleaned_summary


    def parse_title(soup_after_opening_link):
        """
        기사 제목을 뽑아내는 함수

        :param soup_after_opening_link:
        :return:
        """
        title = None

        if soup_after_opening_link.find(id='articleTitle'):  # 일반 기사
            title = soup_after_opening_link.find(id='articleTitle').text
            title = title.strip()

        elif soup_after_opening_link.find('h4', {'class': 'title'}): # 스포츠 뉴스
            title = soup_after_opening_link.find('h4', {'class': 'title'}).text
            title = title.strip()

        elif soup_after_opening_link.find('h2', {'class': 'end_tit'}): # TV연예 뉴스
            title = soup_after_opening_link.find('h2', {'class': 'end_tit'}).text
            title = title.strip()

        if not title:
            raise Exception('news title not found.')

        return title


    title = parse_title(soup_after_opening_link)
    news_article.title = title

    article_uploaded_date = parse_uploaded_date(soup_after_opening_link)

    news_article.uploaded_date = article_uploaded_date

    # # 기사의 사진에 관한 설명 부분
    # about_photo_text = ''
    # about_photo_lst = soup_after_opening_link.findAll('em', {'class': 'img_desc'})
    # if about_photo_lst:
    #     about_photo_text = about_photo_lst[0].text

    article_raw, summary = parse_content_body(soup_after_opening_link)

    news_article.content_raw = article_raw
    news_article.summary = summary


    # # 기사에 사진에 관한 설명은 삭제
    # if about_photo_text != '':
    #     text = text.replace(about_photo_text, '')

    # divided_text = my_news_normalizer(text)
    #
    # # 텍스트 normalization 후에 남은 텍스트가 없는 경우에는 None을 리턴
    # if divided_text == None or len(divided_text) == 0:
    #     print('Loop Continue : No setences.')
    #
    #     return None
    #     # print('\tURL : ', article_url)

    news_article.url = article_url

    return news_article


def line_split(text):
    """
    p 및 br 태그로 구분된 항목을 문장으로 변환

    :param text:
    :return:
    """
    paragraphs = text.split('#p#')
    cleaned_sentences = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if len(paragraph) == 0:
            continue

        sentences = paragraph.split('#br#')


        for sentence in sentences:
            if len(sentence) == 0:
                continue

            cleaned_sentences.append(sentence.strip())

    return cleaned_sentences


def get_content_before_endpoint(text):
    """
    기자의 이메일 부분을 찾아서 그 뒷부분을 날림.
    이메일은 대부분 마지막 기자 이름쪽에만 등장하는 것으로 판단됨.

    :param text:
    :return:
    """
    pattern_email = re.compile(r'[(\[<]?[a-z0-9_+.-]+@([a-z0-9-]+[.])+[a-z0-9]{2,4}[)\]>]?')
    pattern_ads = [
        '디지털타임스 홈페이지 바로가기'
    ]

    paragraphs = text.split('#p#')
    cleaned_paragraphs = []

    is_endpoint_found = False
    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if len(paragraph) == 0:
            continue

        sentences = paragraph.split('#br#')
        cleaned_sentences = []

        for sentence in sentences:
            if len(sentence) == 0:
                continue

            # 기사 하단의 이메일 패턴이 발견될 경우
            if pattern_email.findall(sentence):
                sentence = pattern_email.sub(line_sep, sentence)
                sentence = sentence.split(line_sep)[0]

                if len(sentence) >= 10:
                    cleaned_sentences.append(sentence)

                is_endpoint_found = True
                break

            # 기사 하단의 광고문구 패턴이 발견될 경우
            for pattern_ad in pattern_ads:
                if pattern_ad in sentence:
                    is_endpoint_found = True
                    break

            # 종료조건인 경우 sentences 루프를 빠져나감.
            if is_endpoint_found:
                break

            cleaned_sentences.append(sentence)

        if len(cleaned_sentences) > 0:
            cleaned_paragraphs.append('#br#'.join(cleaned_sentences))

        if is_endpoint_found:
            break

    text = '#p#'.join(cleaned_paragraphs)

    return text