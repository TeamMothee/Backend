import requests
import os
from urllib.parse import quote


def calculate_midpoint_and_circle(start, end, factor=1.1):
    """
    출발점과 목적점의 중점과 반지름을 계산합니다.
    :param start: 출발지 좌표 (x, y)
    :param end: 목적지 좌표 (x, y)
    :param factor: 반지름을 확장할 비율 (디폴트: 1.1)
    :return: 중점, 반지름
    """
    midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    radius = ((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2) ** 0.5 * factor
    return midpoint, radius


def points_within_circle(points, center, radius):
    """
    주어진 원 내부에 있는 점들을 필터링합니다.
    :param points: 후보 점들 [(x, y, weight), ...]
    :param center: 원의 중심 좌표 (x, y)
    :param radius: 원의 반지름
    :return: 원 안에 있는 점들
    """
    filtered_points = []
    for point in points:
        # 좌표와 중심 좌표의 차이를 계산하여 거리 계산
        distance = ((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) ** 0.5

        # 거리가 반지름 이내인 점을 필터링
        if distance <= radius:
            filtered_points.append(point)

    return filtered_points


def select_highest_safety_points(points):
    """
    안전도를 기준으로 가장 높은 두 점을 선택합니다.
    :param points: [(x, y, safety_score), ...]
    :return: [(x1, y1), (x2, y2)]
    """
    # 안전도 기준으로 내림차순 정렬하여 가장 높은 두 점을 반환
    return sorted(points, key=lambda p: p[2], reverse=True)[:2]


def calculate_path_response(start, end, passList=None):
    """
    TMap API를 호출하여 경로 응답 데이터를 반환합니다.
    :param start: 출발지 좌표 (x, y)
    :param end: 도착지 좌표 (x, y)
    :param passList: 경유지 리스트
    :return: TMap API 응답 데이터 또는 None
    """
    url = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "appKey": os.environ.get("TMAP_APP_KEY"),
    }

    payload = {
        "startX": start[0],
        "startY": start[1],
        "endX": end[0],
        "endY": end[1],
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "startName": quote("출발지"),
        "endName": quote("목적지"),
        "searchOption": "0",  # 최단거리 검색
        "sort": "index",
    }

    if passList:
        payload["passList"] = "_".join([f"{p[0]},{p[1]}" for p in passList])

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"TMap API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None


def find_optimal_route(start, end, candidates, alpha=1.5):
    """
    최적 경로의 TMap API 응답 데이터를 반환합니다.
    :param start: 출발지 좌표 (x, y)
    :param end: 도착지 좌표 (x, y)
    :param candidates: 후보 점들의 리스트 [(x1, y1, weight), ...]
    :param alpha: 최단 경로 대비 허용 배수
    :return: 최적 경로에 대한 TMap API 응답 데이터
    """
    # S → E 최단 경로 시간 및 응답 데이터
    shortest_response = calculate_path_response(start, end)
    if not shortest_response:
        return None

    shortest_time = shortest_response["features"][0]["properties"].get(
        "totalTime", float("inf")
    )

    # 후보 점이 2개일 경우 처리
    if len(candidates) >= 2:
        a, b = candidates[:2]  # 첫 두 후보를 a, b로 설정
        paths = [
            calculate_path_response(start, end, passList=[a]),
            calculate_path_response(start, end, passList=[b]),
            calculate_path_response(start, end, passList=[a, b]),
            calculate_path_response(start, end, passList=[b, a]),
        ]

        # 유효한 응답만 필터링
        valid_paths = [r for r in paths if r]

        # 유효한 경로가 없으면 최단 경로 응답 반환
        if not valid_paths:
            return shortest_response

        # 최적 경로 선택
        optimal_response = min(
            valid_paths,
            key=lambda r: r["features"][0]["properties"].get("totalTime", float("inf")),
        )

        # 최적 경로 시간이 alpha 배수보다 크면 None 반환
        if (
            optimal_response["features"][0]["properties"].get("totalTime", float("inf"))
            > alpha * shortest_time
        ):
            return None

        return optimal_response

    # 후보 점이 없거나 1개인 경우
    return shortest_response
