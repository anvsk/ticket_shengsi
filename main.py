import requests
from pprint import pprint
from os import sys

startDate = '2021-05-01'
startDateAgr = sys.argv[1]
if startDateAgr !='1':
    startDate = startDateAgr
print(startDate)
print()

# 南浦 1046
# 枸杞岛 1017
# 嵊山岛 1016
# 嵊泗本岛 1010
# 花鸟 1014
start_port_no = '1046'
end_port_no = '1017'
myline = sys.argv[2]
if myline =="shengsi":
    start_port_no = '1046'
    end_port_no = '1010'
if myline =="shengshan":
    start_port_no = '1046'
    end_port_no = '1016'
if myline =="gouqi":
    start_port_no = '1046'
    end_port_no = '1017'
if myline =="huaniao":
    start_port_no = '1046'
    end_port_no = '1014'

phone_number = '18502177889'
passwd = 'an666777'
# authentication 需要在你登录网站之后的报文里面找，不会变
authentication = '1619682562339839'

# 汽车最晚时间[车船联票时要用到]
latest_bus_time='13:00'

accounts = [
    {
        'phoneNum': phone_number,
        'passwd': passwd,
        'authentication': authentication,
        'passengers': [
            # passId 是乘客的 Id，在报文里面可以找到、在乘车人页面的接口返回可以看到
            {'passName': '邓平安', 'credentialType': 1, 'passId': 1731062},
            # {'passName': '某某某', 'credentialType': 1, 'passId': 222},
        ],
        'seatNeed': 1,
    },
]

for account in accounts:
    code = 0
    while code != 200:
        print('... ....')
        login_res = requests.post('https://www.ssky123.com/api/v2/user/passLogin?phoneNum=' + account['phoneNum'] + '&passwd=' + account['passwd'] + '&deviceType=2').json()
        passengers = account['passengers']

        # print('===================Login Info============================')
        # print(login_res)
        userid = login_res['data']['userId']
        token = login_res['data']['token']

        def get(url, params={}):
            # print('GET to', url)
            requests.get('https://www.ssky123.com/api/v2/user/tokenCheck', headers={'authentication': authentication, 'token': token}).json()
            res = requests.get(url, headers={'authentication': account['authentication'], 'token': token}, params=params).json()
            # print('Response :', res)
            print()
            return res

        def post(url, params={}):
            # print('GET to', url)
            requests.get('https://www.ssky123.com/api/v2/user/tokenCheck', headers={'authentication': authentication, 'token': token}).json()
            res =  requests.post(url, headers={'authentication': account['authentication'], 'token': token}, json=params).json()
            # print('Response :', res)
            print()
            return res

        # print('===================Route Info============================')
        # token_check_res = get('https://www.ssky123.com/api/v2/user/tokenCheck')
        query_ticket_res = post('https://www.ssky123.com/api/v2/line/ship/enq',
                                {
                                    'startPortNo': start_port_no,
                                    'endPortNo': end_port_no,
                                    'startDate': startDate
                                })

        route = None
        for tr in query_ticket_res['data'][::-1]:
            # chekc latest time
            if latest_bus_time!="" and tr['busStartTime']>latest_bus_time:
                continue
            for s in tr['seatClasses'][::-1]:
                if s['localCurrentCount'] >= account['seatNeed']:#打印本地人票数和对外票数
                    print(tr['lineNum'],tr['sx'],'>localCurrentCount:',s['localCurrentCount'],'>className:',s['className'],'>pubCurrentCount:',s['pubCurrentCount'])
                if s['pubCurrentCount'] >= account['seatNeed']:
                    route = tr
                    break
            if route is not None:
                break

        #  route = query_ticket_res['data'][0]
        # print('\nroute:\n')
        pprint(route)
        if route is not None:
            seat = None
            for s in route['seatClasses'][::-1]:
                if s['totalCount'] >= account['seatNeed']:
                    seat = s
            # print('===================Seat Info============================')
            print('\nseat:\n')
            if seat is not None:
                pprint("========seat-getting======")
                pprint(seat)
                # code = 200


                orderItemRequests = []
                for p in passengers:
                    p['seatClassName'] = seat['className']
                    p['seatClass'] = seat['classNum']
                    p['freeChildCount'] = 0
                    p['realFee'] = seat['totalPrice']
                    p['ticketFee'] = seat['totalPrice']
                    orderItemRequests.append(p)
                print('===================Order Info============================')
                # print(orderItemRequests)

                order = route
                order['orderItemRequests'] = orderItemRequests
                order['userId'] = userid
                order['contactNum'] = phone_number
                order['totalFee'] = seat['totalPrice'] * len(passengers)
                order['totalPayFee'] = seat['totalPrice'] * len(passengers)
                order['sailDate'] = startDate
                # pprint(order)
                res = post('https://www.ssky123.com/api/v2/holding/save', order)
                pprint(res)

                code = res['code']

                # post('https://www.ssky123.com/api/v2/user/loginOut')
