import os
import io,re
import time
import json
import requests
import datetime
from bs4 import BeautifulSoup

def fill(n):
    if n < 10:
        return f'0{n}'
    else:
        return n
def secchange(sec):
    intsec = int(sec)
    if intsec >= 3600:
        h = intsec // 3600
        m = (intsec % 3600) // 60
        s = (intsec % 3600) % 60
        h=f'{h}時間'
        m=f'{fill(m)}分' if m else ''
        s=f'{fill(s)}秒' if s else ''
        return h+m+s
    elif intsec >= 60:
        m = (intsec % 3600) // 60
        s = (intsec % 3600) % 60
        m=f'{m}分' if m else ''
        s=f'{fill(s)}秒' if s else ''
        return m+s
    else:
        s = (intsec % 3600) % 60
        s=f'{s}秒' if s else ''
        return s
def stringtime(text,intsec):
    if '時間' in text:
        hour=int(text.split('時間')[0])
        return stringtime(text.split('時間')[1],hour*3600+intsec)
    elif '分' in text:
        mins=int(text.split('分')[0])
        return stringtime(text.split('分')[1],mins*60+intsec)
    elif '秒' in text:
        sec=int(text.split('秒')[0])
        return sec+intsec
    else:
        return intsec
def traintime(fromstop,tostop,timestamp,offset,type='arrival'):
    typeitem={"departure":1,"final":2,"first":3,"arrival":4}
    fromstop=str(fromstop.encode('utf-8')).replace(r"\x","%").replace("'","")[1:]
    tostop=str(tostop.encode('utf-8')).replace(r"\x","%").replace("'","")[1:]
    thetime=str(timestamp+datetime.timedelta(minutes=offset))
    year,month,day,hour,mins=thetime[0:4],thetime[5:7],thetime[8:10],thetime[11:13],thetime[14:16]
    othertp=1
    url=f"https://transit.yahoo.co.jp/search/result?from={fromstop}&to={tostop}&fromgid=&togid=&flatlon=&tlatlon=&via=&viacode=&y={year}&m={month}&d={day}&hh={hour}&m1={mins[0]}&m2={mins[1]}&type={typeitem[type]}&ticket=ic&expkind=1&userpass=1&ws=1&s=0&al={othertp}&shin={othertp}&ex={othertp}&hb={othertp}&lb={othertp}&sr={othertp}&"
    useragent = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
    response = requests.get(url, headers=useragent)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    soupstring = str(soup)
    splitline = soupstring.splitlines()
    contentline=list()
    for i,line in enumerate(splitline):
        if "contents-footer" in line:
            infolist=line.split('{"summaryInfo":')
            for x,info in enumerate(infolist):
                if '"edgeInfoList":' in info:
                    featurelist=list()
                    summary=json.loads(info.split(',"edgeInfoList":')[0].split(',"calendarUrl":')[0]+'}')
                    departure=summary["departureTime"]
                    arrival=summary["arrivalTime"]
                    total=stringtime(summary["totalTime"],0)
                    transfer=summary["transferCount"]
                    price=int(summary["totalPrice"].replace(',',''))
                    summaryitem=dict(departure=departure,arrival=arrival,total=total,transfer=transfer,price=price)
                    info=info.split(',"edgeInfoList":')[1]
                    if '}],"registerInfoList":' in info:
                        content=json.loads(info.split('}],"registerInfoList":')[0].replace('}]},','}]'))
                    else:
                        newinfo=info.replace('}]},','}]')
                        try:
                            content=json.loads(newinfo)
                        except:
                            print(info)
                            print(info[-1])
                            print('error')
                            return
                    for stop in content:
                        station=stop['stationName']
                        rail=stop['railName'].replace('ＪＲ','JR').replace('東京メトロ','Metro').replace('中央・青梅線快速','中央線')
                        timelist=list()
                        for timei in stop["timeInfo"]:
                            timelist.append(timei["time"])
                        if stop["ridingPositionInfo"]:
                            departure=stop["ridingPositionInfo"]['departure'][0]
                            arrival=stop["ridingPositionInfo"]['arrival'][0]
                            position=stop["ridingPositionInfo"]['position'][0].split('[')[0] if stop["ridingPositionInfo"]['position'] else ''
                        else:
                            departure,arrival,position='','',''
                        if stop["priceInfo"]:                            
                            edge=stop["priceInfo"]["edgeGroup"] if stop["priceInfo"]["edgeGroup"] else ''
                            price=int(stop["priceInfo"]["price"].replace(',',''))
                        else:
                            edge,price='',0
                        featurelist.append(dict(station=station,rail=rail,time=timelist,departureline=departure,arrivalline=arrival,position=position,edge=edge,price=price))
                    contentline.append(dict(summary=summaryitem,route=featurelist))
    return contentline
def writetimeline(contentline: list):
    trainicon={'Metro東西':'Ⓜ️','JR中央':'🀄','JR総武':'🟨','JR山手':'🟩','JR埼京':'🗾','湘南新宿ライン':'🟧'}
    numberemoji=['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    writelist=list()
    for s,route in enumerate(contentline):
        content=contentline[s]['route']
        number=numberemoji[s+1] if s+1 < len(numberemoji) else s+1
        writelist.append(f"Route.{number} {route['summary']['departure']}→{route['summary']['arrival']} ({secchange(route['summary']['total'])}) trf:{route['summary']['transfer']} {route['summary']['price']}".replace(' 0',''))
        for c,stop in enumerate(content):
            rail=stop['rail'].replace('山手線外回り・池袋・上野方面','山手線外・池袋上野方面').replace('中央線快速','中央線')
            for key, value in trainicon.items():
                if key in rail:
                    rail=value+rail
                    break
            stop['rail']=rail
        for c,stop in enumerate(content):
            if c == 0:
                writelist.append(f"{stop['time'][0]}発 {stop['station']} {stop['departureline']} {stop['position']}".replace(' None',''))
                diff=(datetime.datetime.strptime(content[c+1]['time'][0],"%H:%M")-datetime.datetime.strptime(stop['time'][0],"%H:%M")).total_seconds()
                if stop['rail'] == '徒歩':
                    writelist.append(f"🚶‍♀️ {secchange(diff)} 乗り換え ({secchange(diff)}徒歩)")
                else:
                    writelist.append(f"⬇️{secchange(diff)} {stop['rail']}")
            elif c == len(content)-1:
                writelist.append(f"{stop['time'][0]}着 {stop['station']} {stop['arrivalline']}".replace(' None',''))
            else:
                if len(stop['time'])==2:
                    diff=(datetime.datetime.strptime(stop['time'][1],"%H:%M")-datetime.datetime.strptime(stop['time'][0],"%H:%M")).total_seconds()
                    diff=diff+86400 if diff < 0 else diff
                    transfericon='🏃‍♀️' if diff < 3 else '🚶‍♀️'
                    diff2=(datetime.datetime.strptime(content[c+1]['time'][0],"%H:%M")-datetime.datetime.strptime(stop['time'][1],"%H:%M")).total_seconds()
                    diff2=diff2+86400 if diff2 < 0 else diff2
                    if content[c-1]['rail'] == '徒歩':
                        originalsec=stringtime(writelist[-1].split(" ")[1],0)
                        if stop['rail'] == '徒歩':
                            walksec=stringtime(writelist[-1].split(" ")[3].replace("(","").replace("徒歩)",""),0)
                            writelist[-1] = f'🚶‍♀️ {secchange(originalsec+diff+diff2)} 乗り換え ({secchange(walksec+diff2)}徒歩)'
                        else:
                            writelist[-1] = f'🚶‍♀️ {secchange(originalsec+diff)} 乗り換え {writelist[-1].split(" ")[3]}'
                    else:
                        writelist.append(f"{stop['time'][0]}着 {stop['station']} {content[c-1]['arrivalline']}".replace('None',''))
                        if stop['rail'] != '徒歩':
                            writelist.append(f"{transfericon} {secchange(diff)} 乗り換え")
                    if stop['rail'] == '徒歩':
                        if content[c-1]['rail'] != '徒歩':
                            writelist.append(f"🚶‍♀️ {secchange(diff+diff2)} 乗り換え ({secchange(diff2)}徒歩)")
                    else:
                        writelist.append(f"{stop['time'][1]}発 {stop['station']} {stop['departureline']} {stop['position']}".replace(' None',''))
                        writelist.append(f"⬇️{secchange(diff2)} {stop['rail']}")
                else:
                    writelist.append(f"{stop['time'][0]}   {stop['station']}【乗換不要】{stop['rail']}")
                    diff=(datetime.datetime.strptime(content[c+1]['time'][0],"%H:%M")-datetime.datetime.strptime(stop['time'][0],"%H:%M")).total_seconds()
                    writelist.append('⬇️'+secchange(diff))
        writelist.append('')
    return writelist
def routeposition(contentline: list):
    routeitem,routeprice=dict(),list()
    for route in contentline:
        group=''
        lineset=set()
        for i in range(len(route['route'])-1):
            if route['route'][i]['position']:
                routename=route['route'][i]['station']+route['route'][i]['rail'].replace('ライン','線').split('線')[0]+route['route'][i+1]['station']+route['route'][i+1]['rail'].replace('ライン','線').split('線')[0]
                routeitem[routename]=route['route'][i]['position'] if routename not in routeitem else routeitem[routename]
        for s,stop in enumerate(route['route']):
            thisstop=re.sub(r'\([^)]*\)', '', stop['station']) if stop['rail'][:2] not in {'JR','Me'} else stop['station']
            if group == stop['edge']:
                lineset.add(stop['rail'][:2])
            elif group:
                found=False
                for item in routeprice:
                    if stopname+thisstop == item['name']:
                        found=True
                        if lineset not in item['line']:
                            item['line'].append(lineset)
                            break
                if not found:
                    routeprice.append(dict(name=stopname+thisstop,price=price,line=[lineset]))
                group = stop['edge']
                price = stop['price']
                lineset = set()
                lineset.add(stop['rail'][:2])
                stopname = thisstop
            elif s == 0:
                group = stop['edge']
                price = stop['price']
                lineset = set()
                lineset.add(stop['rail'][:2])
                stopname = thisstop
    return routeitem,routeprice
def newprice(contentline,routeprice):
    #print(routeprice)
    for route in contentline:
        if not route['summary']['price']:
            startstop=re.sub(r'\([^)]*\)', '', route['route'][0]['station']) if route['route'][0]['rail'][:2] not in {'JR','Me'} else route['route'][0]['station']
            starts=0
            lineset,edgeset=set(),set()
            totalprice=0
            for s,stop in enumerate(route['route']):
                thisstop=re.sub(r'\([^)]*\)', '', stop['station']) if stop['rail'][:2] not in {'JR','Me'} else stop['station']
                name=startstop+thisstop
                for item in routeprice:
                    if name == item['name']:
                        foundline=False
                        if len(edgeset) == 1 and '0_0' not in edgeset:
                            for line in item['line']:
                                for line2 in lineset:
                                    if line2 in line:
                                        foundline=True
                                        break
                                if foundline:
                                    break
                        else:
                            for line in item['line']:
                                if lineset <= line:
                                    foundline=True
                        if foundline:
                            totalprice+=item['price']
                        else:
                            group='0_0'
                            for i in range(starts,s):
                                if route['route'][i]['edge'] != group or route['route'][i]['edge'] == '0_0':
                                    group=route['route'][i]['edge']
                                    totalprice+=route['route'][i]['price']
                        startstop=thisstop
                        starts=s
                        lineset,edgeset=set(),set()
                        break
                lineset.add(stop['rail'][:2])
                edgeset.add(stop['edge'])
            route['summary']['price']=totalprice if totalprice else 0        
    return contentline
def fasterarrivaltime(fromstop,tostop,timestamp,offset):
    contentline=traintime(fromstop,tostop,timestamp,offset)
    timestamp2=datetime.datetime.strptime(str(timestamp)[:10]+' '+min([item['summary']['arrival'] for item in contentline]),'%Y-%m-%d %H:%M')
    contentline=contentline+traintime(fromstop,tostop,timestamp2,-1)
    contentline2=list()
    for r,route in enumerate(contentline):
        featurelist=list()
        for i,stop in enumerate(route['route']):
            if stop['edge'] or i == len(route['route'])-1:
                featurelist.append(stop)
        contentline2.append(dict(summary=route['summary'],route=featurelist))
    count=len(contentline2)
    stoplist,routeset=list(),set()
    trfoffset=2
    summaryset=set([','.join([str(value) for key,value in item['summary'].items()]) for item in contentline2])
    routeitem,routeprice=routeposition(contentline2)
    for r,route in enumerate(contentline2):
        if r == count:
            break
        stoplist=[stop['station'] for stop in route['route']]
        routename=''.join(stoplist)
        if len(stoplist) > 2 and routename not in routeset:
            routeset.add(routename)
            contentlistfinal=traintime(stoplist[-2],stoplist[-1],timestamp,offset)
            for item in contentlistfinal:
                summary,content=item['summary'],item['route']
                for i in range(len(stoplist)-2,0,-1):
                    newtimestamp=datetime.datetime.strptime(str(timestamp)[:10]+' '+summary['departure'],'%Y-%m-%d %H:%M')
                    contentlinetemp=traintime(stoplist[i-1],stoplist[i],newtimestamp,-trfoffset)
                    for contenttemp in contentlinetemp:
                        summarynew,contentnew=contenttemp['summary'],contenttemp['route']
                        diff=(datetime.datetime.strptime(summary['departure'],"%H:%M")-datetime.datetime.strptime(summarynew['arrival'],"%H:%M")).total_seconds()/60
                        diff=diff+1440 if diff < -600 else diff
                        routename=contentnew[-1]['station']+contentnew[-1]['rail'].replace('ライン','線').split('線')[0]+content[0]['station']+content[0]['rail'].replace('ライン','線').split('線')[0]
                        position=routeitem[routename] if routename in routeitem else ''
                        newoffset=trfoffset
                        if contentnew[-1]['rail'][:2] == content[0]['rail'][:2]:
                            plus=False
                            if position:
                                if position != '前/中/後':
                                    newoffset+=1
                                    plus=True
                            if not plus and contentnew[-1]['arrivalline'] and content[0]['departureline']:
                                try:
                                    linediff=abs(int(re.findall(r'\d+',contentnew[-1]['arrivalline'])[0])-int(re.findall(r'\d+',content[0]['departureline'])[0]))
                                    if linediff > 8:
                                        newoffset+=1
                                except:
                                    print('ERROR')
                                    print(contentnew[-1])
                                    return
                        else:
                            newoffset+=2
                            if contentnew[-1]['station'] in {'新宿','東京'}:
                                newoffset+=1
                                if '大江戸線' in content[0]['rail'] or '大江戸線' in contentnew[-1]['rail']:
                                    newoffset+=1
                            elif contentnew[-1]['station'] == '中野(東京都)':
                                newoffset-=2
                        if diff >= newoffset:
                            summary['departure']=summarynew['departure']
                            summary['transfer']=str(int(summary['transfer'])+int(summarynew['transfer'])+1)
                            summary['price']=0
                            content[0]['time'].insert(0,contentnew[-1]['time'][0])
                            contentnew.pop()
                            contentnew[-1]['position']=position
                            content=contentnew+content
                            break
                summary['total']=int((datetime.datetime.strptime(summary['arrival'],"%H:%M")-datetime.datetime.strptime(summary['departure'],"%H:%M")).total_seconds())
                summary['total']=summary['total']+86400 if summary['total'] < 0 else summary['total']
                summaryname=','.join([str(value) for key,value in summary.items()])
                if summaryname not in summaryset:
                    summaryset.add(summaryname)
                    contentline.append(dict(summary=summary,route=content))
    contentline=sorted(contentline, key=lambda k: k['summary']['transfer'])
    contentline=sorted(contentline, key=lambda k: k['summary']['total'])
    contentline=sorted(contentline, key=lambda k: k['summary']['departure'], reverse=True)
    newcontentline=list()
    for i in range(len(contentline)):
        found=False
        for item in newcontentline:
            if contentline[i]['summary']['arrival'] == item['summary']['arrival']:
                found=True
                if contentline[i]['summary']['departure'] > item['summary']['departure'] :
                    item['summary'] = contentline[i]['summary']
                    item['route'] = contentline[i]['route']
                elif contentline[i]['summary']['departure'] == item['summary']['departure']:
                    if contentline[i]['summary']['transfer'] < item['summary']['transfer']:
                        item['summary'] = contentline[i]['summary']
                        item['route'] = contentline[i]['route']
                break 
            elif contentline[i]['summary']['departure'] == item['summary']['departure']:
                found=True
                if contentline[i]['summary']['arrival'] < item['summary']['arrival'] :
                    item['summary'] = contentline[i]['summary']
                    item['route'] = contentline[i]['route']
                break
        if not found:
            newcontentline.append(contentline[i])
            #print(contentline[i]['summary'])
            #print(contentline[i]['route'])
            #print()
    newcontentline=newprice(newcontentline,routeprice)
    return newcontentline
def fasterdeparturetime(fromstop,tostop,timestamp,offset):
    contentline=traintime(fromstop,tostop,timestamp,offset,'departure')
    timestamp2=datetime.datetime.strptime(str(timestamp)[:10]+' '+max([item['summary']['departure'] for item in contentline]),'%Y-%m-%d %H:%M')
    contentline=contentline+traintime(fromstop,tostop,timestamp2,1,'departure')
    contentline2=list()
    for r,route in enumerate(contentline):
        featurelist=list()
        for i,stop in enumerate(route['route']):
            if stop['edge'] or i == len(route['route'])-1:
                featurelist.append(stop)
        contentline2.append(dict(summary=route['summary'],route=featurelist))
    count=len(contentline2)
    stoplist,routeset=list(),set()
    trfoffset=2
    summaryset=set([','.join([str(value) for key,value in item['summary'].items()]) for item in contentline2])
    routeitem,routeprice=routeposition(contentline2)
    for r,route in enumerate(contentline2):
        if r == count:
            break
        stoplist=[stop['station'] for stop in route['route']]
        routename=''.join(stoplist)
        if len(stoplist) > 2 and routename not in routeset:
            routeset.add(routename)
            contentlistfirst=traintime(stoplist[0],stoplist[1],timestamp,offset,'departure')
            for item in contentlistfirst:
                summary,content=item['summary'],item['route']
                for i in range(1,len(stoplist)-1):
                    newtimestamp=datetime.datetime.strptime(str(timestamp)[:10]+' '+summary['arrival'],'%Y-%m-%d %H:%M')
                    contentlinetemp=traintime(stoplist[i],stoplist[i+1],newtimestamp,trfoffset,'departure')
                    for contenttemp in contentlinetemp:
                        summarynew,contentnew=contenttemp['summary'],contenttemp['route']
                        diff=(datetime.datetime.strptime(summarynew['departure'],"%H:%M")-datetime.datetime.strptime(summary['arrival'],"%H:%M")).total_seconds()/60
                        diff=diff+1440 if diff < -600 else diff
                        routename=content[-1]['station']+content[-1]['rail'].replace('ライン','線').split('線')[0]+contentnew[0]['station']+contentnew[0]['rail'].replace('ライン','線').split('線')[0]
                        position=routeitem[routename] if routename in routeitem else ''
                        newoffset=trfoffset
                        if content[-1]['rail'][:2] == contentnew[0]['rail'][:2]:
                            plus=False
                            if position:
                                if position != '前/中/後':
                                    newoffset+=1
                                    plus=True
                            if not plus and content[-1]['arrivalline'] and contentnew[0]['departureline']:
                                linediff=abs(int(re.findall(r'\d+',content[-1]['arrivalline'])[0])-int(re.findall(r'\d+',contentnew[0]['departureline'])[0]))
                                if linediff > 8:
                                    newoffset+=1
                        else:
                            newoffset+=2
                            if content[-1]['station'] in {'新宿','東京'}:
                                newoffset+=1
                                if '大江戸線' in contentnew[0]['rail'] or '大江戸線' in content[-1]['rail']:
                                    newoffset+=1
                            elif content[-1]['station'] == '中野(東京都)':
                                newoffset-=2
                        if diff >= newoffset:
                            summary['arrival']=summarynew['arrival']
                            summary['transfer']=str(int(summary['transfer'])+int(summarynew['transfer'])+1)
                            summary['price']=0
                            contentnew[0]['time'].insert(0,content[-1]['time'][0])
                            content.pop()
                            content[-1]['position']=position
                            content=content+contentnew
                            break
                summary['total']=int((datetime.datetime.strptime(summary['arrival'],"%H:%M")-datetime.datetime.strptime(summary['departure'],"%H:%M")).total_seconds())          
                summaryname=','.join([str(value) for key,value in summary.items()])
                if summaryname not in summaryset:
                    summaryset.add(summaryname)
                    contentline.append(dict(summary=summary,route=content))
    contentline=sorted(contentline, key=lambda k: k['summary']['transfer'])
    contentline=sorted(contentline, key=lambda k: k['summary']['total'])
    contentline=sorted(contentline, key=lambda k: k['summary']['arrival'])
    for i in range(len(contentline)):
        print(contentline[i]['summary'])
        print(contentline[i]['route'])
        print()
    newcontentline=list()
    for i in range(len(contentline)):
        found=False
        for item in newcontentline:
            if contentline[i]['summary']['departure'] == item['summary']['departure']:
                found=True
                if contentline[i]['summary']['arrival'] < item['summary']['arrival'] :
                    item['summary'] = contentline[i]['summary']
                    item['route'] = contentline[i]['route']
                elif contentline[i]['summary']['arrival'] == item['summary']['arrival']:
                    if contentline[i]['summary']['transfer'] < item['summary']['transfer']:
                        item['summary'] = contentline[i]['summary']
                        item['route'] = contentline[i]['route']
                break 
            elif contentline[i]['summary']['arrival'] == item['summary']['arrival']:
                found=True
                if contentline[i]['summary']['departure'] > item['summary']['departure'] :
                    item['summary'] = contentline[i]['summary']
                    item['route'] = contentline[i]['route']
                break
        if not found:
            newcontentline.append(contentline[i])
            #print(contentline[i]['summary'])
            #print(contentline[i]['route'])
            #print()
    newcontentline=newprice(newcontentline,routeprice)
    return newcontentline
def fastertime(fromstop: str,tostop: str,timestamp: datetime.datetime,offset: int,type: str='arrival') -> list:
    if type=='arrival':
        return fasterarrivaltime(fromstop,tostop,timestamp,offset)
    elif type=='departure':
        return fasterdeparturetime(fromstop,tostop,timestamp,offset)
    else:
        return traintime(fromstop,tostop,timestamp,offset,type)
def main():
    #timestamp=datetime.datetime.now()
    timestamp=datetime.datetime.strptime('2022-06-17 10:00','%Y-%m-%d %H:%M')
    for line in writetimeline(fastertime('高円寺','池袋',timestamp,0)):
        print(line)

if __name__ == "__main__":
    main()