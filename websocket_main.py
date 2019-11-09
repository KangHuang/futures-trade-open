# coding=utf-8
import json
import zlib
import time
import websocket
import base64
import hmac
import hashlib
import glob
import configparser
import logging
from urllib import parse
from datetime import datetime
from HuobiDMService import HuobiDM

# 从配置文件中获取初始化参数
__iniFilePath = glob.glob("params.ini")
cfg = configparser.ConfigParser()
cfg.read(__iniFilePath, encoding='utf-8')
accessKey = cfg.get('ws', 'accessKey')
secretKey = cfg.get('ws', 'secretKey')

protocol = cfg.get('ws', 'protocol')
_host = cfg.get('ws', '_host')
path = cfg.get('ws', 'path')

apiUrl = 'https://api.btcgateway.pro'

logger = logging.getLogger("sub")
fh = logging.FileHandler("subscribe.log")
logger.setLevel(logging.INFO)
logger.addHandler(fh)

step = 0.3 / 100  #网格大小

# 组建获取请求的url
url = protocol + _host + path

dm = HuobiDM(apiUrl, accessKey, secretKey)


class Message:

    # 鉴权信息
    def _auth(self, auth):
        # 获取需要签名的信息
        authenticaton_data = auth[1]

        # 获取 secretkey
        _accessKeySecret = auth[0]
        # 计算签名Signature
        authenticaton_data['Signature'] = _sign(authenticaton_data, _accessKeySecret)
        print(authenticaton_data)
        return json.dumps(authenticaton_data)

    # 发送sub请求
    def sub_padding(self, ws, message, data=None, totalcount=None):
        # 接收服务器的数据  进行解压操作
        ws_result = str(zlib.decompressobj(31).decompress(message), encoding="utf-8")
        js_result = json.loads(ws_result)
        # ss = (int(round(time.time() * 1000)) - js_result['ts'])
        # TODO 自定义打印服务器传回的信息
        # print('接收服务器数据为 ：%s' % ws_result)

        if totalcount < 1:
            for k in data:
                print('向服务器发送订阅 :%s' % k)
                ws.send(json.dumps(k))

        # 维持ping pong
        ping_id = json.loads(ws_result).get('ts')
        if 'ping' in ws_result:
            pong_data = '{"op":"pong","ts": %s}' % ping_id
            ws.send(pong_data)
            # print('向服务器发送pong :%s' % pong_data)

        elif js_result['op'] == "notify":
            self.process_sub_msg(js_result)

    # 发送req请求
    def req(self, ws, message, data, totalcount):
        # 接收服务器的数据  进行解压操作
        ws_result = str(zlib.decompressobj(31).decompress(message), encoding="utf-8")
        # TODO 自定义打印服务器传回的信息
        print('服务器响应数据%s' % ws_result)
        print(time.time())
        if totalcount < 1:
            print('向服务器发送数据1%s' % data)
            ws.send(json.dumps(data))
        ping_id = json.loads(ws_result).get('ts')
        # 维持ping pong
        if 'ping' in ws_result:
            pong_data = '{"op":"pong","ts": %s}' % ping_id
            ws.send(pong_data)
            print('向服务器发送pong :%s' % pong_data)

    def process_sub_msg(self, message):

        logger.info("start processing order msg")
        if message['order_type'] != 1:
            return

        if message['status'] != 4 and message['status'] != 6:
            return

        logger.info("receive valid msg:"+json.dumps(message))

        symbol = message['symbol']
        contract_type = message['contract_type']
        volume = message['trade_volume']
        trade_price = message['trade_avg_price']
        direction = message['direction']
        offset = message['offset']
        lever_rate = message['lever_rate']

        if offset == 'open' and direction == 'buy':
            new_offset = 'close'
            new_dir = 'sell'
            new_price = trade_price + step

        elif offset == 'open' and direction == 'sell':
            new_offset = 'close'
            new_dir = 'buy'
            new_price = trade_price - step

        elif offset == 'close' and direction == 'buy':
            new_offset = 'open'
            new_dir = 'sell'
            new_price = trade_price + step

        elif offset == 'close' and direction == 'sell':
            new_offset = 'open'
            new_dir = 'buy'
            new_price = trade_price - step

        else:
            logger.info("offset and type not match")
            return

        result = dm.send_contract_order(symbol=symbol, contract_type=contract_type, contract_code='', client_order_id='',
                                        price=round(new_price, 4), volume=volume, direction=new_dir, offset=new_offset,
                                        lever_rate=lever_rate, order_price_type='limit')

        now_time = get_now_time()
        if result['status'] == 'ok':
            logger.info("new order placed")
        else:
            logger.info(now_time + " order place failed:" + result['err-msg'] + "," + result['err-msg'])


# websocket
class websockClient():

    def __init__(self):
        self.req_ws = None
        self.instance_id = ''
        self.count = 0
        self.totalcount = 0
        self.func = None
        self._auth = None

    # 接收消息
    def on_message(self, ws, message):
        self.req_ws = ws
        # TODO 接收消息自定义处理
        MSG = Message()
        # 初始化传入的sub 获取 req函数
        if self.func:
            hasattr(self, self.func)
            func = getattr(MSG, self.func)
            # 调用传入的sub_padding或者是req函数
            func(ws, message, data=self.data, totalcount=self.totalcount)
            self.totalcount += 1

    # 发生错误
    def on_error(self, ws, error):
        # TODO 填写因发送异常，连接断开的处理操作
        print("error occur, exitng")
        print(ws.on_error.__dict__)
        exit(0)

    # 连接断开
    def on_close(self, ws):
        # TODO 填写连接断开的处理操作
        logger.error("### closed ###")
        exit(0)

    # 发送数据
    def send_auth_data(self):
        # 发送信息操作
        _auth = Message()._auth(self._auth)
        return _auth

    # 建立连接
    def on_open(self, ws):
        # 建连发送auth
        logger.info("conn open")
        def run(*args):
            ws.send(self.send_auth_data())
            time.sleep(1)

        run()

    def start_websocket(self, func, data, authdata):
        # 调用的函数
        self.func = func
        # 发送服务器的数据
        self.data = data
        # 鉴权数据
        self._auth = authdata
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        ws.run_forever()

    def get_ws(self):
        return self.req_ws


# 计算鉴权签名
def _sign(param=None, _accessKeySecret=None):
    # 签名参数:
    params = {}
    params['SignatureMethod'] = param.get('SignatureMethod') if type(param.get('SignatureMethod')) == type(
        'a') else '' if param.get('SignatureMethod') else ''
    params['SignatureVersion'] = param.get('SignatureVersion') if type(param.get('SignatureVersion')) == type(
        'a') else '' if param.get('SignatureVersion') else ''
    params['AccessKeyId'] = param.get('AccessKeyId') if type(param.get('AccessKeyId')) == type(
        'a') else '' if param.get('AccessKeyId') else ''
    params['Timestamp'] = param.get('Timestamp') if type(param.get('Timestamp')) == type('a') else '' if param.get(
        'Timestamp') else ''
    print(params)
    # 对参数进行排序:
    keys = sorted(params.keys())
    # 加入&
    qs = '&'.join(['%s=%s' % (key, _encode(params[key])) for key in keys])
    # 请求方法，域名，路径，参数 后加入`\n`
    payload = '%s\n%s\n%s\n%s' % ('GET', _host, path, qs)
    dig = hmac.new(_accessKeySecret, msg=payload.encode('utf-8'), digestmod=hashlib.sha256).digest()
    # 进行base64编码
    return base64.b64encode(dig).decode()


# 获取UTC时间
def _utc():
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')


# 进行编码
def _encode(s):
    # return urllib.pathname2url(s)
    return parse.quote(s, safe='')


# 获取当前时间
def get_now_time():
    timestamp = int(time.time())
    time_local = time.localtime(timestamp)
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return now_time


# 发送的authData数据
authdata = [
    secretKey.encode('utf-8'),
    {
        "op": "auth",
        "type": "api",
        "AccessKeyId": accessKey,
        "SignatureMethod": "HmacSHA256",
        "SignatureVersion": "2",
        "Timestamp": _utc()
    }
]

# TODO sub订阅参数 可填写多个请求以数组形式添加
datasymbols = [
    {
        "op": "sub",
        "cid": "40sG903yz80oDFWr",
        "topic": "orders.xrp"
    }
]

#
# TODO req查询参数数组 accounts.list , orders.detail , orders.list
datareq = [
    {
        "op": "req",
        "topic": "accounts.list",
        "cid": 'sfdsfsfdsf'
    },
    {
        "op": "req",
        "topic": "orders.detail",
        'cid': '40sdfkajs',
        "order-id": '1543924'
    },
    {
        "op": "req",
        "topic": "orders.list",
        "cid": '32sdfsawa',
        "account-id": 18580,
        "symbol": 'ethusdt',
        "types": "",
        "start-date": "",
        "end-date": "",
        "states": "submitted,filled,partial-canceled,partial-filled,canceled",
        "from": "1543875",
        "direct": "next",
        "size": '200'
    }
]

# TODO 发送req请求
# websockClient().start_websocket(func='req' ,data=datareq[2],authdata=authdata)
# websockClient().start_websocket(func='req',data=datareq[1],authdata=authdata)
# websockClient().start_websocket(func='req',data=datareq[0],authdata=authdata)


# TODO 发送sub 订阅或取消订阅
websockClient().start_websocket(func='sub_padding', data=datasymbols, authdata=authdata)
