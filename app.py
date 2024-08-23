from flask import Flask, render_template, request
from transformers import pipeline
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

# Initialize the summarizer
summarizer = pipeline('summarization')

def get_article_text(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    results = soup.find_all(['h1', 'p'])
    text = [result.text for result in results]
    article = ' '.join(text)
    return article

def summarize_article(article):
    article = article.replace('.', '.<eos>')
    article = article.replace('?', '?<eos>')
    article = article.replace('!', '!<eos>')
    sentences = article.split('<eos>')
    
    max_chunk = 500
    current_chunk = 0 
    chunks = []
    
    for sentence in sentences:
        if len(chunks) == current_chunk + 1: 
            if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
                chunks[current_chunk].extend(sentence.split(' '))
            else:
                current_chunk += 1
                chunks.append(sentence.split(' '))
        else:
            chunks.append(sentence.split(' '))
    
    for chunk_id in range(len(chunks)):
        chunks[chunk_id] = ' '.join(chunks[chunk_id])
    
    res = summarizer(chunks, max_length=50, min_length=30, do_sample=False)
    
    summary = ' '.join([summ['summary_text'] for summ in res])
    return summary

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        url = request.form['url']
        try:
            article = get_article_text(url)
            summary = summarize_article(article)
        except Exception as e:
            # Log the error and display a friendly message
            print(f"Error processing URL: {e}")
            summary = "Sorry, there was an error processing the blog post."
        return render_template('index.html', summary=summary)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
