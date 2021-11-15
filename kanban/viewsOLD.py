from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import InvitedProjects, Portfolio, Project, Board
from vifApp.models import User
from .serializers import PortfolioSerializer, KanbanProjectSerializer, TaskSerializer, ProjectSerializer, PPSerializer, BoardSerializer, KanbanboardSerializer
from rest_framework import status
import jwt
from django.db.utils import IntegrityError
from django.conf import settings
from vifApp.utils import VifUtils
import requests
from urllib.parse import urlparse


'''
PORTFOLIO PART
'''

class AllPortfoliosView(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        portfolios = Portfolio.objects.filter(portfolio_user=user)
        data = [{"Portfolio Name": nt.portfolio_name, 
                "projects": ProjectSerializer(nt.project_set.all(), many=True).data} 
                for nt in portfolios] 
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my Portfolios', 'data': data}
        return Response(response)


class CreatePortfolio(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = PortfolioSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            try:
                Portfolio.objects.create(portfolio_user=user, portfolio_name=user_data["portfolio_name"])
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio Already exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{user_data["portfolio_name"]} Portfolio has been created.'}
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class PinPortfolio(APIView):
    def get(self, request, pf, state):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        if portfolio:
            if state == 1:
                portfolio.pined_portfolio = True
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{pf} pined seccessfuly'}
            else:
                portfolio.pined_portfolio = False
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{pf} unpined seccessfuly'}
            portfolio.save()
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Porfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

'''
Porject PART
'''


class GetProject(APIView):
    def get(self, request, pf, prjct): # add parameter for invited project
        invited = int(request.GET["invited"])
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        if not invited:
            # get current user project
            project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        else:
            # get inviter project
            project_uid = request.GET["prj_uid"]
            invited_project = InvitedProjects.objects.filter(iuser=user, project=f"{pf}/{prjct}", project_uid=project_uid).first()
            if invited_project:
                user_inviter = User.objects.filter(email=invited_project.inviter).first()
                project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user_inviter, portfolio__portfolio_name=pf).first()
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)

        if project:
            data = {"Project Name": project.name, "Project Description": project.project_description,
                    "Agile Framwork": project.agile_framwork, "Project ID":  project.project_uuid, "Invited": project.invited_users,
                    # "Product Owner": project.product_owner, "Scrum Master": project.scrum_master,
                    "boards":  BoardSerializer(project.board_set.all(), many=True).data}  
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project Details', 'data': data}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class GetAllProjects(APIView):
    def get(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        projects = Project.objects.filter(portfolio__portfolio_user=user)
        invited_projects = InvitedProjects.objects.filter(iuser=user)
        data = {}
        if projects:
            my_projects = [{"portfolio_name": prj.portfolio.portfolio_name, "project_name": prj.name, "project_uid": prj.project_uuid} for prj in projects]
            data["my_projects"] = my_projects
        if invited_projects: 
            invited_prj_list = [{"portfolio_name": prj.project.split("/")[0], "project_name": prj.project.split("/")[1], "project_uid": prj.project_uid} for prj in invited_projects]
            data["invited_projects"] = invited_prj_list
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'All Projects', 'data': data}
        return Response(response)


class CreateProject(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = KanbanProjectSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=user_data["portfolio"]).first()
            try:
                if portfolio:
                    prdowner_scrummster_json = {}
                    if user_data["productowner"]:
                        prdowner_scrummster_json[user_data["productowner"]] = {"profile_img": "https://vifbox.org/api/media/default.jpg", "role": "Product owner"}
                    if user_data["scrummaster"]:
                        prdowner_scrummster_json[user_data["scrummaster"]] = {"profile_img": "https://vifbox.org/api/media/default.jpg", "role": "Scrum master"}
                    Project.objects.create(portfolio=portfolio, name=user_data["name"], 
                                            project_description=user_data["projectdescription"],
                                            agile_framwork=user_data["agileframwork"],
                                            invited_users=prdowner_scrummster_json
                                            )
                    response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{user_data["name"]} Kanban board has been created.'}
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


class PinProject(APIView):
    def get(self, request, pf, prjct, state):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        if project:
            if state == 1:
                project.pined_project = True
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{prjct} pined seccessfuly'}
            else:
                project.pined_project = False
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{prjct} unpined seccessfuly'}
            project.save()
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project or portfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
Tasks PART
'''
class UplaodFileAWS(APIView):
    def post(self, request):
        try:
            payload = permission_authontication_jwt(request)
            user = User.objects.filter(id=payload['id']).first()
            file = request.FILES['attached_file']
            utils_cls = VifUtils()
            img_url = utils_cls.aws_upload_file(user, file, for_profile=False)
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'File Uploaded successfuly.', "data": {"file_url": img_url}}
            return Response(response)
        except:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        try:
            permission_authontication_jwt(request) # current_user = User.objects.filter(id=payload['id']).first() 
            file_url = request.GET["file_url"]
            res = requests.get(file_url)
            if res.status_code <= 200:
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'file info.', "data": {"file_url": file_url}}
                return Response(response)
            else:
                file_aws_name = urlparse(file_url).path[1:]
                utils_cls = VifUtils()
                file_url = utils_cls.create_presigned_url(bucket_name=settings.BUCKET_NAME, region_name=settings.REGION_NAME, object_name=file_aws_name, expiration=600000)
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'file info.', "data": {"file_url": file_url}}
                return Response(response)
        except:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'bad request'}
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