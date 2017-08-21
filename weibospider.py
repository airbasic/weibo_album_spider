#!/usr/bin/env python2
# -*- coding:utf-8 -*-

import os,sys
import re
import time
import json
import urllib2,urllib
import cookielib
import requests
import logging
import random


from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


reload(sys)
sys.setdefaultencoding('utf8')


log_format = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=log_format)
logger = logging.getLogger('LOG')
logger.setLevel(logging.DEBUG)


class Weibospider():
	def __init__(self):
		pass
	def run(self):
		logger.debug('开工...')
		uidList = [{'uid':'3344758714','nick':'root'}]
		fanList = []
		imgList = []

		driver = self._loginWeibo()
		#fanList = self._getFans(driver)
		for item in uidList:
			fanList += self._getFans(driver,item['uid'])
		for item in fanList:
			imgListTmp = []
			imgListTmp = self._getPhotos(driver,item['uid'])
			imgList.append({'uid':item['uid'],'imgList':imgListTmp})
		for item in imgList:
			if os.path.exists('rices/'+item['uid']):
				continue
			else:
				os.mkdir('rices/'+item['uid'])
				for itemB in item['imgList']:
					listTmp = itemB.split('/')
					filename = listTmp[len(listTmp)-1]
					urllib.urlretrieve(itemB, 'rices/%s' % filename)

		driver.quit()


	def _unifyImgUrl(self,imgurl,uid='null'):
		listTmp = imgurl.split('/')
		human_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
						 'User-Agent': 'Mozilla/5.0 (Linux; U; Android 5.1.1; en-us; KIW-AL10 Build/HONORKIW-AL10) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 UCBrowser/1.0.0.100 U3/0.8.0 Mobile Safari/534.30 AlipayDefined(nt:WIFI,ws:360|592|3.0) AliApp(AP/9.5.3.030408) AlipayClient/9.5.3.030408 Language/zh-Hans'
						}
		if len(listTmp) == 5:
			listTmp[3] = 'large'
			imgurl = '/'.join(listTmp)
			if os.path.exists('rices/'+uid)==False:
				os.mkdir('rices/'+uid)
			#urllib.urlretrieve(imgurl, 'rices/%s/%s' % (uid,listTmp[4]))
			resp = requests.get(imgurl,headers=human_headers,stream=True)
			imgFileName = 'rices/%s/%s' % (uid,listTmp[4])
			with open(imgFileName,'wb') as fd:
				for chunk in resp.iter_content():
					fd.write(chunk)
				fd.close()

		else:
			logger.debug('无法解析小图url,保留缩略图:%s' % imgurl)
		return '/'.join(listTmp)

	def _getPhotos(self,driver,uid='2607577687'):
		logger.debug('正在抓uid:[%s]的1~10页相册~' % uid)
		imgList = []
		for x in xrange(1,10):
			imgListtmp = self._getPhotosByuidPerPage(driver,uid,page=x)
			if len(imgListtmp) == 0:
				break
			else:
				imgList = imgList + imgListtmp
		#sleep some time
		self._beHuman(driver)
		return imgList

	def _beHuman(self,driver):
		timeWait = random.randint(10,30)
		logger.debug('休息一段时间...%s秒' % str(timeWait))
		time.sleep(timeWait)
		driver.get('http://weibo.cn/')
		self._waitUntil(driver)

	def _getPhotosByuidPerPage(self,driver,uid='2607577687',page=1):
		#请登陆weibo.cn用传统列表
		url = "http://weibo.cn/album/albummblog?fuid=%s&page=%s&DisplayMode=2" % (uid,str(page))
		self._openUrl(driver,url)
		imgList = []
		try:
			logger.debug('正在抓uid:[%s]的第%s页' % (uid,str(page)))
			imgLast = driver.find_element_by_xpath("//table[last()]//img").get_attribute('src')
			imgLast = self._unifyImgUrl(imgLast,uid=uid)
			imgList.append(imgLast)
			i = 1
			img = driver.find_element_by_xpath("//table[1]//img").get_attribute('src')
			img = self._unifyImgUrl(img,uid=uid)
			while img != imgLast:
				imgList.append(img)
				i = i + 1
				img = driver.find_element_by_xpath("//table["+str(i)+"]//img").get_attribute('src')
				img = self._unifyImgUrl(img,uid=uid)
			return imgList
		except Exception as e:
			print e.message
			logger.debug('啊..uid:[%s]的相册..还没到20页就已经满...满了呢~' % uid)
			return []

	def _getFans(self,driver,startID='2607577687'):
		logger.debug('正在抓uid:[%s]的1~20页粉丝列表~' % startID)
		fanList = []
		for x in xrange(1,20):
			fanListtmp = self._getFansPerPage(driver,startID,page=x)
			if len(fanListtmp) == 0:
				continue
			else:
				fanList = fanList + fanListtmp
		return fanList

	def _getFansPerPage_isGirl(self,table,uid):
		sexEle = table.find_element_by_xpath("a[2]")
		sex = sexEle.get_attribute('innerHTML')
		if '她' in sex:
			logger.debug('[%s]这个id是女孩子...收入囊中...' % uid)
			return True
		else:
			logger.debug('[%s]这个id不是女孩子...丢掉~' % uid)
			#print sex
			return False

	def _getFansPerPage(self,driver,startID='6174268096',page=1):
		logger.debug('获取粉丝列表 page:%s' % page)
		url = "http://weibo.cn/%s/fans?page=%s" % (startID,str(page))
		self._openUrl(driver,url)
		fanlist = []
		try:
			tableLast = driver.find_element_by_xpath("//div[@class='c']/table[last()]//td[2]")
			td = tableLast.find_element_by_xpath("a[1]")
			#print td.get_attribute('innerHTML')
			atmp = td.get_attribute('href').split('/')
			uid = atmp[len(atmp)-1]
			name = td.text
			#print name
			#fanlist.append({'uid':uid,'nick':name})
			if self._getFansPerPage_isGirl(tableLast,uid):
				fanlist.append({'uid':uid,'nick':name})

			table = driver.find_element_by_xpath("//div[@class='c']/table[1]//td[2]")
			i = 1
			while table != tableLast:
				#print table.get_attribute('innerHTML')
				#print '\n----------\n'
				td = table.find_element_by_xpath("a[1]")
				#print td.get_attribute('innerHTML')
				atmp = td.get_attribute('href').split('/')
				uid = atmp[len(atmp)-1]
				name = td.text
				if self._getFansPerPage_isGirl(table,uid):
					fanlist.append({'uid':uid,'nick':name})
				i = i + 1
				table = driver.find_element_by_xpath("//div[@class='c']/table["+str(i)+"]//td[2]")
			return fanlist

		except Exception as e:
			print e.message
			logger.debug('啊..uid:[%s]的粉丝还没到20页就已经满...满了呢~' % startID)
			return []



	def _openUrl(self,driver,url):
		driver.get(url)
		self._waitUntil(driver)
		if '请输入图片中的字符' in driver.page_source:
			logger.debug('需要验证码，自动退出')
			exit(1)

	def _waitUntil(self,driver):
		pagesourceOld = 'Hello world'
		pagesource = driver.page_source
		timeA = 0
		while pagesource != pagesourceOld and timeA <= 30:
			timeA = timeA + 1
			pagesourceOld = driver.page_source
			time.sleep(0.2)
			pagesource = driver.page_source

	
	def _loginWeiboSSO(self):
		human_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
						 'User-Agent': 'Mozilla/5.0 (Linux; U; Android 5.1.1; en-us; KIW-AL10 Build/HONORKIW-AL10) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 UCBrowser/1.0.0.100 U3/0.8.0 Mobile Safari/534.30 AlipayDefined(nt:WIFI,ws:360|592|3.0) AliApp(AP/9.5.3.030408) AlipayClient/9.5.3.030408 Language/zh-Hans',
						 'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=http%3A%2F%2Fm.weibo.cn%2F'
						}
		url = 'https://passport.weibo.cn/sso/login'
		data = {'username':'87798606@qq.com','password':'what','savestate':'1','r':'http://m.weibo.cn','ec':'0','pagerefer':'https://passport.weibo.cn/signin/welcome?entry=mweibo&r=http%3A%2F%2Fm.weibo.cn%2F','entry':'entry:mweibo','wentry':'','loginfrom':'','client_id':'','code':'','qq':'','mainpageflag':'1','hff':'','hfp':''}
		r = requests.post(url,data=data,headers=human_headers)
		logincallback = json.loads(r.text)
		#print r.text
		if logincallback['retcode'] != 20000000:
			logger.debug('基础POST登录失败')
			exit(1)
		sso = logincallback
		logger.debug('微博登陆似乎成功了~')
		return sso

	def _loginWeibo(self):
		dcap = dict(DesiredCapabilities.PHANTOMJS)
		dcap["phantomjs.page.settings.resourceTimeout"] = 10
		dcap["loadImages"] = False
		human_headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
						 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
									   'Chrome/32.0.1700.76 Safari/537.36',
						}
		for key,value in human_headers.iteritems():
			dcap['phantomjs.page.customHeaders.{}'.format(key)] = value
		driver = webdriver.PhantomJS(executable_path=os.getcwd()+'/phantomjs',desired_capabilities=dcap)
		result = self._loginWeiboSSO()
		loginUrl = result['data']['loginresulturl']
		driver.get(loginUrl)
		driver.set_window_size(1920, 1080)
		self._waitUntil(driver)
		if '20000000' not in driver.page_source:
			logger.debug('sso登陆失败')
			exit(1)
		#print driver.page_source
		driver.get("http://weibo.cn/")
		self._waitUntil(driver)
		if '登录' in driver.page_source:
			logger.debug('sso跳转登陆失败')
			exit(1)
		#print driver.page_source
		logger.debug('微博登陆真的成功了!')
		#driver.get("http://weibo.com/")
		#print driver.page_source
		#exit()
		return driver


if __name__ == '__main__':
	weibos = Weibospider()
	weibos.run()
