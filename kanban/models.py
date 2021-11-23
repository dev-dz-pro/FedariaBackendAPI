from django.db import models
from vifApp.models import User
from django.utils import timezone
import datetime
import uuid


class Workspace(models.Model):
    workspace_user = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace_name = models.CharField(max_length=100)
    workspace_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    work_email = models.EmailField(max_length=100)
    class Meta:
        unique_together = ('workspace_name', 'workspace_user') 
    def __str__(self):
        return self.workspace_name + "  ("+  self.workspace_user.email + ")"

class Portfolio(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    portfolio_name = models.CharField(max_length=50)
    portfolio_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    pined_portfolio = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('portfolio_name', 'workspace') 
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.portfolio_name + "  ("+  self.workspace.workspace_name + ")  -  ("+  self.workspace.workspace_user.email + ")"


class Project(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    name = models.CharField(max_length=50) 
    project_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    invited_users = models.JSONField(null=True)
    project_description = models.CharField(max_length=250)
    pined_project = models.BooleanField(default=False)
    AGILE_CHOICES = [('Scrum', 'Scrum'), ('Kanban', 'Kanban')]
    agile_framwork = models.CharField(max_length=6, choices=AGILE_CHOICES, default='Kanban') 
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('name', 'portfolio')
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.name + " | "+  self.portfolio.portfolio_name + " | "+  self.portfolio.workspace.workspace_user.username


def board_default():
    return [{"Backlog":[]}, {"To Do":[]}, {"In Progress":[]}, {"Done":[]}]


class Board(models.Model):
    prj = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    board = models.JSONField(default=board_default)
    class Meta:
        unique_together = ('name', 'prj') 
    def __str__(self):
        return self.prj.name + " | " + self.name


class BoardActivities(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    activity_user_email = models.EmailField(max_length=100)
    activity_description = models.CharField(max_length=250)
    activity_date = models.DateTimeField(auto_now_add=True)
    activity_type = models.CharField(max_length=50)  #v chqnge to slqg 


class InvitedProjects(models.Model):
    iuser = models.ForeignKey(User, on_delete=models.CASCADE)
    inviter_project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='+')
    workspace_uid = models.UUIDField(editable=False) 
    portfolio_uid = models.UUIDField(editable=False)
    project_uid = models.UUIDField(editable=False)
    class Meta:
        unique_together = ('iuser', 'inviter_project') 
    def __str__(self):
        return self.iuser.email + "    --> Invitation from  (" + self.inviter_project.portfolio.workspace.workspace_user.email + ")    --> Project  (" + self.inviter_project.name + ")"



