from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Board, Portfolio, Project, Workspace



class WorkspaceSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(required=True)
    work_email = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)  
    class Meta:
        model = Workspace
        fields = ("workspace_name", "workspace_uuid", "work_email")  


class PortfolioSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(required=True)
    class Meta:
        model = Portfolio
        fields = ("portfolio_name", "portfolio_uuid", "pined_portfolio", "created_at")

    # def validate(self, data):
    #     _name = data.get('portfolio_name')
    #     if str(_name).__contains__('/'):  
    #         raise ValidationError({"portfolio name": "field should not contain '/'."})
    #     return data


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "project_uuid", "created_at")


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ("name", "board")

class PSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ("portfolio_name",)

class PPSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(read_only=True, source="portfolio.portfolio_name")
    class Meta:
        model = Project
        fields = ("portfolio_name", "name")


class BPPSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(read_only=True, source="prj.portfolio.portfolio_name")
    project_name = serializers.CharField(read_only=True, source="prj.name")
    class Meta:
        model = Board
        fields = ("portfolio_name", "project_name", "name")


class KanbanProjectSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    projectdescription = serializers.CharField(allow_blank=True)
    agileframwork = serializers.CharField(required=True)
    productowner = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)
    scrummaster = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)

    # def validate(self, data):
    #     _name = data.get('name')
    #     if str(_name).__contains__('/'):  
    #         raise ValidationError({"name": "field should not contain '/'."})
    #     return data
            


class TaskSerializer(serializers.Serializer):
    board = serializers.CharField(required=True)
    col = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
