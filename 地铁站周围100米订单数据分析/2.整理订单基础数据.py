import pandas as pd
import numpy as np
import sqlalchemy
import geopandas as gpd
from shapely.geometry import Point,LineString
from shapely.ops import transform
from functools import partial
import pyproj

pd.set_option('display.width',None)
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)


'''
存在01不对应数据
    初步分析 多出来的0可能是调度车辆时候的定位 （可以后期验证）
如果连续01 则认为是一次出行
'''


# 链接数据库
engine = ('mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % ('root', 'root', 'localhost', 3306, '共享单车'))
# 获得数据时间 21-25 五天

# sql_time_ = "SELECT DATE_FORMAT(UPDATE_TIME,'%%Y-%%m-%%d') ddate FROM gxdc_dd GROUP BY DATE_FORMAT(UPDATE_TIME,'%%Y-%%m-%%d') "
# lst_time = pd.read_sql(sql_time_,engine)['ddate'].map(lambda x:str(x)).tolist()
# lst_time = pd.read_sql(sql_time_,engine)
# print(lst_time)
# lst_time = ['gxdc_dd_20201221','gxdc_dd_20201222','gxdc_dd_20201223','gxdc_dd_20201224','gxdc_dd_20201225']
lst_time = ['gxdc_dd_20201221']

# 坐标转换 WGS to World Mercator
project = partial(
    pyproj.transform,
    pyproj.Proj('EPSG:4326'),
    pyproj.Proj('EPSG:3395'))


target = [0,1]

for i in lst_time:
    # 选择21号数据
    sql_bicyclename_ = "SELECT BICYCLE_ID FROM " + i + " GROUP BY BICYCLE_ID "
    # 选取所有的unique bicycle id
    # lst_bicyclename = pd.read_sql(sql_bicyclename_,engine)['BICYCLE_ID'].drop_duplicates().tolist()
    # lst_bicyclename = ['b5430282dc6e5288e94aca4b9ddfe30f','c7adbf70ecdb58d6f90192f13ad0c5bb']
    # lst_bicyclename = ['c7adbf70ecdb58d6f90192f13ad0c5bb']
    lst_bicyclename = ['01247bbfeaec0acba4966a7e38e235d1']
    lst_l = []
    lst_p = []
    df_l = pd.DataFrame()
    df_p = pd.DataFrame()
    df_p_0 = pd.DataFrame()
    df_p_1 = pd.DataFrame()
    # df_subwaystationbuff = gpd.read_file(r'file:///Users/ternencekk/Library/CloudStorage/OneDrive-个人/!!!!厦门/code/shp/pytoshp/厦门地铁_buffer100.shp')
    # 以地铁出入口为中心半径为100米的圆  我们姑且认为在地铁出入口100米范围内的订单数据均与地铁出入口发生关系
    df_subwaystationbuff = gpd.read_file('厦门地铁出入口buffer.gpkg')
    # 坐标变成wgs84 方便与dd起讫点数据处理分析
    df_subwaystationbuff=df_subwaystationbuff.to_crs(crs='EPSG:4326')
    for j in lst_bicyclename:  #遍历所有出现的共享单车id
        # 提取每个id当天的订单数据
        sql_ = "SELECT * FROM " + i + "  WHERE BICYCLE_ID = '" + j + "'"
        df = pd.read_sql(sql_,engine)
        if 1 ==1:
            '''
            OD变一行 生成dataframe
            '''
            # 根据车辆开锁状态 01 变成List
            lst_01 = df['LOCK_STATUS'].tolist()
            # 把数据处理为 [0,0,1,0,1] 变  [[0,0],[0,1],[1,0],[0,1]]
            lst_01_chuli = [[lst_01[i],lst_01[i+1]] for i in range(len(lst_01)-1)]
            # 选择01相邻的两列 [[0,0],[0,1],[1,0],[0,1]] 选择lst里面是[0,1]的index为1,3 [index,index+1]为要选取的行 lst为二维list[[1,2],[3,4]]
            index_target = [[index,index+1] for (index,item) in enumerate(lst_01_chuli) if item == target]
            # 选择01相邻的两列 [[1,2],[3,4]] 从二维list变成一维list   [1, 2, 3，4]
            index_target = list(np.array(index_target).flatten())
            # 选择01相邻的两列 选择.iloc[1,2,3,4]的数据
            df_target =df.iloc[index_target].reset_index(drop=True)
            print(df_target)
            # 生成点的geometry
            geometry_p = [Point(xy) for xy in zip(df_target.LONGITUDE.apply(lambda x:float(x)),df_target.LATITUDE.apply(lambda x:float(x)))]
            # 坐标属性放到lst里面 用于后面合成整表
            lst_p.extend(geometry_p)
            # 查看哪些订单起讫点在地铁站出入口buffer100米范围内 坐标为WGS84
            # 选择其对应的经纬度、记录时间和与之相交的出入口所在站 之后去重
            # 得到订单起讫点与地铁站的关系
            r =gpd.sjoin(gpd.GeoDataFrame(df_target,geometry=geometry_p,crs='EPSG:4326'),df_subwaystationbuff)[['LATITUDE','LONGITUDE','UPDATE_TIME','stationname']].drop_duplicates()[['stationname']]
            print(r)
            # 根据选择 两个df的index合并数据
            df_target = pd.merge(df_target,r,left_index=True,right_index=True,how='outer')
            print(df_target)
            # print(r)
            # 用于多df合并
            df_p = pd.concat([df_p,df_target])
            # print(df_p)
            # 如果geometry数量和df_target数量不一致 弹出报错
            if len(geometry_p)!=len(df_target):
                print(j)
                break


        if 1== 1:
            # 数据使用wgs84坐标系
            geod = pyproj.geod.Geod(ellps='WGS84')
            # 选择终点数据
            df_target_1 = df_target[df_target['LOCK_STATUS']==1].reset_index().drop(['index','geometry'],axis=1)
            df_target_1.columns = ['BICYCLE_ID','LATITUDE_1','LONGITUDE_1','LOCK_STATUS_1','UPDATE_TIME_1','stationname_1']
            # 选择起点数据
            df_target_0 = df_target[df_target['LOCK_STATUS']==0].reset_index().drop(['index','geometry'],axis=1)
            df_target_0.columns = ['BICYCLE_ID','LATITUDE_0','LONGITUDE_0','LOCK_STATUS_0','UPDATE_TIME_0','stationname_0']
            # 基于id和时间 横向合并
            df_target_01 = pd.concat([df_target_0,df_target_1],axis=1)
            # 查看订单开始结束之间的时间
            # 得到订单持续时间 用于后期处理数据 如果时间果断 很有可能是因为车辆有问题/车辆不和用户要求（座椅把手脏） 多人此操作可以特别关注
            df_target_01['timedelta'] = (df_target_01['UPDATE_TIME_1'] - df_target_01['UPDATE_TIME_0']).apply(lambda x:x.total_seconds())
            # 生成线的geometry
            df_target_01['geometry_line'] = [LineString([(float(df_target_01['LONGITUDE_0'][i]),float(df_target_01['LATITUDE_0'][i])),(float(df_target_01['LONGITUDE_1'][i]),float(df_target_01['LATITUDE_1'][i]))])for i in range(len(df_target_01))]
            # df_target_01['geometry_line'] = [LineString([(float(df_target_01['LONGITUDE_0'][i]),float(df_target_01['LATITUDE_0'][i])),(float(df_target_01['LONGITUDE_1'][i]),float(df_target_01['LATITUDE_1'][i]))]).coords for i in range(len(df_target_01))]
            # 用于后期合并
            geometry_l = df_target_01['geometry_line'].tolist()
            # print('geometry_l',geometry_l)
            # 得到订单起讫点的欧几米德距离 同样用于后期处理
            df_target_01['Eucliddis'] = df_target_01['geometry_line'].apply(lambda x:geod.geometry_length(x))

            # 简化列
            df_target_01 = df_target_01[['BICYCLE_ID','LATITUDE_0','LONGITUDE_0','LOCK_STATUS_0','UPDATE_TIME_0','stationname_0','LATITUDE_1','LONGITUDE_1','LOCK_STATUS_1','UPDATE_TIME_1','stationname_1','timedelta','Eucliddis']]
            # shp dbf里面没有datatime数据格式 改为str
            df_target_01['UPDATE_TIME_0'] = df_target_01['UPDATE_TIME_0'].apply(lambda x:str(x))
            df_target_01['UPDATE_TIME_1'] = df_target_01['UPDATE_TIME_1'].apply(lambda x:str(x))
            df_target_01 = df_target_01.loc[:, ~df_target_01.columns.duplicated()]

            # print(df_target_01)
            lst_l.extend(geometry_l)
            # df_l = df_l.append(df_target_01)
            df_l = pd.concat([df_l,df_target_01])




    # 生成点坐标
    df_target_geo_p = gpd.GeoDataFrame(df_p,geometry=lst_p,crs='EPSG:4326')
    df_target_geo_p['UPDATE_TIME'] = df_target_geo_p['UPDATE_TIME'].apply(lambda x:str(x))
    # print(df_target_geo_p.head())
    df_target_geo_p_0 =df_target_geo_p[df_target_geo_p['LOCK_STATUS'] == 0]
    df_target_geo_p_1 =df_target_geo_p[df_target_geo_p['LOCK_STATUS'] == 1]
    df_target_geo_p_0.to_file('points_0_221010.shp',driver='ESRI Shapefile',encoding='utf-8')
    df_target_geo_p_1.to_file('points_1_221010.shp',driver='ESRI Shapefile',encoding='utf-8')



    # 生成线
    df_target_geo_l = gpd.GeoDataFrame(df_l,geometry=lst_l,crs='EPSG:4326')
    df_target_geo_l.to_file('lines_221010.shp',driver='ESRI Shapefile',encoding='utf-8')

