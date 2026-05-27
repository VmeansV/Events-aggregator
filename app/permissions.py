from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission


class UnauthenticatedAPIKey(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid or missing API Key."


class HasLMSAPIKey(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get("x-api-key")
        correct_key = settings.LMS_API_KEY

        if api_key == correct_key:
            return True

        raise UnauthenticatedAPIKey()
