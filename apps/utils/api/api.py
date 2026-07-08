#!/usr/bin/env python
# coding: utf-8

import functools
import json
import logging

from django.http import HttpResponse, QueryDict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

logger = logging.getLogger("")


class APIError(Exception):
    def __init__(self, msg, err=None):
        self.err = err
        self.msg = msg
        super().__init__(err, msg)


class ContentType(object):
    json_request = "application/json"
    json_response = "application/json;charset=UTF-8"
    url_encoded_request = "application/x-www-form-urlencoded"
    binary_response = "application/octet-stream"


class JSONParser(object):
    content_type = ContentType.json_request

    @staticmethod
    def parse(body):
        return json.loads(body.decode("utf-8"))


class URLEncodedParser(object):
    content_type = ContentType.url_encoded_request

    @staticmethod
    def parse(body):
        return QueryDict(body)


class JSONResponse(object):
    content_type = ContentType.json_response

    @classmethod
    def response(cls, data):
        resp = HttpResponse(
            json.dumps(data, indent=4, ensure_ascii=False),
            content_type=cls.content_type,
        )
        resp.data = data
        return resp


class APIView(View):
    """
    Django view 的父类, 和 django-rest-framework 的用法基本一致
     - request.data 获取解析之后的 json 或者 url encoded 数据, dict 类型
     - self.success, self.error 和 self.invalid_serializer 可以根据业需求修改,
        写到父类中是为了不同的人开发写法统一,不再使用自己的 success/error 格式
     - self.response 返回一个 django HttpResponse, 具体在 self.response_class 中实现
     - parse 请求的类需要定义在 request_parser 中, 目前只支持 json 和 urlencoded 的类型, 用来解析请求的数据
    """

    request_parsers = (JSONParser, URLEncodedParser)
    response_class = JSONResponse

    def _get_request_data(self, request):
        if request.method not in ["GET", "DELETE"]:
            body = request.body
            content_type = request.META.get("CONTENT_TYPE")
            if not content_type:
                raise ValueError("content_type is required")
            for parser in self.request_parsers:
                if content_type.startswith(parser.content_type):
                    break
            # else means the for loop is not interrupted by break
            else:
                raise ValueError("unknown content_type '%s'" % content_type)
            if body:
                return parser.parse(body)
            return {}
        return request.GET

    def response(self, data):
        return self.response_class.response(data)

    def success(self, data=None):
        return self.response({"error": None, "data": data})

    def error(self, msg="error", err="error"):
        return self.response({"error": err, "data": msg})

    def extract_errors(self, errors, key="field"):
        if isinstance(errors, dict):
            if not errors:
                return key, "Invalid field"
            key = list(errors.keys())[0]
            return self.extract_errors(errors.pop(key), key)
        elif isinstance(errors, list):
            return self.extract_errors(errors[0], key)

        return key, errors

    def invalid_serializer(self, serializer):
        key, error = self.extract_errors(serializer.errors)
        if key == "non_field_errors":
            msg = error
        else:
            msg = "{}: {}".format(key, error)
        return self.error(err="invalid-{}".format(key), msg=msg)

    def server_error(self):
        return self.error(err="server-error", msg="server error")

    def paginate_data(self, request, query_set, object_serializer=None, pagination=True):
        """自定义的 分页 函数，响应
        :param request: django 的 request
        :param query_set: django model 的 query set 或者其他 list like objects
        :param object_serializer: 用来序列化 query set, 如果为 None, 则直接对 query set 切片
        :param pagination: 用来判断是否需要将返回数据按id排序
        """
        try:
            limit = int(request.GET.get("limit", "10"))
        except ValueError:
            limit = 10
        if limit < 0 or limit > 250:
            limit = 10
        try:
            offset = int(request.GET.get("offset", "0"))
        except ValueError:
            offset = 0
        if offset < 0:
            offset = 0

        if pagination:
            results = query_set[offset: offset + limit]
        else:
            results = query_set

        if object_serializer:
            try:
                count = query_set.count()
            except TypeError:
                count = len(query_set)
            results = object_serializer(results, many=True).data
        elif isinstance(query_set, list):
            count = len(query_set)
        else:
            count = query_set.count()
        if not results and offset!=0:
            pagedata_isnull = True
        else:
            pagedata_isnull = False
        data = {"results": results, "total": count, "pagedata_isnull": pagedata_isnull}
        return data

    def dispatch(self, request, *args, **kwargs):
        if self.request_parsers:
            try:
                request.data = self._get_request_data(self.request)
            except ValueError as e:
                return self.error(err="invalid-request", msg=str(e))
        try:
            return super(APIView, self).dispatch(request, *args, **kwargs)
        except APIError as e:
            ret = {"msg": e.msg}
            if e.err:
                ret["err"] = e.err
            return self.error(**ret)
        except Exception as e:
            logger.exception(e)
            return self.server_error()


class CSRFExemptAPIView(APIView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CSRFExemptAPIView, self).dispatch(request, *args, **kwargs)


def validate_serializer(serializer):
    """
    使用装饰器对 view 中的 serializer 做检查，检查通过后，设定 serializer
    使用方法：
        @validate_serializer(TestSerializer)
        def post(self, request):
            return self.success(request.data)
    """

    def validate(view_method):
        @functools.wraps(view_method)
        def handle(*args, **kwargs):
            self = args[0]
            request = args[1]
            s = serializer(data=request.data)
            # 实例化serializer，校验请求数据是否符合设定
            if s.is_valid():
                request.data = s.data
                request.serializer = s
                return view_method(*args, **kwargs)
            else:
                # return args[0].invalid_serializer(s)
                return self.invalid_serializer(s)  # 改为上面的只是为了简单的不报错

        return handle

    return validate
