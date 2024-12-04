import io

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.settings import AI_URL
from .models import RoadStructure
from .function import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import requests
from PIL import Image


class FindRouteView(APIView):
    @swagger_auto_schema(
        operation_summary="경로 탐색 요청",
        operation_description="Find route to the destination",
        manual_parameters=[
            openapi.Parameter(
                "start_x",
                openapi.IN_QUERY,
                description="출발지 경도",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "start_y",
                openapi.IN_QUERY,
                description="출발지 위도",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_x",
                openapi.IN_QUERY,
                description="목적지 경도",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_y",
                openapi.IN_QUERY,
                description="목적지 위도",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: "OK",
            400: "Invalid input arguments",
            404: "Route not found",
        },
    )
    def get(self, request, *args, **kwargs):
        start_x = request.GET.get("start_x")
        start_y = request.GET.get("start_y")
        end_x = request.GET.get("end_x")
        end_y = request.GET.get("end_y")
        if not all([start_x, start_y, end_x, end_y]):
            return Response(
                {"error": "Invalid input arguments"}, status=status.HTTP_400_BAD_REQUEST
            )

        route = self.find_route(start_x, start_y, end_x, end_y)
        if not route:
            return Response(
                {"error": "Route not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(route, status=status.HTTP_200_OK)

    def find_route(self, start_x, start_y, end_x, end_y):
        # 출발지와 목적지 좌표
        start = (float(start_x), float(start_y))
        end = (float(end_x), float(end_y))

        # PostgreSQL에서 후보 좌표들 가져오기
        locations = RoadStructure.objects.all()  # 전체 좌표를 가져옴
        candidates = [
            (loc.longitude, loc.latitude, loc.weight) for loc in locations
        ]  # safety_score는 weight에 해당

        # 출발점과 목적점을 포함하는 일정 크기의 원 내에서 경유지 후보 필터링
        midpoint, radius = calculate_midpoint_and_circle(start, end)
        filtered_candidates = points_within_circle(candidates, midpoint, radius)
        optimal_filtered_candidates = select_highest_safety_points(filtered_candidates)

        # 최적 경로 계산
        optimal_route = find_optimal_route(
            start, end, optimal_filtered_candidates, alpha=1.5
        )
        return optimal_route


class ReportView(APIView):
    @swagger_auto_schema(
        operation_summary="위험 구조물 제보",
        operation_description="Report a dangerous structure",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "latitude": openapi.Schema(type=openapi.TYPE_NUMBER),
                "longitude": openapi.Schema(type=openapi.TYPE_NUMBER),
            },
        ),
        responses={
            200: "OK",
            400: "Invalid input arguments",
        },
    )
    def patch(self, request, *args, **kwargs):
        try:
            latitude = request.data["latitude"]
            longitude = request.data["longitude"]
        except KeyError:
            return Response(
                {"error": "Invalid input arguments"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 이미 존재하는 구조물이면 DB 업데이트(weight 증가), 없으면 새로 추가
        try:
            road_structure = RoadStructure.objects.get(
                latitude=latitude, longitude=longitude
            )
            road_structure.weight += 0.5
            road_structure.save()
        except RoadStructure.DoesNotExist:
            RoadStructure.objects.create(
                latitude=latitude, longitude=longitude, weight=0.5
            )

        return Response(status=status.HTTP_200_OK)


class CallImageCaptionView(APIView):
    @swagger_auto_schema(
        operation_summary="이미지 캡션 생성",
        operation_description="Create a caption for the image",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "image": openapi.Schema(type=openapi.TYPE_FILE),
            },
        ),
        responses={
            200: "OK",
            400: "Invalid input arguments",
            404: "Failed to generate caption",
        },
    )
    def patch(self, request, *args, **kwargs):
        try:
            # 이미지 파일 가져오기
            image = request.FILES["image"]

            # Pillow로 이미지 열어서 원본 형식으로 저장
            image_file = Image.open(image)
            buffer = io.BytesIO()
            image_file.save(buffer, format=image_file.format)
            buffer.seek(0)

            # AI 서버로 이미지 전송
            files = {"image": (image.name, buffer, image.content_type)}
            caption = requests.post(AI_URL, files=files)
            if caption.status_code != 200:
                return Response(
                    {"error": "Failed to generate caption"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(caption, status=status.HTTP_200_OK)
        # request에 이미지 파일이 없는 경우
        except KeyError:
            return Response(
                {"error": "Invalid input arguments"}, status=status.HTTP_400_BAD_REQUEST
            )
        # AI Image Captioning 서버와 통신 실패
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
