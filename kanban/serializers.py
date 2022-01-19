from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Board, BoardActivities, Portfolio, Project, UserDirectMessages, Workspace, ProjectGroupeChat, Wiki
from vifApp.models import User



class WorkspaceSerializer(serializers.ModelSerializer):
    workspace_name = serializers.CharField(required=True, min_length=2)
    work_email = serializers.EmailField(max_length=None, min_length=None, allow_blank=True)  
    class Meta:
        model = Workspace
        fields = ("workspace_name", "workspace_uuid", "work_email")  


class PortfolioSerializer(serializers.ModelSerializer):
    portfolio_name = serializers.CharField(required=True, min_length=2)
    pined_portfolio = serializers.BooleanField(default=False)
    class Meta:
        model = Portfolio
        fields = ("portfolio_name", "portfolio_uuid", "pined_portfolio", "created_at") 


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ("name", "board")

class BoardActivitiesSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source="board.prj.portfolio.workspace.workspace_user.name")
    class Meta:
        model = BoardActivities
        fields = ("name", "activity_user_email", "activity_description", "activity_type", "activity_date")

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


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "project_uuid", "created_at")

class KanbanProjectSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    projectdescription = serializers.CharField(allow_blank=True)
    agileframwork = serializers.CharField(required=True)
    productowner = serializers.EmailField(required=False, max_length=None, min_length=None, allow_blank=True)
    scrummaster = serializers.EmailField(required=False, max_length=None, min_length=None, allow_blank=True)

    def validate(self, data):
        stts = data.get('agileframwork')
        if not stts in ['Kanban', 'Scrum']:
            raise ValidationError({"agileframwork": "should be (Kanban or Scrum)"})
        return data


class WikiSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(read_only=True, source="wiki_project.name")
    class Meta:
        model = Wiki
        fields = ("id", "project_name", "wiki_content", "wiki_created_at", "wiki_updated_at")


class WikiUpdateSerializer(serializers.Serializer):
    body = serializers.CharField(required=True)
    id = serializers.IntegerField(required=True)


class InviteUsersSerializer(serializers.Serializer):
    users_email = serializers.ListField(required=True)
    def validate(self, data):
        l = data.get('users_email')
        for i in l:
            if not i["role"] in ['Product owner', 'Scrum master', 'Project manager', 'Team member']:
                raise ValidationError({"role": "should be ('Product owner', 'Scrum master', 'Project manager' or 'Team member')"})
        return data


class ProjectRolesSerializer(serializers.Serializer):
    role = serializers.CharField(required=True)
    def validate(self, data):
        rl = data.get('role')
        if not rl in ['Product owner', 'Scrum master', 'Project manager', 'Team member']:
            raise ValidationError({"role": "should be ('Product owner', 'Scrum master', 'Project manager' or 'Team member')"})
        return data


class GroupeChatSerializer(serializers.ModelSerializer):
    auditor_name = serializers.CharField(read_only=True, source="auditor.name")
    auditor_email = serializers.CharField(read_only=True, source="auditor.email")
    class Meta:
        model = ProjectGroupeChat
        fields = ("auditor_name", "auditor_email", "content", "attachments", "timestamp")
    

class UserMsgsSerializer(serializers.ModelSerializer):
    sender_user = serializers.CharField(read_only=True, source="sender_user.email")
    receiver_user = serializers.CharField(read_only=True, source="receiver_user.email")
    class Meta:
        model = UserDirectMessages
        fields = ("sender_user", "receiver_user", "content", "attachments", "timestamp")


class TaskSerializer(serializers.Serializer):
    board = serializers.CharField(required=True)
    col = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
