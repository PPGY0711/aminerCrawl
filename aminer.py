# -*- coding:utf-8 -*-
from selenium import webdriver
from lxml import etree
from single_item import Author
import json
import time
import requests
import os


class AminerSpider(object):
    def __init__(self, theme, driver):
        self.driver = driver
        # self.start_url = start_url
        self.theme = theme
        self.items = []
        self.sleeptime = 5
        self.second_parse_sleep = 3
        self.temp_sleep_time = [1.5, 2, 2.5, 3]
        self.username = u'your username'    # 已做和谐处理，请输入自己的Aminer用户名
        self.password = u'your password'    # 输入自己的密码
        self.img_srcs = []
        self.author_infos = []
        self.file_count = 0  # 记录文件切片编号(也对应于开始的页面编号）

    def loginAminer(self, driver):
        # loginUrl = 'https://www.aminer.cn/login'
        # 加载webdriver驱动，用于获取登录页面标签
        # driver = self.driver
        # driver = webdriver.Chrome(executable_path='driver/chromedriver.exe')
        # driver.get(loginUrl)
        time.sleep(self.second_parse_sleep)
        driver.find_element_by_id('userPhone').clear()
        driver.find_element_by_id('userPhone').send_keys(self.username)
        driver.find_element_by_id('phonePassword').clear()
        driver.find_element_by_id('phonePassword').send_keys(self.password)
        driver.find_element_by_id('persist').click()
        submit = driver.find_element_by_tag_name('button')
        submit.click()  # 无验证码,直接登录提交
        time.sleep(self.sleeptime)

    def parse(self):
        driver = self.driver
        loginUrl = 'https://www.aminer.cn/login'
        # 加载webdriver驱动，用于获取登录页面标签
        driver.get(loginUrl)
        self.loginAminer(driver)

        # 直接在跳转之后的网页上爬
        driver.find_element_by_tag_name('input').clear()
        driver.find_element_by_tag_name('input').send_keys(self.theme)
        # <button type="submit" class="ant-btn searchBtn ant-btn-lg"><span style="color: rgb(2, 4, 68);">
        submit = driver.find_element_by_css_selector("[class='ant-btn searchBtn ant-btn-lg']")
        submit.click()
        time.sleep(self.sleeptime)
        total_page = int(driver.find_element_by_css_selector("[class='ant-pagination-simple-pager']")
                         .get_attribute('innerText')[1:])
        # print(total_page)
        # single_item.initialize_json(self.theme)
        next_page_link = driver.find_element_by_xpath(
            '//*[@id="search_body"]/div[2]/div[3]/div[1]/div[2]/div[1]/div[3]/div[2]/div[2]/ul/li[3]')
        for i in range(0, self.file_count):
            next_page_link.click()
            time.sleep(1.5)
        for i in range(1, total_page-self.file_count+1):
            # next_page_link = driver.find_element_by_css_selector("[class='anticon anticon-right']")
            div = driver.find_element_by_css_selector("[class="
                                                      "'a-aminer-components-expert-person-list-personList"
                                                      " person-list v1']")
            list_html = etree.HTML(div.get_attribute('innerHTML'))
            # print(etree.tostring(list_html))
            person_list = list_html.xpath("/html/body/div[@class='a-aminer-components-expert-c-person-item-personItem"
                                          " person-list-item']")
            prefix = 'https://www.aminer.cn'
            # print(len(person_list))
            for person in person_list:
                detail_div = person.xpath('div')[1]
                img_src = detail_div.xpath("div[@class='imgBox']/a/img/@src")[0]
                print(img_src)
                # 解决没有对应图片的作者问题
                if not img_src.startswith('https:'):
                    img_src = 'https:' + img_src
                name = detail_div.xpath("div[@class='content']/div[1]/div/div/a/strong/span/span[@class='name']/text()")[0]
                profile_link = detail_div.xpath("div[@class='content']/div[1]/div/div/a/@href")[0]
                print(profile_link)
                citation = int(detail_div.xpath('div[@class="content"]/div[2]/div/span[3]/span[@class="statst"]/text()')[0])
                paper_num = int(detail_div.xpath('div[@class="content"]/div[2]/div/span[2]/span[@class="statst"]/text()')[0])
                # print(name[0], citation[0])
                # print(paper_list)
                second_driver = get_headless_webdriver()
                interval = paper_num//500
                if interval > 3:
                    interval = 3
                paper_list = self.parse_paper_list_loop(prefix + profile_link, second_driver, self.temp_sleep_time[interval])  # 爬取该作者的paperlist
                second_driver.close()
                author = Author(name=name, img=img_src, citation=citation, paper_list=paper_list, theme=self.theme)
                self.author_infos.append(author.print_to_json())
                print(author.print_to_json())
                self.img_srcs.append({'name': name, 'img_src': img_src[:-4]})
                if len(self.author_infos) == 20:  # 每20个作者写成一个json
                    dump_to_json_file(author_infos=self.author_infos, theme=self.theme, file_count=self.file_count)
                    self.author_infos.clear()
                    download_imgs(self.img_srcs, self.theme, self.file_count)
                    self.img_srcs.clear()
                    self.file_count += 1
            next_page_link.click()
            print('next_page_click')
            time.sleep(self.sleeptime)
        # 最后不足20个的再写到json和下载图片
        if len(self.img_srcs) > 0:
            download_imgs(self.img_srcs, self.theme, self.file_count)
        if len(self.author_infos) > 0:
            dump_to_json_file(self.author_infos, self.theme, self.file_count)
        driver.close()

    def parse_paper_list(self, profile_url, driver, interval, count):
        paper_name_list = []
        prefix = 'https://www.aminer.cn'
        # driver = get_headless_webdriver()
        # driver = webdriver.Chrome(executable_path='driver/chromedriver.exe')
        driver.get(profile_url)
        login_link_html_str = driver.find_element_by_css_selector('[class="info"]').get_attribute('innerHTML')
        login_link_html = etree.HTML(login_link_html_str)
        # 第二次错的时候不能再进这个
        if count == 0:
            login_link = prefix + login_link_html.xpath('//a/@href')[0]
            # print(login_link)
            driver.get(login_link)
            # time.sleep(1)
            self.loginAminer(driver)
        # 重复点击查看全部和加载更多
        try:
            time.sleep(self.sleeptime)  # 给网页足够的加载时间
            while driver.find_element_by_xpath('//*[@id="menu_paper"]/section/div[2]/div[4]'):
                more_paper = driver.find_element_by_xpath('//*[@id="menu_paper"]/section/div[2]/div[4]')
                time.sleep(interval)  # 等待网页加载好之后才能点击"加载更多"
                more_paper.click()
        except Exception:
            paper_name_list = object()
            try:
                if driver.find_element_by_css_selector('[class="a-aminer-components-pub-publication-list'
                                                                     '-aminerPaperList profliePaperList '
                                                                     'publication_list"]'):
                    paper_name_list = self.get_paper_list(driver)
            except Exception:
                time.sleep(self.sleeptime)
                # driver.close()
                paper_name_list = self.parse_paper_list(profile_url, driver, interval, 1)
        # driver.close()
        return paper_name_list

    def parse_paper_list_loop(self, profile_url, driver, interval):
        count = 0
        paper_list = self.parse_paper_list(profile_url, driver, interval, count)
        if len(paper_list) == 0:
            count += 1
            while count <= 2:
                paper_list = self.parse_paper_list(profile_url, driver, interval, count)
                if len(paper_list) > 0:
                    break
                count += 1
        return paper_list

    def get_paper_list(self, driver):
        paper_name_list = []
        paper_list_element = driver.find_element_by_css_selector('[class="a-aminer-components-pub-publication-list'
                                                                 '-aminerPaperList profliePaperList '
                                                                 'publication_list"]').get_attribute('innerHTML')
        paper_list_html = etree.HTML(paper_list_element)
        paper_divs = paper_list_html.xpath('//div[@class="paper-item '
                                           'a-aminer-components-pub-c-publication-item-paperItem end"]')
        if len(paper_divs) > 0:
            name_list = paper_divs[0].xpath('//span[@class="paper-title"]/span/span/text()')
            for paper_name in name_list:
                paper_name_list.append(paper_name.replace('\n', ''))
            print(len(paper_name_list))
        return paper_name_list


def download_imgs(src_dict, theme, file_count):
    for img_dict in src_dict:
        name = img_dict['name']
        src = img_dict['img_src']
        img_suffix = src[src.rfind('.'):]
        img_get = requests.get(src)
        dir_path = 'img/'+theme+"/"+str(file_count)
        create_dir_not_exist(dir_path)
        with open(dir_path+"/"+name+img_suffix, 'wb') as f:
            f.write(img_get.content)


def create_dir_not_exist(path):
    if not os.path.exists(path):
        os.mkdir(path)


def dump_to_json_file(author_infos, theme, file_count):
    Author_dict = {theme: author_infos}
    jsObj = json.dumps(Author_dict)
    fileObject = open('json/ResultOf_'+ theme + '_' + str(file_count) + '.json', 'w', encoding='utf-8')
    fileObject.write(jsObj)
    fileObject.close()


def get_headless_webdriver():
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    driver = webdriver.Chrome(executable_path='driver/chromedriver.exe', options=option)
    return driver


if __name__ == "__main__":
    driver = get_headless_webdriver()
    theme = 'Visualization' # 搜索领域的关键词
    spider = AminerSpider(theme=theme, driver=driver)
    spider.parse()
