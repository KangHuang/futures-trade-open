#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 15:48:13 2018

@author: zhaobo
"""

from HuobiDMService import HuobiDM
from pprint import pprint

#### input huobi dm url
URL = 'https://api.btcgateway.pro'

####  input your access_key and secret_key below:
ACCESS_KEY = '---'
SECRET_KEY = '---'

dm = HuobiDM(URL, ACCESS_KEY, SECRET_KEY)

#### another account:
# dm2 = HuobiDM(URL, "ANOTHER ACCOUNT's ACCESS_KEY", "ANOTHER ACCOUNT's SECRET_KEY")


# %%  market data api ===============

print (u' 获取市场价格 ')
priceInfo = dm.get_contract_trade(symbol="XRP_CQ")
pprint(priceInfo)

if priceInfo['status'] != "ok":
    print ("get price failed")
    exit(2)

currPrice = float(priceInfo['tick']['data'][0]['price'])
if currPrice is None or currPrice < 0:
    print("price invalid")
    exit(0)

print ("current price is %s" % currPrice)

step = currPrice / 100

print (u' 合约批量下单 ')

price = currPrice + step
# 分批下单做空
sell_order_datas = []
while price < currPrice + step * 10:
    order_data = {'symbol': 'XRP', 'contract_type': 'quarter',
                  'client_order_id': '',
                  'price': round(price, 4), 'volume': 3, 'direction': 'sell', 'offset': 'open',
                  'lever_rate': 20, 'order_price_type': 'limit'}
    sell_order_datas.append(order_data)
    price = price + step

result = dm.send_contract_batchorder({'orders_data': sell_order_datas})
if result['status'] == 'ok':
    print("open1 sell success")
    pprint(result)
else:
    print("open1 sell failed")
    pprint(result)

sell_order_datas = []
while price < currPrice + step * 20:
    order_data = {'symbol': 'XRP', 'contract_type': 'quarter',
                  'client_order_id': '',
                  'price': round(price, 4), 'volume': 3, 'direction': 'sell', 'offset': 'open',
                  'lever_rate': 20, 'order_price_type': 'limit'}
    sell_order_datas.append(order_data)
    price = price + 2 * step

result = dm.send_contract_batchorder({'orders_data': sell_order_datas})
if result['status'] == 'ok':
    print("open2 sell success")
    pprint(result)
else:
    print("open2 sell failed")
    pprint(result)

# sell_order_datas = []
# while price < currPrice + step * 45:
#     order_data = {'symbol': 'XRP', 'contract_type': 'quarter',
#                   'client_order_id': '',
#                   'price': round(price, 4), 'volume': 1, 'direction': 'sell', 'offset': 'open',
#                   'lever_rate': 20, 'order_price_type': 'limit'}
#     sell_order_datas.append(order_data)
#     price = price + step
#
# result = dm.send_contract_batchorder({'orders_data': sell_order_datas})
# if result['status'] == 'ok':
#     print("open3 sell success")
#     pprint(result)
# else:
#     print("open3 sell failed")
#     pprint(result)





# 分批下单做多
price = currPrice - step
buy_order_datas = []
while price > currPrice - step * 10:
    order_data = {'symbol': 'XRP', 'contract_type': 'quarter',
                  'client_order_id': '',
                  'price': round(price, 4), 'volume': 3, 'direction': 'buy', 'offset': 'open',
                  'lever_rate': 20, 'order_price_type': 'limit'}
    buy_order_datas.append(order_data)
    price = price - step

result = dm.send_contract_batchorder({'orders_data': buy_order_datas})
if result['status'] == 'ok':
    print("open1 buy success")
    pprint(result)
else:
    print("open1 buy failed")
    pprint(result)

buy_order_datas = []
while price > currPrice - step * 20:
    order_data = {'symbol': 'XRP', 'contract_type': 'quarter',
                  'client_order_id': '',
                  'price': round(price, 4), 'volume': 3, 'direction': 'buy', 'offset': 'open',
                  'lever_rate': 20, 'order_price_type': 'limit'}
    buy_order_datas.append(order_data)
    price = price - 2 * step

result = dm.send_contract_batchorder({'orders_data': buy_order_datas})
if result['status'] == 'ok':
    print("open2 buy success")
    pprint(result)
else:
    print("open2 buy failed")
    pprint(result)
#
# buy_order_datas = []
# while price > currPrice - step * 45:
#     order_data = {'symbol': 'XRP', 'contract_type': 'quarter',
#                   'client_order_id': '',
#                   'price': round(price, 4), 'volume': 1, 'direction': 'buy', 'offset': 'open',
#                   'lever_rate': 20, 'order_price_type': 'limit'}
#     buy_order_datas.append(order_data)
#     price = price - step
#
# result = dm.send_contract_batchorder({'orders_data': buy_order_datas})
# if result['status'] == 'ok':
#     print("open3 buy success")
#     pprint(result)
# else:
#     print("open3 buy failed")
#     pprint(result)