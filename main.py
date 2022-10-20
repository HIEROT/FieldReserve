# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import json
import random
import urllib3
import datetime
import itertools
import re
import cv2 as cv
import numpy as np
import keras
from collections import defaultdict
from t_ocr import predict_image
from time import sleep
from apscheduler.schedulers.blocking import BlockingScheduler

# Press the green button in the gutter to run the script.
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

    cnn_ocr = keras.models.load_model('./cnn_ocr_v1.h5')
    username = '2021310638'
    password = '@TOOSKYravendell@'
    way_to_pay = '1'  # 是线上支付， 线下支付是0
    attempt_num = 3  # 每个场各抢几次
    max_reserve = 2  # 至多抢几个场
    days_ahead = 3  # 提前几天
    # 羽毛球
    time_session = [['18:00-20:00', 4], ['18:00-19:00', 2], ['19:00-20:00', 2]]  # 数字为半小时的倍数
    field_no = ['06', '07', '08', '09', '05', '04', '03', '02', '11', '01', '12', '10']
    gym_code = '3998000'
    field_code = '4045681'
    code_name = '羽'
    cost_per_half_hour = 10
    # 乒乓球
    # time_session = [['8:00-10:00', 4], ['12:00-14:00', 4], ['18:00-20:00', 4]]  # 数字为半小时的倍数
    # field_no = ['6', '7', '8', '9', '5', '4', '3', '2', '1']
    # gym_code = '3998000'
    # field_code = '4037036'
    # code_name = '乒'
    # cost_per_half_hour = 5

    captcha_header = None
    reserve_header = None
    full_cookie = None
    time_diff = None
    field_time = None
    request_date = None
    pred = None
    http = None
    shed = BlockingScheduler()


    def Initializer():
        global full_cookie
        global time_diff
        global request_date
        global captcha_header
        global reserve_header
        global pred
        global http
        global shed
        global field_time

        combination = itertools.product(time_session, field_no)
        request_date = str(datetime.date.today() + datetime.timedelta(days=days_ahead))
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
        accurate_time = datetime.datetime(2022, 10, 20, 8, 0) + time_diff
        if not flag_running_now:
            if shed.get_job('reserve', 'default'):
                shed.reschedule_job('reserve', 'default', 'cron', hour=accurate_time.hour, minute=accurate_time.minute,
                                    second=accurate_time.second)
            else:
                shed.add_job(ReserveLoop, 'cron', hour=accurate_time.hour, minute=accurate_time.minute,
                             second=accurate_time.second,
                             id='reserve')
            print(shed.get_job('reserve', 'default'))
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
        # 登陆
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
        login_response = http.request('POST', 'https://50.tsinghua.edu.cn/j_spring_security_check',
                                      fields=login_load,
                                      headers=login_header,
                                      redirect=False,
                                      encode_multipart=False).data.decode()
        # 抢场地
        # 首先下载一下资源
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
            r"id:'([0-9]+)',time_session:'{}',field_name:'{}{}',overlaySize:'({})',can_net_book:'1'".format(
                i[0], code_name, j, i[1]) for i, j in combination]
        field_time = defaultdict(list)
        count = 0
        for p in pattern:
            res = re.search(p, cache)
            if res:
                idx = count // len(field_no)
                field_time[idx].append(('{}#{}'.format(res.group(1), request_date), res.group(2)))
            count = count + 1
        # 生成抢场组合
        if not len(field_time):
            shed.reschedule_job('reserve', 'default', 'cron', hour=0, minute=0,
                                second=0, month=1, day=1)
            print("今天没有符合要求的场")

        # if len(resource_id) == 1:
        #     field_time = ['{}#{}'.format(i, request_date) for i in resource_id[0]]
        # for idx in range(len(time_session) - 1):
        #     combination = itertools.product(resource_id[idx], resource_id[idx + 1])
        #     for i, j in combination:
        #         field_time.append('{}#{}, {}#{}'.format(i, request_date, j, request_date))

        # 下载验证码
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
        # 这里提前识别好验证码是为了保证第一个场的手速
        jpg_bytes = http.request('GET',
                                 'https://50.tsinghua.edu.cn/Kaptcha.jpg', headers=captcha_header).data
        imag = cv.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv.IMREAD_COLOR)
        imag = cv.resize(imag, (120, 30))
        imag = cv.cvtColor(imag, cv.COLOR_BGR2RGB)
        pred, _ = predict_image(cnn_ocr, imag)
        # cv.imshow(pred, imag)
        # while True:
        #     if cv.waitKey() == 27:
        #         break
        # cv.destroyAllWindows()


    def ReserveLoop():
        global http
        global pred
        global shed
        sleep(time_diff.microseconds / 1e6)  # 决不能在开场前就抢
        session_list = list(field_time.keys())
        field_reserved = 0
        for idx in range(attempt_num):
            # 订场
            for key in session_list:
                for f_t, overlay_size in field_time[key]:
                    # input("Press Enter to continue...")
                    reserve_load = {'bookData.totalCost': str(int(overlay_size) * cost_per_half_hour),
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

                    reserve_response = http.request('POST',
                                                    'https://50.tsinghua.edu.cn/gymbook/gymbook/gymBookAction.do?ms=saveGymBook',
                                                    fields=reserve_load,
                                                    headers=reserve_header,
                                                    redirect=False,
                                                    encode_multipart=False)
                    response_json = json.loads(reserve_response.data.decode('gbk'))
                    jpg_bytes = http.request('GET',
                                             'https://50.tsinghua.edu.cn/Kaptcha.jpg', headers=captcha_header).data
                    imag = cv.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv.IMREAD_COLOR)
                    imag = cv.resize(imag, (120, 30))
                    imag = cv.cvtColor(imag, cv.COLOR_BGR2RGB)
                    pred, _ = predict_image(cnn_ocr, imag)
                    # cv.imshow(pred, imag)
                    # while True:
                    #     if cv.waitKey() == 27:
                    #         break
                    # cv.destroyAllWindows()
                    print(response_json['msg'])
                    if re.match(r'预定成功', response_json['msg']):
                        field_reserved = field_reserved + 1
                        if field_reserved >= max_reserve:
                            return
                            # 抢够了
                        session_list.remove(key)
                        break
                        # 成功抢到一个，下一轮不再抢同一时间的场
                    elif re.match(r'预定失败：未到', response_json['msg']):  # TODO：确认返回消息，由于前面一定保证超过了八点，所以这里得等待一下
                        sleep(1)



        if not flag_running_now:
            acc_time = datetime.datetime(2022, 10, 20, 8, 0) + time_diff
            shed.reschedule_job('reserve', 'default', 'cron', hour=acc_time.hour, minute=acc_time.minute,
                                second=acc_time.second)
            print(shed.get_job('reserve', 'default'))


    if not flag_running_now:
        shed.add_job(Initializer, 'cron', day_of_week='sat,mon,wed', hour=7, minute=58, second=0)
        shed.start()
    else:
        Initializer()
        ReserveLoop()
