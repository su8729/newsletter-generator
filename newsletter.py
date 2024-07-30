!pip install feedparser
!pip install openai
!pip install feedparser beautifulsoup4 requests jinja2 python-dotenv
import feedparser
from bs4 import BeautifulSoup
import requests
from jinja2 import Environment, FileSystemLoader
from google.colab import drive, files
from IPython.display import display, HTML, Image
import time
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv
from dateutil import parser
import base64

# Google Drive 마운트
drive.mount('/content/drive', force_remount=True)

# OpenAI API 키 설정 (환경 변수 사용)
client = OpenAI(api_key="")

def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def summarize_text(text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                {"role": "user", "content": f" 380-400자 이내로 뉴스를 요약해주세요 말투는 - 습니다 체를 사용해주세요 :\n\n{text}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"요약 중 오류 발생: {e}")
        return text
def fetch_news(target_date):
    url = "https://stoz.co.kr/rss"

    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            print("RSS 피드에서 뉴스 항목을 찾을 수 없습니다.")
            return None

        news_items = []
        for entry in feed.entries[:5]:
            try:
                published_at = parser.parse(entry.published)
                if published_at.date() == target_date.date():
                    title = entry.title
                    description = entry.description
                    link = entry.link

                    # 이미지 URL 추출
                    soup = BeautifulSoup(description, 'html.parser')
                    img_tag = soup.find('img')
                    image_url = img_tag['src'] if img_tag else ''

                    # HTML 태그 제거
                    description = BeautifulSoup(description, 'html.parser').get_text()

                    # OpenAI API를 사용하여 설명 요약
                    summarized_description = summarize_text(description)

                    news_items.append({
                        "title": title,
                        "description": summarized_description,
                        "url": link,
                        "source": "STOZ",
                        "published_at": published_at,
                        "image_url": image_url
                    })
            except Exception as e:
                print(f"뉴스 항목 처리 중 오류 발생: {e}")
                continue

        return news_items

    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")

    return None


def create_news_html(template_path, news_items, logo_base64, output_path):
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)), trim_blocks=True, lstrip_blocks=True)
    env.filters['zip'] = zip
    template = env.get_template(os.path.basename(template_path))
    html_content = template.render(news_items=news_items, logo_base64=logo_base64)

    # Base64로 인코딩된 폰트 파일 추가
    font_regular_path = "/content/drive/My Drive/카드뉴스/IBMPlexSansKR-Regular.ttf"
    font_bold_path = "/content/drive/My Drive/카드뉴스/IBMPlexSansKR-Bold.ttf"
    with open(font_regular_path, "rb") as font_file:
        font_regular_base64 = base64.b64encode(font_file.read()).decode('utf-8')
    with open(font_bold_path, "rb") as font_file:
        font_bold_base64 = base64.b64encode(font_file.read()).decode('utf-8')

    # HTML 내 폰트 URL 교체
    html_content = html_content.replace('YOUR_GOOGLE_DRIVE_FONT_URL', f"data:font/woff2;base64,{font_regular_base64}")
    html_content = html_content.replace('YOUR_GOOGLE_DRIVE_BOLD_FONT_URL', f"data:font/woff2;base64,{font_bold_base64}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_path

# 메인 실행 부분
if __name__ == "__main__":
    # 1. 뉴스 날짜 물어보기
    date_input = input("뉴스를 가져올 날짜를 입력하세요 (YYYY-MM-DD 형식): ")
    target_date = datetime.strptime(date_input, "%Y-%m-%d")

    # 뉴스 가져오기
    news_items = fetch_news(target_date)

    if news_items:
        print(f"{target_date.date()} 날짜에 업데이트된 뉴스 {len(news_items)}개를 찾았습니다.")

        # 2. 뉴스 보여주기
        for idx, news in enumerate(news_items, start=1):
            print(f"\n뉴스 {idx}:")
            print(f"제목: {news['title']}")
            print(f"설명: {news['description'][:100]}...")  # 설명의 처음 100자만 출력
            print(f"출처: {news['source']}")
            print(f"URL: {news['url']}")
            print(f"이미지 URL: {news['image_url']}")
            print(f"발행일: {news['published_at']}\n")

        # 뉴스 출력 후 1초 대기
        time.sleep(1)

        # 3. 템플릿 선택 이미지 표시
        print("템플릿 선택 이미지를 표시합니다. 잠시 기다려주세요...")
        display(Image(filename="/content/drive/My Drive/카드뉴스/temsel.png"))

        # 대기 시간 추가
        time.sleep(2)

        # 4. 템플릿 번호 고르기
        template_choice = input("원하는 템플릿 번호를 입력하세요 (1, 2, 3): ")

        # 선택된 템플릿에 따라 파일 경로 설정
        template_path = f"/content/drive/My Drive/카드뉴스/{template_choice}.html"
        output_path = "/content/drive/My Drive/카드뉴스/output.html"
        logo_path = "/content/drive/My Drive/카드뉴스/finger.png"

        # 로고 이미지를 Base64로 인코딩
        logo_base64 = get_image_base64(logo_path)

        # HTML 생성
        result_path = create_news_html(template_path, news_items, logo_base64, output_path)

        # 생성된 HTML 표시
        if result_path:
            with open(result_path, 'r', encoding='utf-8') as f:
                display(HTML(f.read()))

            # Colab 환경에서 파일 다운로드
            files.download(result_path)
    else:
        print("해당 날짜에 업데이트된 뉴스를 찾지 못했습니다.")
