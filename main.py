# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import random
import time

import urllib3
import datetime
import itertools
import re
import numpy as np
import cv2 as cv
import keras
import tensorflow as tf
from collections import defaultdict
from t_ocr import predict_image
from time import sleep
from apscheduler.schedulers.blocking import BlockingScheduler
from goto import with_goto
from goto import goto, label


# Press the green button in the gutter to run the script.

@with_goto
def ReserveLoop(single_field_dict, field_time):
    global num_reserved
    gym_code = single_field_dict['gym_code']
    field_code = single_field_dict['field_code']
    request_date = str(datetime.date.today() + datetime.timedelta(days=days_ahead))
    http = urllib3.PoolManager()
    reserve_header = {'accept': '*/*',
                      'accept-encoding': 'gzip, deflate, br',
                      'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                      'cookie': full_cookie,
                      'dnt': '1',
                      'origin': 'https://50.tsinghua.edu.cn',
                      'referer': 'https://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id={}&item_id={}&time_date={}&userType='.format(
                          gym_code, field_code, request_date),
                      'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                      'sec-ch-ua-mobile': '?0',
                      'sec-ch-ua-platform': '"Windows"',
                      'sec-fetch-dest': 'empty',
                      'sec-fetch-mode': 'cors',
                      'sec-fetch-site': 'same-origin',
                      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                      'x-requested-with': 'XMLHttpRequest'
                      }
    captcha_header = {'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                      'cookie': full_cookie,
                      'dnt': '1', 'origin': 'https://50.tsinghua.edu.cn',
                      'referer': 'https://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id={}&item_id={}&time_date={}&userType='.format(
                          gym_code, field_code, request_date),
                      'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                      'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty',
                      'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
                      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                      'x-requested-with': 'XMLHttpRequest'}
    jpg_bytes = http.request('GET',
                             'https://50.tsinghua.edu.cn/Kaptcha.jpg', headers=captcha_header).data
    pred = CaptchaIndentifier(jpg_bytes)
    session_list = list(field_time.keys())
    current_time = datetime.datetime.now().timestamp()
    reserve_time = (datetime.datetime.combine(datetime.date.today(), datetime.time(8, 0)) + time_diff).timestamp()
    time_remain = reserve_time - current_time - 3
    if time_remain > 0:
        sleep(time_remain)  # 决不能在开场前就抢
    print('服务器时间现为{}'.format(str(datetime.datetime.now() - time_diff)))
    for idx in range(attempt_num):
        # 订场
        for key in session_list:
            for f_t, cost in field_time[key]:
                label.begin_reserve
                # print(f_t)
                reserve_load = {'bookData.totalCost': cost,
                                'bookData.book_person_zjh': '',
                                'bookData.book_person_name': '',
                                'bookData.book_person_phone': '18175862019',
                                'gymnasium_idForCache': gym_code,
                                'item_idForCache': field_code,
                                'time_dateForCache': request_date,
                                'userTypeNumForCache': '1',
                                'code': pred,
                                'putongRes': 'putongRes',
                                'selectedPayWay': way_to_pay,
                                'allFieldTime': f_t}
                # tic = time.time()
                reserve_response = http.request('POST',
                                                'https://50.tsinghua.edu.cn/gymbook/gymbook/gymBookAction.do?ms=saveGymBook',
                                                fields=reserve_load,
                                                headers=reserve_header,
                                                redirect=False,
                                                encode_multipart=False)
                response_json = json.loads(reserve_response.data.decode('gbk'))
                # toc = time.time()
                # print(toc - tic)
                jpg_bytes = http.request('GET',
                                         'https://50.tsinghua.edu.cn/Kaptcha.jpg', headers=captcha_header).data
                pred = CaptchaIndentifier(jpg_bytes)
                tic = time.time()
                # print(tic - toc)
                print(response_json['msg'])
                if re.match(r'预定成功', response_json['msg']):
                    num_reserved += 1
                    if num_reserved >= max_reserve:
                        return
                        # 抢够了
                    session_list.remove(key)
                    break
                    # 成功抢到一个，下一轮不再抢同一时间的场
                elif re.match(r'预定失败：未到预约开放时间', response_json['msg']):
                    goto.begin_reserve
                elif re.match(r'预定失败：预约验证码错误', response_json['msg']):
                    goto.begin_reserve
                elif re.match(r'预定失败：场地已经被预定', response_json['msg']):
                    field_time[key].remove((f_t, cost))
                else:
                    pass


def Preprations():
    global time_diff
    global full_cookie
    global num_reserved
    global field_time_for_every_field
    http = urllib3.PoolManager()
    # 获取cookie
    cookie_request_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0', 'dnt': '1', 'referer': 'http://50.tsinghua.edu.cn/',
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"', 'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site', 'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    cookie_response = http.request_encode_url('POST', 'https://50.tsinghua.edu.cn/gymsite/cacheAction.do',
                                              fields={'ms': 'viewIndex'}, headers=cookie_request_header,
                                              redirect=False)
    GMT_format = '%a, %d %b %Y %H:%M:%S GMT'
    now_server = datetime.datetime.strptime(cookie_response.headers['date'], GMT_format)
    now_local = datetime.datetime.utcnow()
    time_diff = now_local - now_server
    cookie1 = cookie_response.headers['set-cookie'].split(';')[0]
    cookie_request_header = {'accept': '*/*',
                             'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                             'cookie': cookie1, 'dnt': '1',
                             'origin': 'https://50.tsinghua.edu.cn',
                             'referer': 'https://50.tsinghua.edu.cn/gymsite/cacheAction.do?ms=viewIndex',
                             'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                             'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty',
                             'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
                             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                             'x-requested-with': 'XMLHttpRequest'}
    cookie2 = http.request_encode_url('POST', 'https://50.tsinghua.edu.cn/front/frontAction.do',
                                      fields={'ms': 'getIndexVisitNum'}, headers=cookie_request_header,
                                      redirect=False).headers[
        'set-cookie'].split(';')[0]
    full_cookie = cookie2 + '; ' + cookie1
    # 登录
    login_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': full_cookie,
        'dnt': '1',
        'origin': 'https://50.tsinghua.edu.cn', 'referer': 'https://50.tsinghua.edu.cn/dl.jsp',
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    x = random.randint(51, 55)
    y = random.randint(13, 15)
    login_load = {
        'un': username,
        'pw': password,
        'x': str(x),
        'y': str(y)
    }
    http.request('POST', 'https://50.tsinghua.edu.cn/j_spring_security_check',
                 fields=login_load,
                 headers=login_header,
                 redirect=False,
                 encode_multipart=False)

    for key, page in reserve_dict.items():
        ret = ReserveInfoCapture(key, page)
        if ret is not None:
            field_time_for_every_field[key] = ret

    for key, field_time in field_time_for_every_field.items():
        ReserveLoop(reserve_dict[key], field_time)
    num_reserved = 0
    field_time_for_every_field = {}


def ReserveInfoCapture(field_name, single_field_dict):
    time_session = single_field_dict['time_session']
    field_no = single_field_dict['field_no']
    gym_code = single_field_dict['gym_code']
    field_code = single_field_dict['field_code']
    code_name = single_field_dict['code_name']
    combination = itertools.product(time_session, field_no)
    request_date = str(datetime.date.today() + datetime.timedelta(days=days_ahead))
    http = urllib3.PoolManager()

    # 下载一下资源
    get_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cookie': full_cookie,
        'dnt': '1',
        'referer': 'https://50.tsinghua.edu.cn/gymbook/gymBookAction.do?ms=viewGymBook&gymnasium_id={}&item_id={}&time_date={}&userType='.format(
            gym_code, field_code, request_date),
        'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'iframe',
        'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin', 'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
    get_load = {'ms': 'viewBook', 'gymnasium_id': gym_code, 'item_id': field_code, 'time_date': request_date,
                'userType': '1'}
    cache = http.request('GET',
                         'https://50.tsinghua.edu.cn/gymsite/cacheAction.do'.format(
                             request_date), fields=get_load, headers=get_header)
    cache = cache.data.decode('gbk')
    pattern = [
        r"id:'([0-9]+)',time_session:'{}',field_name:'{}{}',overlaySize:'[1-9]+',can_net_book:'1'".format(
            i, code_name, j) for i, j in combination]
    field_time = defaultdict(list)
    count = 0
    for p in pattern:
        res = re.search(p, cache)  # 先找场子
        if res:
            idx = count // len(field_no)
            cost_pattern = r"addCost\('{}','([0-9.]+)'\)".format(res.group(1))
            cost = re.search(cost_pattern, cache).group(1)
            field_time[idx].append(('{}#{}'.format(res.group(1), request_date), cost))
        count = count + 1
    # 生成抢场组合
    if not len(field_time):
        print("今天{}没有符合要求的场".format(field_name))
        return None
    return field_time


def CaptchaIndentifier(jpg_bytes):
    # 这里提前识别好验证码是为了保证第一个场的手速

    imag = cv.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv.IMREAD_COLOR)
    imag = cv.resize(imag, (120, 30))
    imag = cv.cvtColor(imag, cv.COLOR_BGR2RGB)
    pred, _ = predict_image(cnn_ocr, imag)
    # cv.imshow(pred, imag)
    # while True:
    #     if cv.waitKey() == 27:
    #         break
    # cv.destroyAllWindows()
    return pred


if __name__ == '__main__':
    '''
    import json
    with open('packages.json','r') as f:
        dic = json.load(f)
    newdic = {entry['name']:entry['value'] for entry in dic['log']['entries'][1]['request']['headers']}
    newdic2 = {entry['name']:entry['value'] for entry in dic['log']['entries'][1]['request']['postData']['params']}
    newdic3 = {entry['name']:entry['value'] for entry in dic['log']['entries'][1]['request']['queryString']}
    '''
    # 全局变量
    flag_running_now = False
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        # Restrict TensorFlow to only use the first GPU
        try:
            tf.config.set_visible_devices(gpus[0], 'GPU')
            tf.config.experimental.set_memory_growth(gpus[0], True)
            logical_gpus = tf.config.list_logical_devices('GPU')
            print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPU")
        except RuntimeError as e:
            # Visible devices must be set before GPUs have been initialized
            print(e)
    tf.keras.utils.disable_interactive_logging()
    cnn_ocr = keras.models.load_model('./cnn_ocr_v1.h5')
    username = '2021310638'
    password = '@TOOSKYravendell@'
    way_to_pay = '1'  # 是线上支付， 线下支付是0
    attempt_num = 1  # 每个场各抢几次
    max_reserve = 2  # 至多抢几个场
    days_ahead = 3  # 提前几天

    with open('ReserveInfo.json', encoding='utf-8') as f:
        reserve_dict: dict = json.load(f)
    # 乒乓球
    # time_session = [['8:00-10:00', 4], ['12:00-14:00', 4], ['18:00-20:00', 4]]  # 数字为半小时的倍数
    # field_no = ['6', '7', '8', '9', '5', '4', '3', '2', '1']
    # gym_code = '3998000'
    # field_code = '4037036'
    # code_name = '乒'
    # cost_per_half_hour = 5
    time_diff = datetime.timedelta()
    full_cookie = ''
    shed = BlockingScheduler()
    num_reserved = 0
    field_time_for_every_field = {}
    if not flag_running_now:
        shed.add_job(Preprations, 'cron', day_of_week='fri,sat,mon,wed', hour=7, minute=58, second=0)
        shed.start()
    else:
        Preprations()
