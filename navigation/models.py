from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission


class User(AbstractUser):
    # 기본 내장 auth 앱의 User 모델과 사용자 정의 users 앱의 User 모델 사이의 충돌 방지
    groups = models.ManyToManyField(Group, related_name="custom_user_set")
    user_permissions = models.ManyToManyField(
        Permission, related_name="custom_user_set"
    )


class RoadStructure(models.Model):
    """
    교차점 별 위험 구조물 여부
    """

    # 점자블록(설치 0, 미흡 1, 미설치 2)
    braille_block = models.IntegerField(default=0, blank=True)
    # 음향신호기(설치 0, 미설치 1)
    audio_signal = models.IntegerField(default=0, blank=True)
    # 볼라드(미설치 0, 올바른 설치 1, 잘못된 설치 2)
    bollard = models.IntegerField(default=0, blank=True)
    # 위험도(가중치)
    weight = models.FloatField(default=0.0, blank=True)
    # 위도
    latitude = models.FloatField()
    # 경도
    longitude = models.FloatField()

    @classmethod
    def create_table(cls, **kwargs):
        road_structure = cls(
            braille_block=kwargs.get("braille_block"),
            audio_signal=kwargs.get("audio_signal"),
            bollard=kwargs.get("bollard"),
            weight=kwargs.get("weight"),
            latitude=kwargs.get("latitude"),
            longitude=kwargs.get("longitude"),
        )
        road_structure.save()

    @classmethod
    def delete_table(cls, latitude, longitude):
        try:
            road_structure = cls.objects.get(latitude=latitude, longitude=longitude)
            road_structure.delete()
        except cls.DoesNotExist:
            pass
