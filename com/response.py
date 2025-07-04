from enum import Enum
import json
class Status(Enum):
    SUCCESS = 200
    BAD_REQUEST = 400   # 请求无效，服务器无法理解。
    UNAUTHORIZED = 401  # 请求未授权，需要认证信息
    FORBIDDEN = 403     # 请求未授权，需要认证信息
    NOT_FOUND = 404     # 请求未授权，需要认证信息
    UNDEFINED = 500

def to_json(status: Status = Status.SUCCESS, msg: str = None, data: dict = None) -> str:
    response_dict = dict()
    response_dict['code'] = status.value
    if msg is None:
        if status == Status.SUCCESS:
            response_dict['message'] = 'Success'
        elif status == Status.BAD_REQUEST:
            response_dict['message'] = 'Bad Request'
        elif status == Status.UNAUTHORIZED:
            response_dict['message'] = 'Unauthorized'
        elif status == Status.FORBIDDEN:
            response_dict['message'] = 'Forbidden'
        elif status == Status.NOT_FOUND:
            response_dict['message'] = 'Not Found'
        elif status == Status.UNDEFINED:
            response_dict['message'] = 'Undefined'
        elif status == Status.UNAUTHORIZED:
            response_dict['message'] = 'Unauthorized'
    else:
        response_dict['message'] = msg
    if data is not None:
        response_dict['data'] = data
    else:
        response_dict['data'] = {}
    return json.dumps(response_dict)
