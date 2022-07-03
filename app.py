#라이브러리 Import
from urllib import parse, request
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import urllib.request

#Flask 서버
app = Flask(__name__)

#/webhook 호출시
@app.route('/webhook',methods = ['GET','POST'] )
def weather_func():
    #Json형태로 값을 받아옴.
    req = request.get_json(force = True)
    action = req['queryResult']['action']
    
    #필요한 값을 저장함.
    if action in ['날씨', '기온' ,'비', '미세먼지' ,'옷차림']:
        user_local = ' '.join(list(req["queryResult"]["parameters"]["location"].values()))    
        user_day = req["queryResult"]["parameters"]["day"]
     
    else : 
        if 'parameters' in req["queryResult"]['outputContexts'][0].keys():
            param = req["queryResult"]['outputContexts'][0]['parameters']

        elif 'location' in req["queryResult"]['outputContexts'][1]['parameters'].keys():
            param = req["queryResult"]['outputContexts'][1]['parameters']

        elif 'location' in req["queryResult"]['outputContexts'][2]['parameters'].keys():
            param = req["queryResult"]['outputContexts'][2]['parameters']
        
        user_local = ''.join(param['location'].values()).strip()
        user_day = param["day"]
    
    #날짜 설정
    if action in ['오늘날씨', '오늘옷', '오늘기온', '오늘미세먼지', '오늘비']:
        user_day = '오늘'

    elif action in ['내일날씨' , '내일비' , '내일기온','내일미세먼지' ,'내일옷']:
        user_day = '내일'

    elif action in ['모레날씨', '모레비', '모레기온' , '모레미세먼지', '모레옷']:
        user_day = '모레'

    print(user_local, user_day)

    #날씨 검색 및 크롤링
    d = user_day
    d += ' ' + user_local
    d += " 날씨"
    d = parse.quote(d)     
    URL = 'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query='+d
    source = urllib.request.urlopen(URL)
    soup = BeautifulSoup(source.read(), 'html.parser')

    #날짜가 오늘일 경우 데이터 저장
    if user_day=='오늘':
        weather=soup.find("div",{"class":"status_wrap"})
        wea = '날씨 : ' + weather.find("p", {"class":"summary"}).text.strip()
        temp = "온도 : "+ weather.find("div", {"class":"temperature_text"}).text.strip()[5:]
        sumterm = weather.find_all("dt", {"class" : "term"})
        sumdesc = weather.find_all("dd", {"class" : "desc"})
          
        rain = sumterm[0].text.strip() + " : " + sumdesc[0].text.strip()
        hum = sumterm[1].text.strip() + " : " + sumdesc[1].text.strip()
        wind = sumterm[2].text.strip() + " : " + sumdesc[2].text.strip()

        item_today = weather.find("ul",{"class":"today_chart_list"}).find_all("li")
        dust = item_today[0].text.strip()
        dust2 = item_today[1].text.strip()
        sun = item_today[2].text.strip()

    #날짜가 내일이나 모레일 경우 값 저장
    else:
        if user_day == '내일':
            weather = soup.find_all("div", {'class': "weather_info type_tomorrow"})[0].find_all('div',{"class":"inner"})
        elif user_day == '모레':
            weather = soup.find_all("div", {'class': "weather_info type_tomorrow"})[1].find_all('div',{"class":"inner"})

        amtemp = "기온 : " + weather[0].find("div",{"class":"temperature_text"}).text.strip()[5:]
        amweat = weather[0].find("p",{"class":"summary"}).text
        amrain = weather[0].find("dt",{"class":"term"}).text + " : " + weather[0].find("dd",{"class":"desc"}).text
        chartlist = weather[0].find("ul",{"class":"today_chart_list"}).find_all("li")
        amdust = chartlist[0].text.strip()
        amdust2 = chartlist[1].text.strip()

        pmtemp = "기온 : " + weather[1].find("div",{"class":"temperature_text"}).text.strip()[5:]
        pmweat = weather[1].find("p",{"class":"summary"}).text
        pmrain = weather[1].find("dt",{"class":"term"}).text.strip() + " : " + weather[1].find("dd",{"class":"desc"}).text.strip()
        chartlist = weather[1].find("ul",{"class":"today_chart_list"}).find_all("li")
        pmdust = chartlist[0].text.strip()
        pmdust2 = chartlist[1].text.strip()

    #날씨 정보
    if action in ['날씨', '내일날씨', '모레날씨', 'x_날씨', '오늘날씨']:
        if user_day=='오늘':
            weather = user_day + " " + user_local + " 날씨\n" + wea + "\n" + temp + "\t\t" + rain + "\n" + hum + "\t\t" + wind + "\n" + dust + "\t\t" +dust2 + "\n" + sun
            res = {
                "fulfillmentText" : weather,
             }
            return jsonify(res)

        else:    
            answer = user_day + " " + user_local + " 날씨\n" + "***오전***\n" + amtemp + "\t" + amweat + '\n' + amrain + '\n' + amdust + '\t\t' +  amdust2 + '\n'\
                + "***오후***\n" + pmtemp + "\t" + pmweat + '\n' + pmrain + '\n' + pmdust + '\t\t' + pmdust2

            res = {
                "fulfillmentText": answer
            }
            
            return jsonify(res)


    #옷차림 정보
    elif action in ['x_옷', '옷차림', '내일옷', '모레옷', '오늘옷']:
        if user_day == '오늘':
            T = float(temp[4:-1].strip())
            V = float(wind[9:-3].strip())
            C = round(13.12 + 0.6215 * T - 11.37 * V ** 0.16 + 0.3965 * V**0.16 * T, 1)
        
        else:
            C = (float(amtemp[4:-1]) + float(pmtemp[4:-1]))/2

        if C > 28:
            clothes = '민소매, 반팔, 반바지, 원피스 등'
        
        elif C>23:
            clothes = '반팔, 얇은 셔츠, 반바지, 면바지 등'
        
        elif C > 20:
            clothes = '얇은 가디건, 긴팔, 면바지, 청바지 등'
        
        elif C > 17:
            clothes = '얇은 니트, 맨투맨, 가디건, 청바지 등'
        
        elif C > 12:
            clothes = '자켓, 가디건, 야상, 스타킹, 면바지, 청바지 등'

        elif C > 9:
            clothes = '자켓, 트렌치코트, 야상, 니트, 청바지, 스타킹 등'

        elif C > 5:
            clothes = '코트, 가죽자켓, 히트텍, 니트, 레깅스 등'

        else:
            clothes = '패딩, 두꺼운 코트, 목도리, 기모제품 등'

        res = {
                "fulfillmentText": f"예상 체감온도는 {C}℃ 입니다.\n 추천하는 옷차림은 {clothes} 입니다.",
        }

        return jsonify(res)

    #기온
    elif action in ['기온', '내일기온', '모레기온' , '오늘기온', '옷차림_기온' , '비_기온' , '미세먼지_기온' ]:
        if user_day == '오늘':
            res = {
                'fulfillmentText': f'오늘 {user_local} 기온은 {temp[4:]} 입니다.',
            }
        
        else:
            res = {
                'fulfillmentText' : f'{user_day} {user_local} 오전 기온은 {amtemp[4:]} 이고, 오후 기온은 {pmtemp[4:]} 입니다.'
            }
        return jsonify(res)


    #비
    elif action in ['비','내일비', 'x_비' , '모레비', '오늘비']:
        if user_day == '오늘':
            if wea in ['흐리고 비', '흐리고 비/눈', '비']:
                answer = {
                    'fulfillmentText' : '오늘 비 소식이 있습니다:( 외출 시 우산을 챙기세요!'
                }
            else:
                answer = {
                    'fulfillmentText' : '오늘 비 소식은 없습니다:)'
                }
        
        elif user_day == '내일' or user_day == '모레':
            if amweat == '흐리고 비' or amweat == '흐리고 한때 비' or amweat == '흐리고 비/눈' or amweat == '비':
                if pmweat == '흐리고 비' or pmweat == '흐리고 한때 비' or pmweat == '흐리고 비/눈' or pmweat == '비':
                    answer = {
                    'fulfillmentText' : f'{user_day} 오전과 오후에 비 소식이 있습니다:( 외출 시 우산을 챙기세요!'
                }
                else:
                    answer = {
                    'fulfillmentText' : f'{user_day} 오전에 비 소식이 있습니다:( 외출 시 우산을 챙기세요!'
                }
            
            else:
                if pmweat == '흐리고 비' or pmweat == '흐리고 한때 비' or pmweat == '흐리고 비/눈' or pmweat == '비':
                    answer = {
                    'fulfillmentText' : f'{user_day} 오후에 비 소식이 있습니다:( 외출 시 우산을 챙기세요!'
                }
                else:
                    answer = {
                    'fulfillmentText' : f'{user_day} 비/눈 소식이 없습니다:)\n 좋은 하루 보내세요!'
                }
        return jsonify(answer)



    #미세먼지
    elif action in ['미세먼지' , '내일미세먼지', '모레미세먼지', 'x_미세먼지', '오늘미세먼지']:
        if user_day == '오늘':
            danswer = user_day + " " + user_local + " 미세먼지는 " + dust[5:] + " , 초미세먼지는 " + dust2[6:] + "입니다."
            res = {
                "fulfillmentText": danswer,
            }
            return jsonify(res)


        else:
            danswer = user_day + " " + user_local + " 미세먼지\n" + "오전 미세먼지는" + amdust[5:] + '이고, 초미세먼지는 ' + amdust2[6:] + '입니다' \
                     + "오후 미세먼지는" + pmdust[5:] + ' 이고, 초 미세먼지는' + pmdust2[6:] + '입니다.'

            res = {
                "fulfillmentText": danswer
            }

            return jsonify(res)





    else:
        answer = {
            'fulfillmentText': '죄송합니다! 아직 그 부분은 개발 중 입니다ㅠㅠ'
        }

        return jsonify(answer)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)