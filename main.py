# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import random
import sys
import time

import urllib3
import datetime
import itertools
import re
import numpy as np
import cv2 as cv
import tensorflow as tf
from collections import defaultdict
from t_ocr import predict_image
from time import sleep
from apscheduler.schedulers.blocking import BlockingScheduler
from goto import with_goto
from goto import goto, label


# Press the green button in the gutter to run the script.

def AccquireData():
    return
    filename = "气膜馆.json"
    tag_info = {
        "time_session": [
            "7:00-8:00",
            "8:00-9:00",
            "9:00-10:00",
            "10:00-11:00",
            "11:00-11:30",
            "11:30-13:00",
            "13:00-14:00",
            "14:00-15:00",
            "15:00-16:00",
            "16:00-17:00",
            "17:00-18:00",
            "18:00-19:00",
            "19:00-20:00",
            "20:00-22:00",
            "11:00-12:00",
            "12:00-14:00",
            "14:00-16:00",
            "16:00-18:00",
            "18:00-20:00",
            "8:00-10:00",
            "10:00-12:00"
        ],
        "field_no": [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12"
        ],
        "gym_code": "3998000",
        "field_code": "4045681",
        "code_name": "羽",
        "max_reserve": 2,
        "days_ahead": 0
    }
    filename = "西体.json"
    tag_info = {
        "time_session": [
            "7:00-8:00",
            "8:00-10:00",
            "10:00-12:00",
            "12:00-14:00",
            "14:00-16:00",
            "16:00-18:00",
            "18:30-20:30",
            "20:30-22:30",
            "18:00-20:00",
            "20:00-22:00"
        ],
        "field_no": [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8"
        ],
        "gym_code": "4836273",
        "field_code": "4836196",
        "code_name": "羽",
        "max_reserve": 1,
        "days_ahead": 1
    }
    filename = '综体.json'
    tag_info = {
        "time_session": [
            "8:00-10:00",
            "10:00-12:00",
            "12:00-14:00",
            "14:00-16:00",
            "16:00-18:00",
            "11:30-13:00",
            "15:00-17:00",
            "17:00-18:30",
            "18:30-20:30",
            "20:30-22:30",
            "18:00-20:00",
            "20:00-22:00"
        ],
        "field_no": [
            "6",
            "7",
            "8",
            "5",
            "4",
            "3",
            "2",
            "1",
            "9",
            "10"
        ],
        "gym_code": "4797914",
        "field_code": "4797899",
        "code_name": "羽",
        "max_reserve": 1,
        "days_ahead": 0
    }

    with open(filename, encoding='utf-8') as file:
        field_info = json.load(file)
    time_session = tag_info['time_session']
    field_no = tag_info['field_no']
    gym_code = tag_info['gym_code']
    field_code = tag_info['field_code']
    code_name = tag_info['code_name']
    combination = itertools.product(time_session, field_no)
    request_date = str(datetime.date.today() + datetime.timedelta(days=tag_info['days_ahead']))
    http = urllib3.PoolManager()

    # 下载一下资源
    get_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br', 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cookie': '',
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
        r"id:'(\d+)',time_session:'({})',field_name:'({}{})',overlaySize:'\d+',can_net_book:'1'".format(
            i, code_name, j) for i, j in combination]
    for p in pattern:
        res = re.search(p, cache)  # 先找场子
        if res:
            hash_code = re.search(
                r"resourcesm.put\('{}', '(\w+)'\)".format(res.group(1)),
                cache)
            cost_pattern = r"addCost\('{}','([0-9.]+)'\)".format(res.group(1))
            cost = re.search(cost_pattern, cache).group(1)
            field_info[res.group(2) + '#' + res.group(3)] = (hash_code.group(1), cost)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(field_info, file, ensure_ascii=False)


@with_goto
def ReserveLoop(single_field_dict, field_time):
    global num_reserved
    gym_code = single_field_dict['gym_code']
    field_code = single_field_dict['field_code']
    request_date = str(datetime.date.today() + datetime.timedelta(days=single_field_dict['days_ahead']))
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
    time_remain = reserve_time - current_time - 10
    if time_remain > 0 and not flag_running_now:
        sleep(time_remain)
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
                try:
                    response_json = json.loads(reserve_response.data.decode('gbk'))
                except json.JSONDecodeError:
                    jpg_bytes = http.request('GET',
                                             'https://50.tsinghua.edu.cn/Kaptcha.jpg', headers=captcha_header).data
                    pred = CaptchaIndentifier(jpg_bytes)
                    continue
                # toc = time.time()
                # print(toc - tic)
                jpg_bytes = http.request('GET',
                                         'https://50.tsinghua.edu.cn/Kaptcha.jpg', headers=captcha_header).data
                pred = CaptchaIndentifier(jpg_bytes)
                # tic = time.time()
                # print(tic - toc)
                print(response_json['msg'])
                if re.match(r'预定成功', response_json['msg']):
                    num_reserved += 1
                    if num_reserved >= single_field_dict['max_reserve']:
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
    print('Beging Running')
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
    code_name = single_field_dict['code_name']
    combination = itertools.product(time_session, field_no)
    request_date = str(datetime.date.today() + datetime.timedelta(days=single_field_dict['days_ahead']))

    pattern = [i + '#' + code_name + j for i, j in combination]

    with open(field_name + '.json', encoding='utf-8') as file:
        field_info = json.load(file)
    field_time = defaultdict(list)
    count = 0
    for p in pattern:
        if field_info.get(p):
            idx = count // len(field_no)
            field_time[idx].append(('{}#{}'.format(field_info[p][0], request_date), field_info[p][1]))
        count = count + 1
    # 生成抢场组合
    if not len(field_time):
        print("今天{}没有符合要求的场".format(field_name))
        return None
    return field_time


def CaptchaIndentifier(jpg_bytes):
    # tic = time.time()
    imag = cv.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv.IMREAD_COLOR)
    # toc = time.time()
    # print(toc - tic)
    imag = cv.resize(imag, (120, 30))
    # tic = time.time()
    # print(tic - toc)
    imag = cv.cvtColor(imag, cv.COLOR_BGR2RGB)
    # toc = time.time()
    # print(toc - tic)
    pred, _ = predict_image(cnn_ocr, imag)
    # tic = time.time()
    # print(tic - toc)
    # cv.imshow(pred, imag)
    # while True:
    #     if cv.waitKey() == 27:
    #         break
    # cv.destroyAllWindows()
    return pred


way_to_pay = '0'  # 是线上支付， 线下支付是0
attempt_num = 3  # 每个场各抢几次
flag_running_now = False
if __name__ == '__main__':
    '''
    import json
    with open('packages.json','r') as f:
        dic = json.load(f)
    newdic = {entry['name']:entry['value'] for entry in dic['log']['entries'][1]['request']['headers']}
    newdic2 = {entry['name']:entry['value'] for entry in dic['log']['entries'][1]['request']['postData']['params']}
    newdic3 = {entry['name']:entry['value'] for entry in dic['log']['entries'][1]['request']['queryString']}
    '''

    try:
        with open(sys.argv[1], encoding='utf-8') as f:
            print(f.name)
            reserve_dict: dict = json.load(f)
            if not reserve_dict['status']:
                sys.exit(0)
    except IndexError:
        print('需要场地配置json文件')
        sys.exit(1)

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
    cnn_ocr = tf.keras.models.load_model('./cnn_ocr_v1.h5')

    username = reserve_dict['username']
    password = reserve_dict['password']
    time_diff = datetime.timedelta()
    full_cookie = ''
    shed = BlockingScheduler()
    num_reserved = 0
    field_time_for_every_field = {}
    if not flag_running_now:
        shed.add_job(Preprations, 'cron', hour=7, minute=56, second=0)
        shed.start()
    else:
        Preprations()
