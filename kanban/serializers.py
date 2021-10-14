from rest_framework import serializers
from .models import Portfolio, Project



class PortfolioSerializer(serializers.Serializer):
    model = Portfolio
    portfolio_name = serializers.CharField(required=True)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name",)


class PPSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(read_only=True, source="portfolio.portfolio_name")
    class Meta:
        model = Project
        fields = ("portfolio_name", "name")


class KanbanBoardSerializer(serializers.Serializer):
    portfolio = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    projectdescription = serializers.CharField(required=False)
    agileframwork = serializers.CharField(required=True)
    productowner = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)
    scrummaster = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)


class TaskSerializer(serializers.Serializer):
    portfolio = serializers.CharField(required=True)
    project = serializers.CharField(required=True)
    col = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
