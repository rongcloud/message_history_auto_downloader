#! /usr/bin/env python
# coding=utf-8

import os
import re
import ConfigParser
sys.path.append('./')
import json
import time
import logging
import random
import datetime
import hashlib
import commands
commands.getoutput('easy_install requests')
import requests


class ConnectionError(Exception):
    def __init__(self, response, content=None, message=None):
        self.response = response
        self.content = content
        self.message = message

    def __str__(self):
        message = "Failed."
        if hasattr(self.response, 'status_code'):
            message += " Response status: %s." % (self.response.status_code)
        if hasattr(self.response, 'reason'):
            message += " Response message: %s." % (self.response.reason)
        if self.content is not None:
            message += " Error message: " + str(self.content)
        return message

class Redirection(ConnectionError):
    """3xx Redirection
    """
    def __str__(self):
        message = super(Redirection, self).__str__()
        if self.response.get('Location'):
            message = "%s => %s" % (message, self.response.get('Location'))
        return message

class MissingParam(TypeError):
    pass

class MissingConfig(Exception):
    pass

class ClientError(ConnectionError):
    """4xx Client Error
    """
    pass

class BadRequest(ClientError):
    """400 Bad Request
    """
    pass

class UnauthorizedAccess(ClientError):
    """401 Unauthorized
    """
    pass

class ForbiddenAccess(ClientError):
    """403 Forbidden
    """
    pass

class ResourceNotFound(ClientError):
    """404 Not Found
    """
    pass

class ResourceConflict(ClientError):
    """409 Conflict
    """
    pass

class ResourceGone(ClientError):
    """410 Gone
    """
    pass

class ResourceInvalid(ClientError):
    """422 Invalid
    """
    pass

class ServerError(ConnectionError):
    """5xx Server Error
    """
    pass

class MethodNotAllowed(ClientError):
    """405 Method Not Allowed
    """

    def allowed_methods(self):
        return self.response['Allow']

class ApiClient(object):
    api_host = "http://api.cn.ronghub.com"
    response_type = "json"
    message_url = ''

    ACTION_MESSAGE_HISTORY = '/message/history'

    def __init__(self, key=None, secret=None):
        self._app_key = key
        self._app_secret = secret

        if self._app_key is None:
            self._app_key = os.environ.get('rongcloud_app_key')
        if self._app_secret is None:
            self._app_secret = os.environ.get('rongcloud_app_secret')


    @staticmethod
    def _merge_dict(data, *override):
        result = {}
        for current_dict in (data,) + override:
            result.update(current_dict)
        return result

    @staticmethod
    def _join_url(url, *paths):
        for path in paths:
            url = re.sub(r'/?$', re.sub(r'^/?', '/', path), url)
        return url

    @staticmethod
    def _handle_response(response, content):
        """Validate HTTP response
        """
        status = response.status_code
        print status
        if status in (301, 302, 303, 307):
            raise Redirection(response, content)
        elif 200 <= status <= 299:
            return json.loads(content) if content else {}
        elif status == 400:
            raise BadRequest(response, content)
        elif status == 401:
            raise UnauthorizedAccess(response, content)
        elif status == 403:
            raise ForbiddenAccess(response, content)
        elif status == 404:
            raise ResourceNotFound(response, content)
        elif status == 405:
            raise MethodNotAllowed(response, content)
        elif status == 409:
            raise ResourceConflict(response, content)
        elif status == 410:
            raise ResourceGone(response, content)
        elif status == 422:
            raise ResourceInvalid(response, content)
        elif 401 <= status <= 499:
            raise ClientError(response, content)
        elif 500 <= status <= 599:
            raise ServerError(response, content)
        else:
            raise ConnectionError(response, content, "Unknown response code: #{response.code}")

    def _make_common_signature(self):

        """生成通用签名
        一般情况下，您不需要调用该方法
        文档详见 http://docs.rongcloud.cn/server.html#_API_调用签名规则
        :return: {'app-key':'xxx','nonce':'xxx','timestamp':'xxx','signature':'xxx'}
        """

        nonce = str(random.random())
        timestamp = str(
            int(time.time()) * 1000
        )

        signature = hashlib.sha1(
            self._app_secret + nonce + timestamp
        ).hexdigest()


        return {
            "rc-app-key": self._app_key,
            "rc-nonce": nonce,
            "rc-timestamp": timestamp,
            "rc-signature": signature
        }

    def _headers(self):
        """Default HTTP headers
        """
        return self._merge_dict(
            self._make_common_signature(),
            {
                "content-type": "application/x-www-form-urlencoded",
            }
        )

    def _http_call(self, url, method, **kwargs):
        """Makes a http call. Logs response information.
        """
        logging.info("Request[%s]: %s" % (method, url))
        start_time = datetime.datetime.now()

        response = requests.request(method,
                                    url,
                                    verify=False,
                                    **kwargs)
        duration = datetime.datetime.now() - start_time
        logging.info("Response[%d]: %s, Duration: %s.%ss." %
                     (response.status_code, response.reason,
                      duration.seconds, duration.microseconds))

        return self._handle_response(response,response.content.decode("utf-8"))
        print response.content.decode("utf-8")

    def call_api(self, action, params=None, **kwargs):
        """
        调用API的通用方法，有关SSL证书验证问题请参阅
        http://www.python-requests.org/en/latest/user/advanced/#ssl-cert-verification
        :param action: Method Name，
        :param params: Dictionary,form params for api.
        :param timeout: (optional) Float describing the timeout of the request.
        :return:
        """
        return self._http_call(
            url=self._join_url(self.api_host, "%s.%s" % (action, self.response_type)),
            method="POST",
            data=params,
            headers=self._headers(),
            **kwargs
        )

    def message_history(self, date):
        return self.call_api(
            action=self.ACTION_MESSAGE_HISTORY,
            params={
                "date": date,
            }
        )

def download_message(url):
    commands.getoutput('wget -c %s' % url)    


if __name__ == '__main__':

    date1 = str(int(time.strftime('%Y%m%d%H',time.localtime(time.time()))) - 3)
    api1 = ApiClient()
    json_value1 = api1.message_history(date1)
    message_url1 = json_value1["url"]
    print message_url1
    download_message(message_url1)

    date2 = str(int(time.strftime('%Y%m%d%H',time.localtime(time.time()))) - 2)
    api2 = ApiClient()
    json_value2 = api2.message_history(date2)
    message_url2 = json_value2["url"]
    print message_url2
    download_message(message_url2)
