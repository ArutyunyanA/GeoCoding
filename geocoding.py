from flask import Flask, render_template, request, redirect, url_for
from constant import API_KEY
import requests
import folium

def get_coordinate(API_KEY, address):
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
    params = {
        'access_token': API_KEY,
        'limit': 1  # Ограничить результат одним ответом
    }
    response = requests.get(url, params=params)
    try:
        data = response.json()
        if data['features']:
            coordinates = data['features'][0]['geometry']['coordinates']
            print(f"Координаты для '{address}': {coordinates}")
            return coordinates
        else:
            print(f"Не удалось получить координаты: {address}")
            return None
    except requests.exceptions.ConnectionError as error:
        print(f"Не удалось подключиться к серверу: {error}")
        return None

def get_routes(API_KEY, coords1, coords2):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords1[0]},{coords1[1]};{coords2[0]},{coords2[1]}"
    params = {
        'access_token': API_KEY,
        'alternatives': 'true',  # Запрос альтернативных маршрутов
        'geometries': 'geojson'  # Получение геометрии маршрутов в формате GeoJSON
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        if 'routes' in data and data['routes']:
            routes = data['routes']
            return routes
        else:
            print(f"Ошибка в ответе API: {data}")
            return None
    except requests.exceptions.ConnectionError as error:
        print(f"Не удалось подключиться к серверу: {error}")
        return None

def find_best_routes(routes):
    if not routes:
        return None, None
    
    shortest_route = min(routes, key=lambda x: x['distance'])
    fastest_route = min(routes, key=lambda x: x['duration'])
    
    return shortest_route, fastest_route

def visualize_routes(routes, coords_a, coords_b):
    map_ = folium.Map(location=[(coords_a[1] + coords_b[1]) / 2, (coords_a[0] + coords_b[0]) / 2], zoom_start=13)
    colors = ['blue', 'green', 'red']

    for i, route in enumerate(routes):
        points = route['geometry']['coordinates']
        points = [(point[1], point[0]) for point in points]  # Переставить координаты местами (lat, lon)
        
        folium.PolyLine(points, color=colors[i % len(colors)], weight=5, opacity=0.8).add_to(map_)
    
    folium.Marker(location=[coords_a[1], coords_a[0]], popup='Start').add_to(map_)
    folium.Marker(location=[coords_b[1], coords_b[0]], popup='End').add_to(map_)

    map_.save('routes_map.html')
    print("Маршруты визуализированы и сохранены в 'routes_map.html'")

def main():
    origin_address = input("Введите адрес отправления (включая город и страну):\nПример: Vojkova 78, Ljubljana, Slovenia\n")
    destination_address = input("Введите адрес назначения (включая город и страну):\nПример: Rimska 5, Ljubljana, Slovenia\n")
    coords_a = get_coordinate(API_KEY, origin_address)
    coords_b = get_coordinate(API_KEY, destination_address)
    if coords_a and coords_b:
        routes = get_routes(API_KEY, coords_a, coords_b)
        if routes:
            shortest_route, fastest_route = find_best_routes(routes)
            
            if shortest_route:
                print(f"Кратчайший маршрут:\nРасстояние: {shortest_route['distance'] / 1000:.2f} км\nВремя: {shortest_route['duration'] / 60:.2f} минут")
            
            if fastest_route:
                print(f"Самый быстрый маршрут:\nРасстояние: {fastest_route['distance'] / 1000:.2f} км\nВремя: {fastest_route['duration'] / 60:.2f} минут")
            
            # Визуализация маршрутов на карте
            visualize_routes(routes, coords_a, coords_b)
        else:
            print("Не удалось получить маршруты.")
    else:
        print("Не удалось получить координаты для одного из адресов.")

if __name__ == "__main__":
    main()
