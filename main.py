import requests
from pprint import pprint
from os import sys
import yaml
import os
import argparse
import time
import json

# load config  
fileNamePath = os.path.split(os.path.realpath(__file__))[0]
yamlPath = os.path.join(fileNamePath,'config.yaml')
cf = yaml.load(open(yamlPath,'r',encoding='utf-8').read(),Loader=yaml.FullLoader)

# flagOptions > yaml
parser = argparse.ArgumentParser(usage=" option can coverage .yaml ", description="")
parser.add_argument("-f","--from", default=cf['From'], help="出发站", dest="sfrom")
parser.add_argument("-t","--to", default=cf['To'], help="到达站", dest="to")
parser.add_argument("-d","--date", default=cf['Date'], help="订票日期", dest="date")
parser.add_argument("-lbt","--lbt", default=cf['Customization']['LatestBusTime'], help="最晚开车时间", dest="lbt")
parser.add_argument("-lst","--lst", default=cf['Customization']['LatestShipTime'], help="最晚开船时间", dest="lst")
parser.add_argument("-mst","--mst", default=cf['Customization']['MinShipTime'], help="最早开船时间", dest="mst")
parser.add_argument("-line","--line", default=cf['Customization']['LineNum'], help="指定航班", dest="line")
parser.add_argument("-class","--class", default=cf['Customization']['Class'], help="指定舱位", dest="className")
args = parser.parse_args()

account = {
        'phoneNum': cf['User']['mobile'],
        'passwd': cf['User']['password'],
        'authentication': cf['User']['authentication'],
        'passengers': [],
        'seatNeed': 0,
    }

def notice(sss):
    if cf['Notice']['flag'] is False:
        return
    pyload = {"msgtype": "text", "text": {"content":json.dumps(sss,sort_keys=True, indent=2).encode('utf-8').decode('unicode_escape')}}
    requests.post(cf['Notice']['companyWx'], data=json.dumps(pyload),headers={"Content-Type": "application/json; charset=UTF-8"})
# notice("script running  ")
code = 0
errors = 0
tryTimes = 0
login_res = requests.post('https://www.ssky123.com/api/v2/user/passLogin?phoneNum=' + account['phoneNum'] + '&passwd=' + account['passwd'] + '&deviceType=2').json()
passengers = account['passengers']
userid = login_res['data']['userId']
token = login_res['data']['token']
while code != 200 and errors<3: 
    tryTimes+=1
    if tryTimes%100==0:#刷新token
        login_res = requests.post('https://www.ssky123.com/api/v2/user/passLogin?phoneNum=' + account['phoneNum'] + '&passwd=' + account['passwd'] + '&deviceType=2').json()
        token = login_res['data']['token']
    # time.sleep(1)
    print('... ....')

    # print('===================Login Info============================')
    

    def chekcToken():
        requests.get('https://www.ssky123.com/api/v2/user/tokenCheck', headers={'authentication': account['authentication'], 'token': token}).json()
        return

    def get(url, params={}):
        chekcToken()
        res = requests.get(url, headers={'authentication': account['authentication'], 'token': token}, params=params).json()
        return res

    def post(url, params={}):
        chekcToken()
        res =  requests.post(url, headers={'authentication': account['authentication'], 'token': token}, json=params).json()
        return res

    def getPassengers():
        res = get("https://www.ssky123.com/api/v2/user/passenger/list",None)
        for passer in res['data'][::1]:
            if len(cf['User']['passengers'])>0 and passer['passName'] not in cf['User']['passengers']:
                continue
            account['passengers'].append({
                'passName':passer['passName'],
                'passId':passer['id'],
                'credentialType':passer['passType'],
            })
            account['seatNeed']+=1

    def checkSeat(s):
        if args.className!='' and s['className']==args.className:
            return False
        
        if s['pubCurrentCount'] >= 1:
            return True
        return False

    query_ticket_res = post('https://www.ssky123.com/api/v2/line/ship/enq',
                            {
                                'startPortNo': cf['PortNo'][args.sfrom],
                                'endPortNo': cf['PortNo'][args.to],
                                'startDate': args.date
                            })
    route = None
    for tr in query_ticket_res['data'][::-1]:
        # chekc route
        if args.lbt!="" and tr['busStartTime']!="" and tr['busStartTime']>args.lbt:
            continue
        if args.lst!="" and tr['sailTime']!="" and tr['sailTime']>args.lst:
            continue
        if args.mst!="" and tr['sailTime']!="" and tr['sailTime']<args.mst:
            continue
        if args.line!='' and (tr['lineNum']+tr['sx'])!=args.line:
            continue
        ii = 0
        for s in tr['seatClasses'][::-1]:
            # notice localCurrentCount>0 but pubCurrentCount=0 
            if s['localCurrentCount'] >= 1:
                print(tr['lineNum'],tr['sx'],'>localCurrentCount:',s['localCurrentCount'],'>className:',s['className'],'>pubCurrentCount:',s['pubCurrentCount'])
            if checkSeat(s) is True:
                seatIndex = ii
                route = tr
                break
            ii+=1
        if route is not None:
            break

    if route is not None:
        print('===================Route Info============================')
        pprint(route)
        notice(route)
        seat = route['seatClasses'][seatIndex]
        print('===================Seat Info============================')
        pprint(seat)
        notice(seat)
        getPassengers()
        orderItemRequests = []
        for p in passengers:
            p['seatClassName'] = seat['className']
            p['seatClass'] = seat['classNum']
            p['freeChildCount'] = 0
            p['realFee'] = seat['totalPrice']
            p['ticketFee'] = seat['totalPrice']
            orderItemRequests.append(p)

        order = route
        order['orderItemRequests'] = orderItemRequests
        order['userId'] = userid
        order['contactNum'] = account['phoneNum']
        order['totalFee'] = seat['totalPrice'] * len(passengers)
        order['totalPayFee'] = seat['totalPrice'] * len(passengers)
        order['sailDate'] = args.date
        res = post('https://www.ssky123.com/api/v2/holding/save', order)
        code = res['code']
        pprint(res)
        notice(res)
        print(time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime()))
        if code !=200 and code!=300:
            errors+=1
            break



