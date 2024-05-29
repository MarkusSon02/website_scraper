from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
import queue
import random
import time

def read_proxies_from_file(file_path):
    proxies = []
    final_proxies = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                # Remove any leading/trailing whitespace
                line = line.strip()
                if line:  # Ensure the line is not empty
                    proxies.append(line)
        for proxy in proxies:
            ip, port, user, password = proxy.split(':')
            proxy_dict ={
                'http': f'http://{user}:{password}@{ip}:{port}',
                'https': f'http://{user}:{password}@{ip}:{port}'
            }
            final_proxies.append(proxy_dict)
    except Exception as e:
        print(e)
    return final_proxies

# def get_proxy():
#     df = pd.read_csv('./components/Free_Proxy_List.csv')
#     # Filter proxies with high uptime success and low response time
#     filtered_proxies = df[(df['upTimeSuccessCount'] > 5000) & (df['responseTime'] < 100)]

#     # Sort the filtered proxies by response time
#     sorted_proxies = filtered_proxies.sort_values(by='responseTime', ascending=True)
#     proxy_list = [{'http': f"http://{row['ip']}:{row['port']}", 'https': f"https://{row['ip']}:{row['port']}"} for index, row in sorted_proxies.iterrows()]
#     return random.choice(proxy_list)


def load_page(url, user_agent):
    proxies = read_proxies_from_file('./components/Webshare_10_proxies.txt')
    proxy = random.choice(proxies)

    try:
        headers = {
            'User-Agent': user_agent
        }
        response = requests.get(url, timeout=20, headers=headers, proxies=proxy)  # Increase timeout as necessary
        time.sleep(random.uniform(1,3))
        if response.status_code < 400:
            return response.content
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_page(url, user_agent):
    csv_file = open('results/' + f'{url.split("/")[-1]}' + '.csv', 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['headline', 'list', 'paragraph'])

    hrefs = []

    html = load_page(url, user_agent)
    try:
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.find('body')
        h1 = body.find('h1')
        time = body.find('span', class_='date')
        view = body.find('span', class_ = 'view')
        intro_para_1 = body.find('h2', class_ = 'sappo')
        intro_para_2 = body.find_all('h2')[1].find_previous_sibling('p')
        # print(h1.text)
        # print(time.text)
        # print(view.text)
        # print(intro_para_1.text)
        # print(intro_para_2.text)
        
        h2s = body.find_all('h2')
        h2s = h2s[1:]
        for h2 in h2s:
            if h2.find_next_sibling('ul'):
                ul = h2.find_next_sibling('ul')
                p = ul.find_next_sibling('p')
                if p:
                    paragraph = p.text
                    if p.find_next_sibling('p'):
                        p = p.find_next_sibling('p')
                        while p:
                            paragraph += '\n' + p.text
                            p = p.find_next_sibling('p')
                else:
                    paragraph = None
                
                csv_writer.writerow([h2.text, ul.text, paragraph])
                # print(h2.text)
                # print(ul.text)
                # print(p.text)
            elif h2.find_next_sibling('p'):
                p = h2.find_next_sibling('p')
                paragraph = p.text
                if p.find_next_sibling('p'):
                    p = p.find_next_sibling('p')
                    while p:
                        paragraph += '\n' + p.text
                        p = p.find_next_sibling('p')
                csv_writer.writerow([h2.text, '', paragraph])


        related_articles = body.find('div', class_='related-news-block').find_all('a')
        for article in related_articles:
            hrefs.append('https://vinpearl.com/' + article.get('href'))

        # print(hrefs)

        # Load your CSV file
        df = pd.read_csv('results/' + f'{url.split("/")[-1]}' + '.csv', encoding='utf-8')

        # Save to Excel format
        df.to_excel('results/' + f'{url.split("/")[-1]}' + '.xlsx', index=False)

    except Exception as e:
        print(f"Can't access page {url}")
    finally:
        csv_file.close()
        return hrefs
    
def worker(url_queue, url_set, user_agents, max_depth):
    while True:
        try:
            # Timeout is set to ensure that it doesn't hang indefinitely if queue is empty
            url, current_depth = url_queue.get(timeout=5)
        except queue.Empty:
            # If no URLs are left in the queue, exit the thread
            return

        # Process the URL

        user_agent = random.choice(user_agents)
        hrefs = parse_page(url, user_agent)
        if current_depth < max_depth:
            for href in hrefs:
                if href not in url_set:
                    url_set.add(href)
                    url_queue.put((href, current_depth + 1))

        # Signals to the queue that the task is done
        url_queue.task_done()