from django.db import models
from vifApp.models import User
from django.utils import timezone
import datetime
import uuid



class Portfolio(models.Model):
    portfolio_user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio_name = models.CharField(max_length=50)
    pined_portfolio = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('portfolio_name', 'portfolio_user') 
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.portfolio_name + " | "+  self.portfolio_user.username


class Project(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    name = models.CharField(max_length=50) 
    invited_users = models.JSONField(null=True)
    project_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    project_description = models.CharField(max_length=250)
    pined_project = models.BooleanField(default=False)
    AGILE_CHOICES = [('Scrum', 'Scrum'), ('Kanban', 'Kanban')]
    agile_framwork = models.CharField(max_length=6, choices=AGILE_CHOICES, default='Kanban') 
    # product_owner = models.EmailField(max_length=254, blank=True)
    # scrum_master = models.EmailField(max_length=254, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('name', 'portfolio')
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.name + " | "+  self.portfolio.portfolio_name + " | "+  self.portfolio.portfolio_user.username


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


class InvitedProjects(models.Model):
    iuser = models.ForeignKey(User, on_delete=models.CASCADE)
    inviter = models.EmailField(max_length=100)
    project = models.CharField(max_length=101)
    project_uid = models.CharField(max_length=150, null=True)
    class Meta:
        unique_together = ('iuser', 'inviter', 'project')
    def __str__(self):
        return self.iuser.username + "  (" + self.iuser.email + ")  -> Invitation from  (" + self.inviter + ")  ->  (" + self.project + ")"



