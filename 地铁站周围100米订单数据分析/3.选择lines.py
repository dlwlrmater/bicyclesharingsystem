import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon,LineString
import shapely
import pandas as pd
import numpy as np
from scipy.spatial import Voronoi,voronoi_plot_2d
import math
from geographiclib.geodesic import Geodesic
from math import factorial

pd.set_option('display.width',None)
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)



# 贝塞尔曲线
def comb(n,k):
    return factorial(n) // (factorial(k) * factorial(n-k))
def get_bezier_curve(points):
    n = len(points) -1
    return lambda t: sum(
        comb(n,i) * t**i * (1-t) **(n-i) * points[i]
        for i in range(n+1)
    )
def evaluate_bezier(points,total):
    bezier = get_bezier_curve(points)
    new_points = np.array([bezier(t) for t in np.linspace(0,1,total)])
    return new_points[:,0],new_points[:,1]


if 1==1:
    # 读取线图层
    gdf_l = gpd.read_file(r'lines_221010.shp')
    # 起点在地铁站出口100米范围内的订单 线图层
    gdf_l_0 = gdf_l[~gdf_l['stationnam'].isna()]
    # 终点在地铁站出口100米范围内的订单 线图层
    gdf_l_1 = gdf_l[~gdf_l['stationn_1'].isna()]
    # gdf_l_0.to_file(r'lines_221010_0.shp',driver='ESRI Shapefile',encoding='utf-8')
    # gdf_l_1.to_file(r'lines_221010_1.shp',driver='ESRI Shapefile',encoding='utf-8')

    # 基于lst_stationloc为中心点
    lst_stationloc = gpd.read_file(r'C:\Users\dell\OneDrive\!!!!厦门\code\shp\pytoshp\厦门地铁.shp')
    # lst_stationloc = gpd.read_file(r'C:\Users\dell\OneDrive\!!!!厦门\code\shp\pytoshp\厦门地铁_select.shp')
    lst_stationloc['lng'] = lst_stationloc.geometry.x
    lst_stationloc['lat'] = lst_stationloc.geometry.y


name_ = []
geometry_ = []
geometry_bezier_ = []

for i in lst_stationloc.values:
    # e.g.为镇海路
    stationname = i[1]
    print(stationname)
    lng = i[3]
    lat = i[4]
    # print(stationname, lng, lat)

    # 选择 起点在镇海路站的订单线图层
    gdf_l_0_stationname = gdf_l_0[gdf_l_0['stationnam'] == stationname]
    # 删除重复值
    gdf_l_0_stationname_coord = gdf_l_0_stationname[['LONGITUD_1', 'LATITUDE_1']].drop_duplicates()

    # 如果与地铁出入口相关的线路少于三条，基于终点坐标的面无法生成，故lines<3的地铁出入口数据舍弃
    if len(gdf_l_0_stationname_coord) >= 3:
        # 把lng,lat变成float
        gdf_l_0_stationname_coord['LONGITUD_1'] = gdf_l_0_stationname_coord['LONGITUD_1'].apply(lambda x:float(x))
        gdf_l_0_stationname_coord['LATITUDE_1'] = gdf_l_0_stationname_coord['LATITUDE_1'].apply(lambda x:float(x))

        if 1==1:

            # 统计镇海路中心点到各个订单起/终点的角度和距离
            lst_dis = []
            lst_azi2 = []
            r = gdf_l_0_stationname_coord.values.tolist()
            for i in r:
                # 把list里面的坐标从str变成float
                # r1 = list(map(float,i))
                geoo = Geodesic.WGS84.Inverse(lat,lng,i[1],i[0])
                lst_dis.append(geoo['s12'])
                lst_azi2.append(geoo['azi2'])

            # azi2为以lst_stationloc为中心点 剩下的点与他的角度
            gdf_l_0_stationname_coord['azi2'] = lst_azi2
            # s12为以lst_stationloc为中心点 剩下的点与他的距离 （投影坐标系）
            gdf_l_0_stationname_coord['s12'] = lst_dis
            # 根据角度升序排序，保证出来的polygon图形是一个合理的图形
            gdf_l_0_stationname_coord = gdf_l_0_stationname_coord.sort_values(by=['azi2'])
            lst_degree_origin = gdf_l_0_stationname_coord[['LONGITUD_1', 'LATITUDE_1']].values.tolist()
            po_origin = gpd.GeoSeries(Polygon(lst_degree_origin))
            # po_origin.to_file('outfile_origin.shp', driver='ESRI Shapefile')

            # 简化订单起/终点数据，每10度根据这10度里面的avg距离和avg角度简化点
            lst_ra = [i for i in range(-180,180,10)]
            # 统计角度
            def findloc(lst,a):
                r = 0
                for i in lst:
                    if a >i:
                        r = i
                    else:
                        return (r +i)/2

            gdf_l_0_stationname_coord['degree'] = gdf_l_0_stationname_coord['azi2'].apply(lambda x:findloc(lst_ra, x))
            # print(gdf_l_0_stationname_coord.head())
            # print(gdf_l_0_stationname_coord[gdf_l_0_stationname_coord['degree'] == -175])
            def ppercent(x):
                return round(np.percentile(x.tolist(),85),3)

            # 升序排列 得到85%分位数数据作为
            gdf_l_0_zhenhailu_coord_per85 = gdf_l_0_stationname_coord.groupby(['degree'])['s12'].apply(ppercent).reset_index()

            lst_lon2 = []
            lst_lat2 = []
            for i in gdf_l_0_zhenhailu_coord_per85.values:
                loca = Geodesic.WGS84.Direct(lat,lng, i[0], i[1])
                lst_lat2.append(loca['lat2'])
                lst_lon2.append(loca['lon2'])

            # 得到每10度avg之后的点
            lst_degree_10 = [list(i) for i in zip(lst_lon2,lst_lat2)]
            name_.append(stationname)
            geometry_.append(Polygon(lst_degree_10))

        if 1==1:
            points =np.array(lst_degree_origin)
            bx,by = evaluate_bezier(points,100)
            lst_bezier_origin = [[i,j] for i,j in zip(bx,by)]
            geometry_bezier_.append(Polygon(lst_bezier_origin))
print(len(name_),len(geometry_),len(geometry_bezier_))
# 统计数据
# 每10度合并 并取85%分位数距离作为dis属性 生成面图层
po_degree_10_per85 = gpd.GeoDataFrame({'name':name_,'geometry':geometry_}, crs="EPSG:4326")
# 基于出入口订单数据对外点和贝塞尔曲线 生成面图层
po_degree_bezier_100 = gpd.GeoDataFrame({'name':name_,'geometry':geometry_bezier_}, crs="EPSG:4326")
po_degree_10_per85.to_file('outfile_degree_10_per85_1014.shp', driver='ESRI Shapefile',encoding='utf-8')
po_degree_bezier_100.to_file('outfile_degree_bezier_100_1014.shp', driver='ESRI Shapefile',encoding='utf-8')

print('done')










