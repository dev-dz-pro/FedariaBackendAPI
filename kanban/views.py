from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import InvitedProjects, Portfolio, Project, Workspace, BoardActivities, Board
from vifApp.models import User, UserNotification
from .serializers import (PortfolioSerializer, KanbanProjectSerializer, ProjectSerializer, BoardActivitiesSerializer,
                        BoardSerializer, WorkspaceSerializer)
from rest_framework import generics, status
import jwt
from threading import Thread
from django.db.utils import IntegrityError
from django.conf import settings
from vifApp.utils import VifUtils
import pandas as pd
from django.core.mail import send_mass_mail
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime as dt
import csv
import requests
from django.http import HttpResponse
from rest_framework.parsers import MultiPartParser



'''
WORKSPACE PART
'''
class AddGetWorkspaces(generics.GenericAPIView):
    serializer_class = WorkspaceSerializer

    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        workspaces = Workspace.objects.filter(workspace_user=user)
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my workspaces', 'data': self.serializer_class(workspaces, many=True).data}
        return Response(response)


    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first() 
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            try:
                wrkspc = Workspace.objects.create(workspace_user=user, workspace_name=user_data["workspace_name"], work_email=user_data["work_email"])
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace Already exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'({user_data["workspace_name"]}) Workspace has been created.', "data": self.serializer_class(wrkspc).data}
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)

    
class UpdateGetWorkspace(generics.GenericAPIView):
    serializer_class = WorkspaceSerializer

    def get(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
            if workspace:
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my workspace', 
                            'data': self.serializer_class(workspace).data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 
                        'data': []}
            return Response(response, status.HTTP_400_BAD_REQUEST)


    def put(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
            if workspace:
                workspace.workspace_name = request.data["workspace_name"]
                workspace.work_email = request.data["work_email"]
                workspace.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'workspace updated.', 
                            'data': self.serializer_class(workspace).data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 
                        'data': []}
            return Response(response)
    

    def delete(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
            if workspace:
                workspace.delete()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'workspace deleted.', 'data': []}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception:  
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 'data': []}
            return Response(response)


'''
PORTFOLIO PART
'''

class AddGetPortfolios(generics.GenericAPIView):
    serializer_class = PortfolioSerializer

    def get(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            portfolios = Portfolio.objects.filter(workspace__workspace_uuid=workspace_uid, workspace__workspace_user=user)
            if portfolios:
                data = [{"Portfolio Name": nt.portfolio_name, 
                        "Portfolio uid": nt.portfolio_uuid,
                        "Created at": nt.created_at,
                        "Pined": nt.pined_portfolio,
                        "projects": ProjectSerializer(nt.project_set.all(), many=True).data} 
                        for nt in portfolios] 
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my Portfolios', 'data': data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'No Portfolios exists in the workspace.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 'data': []}
            return Response(response, status.HTTP_400_BAD_REQUEST)

    def post(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user_data = serializer.data
                workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
                if workspace:
                    prtfl = Portfolio.objects.create(workspace=workspace, portfolio_name=user_data["portfolio_name"])
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{user_data["portfolio_name"]} Portfolio has been created.', "data": self.serializer_class(prtfl).data}
                    return Response(response)
                else:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio Already exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class SetGetPortfolio(generics.GenericAPIView):
    serializer_class = PortfolioSerializer

    def get(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            portfolio = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, portfolio_uuid=portfolio_uid).first()
            if portfolio:
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my portfolio', 
                            'data': self.serializer_class(portfolio).data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio or workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 
                        'data': []}
            return Response(response, status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                portfolio = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, 
                                                        portfolio_uuid=portfolio_uid).first()
                if portfolio:
                    portfolio.portfolio_name = request.data["portfolio_name"]
                    portfolio.save()
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'portfolio updated.', 
                                'data': self.serializer_class(portfolio).data}
                    return Response(response)
                else:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists.', 'data': []}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 'data': []}
                return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)    
        user = User.objects.filter(id=payload['id']).first()
        try:
            portfolio = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, 
                                                        portfolio_uuid=portfolio_uid).first()
            if portfolio:
                portfolio.delete()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'portfolio deleted.', 'data': []}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 'data': []}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class PinPortfolio(APIView):
    @swagger_auto_schema(operation_description="workspace_uid & portfolio_uid should be TYPE of **UUID**, and PIN should be **1 or 0**")
    def get(self, request, workspace_uid, portfolio_uid, pin):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        
        # check if pined portfolios greqter then 3
        pined_portfolios = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, pined_portfolio=True).count()
        if pined_portfolios > 2:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': "You cant't pin more then 3 portfolios."}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        
        portfolio = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, 
                                            portfolio_uuid=portfolio_uid).first()
        if portfolio:
            if pin == 1:
                portfolio.pined_portfolio = True
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{portfolio.portfolio_name} pined seccessfuly'}
            else:
                portfolio.pined_portfolio = False
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{portfolio.portfolio_name} unpined seccessfuly'}
            portfolio.save()
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Porfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

'''
Porject PART
'''
class GetAllProjects(APIView):
    def get(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        projects = Project.objects.filter(portfolio__workspace__workspace_user=user, portfolio__workspace__workspace_uuid=workspace_uid)
        data = {}
        if projects:
            my_projects = [{"portfolio_name": prj.portfolio.portfolio_name, "project_name": prj.name, "workspace_uid": prj.portfolio.workspace.workspace_uuid, "portfolio_uid": prj.portfolio.portfolio_uuid, "project_uid": prj.project_uuid, "Pined": prj.pined_project} for prj in projects]
            data["my_projects"] = my_projects
        invited_projects = InvitedProjects.objects.filter(iuser=user)
        if invited_projects: 
            invited_prj_list = [{"portfolio_name": prj.inviter_project.portfolio.portfolio_name, "project_name": prj.inviter_project.name, "workspace_uid": prj.inviter_project.portfolio.workspace.workspace_uuid, "portfolio_uid": prj.inviter_project.portfolio.portfolio_uuid, "project_uid": prj.inviter_project.project_uuid, "Pined": prj.inviter_project.pined_project} for prj in invited_projects]
            data["invited_projects"] = invited_prj_list
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'All Projects', 'data': data}
        return Response(response)


class GetProject(generics.GenericAPIView):
    serializer_class = ProjectSerializer

    def get(self, request, workspace_uid, portfolio_uid, project_uid): 
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()

        # get current user project
        project = Project.objects.filter(portfolio__workspace__workspace_user=user, portfolio__workspace__workspace_uuid=workspace_uid, portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
        if project:
            data = {"Project Name": project.name, "Project Description": project.project_description, "Agile Framwork": project.agile_framwork, 
                    "Project ID":  project.project_uuid, "boards":  BoardSerializer(project.board_set.all(), many=True).data}  
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project Details', 'data': data}
            return Response(response)

        # get inviter project
        invited_project = InvitedProjects.objects.filter(iuser=user, workspace_uid=workspace_uid, portfolio_uid=portfolio_uid, project_uid=project_uid).first()
        if invited_project:
            project = invited_project.inviter_project
            if project:
                data = {"Project Name": project.name, "Project Description": project.project_description, "Agile Framwork": project.agile_framwork, 
                        "Project ID":  project.project_uuid, "boards":  BoardSerializer(project.board_set.all(), many=True).data}  
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project Details', 'data': data}
                return Response(response)
                
        response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
        return Response(response, status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, workspace_uid, portfolio_uid, project_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(portfolio__workspace__workspace_user=user, 
                                    portfolio__workspace__workspace_uuid=workspace_uid,
                                    portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
        if project:
            serializer = self.serializer_class(project, data=request.data)
            if serializer.is_valid():
                serializer.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project updated.', 'data': []}
                return Response(response)
            else:
                err = list(serializer.errors.items())
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, workspace_uid, portfolio_uid, project_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(portfolio__workspace__workspace_user=user, 
                                    portfolio__workspace__workspace_uuid=workspace_uid,
                                    portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
        if project:
            project.delete()
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project deleted.', 'data': []}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class CreateProject(generics.GenericAPIView):
    serializer_class = KanbanProjectSerializer
    
    def get(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        projects = Project.objects.filter(portfolio__workspace__workspace_user=user, portfolio__workspace__workspace_uuid=workspace_uid, portfolio__portfolio_uuid=portfolio_uid)
        data = {}
        if projects:
            my_projects = [{"portfolio_name": prj.portfolio.portfolio_name, "project_name": prj.name, "workspace_uid": prj.portfolio.workspace.workspace_uuid, "portfolio_uid": prj.portfolio.portfolio_uuid, "project_uid": prj.project_uuid, "Pined": prj.pined_project} for prj in projects]
            data["my_projects"] = my_projects
        invited_projects = InvitedProjects.objects.filter(iuser=user)
        if invited_projects: 
            invited_prj_list = [{"portfolio_name": prj.inviter_project.portfolio.portfolio_name, "project_name": prj.inviter_project.name, "workspace_uid": prj.inviter_project.portfolio.workspace.workspace_uuid, "portfolio_uid": prj.inviter_project.portfolio.portfolio_uuid, "project_uid": prj.inviter_project.project_uuid, "Pined": prj.inviter_project.pined_project} for prj in invited_projects]
            data["invited_projects"] = invited_prj_list
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'All Projects', 'data': data}
        return Response(response)

    def post(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            portfolio = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, portfolio_uuid=portfolio_uid).first()
            try:
                if portfolio:
                    prdowner_scrummster_json = {}
                    if user_data["productowner"]:
                        prdowner_scrummster_json[user_data["productowner"]] = {"profile_img": "https://vifbox.org/api/media/default.jpg", "role": "Product owner"}
                    if user_data["scrummaster"]:
                        prdowner_scrummster_json[user_data["scrummaster"]] = {"profile_img": "https://vifbox.org/api/media/default.jpg", "role": "Scrum master"}
                    prj_obj = Project.objects.create(portfolio=portfolio, name=user_data["name"], project_description=user_data["projectdescription"],
                                            agile_framwork=user_data["agileframwork"], invited_users=prdowner_scrummster_json)
                    Thread(target=self.invite_users_email, args=(workspace_uid, portfolio_uid, prj_obj.project_uuid, user, [{"email": user_data["productowner"], "role": "Project manager"}, {"email": user_data["scrummaster"], "role": "Scrum master"}])).start()
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'({user_data["name"]}) project has been created.', "data": ProjectSerializer(prj_obj).data}
                    return Response(response)
                else:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists'}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project Already exist in the portfolio'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)
    
    def invite_users_email(self, ws, pf, pj, usr, invited_users):
        invprj, ntfs, invusrs = [], [], []
        for invited in invited_users:
            if invited != "":
                invited_user = User.objects.filter(email=invited["email"]).first()
                if invited_user:
                    project_url = f"http://localhost:8000/api/dash/workspaces/{ws}/portfolios/{pf}/projects/{pj}/"  # will change to front
                    email_body = f'Hi, you have been invited by {usr.name} ({usr.email}) to the project ({project_url}).'
                    invusrs.append(('you have been invited to project', email_body, settings.EMAIL_HOST_USER, [invited_user.email]))
                    prj = Project.objects.filter(portfolio__workspace__workspace_user=usr, portfolio__workspace__workspace_uuid=ws, portfolio__portfolio_uuid=pf, project_uuid=pj).first()
                    invprj.append(InvitedProjects(iuser=invited_user, inviter_project=prj, workspace_uid=ws, portfolio_uid=pf, project_uid=pj))  # , inviter=usr.email
                    ntfs.append(UserNotification(notification_user=invited_user, notification_text=email_body, notification_from=usr, notification_url=project_url))
        if invusrs:
            InvitedProjects.objects.bulk_create(invprj)
            UserNotification.objects.bulk_create(ntfs)
            send_mass_mail(invusrs)


class PinUnpinProject(APIView):
    @swagger_auto_schema(operation_description="workspace_uid & portfolio_uid & project_uid should be TYPE of **UUID**, and PIN should be **1 or 0**")
    def get(self, request, workspace_uid, portfolio_uid, project_uid, pin):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()

        # check if pined projects greater then 3
        pined_projects = Project.objects.filter(portfolio__workspace__workspace_user=user, portfolio__workspace__workspace_uuid=workspace_uid, 
                                                portfolio__portfolio_uuid=portfolio_uid, pined_project=True).count()
        if pined_projects > 2:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': "You cant't pin more then 3 projects."}
            return Response(response, status.HTTP_400_BAD_REQUEST)

        project = Project.objects.filter(project_uuid=project_uid, portfolio__workspace__workspace_user=user, portfolio__workspace__workspace_uuid=workspace_uid, portfolio__portfolio_uuid=portfolio_uid).first()
        if project:
            if pin == 1:
                project.pined_project = True
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{project.name} pined seccessfuly'}
            else:
                project.pined_project = False
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{project.name} unpined seccessfuly'}
            project.save()
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project or portfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class ExportProjectActivities(APIView):

    board_param_config = openapi.Parameter('board', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by **Board name**", required=False) 
    type_param_config = openapi.Parameter('type_of_activity', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by **Type of activity**", required=False) 
    useremail_param_config = openapi.Parameter('user_email', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Filter by **User email**", required=False) 
    @swagger_auto_schema(manual_parameters=[board_param_config, type_param_config, useremail_param_config])
    def get(self, request, workspace_uid, portfolio_uid, project_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(portfolio__workspace__workspace_uuid=workspace_uid, portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
        
        prj_user = project.portfolio.workspace.workspace_user 
        if user.email in project.invited_users:
            current_user_role = project.invited_users[user.email]["role"]
        elif user == prj_user:
            current_user_role = 'Project manager'
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not invited to this project'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        
        if current_user_role in ['Product owner', 'Project manager', 'Scrum master']:

            if not "board" in request.GET:
                board = None
            else:
                board = request.GET["board"]
            if not "type_of_activity" in request.GET:
                type_of_activity = None
            else:
                type_of_activity = request.GET["type_of_activity"]
            if not "user_email" in request.GET:
                user_email = None
            else:
                user_email = request.GET["user_email"]

            if project:
                response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': f'attachment; filename="Project_activites_{project.name}.csv"'},)
                writer = csv.writer(response)
                boards = self.board_project_activities(project, board, type_of_activity, user_email)
                writer.writerow(['Name', 'Email', 'Activity description', 'Activity type', 'Activity date'])
                for brd in boards:
                    writer.writerow(brd.values())
                return response
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project or portfolio not exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not allowed to download project activites'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


    def board_project_activities(self, project, board, type_of_activity, user_email):
            dct = {"board__prj": project}
            if board:
                dct["board__name"] = board
            if type_of_activity:
                dct["activity_type"] = type_of_activity
            if user_email:
                dct["activity_user_email"] = user_email
            boards = BoardActivities.objects.filter(**dct) 
            return BoardActivitiesSerializer(boards, many=True).data


class ExportBoard(APIView):

    board_param_config = openapi.Parameter('board', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Enter **Board name**", required=True) 

    @swagger_auto_schema(manual_parameters=[board_param_config])
    def get(self, request, workspace_uid, portfolio_uid, project_uid):
        if not "board" in request.GET:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'No board name provided'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(portfolio__workspace__workspace_uuid=workspace_uid, portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
        prj_user = project.portfolio.workspace.workspace_user 
        if user.email in project.invited_users:
            current_user_role = project.invited_users[user.email]["role"]
        elif user == prj_user:
            current_user_role = 'Admin'
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not invited to this project'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        if current_user_role in ['Admin', 'Product owner', 'Project manager', 'Scrum master']:
            board_name = request.GET["board"]
            board = Board.objects.filter(prj=project, name=board_name).first()
            if board:
                response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': f'attachment; filename="Project_activites_{project.name}.csv"'},)
                writer = csv.writer(response)
                writer.writerow(['portfolio_name', 'project_name', 'board_name', 'col_name', 'name', 'created_at', 'story', 'due_date', 'aging', 'files', 'labels', 'subtasks', 'assignees'])
                for col in board.board:
                    for col_name, tsks in col.items():
                        for tsk in tsks:
                            aging = None
                            if "first_move_date" in tsk and "last_move_date" in tsk:
                                d1 = dt.strptime(tsk["first_move_date"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                                d2 = dt.strptime(tsk["last_move_date"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                                aging = str(d2-d1)
                            writer.writerow((board.prj.portfolio.portfolio_name, board.prj.name, board_name, 
                                        col_name, tsk["name"], tsk["created_at"], 
                                        tsk["story"], tsk["due_date"], aging, tsk["files"], 
                                        tsk["labels"], tsk["subtasks"], tsk["assignees"]))
                return response
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Board not exists.'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not allowed to download project activites'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class ImportBoard(APIView):

    parser_classes = (MultiPartParser, )
    csv_file_param = openapi.Parameter('board_csv_file', in_=openapi.IN_FORM, description='Upload **board csv file**', type=openapi.TYPE_FILE, required=True)
    board_name_param = openapi.Parameter('board_name', in_=openapi.IN_FORM, description='Enter **board name**', type=openapi.TYPE_STRING, required=False)
    @swagger_auto_schema(manual_parameters=[csv_file_param, board_name_param])
    def post(self, request, workspace_uid, portfolio_uid, project_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(portfolio__workspace__workspace_uuid=workspace_uid, 
                                        portfolio__portfolio_uuid=portfolio_uid, 
                                        project_uuid=project_uid).first()
        prj_user = project.portfolio.workspace.workspace_user 
        if user.email in project.invited_users:
            current_user_role = project.invited_users[user.email]["role"]
        elif user == prj_user:
            current_user_role = 'Admin'
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not invited to this project'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        if current_user_role in ['Admin', 'Product owner', 'Project manager', 'Scrum master']:
            try:
                board_csv_file = request.FILES['board_csv_file']
                dataframe1 = pd.read_csv(board_csv_file.temporary_file_path())
                brd_json = {}
                for i, row in dataframe1.iterrows():
                    if i == 0:
                        try:
                            board = Board.objects.create(prj=project, name=row["board_name"])
                        except IntegrityError:
                            if "board_name" in request.data and request.data["board_name"]:
                                board = Board.objects.create(prj=project, name=request.data["board_name"])
                            else:
                                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Board name is required'}
                                return Response(response, status.HTTP_400_BAD_REQUEST)

                    if row["col_name"] in brd_json:
                        brd_json[row["col_name"]].append({
                                "name": row["name"],
                                "files": eval(row["files"]),
                                "story": row["story"],
                                "labels": eval(row["labels"]),
                                "due_date": row["due_date"],
                                "subtasks": eval(row["subtasks"]),
                                "assignees": eval(row["assignees"]),
                                "created_at": row["created_at"]
                            })
                    else:
                        brd_json[row["col_name"]] = [
                            {
                                "name": row["name"],
                                "files": eval(row["files"]),
                                "story": row["story"],
                                "labels": eval(row["labels"]),
                                "due_date": row["due_date"],
                                "subtasks": eval(row["subtasks"]),
                                "assignees": eval(row["assignees"]),
                                "created_at": row["created_at"]
                            }
                        ]
                if brd_json:
                    board.board = [{k: v} for k, v in brd_json.items()]
                    board.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Board imported successfuly.', "data": []}
                return Response(response)
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Board name already exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
            except:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not allowed to download project activites'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
Tasks PART
'''
class UplaodFileAWS(APIView):
    parser_classes = (MultiPartParser, )
    file_param = openapi.Parameter('attached_file', in_=openapi.IN_FORM, description='Upload **File**', type=openapi.TYPE_FILE, required=True)
    @swagger_auto_schema(manual_parameters=[file_param])
    def post(self, request, workspace_uid, portfolio_uid, project_uid):
        if not 'attached_file' in request.FILES:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'File is required'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(portfolio__workspace__workspace_uuid=workspace_uid, 
                                        portfolio__portfolio_uuid=portfolio_uid, 
                                        project_uuid=project_uid).first()
        prj_user = project.portfolio.workspace.workspace_user 
        if user.email in project.invited_users or user == prj_user:
            try:
                file = request.FILES['attached_file']
                utils_cls = VifUtils()
                img_url = utils_cls.aws_upload_file(prj_user, file, for_profile=False)
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'File Uploaded successfuly.', "data": {"file_url": img_url}}
                return Response(response)
            except:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'You are not invited to this project'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
MICROSOFT CALENDAR PART
'''
class GetMSCalendarEvents(APIView):
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['token'], properties={'token': openapi.Schema(type=openapi.TYPE_STRING)})
    @swagger_auto_schema(request_body=request_body)
    def post(self, request):
        permission_authontication_jwt(request)
        url = "https://graph.microsoft.com/v1.0/me/events?$select=subject,body,bodyPreview,organizer,attendees,start,end,location"
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Calendar events fetched successfuly.', "data": res.json()}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

class GetMSEvent(APIView):
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['token', 'event_id'], properties={'token': openapi.Schema(type=openapi.TYPE_STRING), 'event_id': openapi.Schema(type=openapi.TYPE_STRING)})
    @swagger_auto_schema(request_body=request_body)
    def post(self, request):
        permission_authontication_jwt(request)
        url = "https://graph.microsoft.com/v1.0/me/events/{}".format(request.data["event_id"])
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Calendar events fetched successfuly.', "data": res.json()}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class DeleteMSEvent(APIView):
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['token', 'event_id'], properties={'token': openapi.Schema(type=openapi.TYPE_STRING), 'event_id': openapi.Schema(type=openapi.TYPE_STRING)})
    @swagger_auto_schema(request_body=request_body)
    def delete(self, request):
        permission_authontication_jwt(request)
        url = "https://graph.microsoft.com/v1.0/me/events/{}".format(request.data["event_id"])
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.delete(url, headers=headers)
        if res.status_code == 204:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Event deleted successfuly.', "data": []}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class CancelMSEvent(APIView):
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['token', 'event_id'], properties={'token': openapi.Schema(type=openapi.TYPE_STRING), 'event_id': openapi.Schema(type=openapi.TYPE_STRING)})
    @swagger_auto_schema(request_body=request_body)
    def post(self, request):
        permission_authontication_jwt(request)
        url = "https://graph.microsoft.com/v1.0/me/events/{}/cancel".format(request.data["event_id"])
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.post(url, headers=headers)
        if res.status_code == 202:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Event cancelled successfuly.', "data": []}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
GOOGLE CALENDAR PART
'''
class GetGGLEvents(APIView):
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['token'], properties={'token': openapi.Schema(type=openapi.TYPE_STRING)})
    @swagger_auto_schema(request_body=request_body)
    def post(self, request):
        permission_authontication_jwt(request)
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/"
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Calendar events fetched successfuly.', "data": res.json()["items"]}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class GetDeleteGGLEvent(APIView):
    request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['token', 'event_id'], properties={'token': openapi.Schema(type=openapi.TYPE_STRING), 'event_id': openapi.Schema(type=openapi.TYPE_STRING)})
    @swagger_auto_schema(request_body=request_body)
    def post(self, request):
        permission_authontication_jwt(request)
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/{}".format(request.data["event_id"])
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Calendar events fetched successfuly.', "data": res.json()}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=request_body)
    def delete(self, request):
        permission_authontication_jwt(request)
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events/{}".format(request.data["event_id"])
        access_token = request.data['token']
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.delete(url, headers=headers)
        if res.status_code == 204:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Event deleted successfuly.', "data": []}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
    


'''
Authontication
'''
def permission_authontication_jwt(request):
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[-1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.DecodeError:
        response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Token Expired!'
            }
        raise AuthenticationFailed(response)
    except jwt.ExpiredSignatureError:
        response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': "UNAUTHONTICATED"
            }
        raise AuthenticationFailed(response)
    except KeyError:
        response = {
                'status': 'error',
                'code': status.HTTP_403_FORBIDDEN,
                'message': 'Invalid AUTHORIZATION!'
            }
        raise AuthenticationFailed(response)
    return payload














# user_inviter = User.objects.filter(email=invited_project.inviter, workspace__workspace_uuid=workspace_uid,
#                                                 workspace__portfolio__portfolio_uuid=portfolio_uid,
#                                                 workspace__portfolio__project__project_uuid=project_uid).first()
# project = Project.objects.filter(portfolio__workspace__workspace_user=user_inviter, 
#                                 portfolio__workspace__workspace_uuid=workspace_uid, 
#                                 portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()


# def get(self, request):
#     permission_authontication_jwt(request)
#     try:
#         file_url = request.data["file_url"]
#         res = requests.get(file_url)
#         if res.status_code <= 200:
#             response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'file info.', "data": {"file_url": file_url}}
#             return Response(response)
#         else:
#             file_aws_name = urlparse(file_url).path[1:]
#             utils_cls = VifUtils()
#             file_url = utils_cls.create_presigned_url(bucket_name=settings.BUCKET_NAME, region_name=settings.REGION_NAME, object_name=file_aws_name, expiration=600000)
#             response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'file info.', "data": {"file_url": file_url}}
#             return Response(response)
#     except:
#         response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
#         return Response(response, status.HTTP_400_BAD_REQUEST)



# def delete(self, request): 
#     payload = permission_authontication_jwt(request)
#     user = User.objects.filter(id=payload['id']).first()
#     try:
#         file_url = request.data["file_url"]
#         file_aws_name = urlparse(file_url).path[1:]
#         utils_cls = VifUtils()
#         utils_cls.delete_from_s3(user, file_aws_name)
#         response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'file deleted successfuly.'}
#         return Response(response)
#     except:
#         response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
#         return Response(response, status.HTTP_400_BAD_REQUEST)


# class CreateBoard(APIView):
#     def post(self, request):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         serializer = KanbanboardSerializer(data=request.data)
#         if serializer.is_valid():
#             user_data = serializer.data
#             project = Project.objects.filter(portfolio__portfolio_user=user, 
#                                             portfolio__portfolio_name=user_data["portfolio"], 
#                                             name=user_data["project"]).first()
#             is_board_exist = Board.objects.filter(prj=project, name=user_data["name"])
#             if is_board_exist:
#                 response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Board already exists.'}
#                 return Response(response, status.HTTP_400_BAD_REQUEST)
#             else:
#                 if user_data["name"].strip() == "":
#                     board_count = Board.objects.filter(prj=project).count() + 1
#                     Board.objects.create(prj=project, name=f"kanban Board {board_count}")
#                 else:
#                     Board.objects.create(prj=project, name=user_data["name"])
#                 response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{user_data["name"]} Kanban board has been created.'}
#                 return Response(response)
#         else:
#             err = list(serializer.errors.items())
#             response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
#             return Response(response, status.HTTP_400_BAD_REQUEST)

# class GetBoard(APIView):
#     def get(self, request, pf, prj, brd):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         board = Board.objects.filter(prj__portfolio__portfolio_user=user, 
#                                     prj__portfolio__portfolio_name=pf, 
#                                     prj__name=prj, name=brd).first()
#         if board:
#             response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'({brd}) Kanban board info.', "data": {"board": board.board}}
#             return Response(response)
#         else:
#             response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Board not exists.'}
#             return Response(response, status.HTTP_400_BAD_REQUEST)

# class GetTaskView(APIView):
#     def get(self, request, pf, prjct, brd, col_pos, task_pos):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         board = Board.objects.filter(name=brd, prj__name=prjct, prj__portfolio__portfolio_user=user, prj__portfolio__portfolio_name=pf).first()
#         if board:  
#             try:
#                 col_values = board.board[int(col_pos)].values()
#                 data = list(col_values)[0][int(task_pos)]
#                 response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Task info.', "data": data}
#                 return Response(response)
#             except Exception:
#                 response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Bad request'}
#                 return Response(response, status.HTTP_400_BAD_REQUEST)
#         else:
#             response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'The Project or the Portfolio not exists'}
#             return Response(response, status.HTTP_400_BAD_REQUEST)