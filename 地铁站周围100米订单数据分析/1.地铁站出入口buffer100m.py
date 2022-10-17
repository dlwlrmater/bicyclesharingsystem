import geopandas as gpd
import pandas as pd

pd.set_option('display.width',None)
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)

# 数据来源为osm数据+基于谷歌地球历史影像数据（2021/1/19）标注
gdf_p = gpd.read_file(r'C:\Users\dell\OneDrive\!!!!厦门\code\厦门地铁出入口.gpkg')
# 在做缓冲区的时候修改为投影坐标系
gdf_p = gdf_p.to_crs('epsg:3349')
# 缓冲区为圆半径为100
gdf_p['buffer'] = gdf_p.buffer(distance=100)
# 图层从点变成面
gdf_buffer = gdf_p.drop(columns=['geometry']).set_geometry('buffer')
gdf_buffer = gdf_buffer.to_crs('epsg:4326')
gdf_buffer.to_file(r'厦门地铁出入口buffer.gpkg',driver='GPKG')
print(gdf_buffer.head())