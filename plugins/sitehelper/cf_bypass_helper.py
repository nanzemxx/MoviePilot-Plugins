"""
CloudFlare 绕过辅助工具
用于 sitehelper 插件绕过 CloudFlare 防护
借鉴 deepflood/nodeseek 插件的成功经验
"""
import random
import time
import requests
from typing import Optional, Dict, Any
from app.log import logger

# 尝试导入 cloudscraper
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except Exception:
    HAS_CLOUDSCRAPER = False

# 尝试导入 curl_cffi
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False


class CloudFlareBypassHelper:
    """CloudFlare 绕过辅助类,使用三层降级策略"""
    
    def __init__(self, proxies=None, verify_ssl=False):
        """
        初始化
        :param proxies: 代理配置
        :param verify_ssl: 是否验证SSL证书
        """
        self.proxies = self._normalize_proxies(proxies)
        self.verify_ssl = verify_ssl
        self._scraper = None
        
        # 初始化 cloudscraper
        if HAS_CLOUDSCRAPER:
            try:
                self._scraper = cloudscraper.create_scraper(browser="chrome")
                if self.proxies:
                    self._scraper.proxies = self.proxies
                logger.info("CloudFlare 绕过工具: cloudscraper 初始化成功")
            except Exception as e:
                logger.warning(f"cloudscraper 初始化失败: {str(e)}")
                self._scraper = None
    
    def smart_get(self, url, headers=None, cookies=None, timeout=30):
        """
        智能 GET 请求,三层降级策略
        1) cloudscraper (优先)
        2) curl_cffi (次选)
        3) requests (兜底)
        
        :param url: 请求URL
        :param headers: 请求头
        :param cookies: Cookie字典
        :param timeout: 超时时间
        :return: Response 对象
        """
        last_error = None
        
        # 第1层: cloudscraper
        if HAS_CLOUDSCRAPER and self._scraper:
            try:
                logger.info("使用 cloudscraper 发送 GET 请求")
                # 合并cookies到scraper
                if cookies:
                    for key, value in cookies.items():
                        self._scraper.cookies.set(key, value)
                
                resp = self._scraper.get(url, headers=headers, timeout=timeout, verify=self.verify_ssl)
                
                # 检查响应
                ct = resp.headers.get('Content-Type', '')
                if resp.status_code in (400, 403) or 'text/html' in ct.lower():
                    logger.info("cloudscraper 返回非预期,尝试 curl_cffi")
                else:
                    return resp
            except Exception as e:
                last_error = e
                logger.warning(f"cloudscraper GET 失败: {str(e)}")
        
        # 第2层: curl_cffi
        if HAS_CURL_CFFI:
            try:
                logger.info("使用 curl_cffi 发送 GET 请求 (Chrome-110 仿真)")
                session = curl_requests.Session(impersonate="chrome110")
                if self.proxies:
                    session.proxies = self.proxies
                
                resp = session.get(url, headers=headers, cookies=cookies, timeout=timeout, verify=self.verify_ssl)
                
                ct = resp.headers.get('Content-Type', '')
                if resp.status_code not in (400, 403) and 'text/html' not in ct.lower():
                    return resp
                else:
                    logger.info("curl_cffi 返回非预期,尝试 requests")
            except Exception as e:
                last_error = e
                logger.warning(f"curl_cffi GET 失败: {str(e)}")
        
        # 第3层: requests 兜底
        try:
            logger.info("使用 requests 发送 GET 请求")
            resp = requests.get(url, headers=headers, cookies=cookies, proxies=self.proxies,
                              timeout=timeout, verify=self.verify_ssl)
            return resp
        except Exception as e:
            logger.error(f"requests GET 失败: {str(e)}")
            if last_error:
                logger.error(f"之前的错误: {str(last_error)}")
            raise
    
    def smart_post(self, url, headers=None, data=None, json=None, cookies=None, timeout=30):
        """
        智能 POST 请求,三层降级策略
        
        :param url: 请求URL
        :param headers: 请求头
        :param data: POST数据
        :param json: JSON数据
        :param cookies: Cookie字典
        :param timeout: 超时时间
        :return: Response 对象
        """
        last_error = None
        
        # 第1层: cloudscraper
        if HAS_CLOUDSCRAPER and self._scraper:
            try:
                logger.info("使用 cloudscraper 发送 POST 请求")
                # 合并cookies
                if cookies:
                    for key, value in cookies.items():
                        self._scraper.cookies.set(key, value)
                
                resp = self._scraper.post(url, headers=headers, data=data, json=json,
                                         timeout=timeout, verify=self.verify_ssl)
                
                ct = resp.headers.get('Content-Type', '')
                if resp.status_code in (400, 403) or 'text/html' in ct.lower():
                    logger.info("cloudscraper 返回非预期,尝试 curl_cffi")
                else:
                    return resp
            except Exception as e:
                last_error = e
                logger.warning(f"cloudscraper POST 失败: {str(e)}")
        
        # 第2层: curl_cffi
        if HAS_CURL_CFFI:
            try:
                logger.info("使用 curl_cffi 发送 POST 请求 (Chrome-110 仿真)")
                session = curl_requests.Session(impersonate="chrome110")
                if self.proxies:
                    session.proxies = self.proxies
                
                resp = session.post(url, headers=headers, data=data, json=json,
                                   cookies=cookies, timeout=timeout, verify=self.verify_ssl)
                
                ct = resp.headers.get('Content-Type', '')
                if resp.status_code not in (400, 403) and 'text/html' not in ct.lower():
                    return resp
                else:
                    logger.info("curl_cffi 返回非预期,尝试 requests")
            except Exception as e:
                last_error = e
                logger.warning(f"curl_cffi POST 失败: {str(e)}")
        
        # 第3层: requests 兜底
        try:
            logger.info("使用 requests 发送 POST 请求")
            resp = requests.post(url, headers=headers, data=data, json=json,
                                cookies=cookies, proxies=self.proxies,
                                timeout=timeout, verify=self.verify_ssl)
            return resp
        except Exception as e:
            logger.error(f"requests POST 失败: {str(e)}")
            if last_error:
                logger.error(f"之前的错误: {str(last_error)}")
            raise
    
    def warmup_and_get(self, url, cookies=None, headers=None, timeout=30):
        """
        预热 + GET 请求,专门用于签到场景
        先访问首页建立信任,再访问目标页面
        
        :param url: 目标URL
        :param cookies: Cookie字典
        :param headers: 请求头
        :param timeout: 超时时间
        :return: Response 对象
        """
        if not (HAS_CLOUDSCRAPER and self._scraper):
            # 没有 cloudscraper,直接使用 smart_get
            return self.smart_get(url, headers, cookies, timeout)
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            home_url = f"{parsed.scheme}://{parsed.netloc}/"
            
            # 步骤1: 预热 - 访问首页
            logger.info(f"预热: 访问首页 {home_url}")
            self._scraper.get(home_url, timeout=timeout)
            
            # 步骤2: 注入用户 Cookie
            if cookies:
                for key, value in cookies.items():
                    self._scraper.cookies.set(key, value, domain=parsed.netloc)
                logger.info(f"已注入 {len(cookies)} 个 Cookie")
            
            # 步骤3: 访问目标页面
            logger.info(f"访问目标页面: {url}")
            resp = self._scraper.get(url, headers=headers, timeout=timeout, verify=self.verify_ssl)
            return resp
            
        except Exception as e:
            logger.warning(f"预热失败,降级到 smart_get: {str(e)}")
            return self.smart_get(url, headers, cookies, timeout)
    
    @staticmethod
    def _normalize_proxies(proxies_input):
        """
        归一化代理配置为 requests 兼容格式
        
        :param proxies_input: 代理配置 (字符串或字典)
        :return: 归一化后的代理字典
        """
        if not proxies_input:
            return None
        
        if isinstance(proxies_input, str):
            return {"http": proxies_input, "https": proxies_input}
        
        if isinstance(proxies_input, dict):
            http_url = proxies_input.get("http") or proxies_input.get("HTTP") or \
                      proxies_input.get("https") or proxies_input.get("HTTPS")
            https_url = proxies_input.get("https") or proxies_input.get("HTTPS") or \
                       proxies_input.get("http") or proxies_input.get("HTTP")
            
            if not http_url and not https_url:
                return None
            
            return {
                "http": http_url or https_url,
                "https": https_url or http_url
            }
        
        return None
