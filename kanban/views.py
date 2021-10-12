from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import Portfolio, Project
from vifApp.models import User
from .serializers import PortfolioSerializer, KanbanBoardSerializer, TaskSerializer, ProjectSerializer, PPSerializer
from rest_framework import status
import jwt
from django.db.utils import IntegrityError
from django.conf import settings


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
    def get(self, request, pf, prjct):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        if project:
            data = {"Project Name": project.name, "Project Description": project.project_description,
                    "Agile Framwork": project.agile_framwork,
                    "Product Owner": project.product_owner, "Scrum Master": project.scrum_master,
                    "board": project.board["board"]}
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project Details', 'data': data}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)

        

class CreateProject(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = KanbanBoardSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=user_data["portfolio"]).first()
            try:
                if portfolio:
                    Project.objects.create(portfolio=portfolio, name=user_data["name"], 
                                            project_description=user_data["projectdescription"],
                                            agile_framwork=user_data["agileframwork"],
                                            product_owner=user_data["productowner"],
                                            scrum_master=user_data["scrummaster"])
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
class GetTaskView(APIView):
    def get(self, request, pf, prjct, col_pos, task_pos):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        if project:  
            try:
                col_values = project.board["board"][int(col_pos)].values()
                data = list(col_values)[0][int(task_pos)]
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Task info.', "data": data}
                return Response(response)
            except Exception:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Bad request'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'The Project or the Portfolio not exists'}
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

