import json
import string
import urllib
from urlparse import urljoin

from BeautifulSoup import BeautifulSoup
import concurrent.futures
import requests

BASE_URL = 'https://developer.apple.com/library/ios/navigation/'
METADATA_URL = 'https://developer.apple.com/library/ios/navigation/library.json'

def download_pdf_from_html_page(url, lang='en'):
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    if soup and soup.html:
        html_lang = soup.html.get('lang')
        if html_lang and html_lang != lang:
            return

    title_tag = soup.find('meta', {'id': 'book-title'})
    title = title_tag.get('content') if title_tag else None
    pdf_urls = filter(
        None, [
            link.get('href') for link
            in soup.findAll('a')
            if link.text.strip().upper().endswith('PDF')
        ] + [
            link.get('contents') for link
            in soup.findAll('meta', {'name': 'pdf'})
        ]
    )

    if title and pdf_urls:
        print u'Downloading "{0}"...'.format(title)
        pdf_url = urljoin(url, pdf_urls[0])
        urllib.urlretrieve(pdf_url, '{0}.pdf'.format(safe_filename(title)))

def safe_filename(s):
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits, )
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

def download_metadata():
    print 'Downloading metadata...'
    r = requests.get(METADATA_URL)
    print 'Parsing metadata...'
    library = json.loads(r.text)
    return library

def main():
    library = download_metadata()
    documents = library['documents']

    urls = []
    for document in documents:
        if document[2] == 3:
            url = urljoin(BASE_URL, document[9])
            urls.append(url)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {}
        for url in urls:
            future = executor.submit(download_pdf_from_html_page, url)
            future_to_url[future] = url

        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))

if __name__ == '__main__':
    main()
