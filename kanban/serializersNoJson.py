from rest_framework import serializers
from .models import Portfolio, KanbanBoard, Task

class PortfolioSerializer(serializers.Serializer):
    model = Portfolio
    portfolio_name = serializers.CharField(required=True)


class KanbanBoardSerializer(serializers.Serializer):
    model = KanbanBoard
    portfolio = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    projectdescription = serializers.CharField(required=True)
    agileframwork = serializers.CharField(required=True)
    productowner = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)
    scrummaster = serializers.EmailField(max_length=None, min_length=None, allow_blank=False)


class TaskSerializer(serializers.Serializer):
    model = Task
    portfolio = serializers.CharField(required=True)
    project = serializers.CharField(required=True)
    col = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
