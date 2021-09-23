from scrapy_selenium import SeleniumRequest
import scrapy
from scrapy.crawler import CrawlerProcess
import csv
import os
import sys
from urllib.parse import urlparse, urljoin
import re
import platform
import stat
import zipfile
import tldextract
import time
import logging

# headers = {
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) Gecko/20100101 Firefox/80.0"
# }
headers = {
	"user-agent" : "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Mobile Safari/537.36 (contact xxx at xxx dot com)",
	"accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
	"accept-encoding" : "gzip, deflate, br",
	"accept-language" : "en-US,en;q=0.9",
	"cache-control" : "max-age=0",
	"sec-fetch-dest": "document",
	"sec-fetch-mode": "navigate",
	"sec-fetch-site": "none",
	"sec-fetch-user": "?1",
	"upgrade-insecure-requests": "1"
}
MAX_DEPTH=2

db_file='campaigndb.csv'
# error_file=open("error_suburls",'w')
logging.basicConfig(filename='scrapy_run.log', format='%(levelname)s:%(message)s',level=logging.DEBUG)

if os.path.isfile(db_file):
    recorder=open(db_file,'a')
else:
    recorder=open(db_file,'w')

writer=csv.writer(recorder,delimiter=',')
writer.writerow(['name','url','filepath','depth'])

def configureChromeDriver():
    system = platform.system()

    if os.path.isfile('chromedriver/chromedriver'):
        os.remove('chromedriver/chromedriver')

    if system == 'Darwin':
        filename = 'chromedriver/chromedriver_mac.zip'
    elif system == 'Linux':
        filename = 'chromedriver/chromedriver_linux.zip'
    else:
        print("Warning: Could not detect platform. Not using Selenium...")
        return False

    try:
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall('chromedriver/')
    except FileNotFoundError:
        logging.error('Chromedriver file not found')
        return False

    if os.path.isfile('chromedriver/chromedriver'):
        st = os.stat('chromedriver/chromedriver')
        os.chmod('chromedriver/chromedriver', st.st_mode | stat.S_IEXEC)
        return True
    else:
        print('error')
        return False

def saveHtml(response,depth):
    candidatename=response.meta['name'].replace(' ','')
    fullpath=os.path.join('html',candidatename)
    if not os.path.exists(fullpath):
        os.mkdir(fullpath)

    page_title=response.css('title::text').get()
    current_url=response.meta['url']

    relativeurlpath=urlparse(current_url).path
    rooturlpath=urlparse(current_url).netloc
    if relativeurlpath:
        relativepath=relativeurlpath.replace('/','|')
        filetocreate=os.path.join(fullpath,rooturlpath+relativepath+str(int(time.time())))
    else:
        filetocreate=os.path.join(fullpath,rooturlpath+str(int(time.time())))
    with open(filetocreate,'w') as f:
        f.write(response.text)
    logging.info(f'saved to {filetocreate}')

    writer.writerow([candidatename,current_url,filetocreate,depth])



class CampaignCrawler(scrapy.Spider):
    name="campaign_crawler"
    handle_httpstatus_list = [200, 301]
    custom_settings={
        "ROBOTSTXT_OBEY" : True,
        "DOWNLOAD_TIMEOUT": 20,
        "SELENIUM_DRIVER_NAME" : 'chrome',
        "DOWNLOADER_MIDDLEWARES" : {'scrapy_selenium.SeleniumMiddleware': 800 },
        "SELENIUM_DRIVER_EXECUTABLE_PATH" : 'chromedriver/chromedriver',
        "SELENIUM_DRIVER_ARGUMENTS" : ['--headless'],
        "DEPTH_PRIORITY" : 1,
        "SCHEDULER_DISK_QUEUE" : 'scrapy.squeues.PickleFifoDiskQueue',
        "SCHEDULER_MEMORY_QUEUE" : 'scrapy.squeues.FifoMemoryQueue'
    }

    def loadCampaignSites(self, filename='urllist.csv'):
        results=set()
        with open(filename,'r') as inputfile:
            csvreader=csv.reader(inputfile,delimiter=',')
            next(csvreader)
            for row in csvreader:
                name=row[0]
                site=row[-1]
                if site is None or len(site)==0:
                    continue
                results.add((name,site))
        return results

    def start_requests(self):
        print('----------started-----------')
        logging.info('----------started-----------')
        sites=self.loadCampaignSites()
        for name,link in sites:
            print(name,link)
            logging.info(f'Working on {name}:{link}')
            if link.startswith("file://"):
                yield scrapy.Request(url=link,callback=self.crawlCampaignSite, meta={"name":name,"url":link,"depth":0}, headers=headers)
            else:
                yield SeleniumRequest(url=link,callback=self.crawlCampaignSite, meta={"name":name,"url":link,"depth":0}, headers=headers)

    def skipUrl(self, url):
        url = url.strip()
        if url.startswith('tel:') or url.startswith('mailto:') or url.startswith('#'):
            return True
        return False

    def isAbsolute(self, link):
        return bool(urlparse(link).netloc)

    def isSameDomain(self, source_link, dest_link):
        if dest_link is None or len(dest_link) == 0:
            return False
        source_link=source_link.lower()
        dest_link=dest_link.lower()

        dest_domain = urlparse(dest_link).netloc
        source_domain = urlparse(source_link).netloc

        if not self.isAbsolute(dest_link):
            return True

        if dest_domain == source_domain:
            return True

        dest_root=tldextract.extract(dest_domain).domain
        source_root=tldextract.extract(source_domain).domain
        return dest_root==source_root

    def crawlCampaignSite(self, response):
        depth=response.meta['depth']
        logging.debug(f"{str(response.url)}, {str(response.status)}, {str(response.meta['url'])}")
        print(f'saving {response.url}')
        logging.info(f'Saving {response.url}')
        if str(response.status)!='200':
            logging.error(str(response.status)+' error on url '+str(response.url)+'\n')
            # error_file.write(str(response.status)+' error on suburl '+str(response.url)+'\n')
        saveHtml(response,depth=depth)
        print(response.url,response.status,response.meta['url'])

        if response.meta['depth']>MAX_DEPTH:
            return

        foundLink=False
        for link in response.xpath("//a"):
            foundLink=True
            destLink=link.xpath("@href").extract_first()
            if destLink is None or len(destLink)==0 or self.skipUrl(destLink):
                logging.debug(f"{destLink} ignored")
                continue

            if not self.isSameDomain(response.meta["url"], destLink):
                logging.debug(f"{destLink} ignored. Outbound link.")
                continue

            if not self.isAbsolute(destLink):
                destLink = urljoin(response.meta["url"], destLink)

            if not re.search(r'^http(s)?:', destLink):
                logging.debug(f"{destLink} ignored. Not proper link")
                continue

            if destLink.startswith("file://"):
                yield scrapy.Request(url=destLink,callback=self.crawlCampaignSite, meta={"name":response.meta["name"],"url":destLink,"depth":depth+1}, headers=headers)
            else:
                yield SeleniumRequest(url=destLink,callback=self.crawlCampaignSite, meta={"name":response.meta["name"],"url":destLink,"depth":depth+1}, headers=headers)
        if not foundLink:
            print("\tNo Links...", response.meta["url"], response.url, response.status)
            logging.debug(f"\tNo Links... {response.meta['url']}, {response.url}, {str(response.status)}")

def main():
    if not configureChromeDriver():
        logging.error('Error setting up selenium..')
        return
    if not os.path.exists("html"):
        os.mkdir("html")

    process = CrawlerProcess()
    process.crawl(CampaignCrawler)
    process.start()

if __name__ == '__main__':
    start_time=time.time()
    main()
    print('----Time taken in seconds----:',time.time()-start_time)
