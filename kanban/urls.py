from django.urls import path
from . import views

urlpatterns = [
    path('workspaces/', views.AddGetWorkspaces.as_view(), name="workspace"),
    path('workspaces/<uuid:workspace_uid>/', views.SetGetWorkspace.as_view(), name="set-workspace"),

    path('workspaces/<uuid:workspace_uid>/portfolios/', views.AddGetPortfolios.as_view(), name="portfolios"),
    path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/', views.SetGetPortfolio.as_view(), name="set-portfolio"),
    path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/<int:state>/', views.PinPortfolio.as_view(), name="pin-unpin-portfolio"),


    path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/projects/', views.CreateProject.as_view(), name="create-project"),
    path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/projects/<uuid:project_uid>/', views.GetProject.as_view(), name="project"),
    path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/projects/<uuid:project_uid>/<int:state>/', views.PinUnpinProject.as_view(), name="pin-unpin-project"),
    path('workspaces/<uuid:workspace_uid>/projects/', views.GetAllProjects.as_view(), name="projects"), 

    # path('search_project/<str:project_name>/', views.Search4Project.as_view(), name="search-project"), # wss

    # path('create_board/', views.CreateBoard.as_view(), name="create-board"),  # wss
    # path('board/<str:pf>/<str:prj>/<str:brd>/', views.GetBoard.as_view(), name="board"), # wss

    # path('create_task/', views.CreateTaskView.as_view(), name="create-task"), # wss
    # path('task/<str:pf>/<str:prjct>/<str:brd>/<int:col_pos>/<int:task_pos>/', views.GetTaskView.as_view(), name="get-task"),
    path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/projects/<uuid:project_uid>/upload_file/', views.UplaodFileAWS.as_view(), name="aws-files"), 

    # path('change_tasks_col/<str:pf>/<str:prjct>/<str:from_col>/<str:tasks_ids>/<str:to_col>/<int:in_pos>/', views.ChangeTasksCol.as_view(), name="change-tasks-col"), # wss
    # TODO path('workspaces/<uuid:workspace_uid>/portfolios/<uuid:portfolio_uid>/projects/<uuid:project_uid>/csv_test/', views.ProjectActivities.as_view(), name="csv-test"), 
    # path('add_col/<str:pf>/<str:prjct>/<str:colname>/', views.AddCol.as_view(), name="add-col"), # wss
    # path('delete_col/<str:pf>/<str:prjct>/<int:col_index>/', views.DeleteCol.as_view(), name="delete-col"), # wss
    # path('change_col_order/<str:pf>/<str:prjct>/<int:col_index>/<int:to_index>/', views.ChangeColOrder.as_view(), name="change-col-order"), # wss
]