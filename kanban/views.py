from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import InvitedProjects, Portfolio, Project, Workspace
from vifApp.models import User, UserNotification
from .serializers import (PortfolioSerializer, KanbanProjectSerializer, ProjectSerializer, 
                        BoardSerializer, WorkspaceSerializer)
from rest_framework import status
import jwt
from threading import Thread
from django.db.utils import IntegrityError
from django.conf import settings
from vifApp.utils import VifUtils
import requests
from django.core.mail import send_mass_mail
from urllib.parse import urlparse

'''
WORKSPACE PART
'''
class AddGetWorkspaces(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        workspaces = Workspace.objects.filter(workspace_user=user)
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my workspaces', 
                    'data': WorkspaceSerializer(workspaces, many=True).data}
        return Response(response)


    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first() 
        serializer = WorkspaceSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            try:
                wrkspc = Workspace.objects.create(workspace_user=user, workspace_name=user_data["workspace_name"], work_email=user_data["work_email"])
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace Already exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'({user_data["workspace_name"]}) Workspace has been created.', "data": WorkspaceSerializer(wrkspc).data}
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)

    
class SetGetWorkspace(APIView):
    def get(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
            if workspace:
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my workspace', 
                            'data': WorkspaceSerializer(workspace).data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
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
                workspace.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'workspace updated.', 
                            'data': WorkspaceSerializer(workspace).data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
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
        except Exception as e:  
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 'data': []}
            return Response(response)


'''
PORTFOLIO PART
'''

class AddGetPortfolios(APIView):
    def get(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            portfolios = Portfolio.objects.filter(workspace__workspace_uuid=workspace_uid, workspace__workspace_user=user)
            data = [{"Portfolio Name": nt.portfolio_name, 
                    "Portfolio uid": nt.portfolio_uuid,
                    "Created at": nt.created_at,
                    "Pined": nt.pined_portfolio,
                    "projects": ProjectSerializer(nt.project_set.all(), many=True).data} 
                    for nt in portfolios] 
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my Portfolios', 'data': data}
            return Response(response)
        except Exception as e:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 'data': []}
            return Response(response, status.HTTP_400_BAD_REQUEST)

    def post(self, request, workspace_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = PortfolioSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_data = serializer.data
                workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
                if workspace:
                    prtfl = Portfolio.objects.create(workspace=workspace, portfolio_name=user_data["portfolio_name"])
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{user_data["portfolio_name"]} Portfolio has been created.', "data": PortfolioSerializer(prtfl).data}
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


class SetGetPortfolio(APIView):
    def get(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        try:
            workspace = Workspace.objects.filter(workspace_user=user, workspace_uuid=workspace_uid).first()
            if workspace:
                portfolio = Portfolio.objects.filter(workspace=workspace, portfolio_uuid=portfolio_uid).first()
                if portfolio:
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my portfolio', 
                                'data': PortfolioSerializer(portfolio).data}
                    return Response(response)
                else:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists.', 'data': []}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Workspace not exists.', 'data': []}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad_request', 
                        'data': []}
            return Response(response, status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = PortfolioSerializer(data=request.data)
        if serializer.is_valid():
            try:
                portfolio = Portfolio.objects.filter(workspace__workspace_user=user, workspace__workspace_uuid=workspace_uid, 
                                                        portfolio_uuid=portfolio_uid).first()
                if portfolio:
                    portfolio.portfolio_name = request.data["portfolio_name"]
                    portfolio.save()
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'portfolio updated.', 
                                'data': PortfolioSerializer(portfolio).data}
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
    def get(self, request, workspace_uid, portfolio_uid, state):
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
            if state == 1:
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


class GetProject(APIView):
    def get(self, request, workspace_uid, portfolio_uid, project_uid): 
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()

        # get current user project
        project = Project.objects.filter(portfolio__workspace__workspace_user=user, 
                                    portfolio__workspace__workspace_uuid=workspace_uid,
                                    portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
        if project:
            data = {"Project Name": project.name, "Project Description": project.project_description,
                    "Agile Framwork": project.agile_framwork, "Project ID":  project.project_uuid,
                    "boards":  BoardSerializer(project.board_set.all(), many=True).data}  
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project Details', 'data': data}
            return Response(response)

        # get inviter project
        invited_project = InvitedProjects.objects.filter(iuser=user, workspace_uid=workspace_uid, portfolio_uid=portfolio_uid, project_uid=project_uid).first()
        if invited_project:
            user_inviter = User.objects.filter(email=invited_project.inviter, workspace__workspace_uuid=workspace_uid,
                                                workspace__portfolio__portfolio_uuid=portfolio_uid,
                                                workspace__portfolio__project__project_uuid=project_uid).first()
            project = Project.objects.filter(portfolio__workspace__workspace_user=user_inviter, 
                                            portfolio__workspace__workspace_uuid=workspace_uid, 
                                            portfolio__portfolio_uuid=portfolio_uid, project_uuid=project_uid).first()
            if project:
                data = {"Project Name": project.name, "Project Description": project.project_description,
                        "Agile Framwork": project.agile_framwork, "Project ID":  project.project_uuid,
                        "boards":  BoardSerializer(project.board_set.all(), many=True).data}  
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
            serializer = ProjectSerializer(project, data=request.data)
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


class CreateProject(APIView):
    def post(self, request, workspace_uid, portfolio_uid):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = KanbanProjectSerializer(data=request.data)
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
                    prj_obj = Project.objects.create(portfolio=portfolio, name=user_data["name"], 
                                            project_description=user_data["projectdescription"],
                                            agile_framwork=user_data["agileframwork"],
                                            invited_users=prdowner_scrummster_json
                                            )
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
                    prj = Project.objects.filter(portfolio__workspace__workspace_uuid=ws, portfolio__portfolio_uuid=pf, project_uuid=pj).first()
                    invprj.append(InvitedProjects(iuser=invited_user, inviter_project=prj, inviter=usr.email, workspace_uid=ws, portfolio_uid=pf, project_uid=pj))
                    ntfs.append(UserNotification(notification_user=invited_user, notification_text=email_body, notification_from=usr, notification_url=project_url))
        if invusrs:
            InvitedProjects.objects.bulk_create(invprj)
            UserNotification.objects.bulk_create(ntfs)
            send_mass_mail(invusrs)


class PinUnpinProject(APIView):
    def get(self, request, workspace_uid, portfolio_uid, project_uid, state):
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
            if state == 1:
                project.pined_project = True
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{project.name} pined seccessfuly'}
            else:
                project.pined_project = False
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{project_uid} unpined seccessfuly'}
            project.save()
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project or portfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
Tasks PART
'''
class UplaodFileAWS(APIView):
    def post(self, request, workspace_uid, portfolio_uid, project_uid):
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
Authontication
'''

def permission_authontication_jwt(request):
    try:
        token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
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