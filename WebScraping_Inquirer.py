from flask import Flask, render_template, request, jsonify
import csv
import os
from bs4 import BeautifulSoup
import requests
import re

app = Flask(__name__)

# Scraping function
def scrape_news_article(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.78 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find('h1').text.strip() if soup.find('h1') else 'No title found'
        author = 'No author found'

        # Handle author extraction for pop.inquirer.net
        if 'pop.inquirer.net' in url:
            author_tag = soup.find('a', rel='tag')
            if author_tag:
                author = author_tag.text.strip()

        # Existing logic for other sites
        if author == 'No author found':
            meta_author = soup.find('meta', {'name': 'author'})
            if meta_author and meta_author.get('content'):
                author = meta_author['content'].strip()

            if author == 'No author found':
                possible_author_classes = [
                    'byline__author-name', 'author__name', 'author', 
                    'byline', 'byline-author', 'author-name'
                ]
                for class_name in possible_author_classes:
                    author_tag = soup.find(['span', 'a', 'div'], class_=class_name)
                    if author_tag and author_tag.text.strip():
                        author = author_tag.text.strip()
                        break

        pub_date = 'No date found'
        possible_date_tags = ['time', 'span', 'div', 'p']
        possible_date_classes = [
            'published-date', 'publication-date', 'pub-date', 
            'article-date', 'posted-date', 'entry-date'
        ]

        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            pub_date = time_tag['datetime'].strip()
        elif time_tag and time_tag.text.strip():
            pub_date = time_tag.text.strip()
        else:
            for tag in possible_date_tags:
                for class_name in possible_date_classes:
                    date_tag = soup.find(tag, class_=class_name)
                    if date_tag and date_tag.text.strip():
                        pub_date = date_tag.text.strip()
                        break
                if pub_date != 'No date found':
                    break

        if pub_date == 'No date found':
            meta_date = soup.find('meta', {'property': 'article:published_time'})
            if meta_date and meta_date.get('content'):
                pub_date = meta_date['content'].strip()

        if pub_date == 'No date found':
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string:
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', script.string)
                    if date_match:
                        pub_date = date_match.group(0)
                        break

        if pub_date == 'No date found':
            url_date_match = re.search(r'\d{4}/\d{2}/\d{2}', url)
            if url_date_match:
                pub_date = url_date_match.group(0).replace('/', '-')

        content = 'No content found'
        category = 'Unknown'
        if 'newsinfo' in url:
            category = 'newsinfo'
        elif 'business' in url:
            category = 'business'
        elif 'entertainment' in url:
            category = 'entertainment'
        elif 'lifestyle' in url:
            category = 'lifestyle'
        elif 'sports' in url:
            category = 'sports'
        elif 'bandera' in url:
            category = 'bandera'

        content_classes_by_category = {
            'newsinfo': ['article-content', 'post-content', 'content'],
            'business': ['article-body', 'content'],
            'entertainment': ['article-body', 'content'],
            'lifestyle': ['article-body', 'content'],
            'sports': ['article-body', 'content'],
            'bandera': ['article-body', 'content'],
            'Unknown': ['article-body', 'content']
        }

        possible_content_classes = content_classes_by_category.get(category, ['article-body', 'content'])

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

        news_source = 'Inquirer'

        # Classification logic
        classification = '1'  # You can customize this logic

        return {
            'title': title,
            'author': author,
            'publication_date': pub_date,
            'content': content,
            'news_source': news_source,
            'link': url,  
            'classification': classification
        }

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None


# Function to save the article to CSV
def save_article_to_csv(article_info, filename):
    file_exists = os.path.isfile(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'author', 'publication_date', 'content', 'news_source', 'link', 'classification']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()
        
        writer.writerow(article_info)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inquirer News Scraper</title>
        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: #f8f9fa;
                font-family: Arial, sans-serif;
            }
            .container {
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                font-size: 2rem;
                color: #343a40;
                margin-bottom: 20px;
            }
            textarea {
                font-size: 1.1rem;
                padding: 10px;
                resize: none;
            }
            #messageBox {
                margin-top: 20px;
                display: none;
            }
            footer {
                margin-top: 30px;
                text-align: center;
                color: #6c757d;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center">Inquirer News Scraper</h1>
            <form id="articleForm">
                <div class="form-group">
                    <textarea id="urlInput" class="form-control" rows="3" placeholder="Paste Inquirer article URL here..."></textarea>
                </div>
                <div class="alert" id="messageBox"></div>
            </form>
        </div>

        <script>
            document.getElementById('urlInput').addEventListener('input', function() {
                let url = this.value.trim();
                if (url) {
                    fetch('/save_article', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: 'url=' + encodeURIComponent(url)
                    })
                    .then(response => response.json())
                    .then(data => {
                        let messageBox = document.getElementById('messageBox');
                        messageBox.style.display = 'block';
                        if (data.status === 'success') {
                            messageBox.className = 'alert alert-success';
                            messageBox.textContent = data.message;
                        } else {
                            messageBox.className = 'alert alert-danger';
                            messageBox.textContent = data.message;
                        }
                        document.getElementById('urlInput').value = ''; // Clear input after submission
                    });
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/save_article', methods=['POST'])
def save_article():
    url = request.form.get('url')
    if not url:
        return jsonify({'status': 'fail', 'message': 'URL not provided'})

    article_info = scrape_news_article(url)
    if article_info:
        filename = 'train.csv'
        
        if not os.path.isfile(filename):
            save_article_to_csv(article_info, filename)
            return jsonify({'status': 'success', 'message': 'Article saved successfully'})
        
        # Check for duplicates based on title and publication date
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['title'] == article_info['title'] and row['publication_date'] == article_info['publication_date']:
                    return jsonify({'status': 'fail', 'message': 'Duplicate article. Already saved.'})
        
        save_article_to_csv(article_info, filename)
        return jsonify({'status': 'success', 'message': 'Article saved successfully'})
    
    return jsonify({'status': 'fail', 'message': 'Failed to scrape the article'})

if __name__ == '__main__':
    app.run(debug=True)
