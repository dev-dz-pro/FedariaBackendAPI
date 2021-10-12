from django.db import models
from vifApp.models import User
from django.utils import timezone
import datetime



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
        return self.portfolio_name

def board_default():
    return {"board": [
                        {"Backlog":[]}, 
                        {"To Do":[]},
                        {"In Progress":[]},
                        {"Done":[]},
                    ]
            }


class Project(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    project_description = models.CharField(max_length=250)
    pined_project = models.BooleanField(default=False)
    AGILE_CHOICES = [('Scrum', 'Scrum'), ('Kanban', 'Kanban')]
    agile_framwork = models.CharField(max_length=6, choices=AGILE_CHOICES, default='Kanban') 
    product_owner = models.EmailField(max_length=254)
    scrum_master = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    board = models.JSONField(default=board_default)
    class Meta:
        unique_together = ('name', 'portfolio')
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return str(self.agile_framwork) + " - " + self.name

