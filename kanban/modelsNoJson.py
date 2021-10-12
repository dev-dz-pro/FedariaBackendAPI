from django.db import models
from vifApp.models import User
from django.utils import timezone
import datetime



class Portfolio(models.Model):
    portfolio_user = models.ForeignKey(User, on_delete=models.CASCADE)
    portfolio_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = (('portfolio_name', 'portfolio_user'),)
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return self.portfolio_name


class KanbanBoard(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    project_description = models.CharField(max_length=250)
    AGILE_CHOICES = [('Scrum', 'Scrum'), ('Kanban', 'Kanban')]
    agile_framwork = models.CharField(max_length=6, choices=AGILE_CHOICES, default='Kanban') # models.TextChoices('Kanban', 'Scrum')
    product_owner = models.EmailField(max_length=254)
    scrum_master = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = (('name', 'portfolio'),)
    def was_published_today(self):
        return self.created_at >= timezone.now() - datetime.timedelta(days=1)
    def __str__(self):
        return str(self.agile_framwork) + " - " + self.name


class BoardCol(models.Model):
    board = models.ForeignKey(KanbanBoard, on_delete=models.CASCADE)
    col_name = models.CharField(max_length=50) 
    class Meta:
        unique_together = (('board', 'col_name'),)
    def __str__(self):
        return self.col_name + " - Project(" + self.board.name + ")"


class Task(models.Model):
    col = models.ForeignKey(BoardCol, on_delete=models.CASCADE)
    des = models.CharField(max_length=250) 
    id_col = models.BigIntegerField() 
    class Meta:
        unique_together = (('col', 'id_col'),)
    def __str__(self):
        return str(self.col_id) + " - " + self.des  + " - " + self.col.col_name + " - " + self.col.board.name







# def contact_default():
#     return {"email": "to1@example.com"}

# contact_info = JSONField("ContactInfo", default=contact_default)
