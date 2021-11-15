from django.urls import path
from . import views

urlpatterns = [
    path('portfolios/', views.AllPortfoliosView.as_view(), name="portfolios"),
    path('create_portfolio/', views.CreatePortfolio.as_view(), name="create-portfolio"),
    path('pin_unpin_portfolio/<str:pf>/<int:state>/', views.PinPortfolio.as_view(), name="pin-unpin-portfolio"),

    path('create_project/', views.CreateProject.as_view(), name="create-project"),
    path('project/<str:pf>/<str:prjct>/', views.GetProject.as_view(), name="project"),
    path('projects/', views.GetAllProjects.as_view(), name="projects"), 
    # path('search_project/<str:project_name>/', views.Search4Project.as_view(), name="search-project"), # wss

    # path('create_board/', views.CreateBoard.as_view(), name="create-board"),  # wss
    # path('board/<str:pf>/<str:prj>/<str:brd>/', views.GetBoard.as_view(), name="board"), # wss

    # path('create_task/', views.CreateTaskView.as_view(), name="create-task"), # wss
    # path('task/<str:pf>/<str:prjct>/<str:brd>/<int:col_pos>/<int:task_pos>/', views.GetTaskView.as_view(), name="get-task"),
    path('task/aws_files/', views.UplaodFileAWS.as_view(), name="aws-files"), 

    # path('change_tasks_col/<str:pf>/<str:prjct>/<str:from_col>/<str:tasks_ids>/<str:to_col>/<int:in_pos>/', views.ChangeTasksCol.as_view(), name="change-tasks-col"), # wss
    
    # path('add_col/<str:pf>/<str:prjct>/<str:colname>/', views.AddCol.as_view(), name="add-col"), # wss
    # path('delete_col/<str:pf>/<str:prjct>/<int:col_index>/', views.DeleteCol.as_view(), name="delete-col"), # wss
    # path('change_col_order/<str:pf>/<str:prjct>/<int:col_index>/<int:to_index>/', views.ChangeColOrder.as_view(), name="change-col-order"), # wss
]