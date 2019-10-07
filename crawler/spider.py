import requests
from requests.cookies import RequestsCookieJar
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from tools.configreader import config
import os
import pickle
import time
import re


class Spider():
    def __init__(self):
        self.username = config.get('Account','username')
        self.password = config.get('Account','password')
        self.questionid = config.get('Account','questionid')
        self.answer = config.get('Account','answer')
        self.login_url = config.get('Urls','login_url')
        self.target_url = config.get('Urls','target_url')
        self.cookies_path = os.path.abspath(__file__+'/../../'+config.get('Spider','cookies_path'))
        self.record_path = os.path.abspath(__file__+'/../../'+config.get('Spider','record_path'))
        self.cookies = self.load_cookies()
        self.filter_word = eval(config.get('Spider','filter_word'))
        self.limits = config.getint('Spider','limits')
        self.pattern1 = re.compile(r'阅读权限 \d+')
        self.pattern2 = re.compile(r'\d+')
        self.record = self.load_record()

    def login(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.login_url)
        driver.find_element_by_id('messagelogin').find_element('name', 'username').send_keys(self.username)
        driver.find_element_by_id('messagelogin').find_element('name', 'password').send_keys(self.password)
        Select(driver.find_element_by_id('messagelogin').find_element('name', 'questionid')).select_by_value(self.questionid)
        driver.find_element_by_id('messagelogin').find_element('name', 'answer').send_keys(self.answer)
        driver.find_element_by_id('messagelogin').find_element('name', 'loginsubmit').click()
        time.sleep(1)
        cookies = driver.get_cookies()

        try:
            driver.get(self.target_url)
            time.sleep(0.5)
            driver.find_element_by_id('um')
        except:
            cookies = []

        driver.quit()
        self.save_cookies(cookies)
        return cookies

    def load_cookies(self):
        if os.path.exists(self.cookies_path):
            with open(self.cookies_path,'rb') as f:
                cookies = pickle.load(f)
                cookies = self.valid_cookies(cookies)
        else:
            cookies = self.login()
        return cookies

    def valid_cookies(self,cookies):
        jar = RequestsCookieJar()
        for cookie in cookies:
            jar.set(cookie['name'], cookie['value'])

        s = requests.session()
        r = s.get(self.target_url, cookies=jar)
        html = r.text
        bsj = BeautifulSoup(html, 'lxml')
        um = bsj.find('div',{'id':'um'})
        if um:
            return cookies
        else:
            cookies = self.login()
        return cookies

    def save_cookies(self,cookies):
        with open(self.cookies_path,'wb') as f:
            pickle.dump(cookies,f)

    def load_record(self):
        if os.path.exists(self.record_path):
            with open(self.record_path,'rb') as f:
                record = pickle.load(f)
        else:
            record = []
        return record

    def save_record(self,record):
        length = len(self.record)+len(record)
        if length<=200:
            record = record+self.record
        else:
            delete_num = length-200
            if delete_num<len(self.record):
                self.record = self.record[:-delete_num]
                record = record + self.record
            else:
                record = record[:200]

        with open(self.record_path,'wb') as f:
            pickle.dump(record,f)

    def cleaner(self,text):
        state = 1
        for word in self.filter_word:
            if word in text:
                state = 0
                break
        if state:
            match_text = self.pattern1.search(text)
            if match_text:
                limit_text = match_text.group()
                match_num = self.pattern2.search(limit_text).group()
                if int(match_num) > self.limits:
                    state = 0
        if state:
            if text in self.record:
                state = 0

        return state

    def detail(self,href):
        jar = RequestsCookieJar()
        for cookie in self.cookies:
            jar.set(cookie['name'],cookie['value'])

        s = requests.session()
        r = s.get(href,cookies = jar)
        html = r.text
        bsj = BeautifulSoup(html,'lxml')
        try:
            div = bsj.find('div',{'id':'postlist'})
            content = div.find('div',{'class':'t_fsz'})
            content_text = content.text.strip()
            content_text = content_text.replace('\n','')
            img_urls = []
            for i in content.find_all('img'):
                if i.has_attr('file'):
                    img_url = i['file']
                    img_urls.append(img_url)
            for j in content.find_all('ignore_js_op'):
                text = j.text
                text = text.strip().replace('\n','')

                if text in content_text:
                    content_text = content_text.replace(text,'')

            content_text = content_text+'\n'+'\n'.join(img_urls)
        except:
            content_text = ''
        return content_text

    def fetcher(self):
        titles = []
        contents = []
        chrome_options = Options()
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.target_url)
        time.sleep(0.5)
        for cookie in self.cookies:
            cookie_dict = {'name':cookie['name'],'value':cookie['value']}
            driver.add_cookie(cookie_dict)

        driver.get(self.target_url)
        time.sleep(0.5)
        try:
            driver.find_element_by_id('um').text
        except:
            return titles,contents

        div = driver.find_element_by_id('threadlist')
        tbodys = div.find_elements_by_tag_name('tbody')[3:]
        fetch_hrefs = []
        for tbody in tbodys:
            post = tbody.find_element_by_tag_name('a')
            href = post.get_attribute('href')
            title = tbody.find_element_by_tag_name('th').text
            if self.cleaner(title):
                fetch_hrefs.append(href)
                titles.append(title)
        driver.quit()

        for href in fetch_hrefs:
            content = self.detail(href)
            contents.append(content)
        self.save_record(titles)

        return titles,contents


if __name__ == '__main__':
    spider = Spider()
    titles,contents = spider.fetcher()






