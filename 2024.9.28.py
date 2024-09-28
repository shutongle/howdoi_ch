#test
#a=2+2
#print(a)
import gc
gc.disable()

import argparse
import inspect
import json
import os
import re
import sys
import textwrap

from urllib.request import getproxies
from urllib.parse import quote as url_quote, urlparse, parse_qs

from multiprocessing import Pool

import logging
import appdirs
import requests

from cachelib import FileSystemCache, NullCache

from keep import utils as keep_utils

from pygments.lexers import guess_lexer, get_lexer_by_name
from pygments.util import ClassNotFound
from rich.syntax import Syntax
from rich.console import Console
#continue last time


from pyquery import PyQuery as pq #html解析操作库
from requests.exceptions import ConnectionError as RequestsConnectionError #处理连接异常
from requests.exceptions import SSLError

from colorama import init #彩色输出
init()

from howdoi import __version__
from howdoi.errors import GoogleValidationError

logging.basicConfig(format='%(levelname)s:%(message)s') #设置日志消息格式
if os.getnev('HOWDOI_DISABLE_SSL'):
		SCHEME = 'http://'
		VERIFY_SSL_CERTIFICATE = False
else:
		SCHEME = 'https://'
		VERIFY_SSL_CERTIFICATE = True #检查环境变量？
		
SUPPORTED_SEARCH_ENGINES = ('google','bing','duckduckgo') #元组tumple

URL = os.getnev('HOWDOI_URL') or 'stackoverflow.com'
USER_AGENTS = (
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0)Gecko/20100101 Firefox/11.0',
	'Mozilla/5.0'
	) #模拟不同浏览器和操作系统
	
SEARCH_URLS = {
	'bing': SCHEME +'www.bing.com/search?q=site:{0}%20{1}&hl=en',
	'google'
} #允许动态构建查询

BLOCK_INDICATORS = (
		'form id ="captcha-form"',
		'This page appears when Google automatically detects requests coming from your computer '
		'network which appear to be in violation of the <a href="//www.google.com/policies/terms/">Terms of Service'
	) #处理请求被阻止的情况

BLOCKED_QUESTION_FRAGMENTS = (
	'webcache.googleusercontent.com',
	)
	
STAR_HEADER = '\u2605' #输出格式化
ANSWER_HEADER = '{2} Answer from {0} {2}\n{1}' #定义答案格式
NO_ANSWER_MSG = '< no answer given >'

CACHE_EMPTY_VAL = "NULL"
CACHE_DIR = appdirs.user_cache_dir('howdoi')
CACHE_EMPTY_MAX = 128 #缓存中最大变量数

HTML_CACHE_PATH = 'page_cache' #缓存HEML
SUPPORTED_HELP_QUERIES = ['use howdoi','howdoi', 'run howdoi', 'setup howdoi', 
	'do howdoi', 'howdoi howdoi', 'howdoi use howdoi']
NO_RESULTS_MESSAGE = "Sorry, couldn't find any help with that topic"

STASH_SAVE = 'save'
STASH_VIEW = 'view'
STASH_REMOVE = 'remove'
STASH_EMPTY = 'empty'

#缓存初始化
if os.getnev('HOWDOI_DISABLE_CACHE'):
	cache = NullCache()
else:
	cache = FileSystemCache(CACHE_DIR, CACHE_EMTRY_MAX, default_timeout=0)
 
howdoi_session = request.session()

class BlockError(RuntimeError):
	 		pass

class IntRange:
		def __init__(self, imin=None, imax=None):
				self.imin = imin
				self.imax = imax
				
		def __call__(self, arg):
				try:
						value = int(arg)
				except ValueError as value_error
						raise self.exception() from value.error
				if(self.imin is not None and value < self.imin) or (self.imax is not None and value > self.imax):
					raise self.exception()
				return value
				
		def exception(self):
				if self.imin is not None and self.imax is not None:
						return argparse.ArgumentTypeError(f'Must be an interger in the range [{self.imin}, {slef.imax}]')
				if self.imin is not None:
						return argparse.ArgumentTypeError(f'Must be an interger >= {self.imin}')
				if self.imax is not None:
						return argparse.ArgumentTypeError(f'Must be an interger <= self.imax')
				return argparse.ArgumentTypeError('Must be an interger')


def _random_int(width):
	bres = os.urandom(width)
	if sys.version < '3':
			ires = int(bres.encode('hex'), 16)
	else:
			ires = int.from_bytes(bres, 'little')
	
	return ires
		#生成width字节长度的随机整数，小端存储
		
def _random_choice(seq):
		return seq[_random_int(1) % len(seq)] #随机选择元素
		
def get_proxies():
		proxies = getproxies()
		filtered_proxies = {}
		for key, value in proxies.item():
				if key.startswith('http'):
						if not value.startswith('http'):
							filtered_proxies[key] = f'http://{value}'
				else:
						filtered_proxies[key] = value
		return filtered_proxies #过滤hhtp代理
		
def _get_result(url):
		try:
				resp = howdoi_session.get(url, headers={'User-Agent':_random_choice(USER_AGENTS)},
							proxies=get_proxies(),
							verify=VERIFY_SSL_CERTIFICATE,
							cookies={'CONSENT': 'YES+US.en+20170717-00-0'}	)
				resp.raise_for_status()
				return resp.text
			except requests.exceptions.SSLError as error:
				logging,error('%sEncountered an SSL Error. Try using HTTP instead of '
				'HTTPS by setting the enviroment variable "HOWDOI_DISABLE_SSL".\n%s', RED, END_FORMAT)
				raise error #处理网络请求，可能的SSL错误
				
	def _get_from_cache(cache_key):
			current_log_level = logging.getLogger().getEffectiveLevel()
			logging.getLogger().setLevel(logging.ERROR)
			page = cache.get(cache_key)
			logging.getLogger().setLevel(current_log_level)
			return page #缓存管理，不必要的日志输出
			
def _add_link_to_text(element):
		hyperlink = element.find('a')
		
		for hyperlink in hyperlinks:
				pquery_object = pq(hhyperlink)
				href = hyperlink.attrib['href']
				copy = pquery_object.text()
				if copy == href:
						replacement = copy
				else:
						replacement = f'[{copy}]({href})'
				pquery_object.replacement_with(replacemnt) 
    #将超链接模式转换成md格式
    
def get_text(element):
		'''return inner text in pyquery element'''
		_add_links_to_text(element)
		try:
				return element.text(squash_space=False)
		except TypeError:
				return element.text()
		#获取文本内容
		
def _extract_links_from_bing(html):
		html.remove_namespaces()
		return [a.attrib['href'] for a in html('.b_algo')('h2')('a')]
		#提取链接，从bing

def _clean_google_link(link):
		if '/url?' in link:
				prased_link = urlparse(link)
				query_params = parse_qs(parsed_link.query)
				url_params = query_params.get('q', []) or query_params.get('url', [])
				if url_params:
						return url_params[0]
		return link
		#提取google实际 url
		
def _extract-links_from_google(query_object):
		html = query_object.html()
		link_pattern = re.compile(fr"https?://{URL}?questions/[0-9]*/[a-z0-9-]*")
		links = link_pattern.findall(html)
		links = [_clean_google_link(link) for link in links]
		return links
		#正则匹配

def _extract_links_from_duckduckgo(html):
		html.remove_namespaces()
		links_anchors = html.find('a.result__a')
		results = []
		for anchor in links_anchors:
				link = anchor.attrib['href']
				url_obj = urlparse(link)
				parsed_url = parse_qs(url_obj.query).get('uddg', '')
				if parsed_url:
						results.append(parsed_url[0])
		return results
		
def _extract_links(html, search_engine):
		if search_engine == 'bing':
				return _extract_links_from_bing(html)
		if search_engine == 'duckduckgo':	
				return _extarct_links_from_duckduckgo(html)
		return _extract_links_from_google(html)

def _get_search_url(search_engine):
		return SEARCH_URLS.get(search_engine, SEARCH_URLS['google'])		

def _is_blocked(page):
		for indicator in BLOCK_INDICATORS:
				if page.find(indicator) != -1:
						return True
						
		return False				

def _get_links(query):
		search_engine = os.getnev('HOWDOI_SEARCH_ENGINE', 'google')
		search_url = _get_search_url(search_engine).format(URL, url_quote(query))
		logging.info('Searching %s with URL: %s', search_engine, search_url)
		try:
				result = _get_result(search_url)
		except requests.HTTPError:
				logging.info('Received HTTPError')
				result = None
		if not result or _is_blocked(result):
				html = pq(result)
				links = _extract_links(html, search_engine)
		if len(links) == 0:
				logging.info('Search engine %s found no StackOverflow links, return HTML is:', search_engine)
		return list(dict.fromkeys(links)) #利用dict取出重复项
		
def get_link_at_pos(links, position):
		if not links:
				return False
				
		if len(links) >= position:
				link = links[position - 1]
		else:
				link = links[-1]
		return link
		#1.links非空，False
		 2.超出范围请求，返回最后一个链接
		 
def _format_output(args, code):
		if not args['color']:
				return code
		lexer = None
		for keyword in args['query'].split() + args['tags']:
				try:
						lexer = get_lexer_by_name(keyword).name
						break
				except ClassNotFound:
						pass
						
		if not lexer:
				try:
						lexer = guess_lexer(code).name
				except ClassNotFound:
						return code
						
		syntax = Syntax(code, lexer, backgroud_color="default", line_numbers=False)
		console = Console(record=True)
		with console.captrue() as capture:
				console.print(syntax)
		return capture.get()
		#智能选择语法高亮器
		
def _is_question(link):
		for fragment in BLOCKED_QUESTION_FRAGMENT:
				if fragment in link:
						return False
		return re.search(r'question/\d+/', link)
		#过滤有效问题链接
		
def _get_questions(links):
		return [link for link in links if _is_question(link)]
		#列表推导式
		
def _get_answer(args, link):
		cache_key = _get_cache_key(link)
		page = _get_from_cache(cache_key)
		if not page:
				logging.info('Fetching page: %s', link)
				page = _get_result(link + '?answertab=votes')
				cache.set(cache_key, page)
		else:
				logging.info('Using cached page: %s', link)
				
		html = pq(page)
		
		first_answer = html('.answercell').eq(0) or html('.answer').eq(0)
		
		instructions = first_answer.find('pre') or first_answer.find('code')
		args['tags'] = [t.text for t in html('.post-tag')]
		
		if first_answer.find(".js-post-body"):
				answer_body_cls = ".js-post-body"
		else:
				answer_body_cls = ".post-text"
				
		if not instructions and not args['all']:
				logging.info('No code sample found, returning entire answer')
				text = get_text(first_answer.find(answer_body_cls).eq(0))
		elif args['all']:
				logging.info('Returning entire answer')
				texts = []
				for html_tag in first_answer.items(f'{answer-body_cls} > *'):
						current_text = get_text(html_tag)
						if current_text:
								if html_tag[0].tag in ['pre', 'code']:
										texts.append(_format_output(args, current_text))
								else:
										texts.append(current_text)
				text = '\n'.join(texts)
		else:
				text = _format_output(args, get_text(instructions.eq(0)))
				
		if text is None:
				logging.info('%sAnswer was empty%s', RED, END_FORMAT)
				text = NO_ANSWER_MSG
		text = text.strip()
		return text
		#放进缓存中——提升性能
		#日志记录
		
def _get_links_with_cache(query):
		cache_key = _get_cache_key(query)
		res = _get_from_cache(cache_key)
		if res:
				logging.info('Using cached links')
				if res == CACHE_EMPTY_VAL:
						logging.info('NO StackOverflow links found incached search engine results - will make live query')
				else:
						return res
				
		links = _get_links(query)
		if not links:
				cache.set(cache_key, CACHE_EMPTY_VAL)
				
		question_links = _get_question(links)
		cache.set(cache_key, question_links or CACHE_EMPTY_VAL)
		
		return question_links
		#2024.9.29 11:30
				
