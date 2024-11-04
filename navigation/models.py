from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission


class User(AbstractUser):
    # 기본 내장 auth 앱의 User 모델과 사용자 정의 users 앱의 User 모델 사이의 충돌 방지
    groups = models.ManyToManyField(Group, related_name="custom_user_set")
    user_permissions = models.ManyToManyField(
        Permission, related_name="custom_user_set"
    )


class Detection(models.Model):
    """
    사용자 제보 위험 구조물
    """

    # user_id = models.ForeignKey(
    #     User, on_delete=models.CASCADE, related_name="detected_danger"
    # )
    image = models.ImageField(upload_to="images/")
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_table(cls, image, latitude, longitude):
        detection = cls(image=image, latitude=latitude, longitude=longitude)
        detection.save()

    @classmethod
    def delete_table(cls, latitude, longitude):
        try:
            detection = cls.objects.get(latitude=latitude, longitude=longitude)
            detection.delete()
        except cls.DoesNotExist:
            pass


class RoadStructure(models.Model):
    """
    교차점 별 위험 구조물 여부
    """

    # 설치 0, 미흡 1, 미설치 2
    braille_block = models.FloatField()
    audio_signal = models.FloatField()
    bollard = models.FloatField()
    weight = models.IntegerField()  # 가중치
    latitude = models.FloatField()
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
