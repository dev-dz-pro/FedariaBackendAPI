from django.contrib import admin
from .models import Project, Portfolio, Board, InvitedProjects, Workspace, BoardActivities

admin.site.register(Workspace)
admin.site.register(InvitedProjects)
admin.site.register(Portfolio)
admin.site.register(Project)
admin.site.register(Board)
admin.site.register(BoardActivities)



