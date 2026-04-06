import requests
from bs4 import BeautifulSoup
import csv
import os
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

def scrape_news_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find('h1').text.strip() if soup.find('h1') else 'No title found'

        author = 'No author found'
        meta_author = soup.find('meta', {'name': 'author'})
        if meta_author and meta_author.get('content'):
            author = meta_author['content'].strip()

        if author == 'No author found':
            possible_author_tags = ['span', 'a', 'div']
            possible_author_classes = [
                'byline__author-name',
                'author__name',
                'author',
                'byline',
                'byline-author',
                'author-name'
            ]

            for tag in possible_author_tags:
                for class_name in possible_author_classes:
                    author_tag = soup.find(tag, class_=class_name)
                    if author_tag and author_tag.text.strip():
                        author = author_tag.text.strip()
                        break
                if author != 'No author found':
                    break

        pub_date = soup.find('time').text.strip() if soup.find('time') else 'No date found'

        content = 'No content found'
        possible_content_classes = ['article-body', 'article-content', 'main-article', 'post-content', 'content']

        for class_name in possible_content_classes:
            article_body = soup.find('div', class_=class_name)
            if article_body:
                paragraphs = article_body.find_all('p')
                if paragraphs:
                    content = '\n'.join([para.text.strip() for para in paragraphs])
                    break

        if content == 'No content found':
            for div in soup.find_all('div'):
                paragraphs = div.find_all('p')
                if len(paragraphs) > 5:
                    content = '\n'.join([para.text.strip() for para in paragraphs])
                    break

        unwanted_texts = [
            "This is AI generated summarization, which may have errors. For context, always refer to the full article.",
            "CONTAINMENT.",
            "SUMMARY"
        ]

        for text in unwanted_texts:
            content = content.replace(text, '').strip()

        news_source = 'Rappler' if 'rappler.com' in url else 'Unknown'

        return {
            'title': title,
            'author': author,
            'publication_date': pub_date,
            'content': content,
            'news_source': news_source,
            'link': url,
            'classification': 1
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def save_article_to_csv(article_info, filename):
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'author', 'publication_date', 'content', 'news_source', 'link', 'classification']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(article_info)

def read_existing_links(filename):
    if not os.path.isfile(filename):
        return set()

    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return {row['link'] for row in reader}

@app.route('/')
def index():
    return render_template_string('''
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
            <title>Rappler News Scraper</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
              }
              .container {
                background: #ffffff;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                padding: 20px;
                max-width: 500px;
                width: 100%;
                text-align: center;
              }
              h1 {
                margin-bottom: 20px;
                color: #333;
              }
              input[type="text"] {
                width: calc(100% - 22px);
                padding: 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                box-sizing: border-box;
                margin-bottom: 10px;
              }
              #message {
                margin-top: 15px;
              }
              p {
                margin: 0;
                padding: 5px;
              }
              p.success {
                color: #28a745;
              }
              p.warning {
                color: #ffc107;
              }
              p.error {
                color: #dc3545;
              }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>Rappler News Scraper</h1>
              <form id="scrape-form">
                <input type="text" id="url-input" placeholder="Enter Rappler news URL">
              </form>
              <div id="message"></div>
            </div>
            <script>
              document.getElementById('url-input').addEventListener('input', function() {
                const url = document.getElementById('url-input').value;
                if (url) {
                  scrapeArticle(url);
                }
              });

              function scrapeArticle(url) {
                fetch('/scrape', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({ url: url })
                })
                .then(response => response.json())
                .then(data => {
                  const messageDiv = document.getElementById('message');
                  if (data.success) {
                    messageDiv.innerHTML = '<p class="success">Article saved to train.csv</p>';
                  } else if (data.message === 'exists') {
                    messageDiv.innerHTML = '<p class="warning">This link already exists in the CSV file.</p>';
                  } else {
                    messageDiv.innerHTML = '<p class="error">Failed to retrieve or save the article.</p>';
                  }
                  
                  // Clear the input field
                  document.getElementById('url-input').value = '';
                });
              }
            </script>
          </body>
        </html>
    ''')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')
    filename = 'train.csv'
    existing_links = read_existing_links(filename)

    if url in existing_links:
        return jsonify({'success': False, 'message': 'exists'})

    article_info = scrape_news_article(url)
    if article_info:
        save_article_to_csv(article_info, filename)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
