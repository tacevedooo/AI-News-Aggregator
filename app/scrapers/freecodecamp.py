import requests
from bs4 import BeautifulSoup
import time
import json

def get_full_article_content(article_url):
    """
    Visits the specific article page and extracts all text within <p> tags.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(article_url, headers=headers, timeout=10)
        article_soup = BeautifulSoup(response.text, 'html.parser')
        
        # FreeCodeCamp usually puts the main text in 'post-content'
        content_section = article_soup.find(['section', 'div'], class_='post-content')

        if content_section:
            # Collect all paragraphs
            paragraphs = content_section.find_all('p')
            # Join them with double newlines for readability
            full_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
            return full_text
        
        return "Content body could not be located on the page."
    except Exception as e:
        return f"Error downloading content: {e}"

def scrape_recent_freecodecamp():
    """
    Scrapes articles from the last 24 hours and saves their full text.
    """
    base_url = "https://www.freecodecamp.org/news/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    print("Fetching the main feed...")
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    news_list = []
    # Identify all article cards on the homepage
    articles = soup.find_all('article', class_='post-card')

    for post in articles:
        # 1. Locate the time tag with class 'meta-item'
        time_tag = post.find('time', class_='meta-item')
        
        if time_tag:
            time_text = time_tag.get_text(strip=True).lower()
            
            # 2. FILTER: Only proceed if it was published in the last 24 hours
            if "hour" in time_text or "minute" in time_text:
                title_element = post.find('h2', class_='post-card-title')
                link_tag = post.find('a', href=True)
                
                if title_element and link_tag:
                    full_link = "https://www.freecodecamp.org" + link_tag['href']
                    article_name = title_element.get_text(strip=True)
                    
                    print(f"Found Recent Article ({time_text}): {article_name}")
                    print(f"   --> Downloading full content...")
                    
                    # 3. DEEP SCRAPE: Get the full body text
                    full_body = get_full_article_content(full_link)
                    
                    # Store everything in the list
                    news_list.append({
                        "name": article_name,
                        "published_relative": time_text,
                        "timestamp": time_tag.get('datetime'),
                        "link": full_link,
                        "full_content": full_body,
                        "source": "FreeCodeCamp"
                    })
                    
                    # Polite delay between article requests
                    time.sleep(1.5)
            else:
                # If it's days/weeks old, skip it
                continue

    # 4. SAVE: Store the results in a JSON file
    if news_list:
        with open('recent_full_articles.json', 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=4)
        print(f"\nSuccess! Saved {len(news_list)} full articles to 'recent_full_articles.json'.")
    else:
        print("\nNo articles found from the last 24 hours.")

if __name__ == "__main__":
    scrape_recent_freecodecamp()