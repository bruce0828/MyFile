
# coding: utf-8

# ## 0 摘要
# ---
# 
# ### (1) 主要工具
# * [**requests 官方教程**](https://realpython.com/python-requests/)
# * [**BeautifulSoup**](https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/)
# * [**json代码解析工具**](https://www.json.cn/)
# 
# ### (2) 网站资源
# * **8464公交查询网站** (https://shanghai.8684.cn/)
# * **高德地图公交线路信息** (https://restapi.amap.com/v3/bus/linename?key=a432e1e304ba9ec3bb834ef55a7aba67&city=上海&keywords=上海186路公交车路线&s=rsv3&extensions=all&offset=1&paltform=JS)
# 
# ### (3) 参考资料
# * [**Python爬虫——城市公交网络站点数据的爬取**](https://blog.csdn.net/wenwu_both/article/details/70168760)
# * [**Python爬虫——城市公交、地铁站点和线路数据采集**](https://www.bbsmax.com/A/pRdBB1pPdn/)
# * https://github.com/jsnuwjl/get_Bus_lines/blob/master/get_line.py
# * https://github.com/ozzychow/busLineSpyder/blob/master/getBusLineStation.py

# In[1]:


# 基本库
import os
import requests
import urllib
import json
from lxml import etree
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd
import math
import time
import random

import folium
import math
from shapely.geometry import Point, LineString
import shapefile
import geopandas as gpd
import matplotlib.pyplot as plt
get_ipython().magic('matplotlib inline')


# In[2]:


os.chdir(r'E:\zy城市群数据分析\上海公交数据')


# ## 1 公交线路名称获取
# ---
# 
# * 通过图吧公交、公交网、8684、本地宝等网站获取，以下通过8684网站获取
# * 不同城市设置不同的url，对于<font color=brown>上海</font>，设为 <u>https://shanghai.8684.cn</u>

# In[3]:


def get_buslist_from_gongjiaowang(city):
    #city = 'shanghai'
    url = 'http://{}.gongjiao.com/lines_all.html'.format(city)
    r = requests.get(url)
    soup = BeautifulSoup(r.text,'html.parser')
    li = soup.find_all(name='div',class_='list')
    busList = []
    for l in li[0].find_all('li'):
        busList.append(l.text)
    return busList


# In[4]:


def get_buslists_from_8684(city, savePath=None):
    # 8684网址上爬取公交线路信息, 输入参数city: shanghai
    # 返回城市所有常规公交的 线路名称、站点数目、公交公司、运行时间、数据更新日期，格式为 DataFrame
    t0 = time.time()
    
    busInfo = list()
    
    # 第一层
    headers =  {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)                 Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'}
    url1 = 'https://{}.8684.cn'.format(city)    # url1 = 'https://nanjing.8684.cn'
    text1 = requests.get(url1, headers=headers).text
    soup1 = BeautifulSoup(text1,'lxml')
    info1 = soup1.find('div',class_='bus_kt_r1').find_all('a')
    group1 = re.findall('"(.*?)"',str(info1))

    # 第二层
    for url2 in [url1 + x for x in group1]:
        text2 = requests.get(url2, headers=headers).text
        soup2 = BeautifulSoup(text2,'lxml')
        info2 = soup2.find('div',class_='cc_content').find_all('div')[-1].find_all('a')
        group2 = re.findall('href="(.*?)"',str(info2))

        # 第三层
        for url3 in [url1 + x for x in group2]:
            try: 
                text3 = requests.get(url3, headers=headers).text
                soup3 = BeautifulSoup(text3,'lxml')

                # 信息提取
                busName = soup3.find('div',class_='bus_i_t1').find('h1').get_text().replace('&nbsp','').replace('路线','')
                busTime = soup3.find_all('p',class_='bus_i_t4')[0].get_text().replace('运行时间：','')
                busCompany = soup3.find_all('p',class_='bus_i_t4')[2].find('a').get_text()
                busUpdate = soup3.find_all('p',class_='bus_i_t4')[3].get_text().replace('最后更新：','')
                busStopNum = int(re.findall('\xa0(.*?)\xa0',soup3.find_all('span',class_='bus_line_no')[0].get_text())[0])

                busLine = soup3.find_all('div',class_='bus_line_site')
                busLine1 = re.findall('>(.*?)</a>',str(busLine[0].find_all('a')))
                if len(busLine) == 2:  # 上下行
                    busLine2 = re.findall('>(.*?)</a>',str(busLine[1].find_all('a')))
                elif len(busLine) == 1: # 环线
                    busLine2 = []
                else: print('Error!')
                busInfo.append([busName, busStopNum, busCompany, busTime, busUpdate, busLine1, busLine2])
                # print(busName)
            except:
                print('{} 返回错误！'.format(url3))
                pass
    
    busInfo = pd.DataFrame(busInfo, columns=['Name','StopNum','Company','Time','Update','Line1','Line2'])
    if not savePath:
        if not os.path.exists(savePath):
            os.makedirs(savePath)
        busInfo.to_csv(savePath,index=False,encoding='gbk')
        
    print('8684网站爬取线路信息完成, 耗时 {} s，总共 {} 条常规公交线路'.format(time.time()-t0, len(busInfo)))
    return busInfo


# ## 2 公交站点获取
# ---
# 
# ### (1) 高德地图入口
# * 方法一：高德API接口，key类型为<font color=red>web端</font>。
# 
# * 方法二：打开[<font color=blue>高德地图</font>](https://amap.com), 按F12检查网页代码，选择‘<font color=red>Network</font>',输入公交线路，找到<font color=red>poiInfo?</font>对应的地址。
# 
# ### (2) 解析返回数据
# * 方法一：[<font color=blue>json解析工具</font>](https://www.json.cn/)
# * 方法二：用json.loads()
# 
# ### (3) 坐标转换
# * 高德坐标为GCJ-02（火星坐标系），转化为WGS-84坐标系
# * 经纬度测试
#   * 方法一：坐标测试：打开 http://geojson.io ，导入转化坐标后的公交线路文件
#   * 方法二：运用<font color=red>folium库</font>的地图功能
#   
# ### (4) 生成地理文件
# * 方法一：from shapely.geometry import Point LineString
# * 方法二：import shapefile (https://pypi.org/project/pyshp/)
# * [shapely 与 shapefile 比较](https://geospatialtraining.com/accessing-geospatial-data-with-pyshp-shapely-and-fiona/)
#     * shapely: is used for manipulation and analysis of geometric objects. It can be described as a more Pythonic version of the OGR library, that has mainly the same functions and classes as Shapely. OGR is part of GDAL, a popular open source library that deals with vector data. It is very powerful and is used by many geospatial applications.
#     * pyshp: This full name of this Python library is Python Shapefile Library. Its use is quite limited: it is meant for reading and writing shapefiles. The Esri API for Python uses it to read and write shapefiles when it cannot find a local installation of the arcpy site package.

# In[5]:


class TransformCoordinates(object):
    # 坐标转化，主要用到 gcj02_wgs84()
    def __init__(self):
        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0
        self.pi = 3.1415926535897932384626  # π
        self.a = 6378245.0  # 长半轴
        self.ee = 0.00669342162296594323  # 扁率

    def gcj02_bd09(self,lng, lat):
        # 火星坐标系(GCJ-02)转百度坐标系(BD-09)，谷歌、高德——>百度
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * self.x_pi)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * self.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return [bd_lng, bd_lat]

    def bd09_gcj02(self,bd_lon, bd_lat):
        # 百度坐标系(BD-09)转火星坐标系(GCJ-02)， 百度——>谷歌、高德
        x = bd_lon - 0.0065
        y = bd_lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * self.x_pi)
        gg_lng = z * math.cos(theta)
        gg_lat = z * math.sin(theta)
        return [gg_lng, gg_lat]

    def wgs84_gcj02(self,lng, lat):
        # WGS84转GCJ02(火星坐标系)
        if self.out_of_china(lng, lat):  # 判断是否在国内
            return lng, lat
        dlat = self.transformlat(lng - 105.0, lat - 35.0)
        dlng = self.transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [mglng, mglat]

    def gcj02_wgs84(self,lng, lat):
        # GCJ02(火星坐标系)转GPS84
        if self.out_of_china(lng, lat):
            return lng, lat
        dlat = self.transformlat(lng - 105.0, lat - 35.0)
        dlng = self.transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return [lng * 2 - mglng, lat * 2 - mglat]

    def transformlat(self,lng, lat):
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 *  math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * self.pi) + 40.0 * math.sin(lat / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * self.pi) + 320 * math.sin(lat * self.pi / 30.0)) * 2.0 / 3.0
        return ret

    def transformlng(self,lng, lat):
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 * math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * self.pi) + 40.0 * math.sin(lng / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * self.pi) + 300.0 * math.sin(lng / 30.0 * self.pi)) * 2.0 / 3.0
        return ret

    def out_of_china(self,lng, lat):
        # 判断是否在国内，不在国内不做偏移
        if lng < 72.004 or lng > 137.8347:
            return True
        if lat < 0.8293 or lat > 55.8271:
            return True
        return False


# In[6]:


def get_buslines_from_amap(city,buslinename,key):
    # 从高德API上爬取公交站点信息与公交路线信息
    # 输入参数 city = '上海' ，buslinename = '上海186路公交车路线'
    amap_url = 'https://restapi.amap.com/v3/bus/linename?'
    params = {'key': key,              'city': city,              'keywords': buslinename,              's':'rsv3',              'extensions': 'all',              'offset':1,              'paltform':'JS'}
    url = amap_url + urllib.parse.urlencode(params)

    response = requests.get(url).text
    busData = json.loads(response)
    return busData


# In[7]:


def get_busline_poly(city, busNameList, key, save_shp):
    # 根据8684网站上的公交线路名称 获取 各条公交线路的shp文件
    # city = '上海', lines = busInfo.name.tolist(),  savePath = './busline/'
    t0 = time.time()
    
    folder = os.path.dirname(save_shp)  # 获取路径文件夹
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    w = shapefile.Writer(save_shp)
    w.field('Name','C',40)
    w.field('StartStop','C',40)
    w.field('EndStop','C',40)
    w.field('Distance','F')
    w.field('Price','N')
    w.field('Type','C',40)
    w.field('Company','C',80)

    for busline in busNameList:
        busData = get_buslines_from_amap(city=city,buslinename=busline,key=key)  # 获取公交数据
        if len(busData['buslines']) == 0:  # 8684网站上的部分公交在高德上没有数据
            # print('{} 无线路信息！'.format(busline))
            continue
        else:
            busStartStop = busData['buslines'][0]['start_stop']   # 起始站      
            busEndStop = busData['buslines'][0]['end_stop']       # 终点站       
            busDist = busData['buslines'][0]['distance']          # 线路长度
            busPrice = busData['buslines'][0]['total_price']      # 票价
            busType = busData['buslines'][0]['type']              # 公交类型
            busCompany = busData['buslines'][0]['company']        # 公交公司
            busLinePoly = busData['buslines'][0]['polyline']      # 公交线路
            if busStartStop == []: busStartStop = '无'
            if busEndStop == []: busEndStop = '无'
            if busDist == []: busDist = 0
            if busPrice == []: busPrice = 0
            if busType == []: busType = '无'
            if busCompany == []: busCompany = '无'

            busLine = []
            for coor in busLinePoly.split(';'):
                lon, lat = coor.split(',')
                lon, lat = float(lon), float(lat)
                tc = TransformCoordinates()
                lonCT, latCT = tc.gcj02_wgs84(lon, lat)
                busLine.append([lonCT,latCT])

            w.line([[[x[0], x[1]] for x in busLine]])  # Add LineString shape, 三维数组
            w.record(busline.encode('gbk'), busStartStop.encode('gbk'), busEndStop.encode('gbk'),                     busDist, busPrice, busType.encode('gbk'), busCompany.encode('gbk'))  # 添加字段
    w.close()
    
    # 添加投影：WGS84
    busLineRes = gpd.read_file(save_shp,encoding='gbk')
    busLineRes.crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    busLineRes.to_file(save_shp[:-4] + '_proj.shp',encoding='gbk')
    print('高德地图爬取公交线路完成, 耗时 {} s'.format(time.time()-t0))
    return busLineRes


# In[8]:


def get_busstop(city, busNameList, key, save_csv):
    # 根据8684网站上的公交线路名称 获取所有公交站点经纬度的csv文件
    # city = '上海', busNameList = busInfo.name.tolist(),  savePath = './busstop/busstop.csv'
    t0 = time.time()
    
    busStopRes = []
    for busline in busNameList:
        busData = get_buslines_from_amap(city=city,buslinename=busline,key=key)
        if len(busData['buslines']) == 0:  # 8684网站上的部分公交在高德上没有数据
            # print('{} 无线路信息！'.format(busline))
            continue
        else:
            busstops = busData['buslines'][0]['busstops']
            for busstop in busstops:
                stopName = busstop['name']
                stopLoc = busstop['location']
                lon, lat = stopLoc.split(',')
                lon, lat = float(lon), float(lat)
                tc = TransformCoordinates()
                lonCT, latCT = tc.gcj02_wgs84(lon, lat)
                busStopRes.append([stopName,lonCT, latCT])

    # 转换为DataFrame格式
    busStopRes = pd.DataFrame(busStopRes,columns=['Name','Lon','Lat'])
    folder = os.path.dirname(save_csv)  # 获取路径文件夹
    if not os.path.exists(folder):
        os.makedirs(folder)
    busStopRes.to_csv(save_csv,index=False,encoding='gbk')
    print('高德地图爬取公交站点完成, 耗时 {} s'.format(time.time()-t0))
    return busStopRes


# In[9]:


def get_subwaylines_from_8684(city):
    # 获取地铁线路名称
    # city = 'sh',   'nj',  'wh',  'cs'
    url = 'https://dt.8684.cn/{}'.format(city)
    r = requests.get(url)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text,'html.parser')
    t1 = soup.find_all(name='div',class_='ib-box')
    for t2 in t1:
        if t2.find_all('div',class_='ib-hd'):
            if t2.find_all(name='a',class_='cm-tt'):
                t3 = t2.find_all(name='a',class_='cm-tt')
                
    subwayLines = []
    for t4 in t3:
        subwayLines.append(t4.text)
    return subwayLines


# In[10]:


def display_busline_on_map(busline, radius=1, color='blue'):
    # 公交线路在OSM上显示，输入busline为二维数组array， [lon,lat]
    location = [busline[:,1].mean(),busline[:,0].mean()]
    maps = folium.Map(location=location,tiles='OpenStreetMap',zoom_start=12)  # "Stamen Terrain", "Stamen Toner"
    for i in range(0,len(busline)):
        folium.CircleMarker([busline[i,1], busline[i,0]],radius=radius,color=color).add_to(maps)
    return maps


# In[11]:


if __name__ == '__main__':
    # 公交线路名称获取——9694网站
    # busInfo = get_buslists_from_8684(city='shanghai',savePath='./bus_info.csv')
    buslines = get_buslist_from_gongjiaowang(city='shanghai')
#     busInfo.to_csv('./bus_info.csv',index=False,encoding='gbk')  # 所有公交线路名称

    # 公交数据获取——高德API
#     buslines = busInfo.Name.tolist()
    key1 = '320a6e2d2124ed241472e0657b745daa'
    busLineRes = get_busline_poly(city='上海', busNameList=buslines, key=key1, save_shp='./busline/busline.shp')  # 公交线路shp
    
    key2 = 'e92c0a87c3ace0b02825ae917a19c79e'
    busStopRes = get_busstop(city='上海', busNameList=buslines, key=key2, save_csv='./busstop/busstop.csv')  # 公交站点csv
    
    # 地铁数据
    subwayLines = get_subwaylines_from_8684('sh')
    key3 = 'a432e1e304ba9ec3bb834ef55a7aba67'
    subwayRes = get_busline_poly(city='上海', busNameList=subwayLines, key=key3, save_shp='./subwayline/subway.shp')  # 公交线路shp
    subwayStopRes = get_busstop(city='上海', busNameList=subwayLines, key=key3, save_csv='./subwaystop/subway.csv')  # 公交站点csv


# In[ ]:


# 以上海186路公交车为例
busData = get_buslines_from_amap(city = '上海',buslinename = '上海186路公交车')
busLinePoly = busData['buslines'][0]['polyline']      # 公交线路
busLine = []
for coor in busLinePoly.split(';'):
    lon, lat = coor.split(',')
    lon, lat = float(lon), float(lat)
    tc = TransformCoordinates()
    lonCT, latCT = tc.gcj02_wgs84(lon, lat)
    busLine.append([lonCT,latCT])
busLine = np.array(busLine)
display_busline_on_map(busline=busLine,radius=0.1,color='blue')

