from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import Portfolio, KanbanBoard, BoardCol, Task
from vifApp.models import User
from .serializers import PortfolioSerializer, KanbanBoardSerializer, TaskSerializer
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
        data = [{"Portfolio Name": nt.portfolio_name} for nt in portfolios] 
        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'my Portfolios', 'data': data}
        return Response(response)


    
class PortfolioProjectsView(APIView):
    def get(self, request, pf):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        if not portfolio is None:
            projects = portfolio.kanbanboard_set.all()
            data = {"Portfolio_Name": portfolio.portfolio_name,
                    "Projects": [{"Project Name": prj.name, "Agile Framwork": prj.agile_framwork,
                                "Product Owner": prj.product_owner, "Scrum Master": prj.scrum_master} 
                                for prj in projects] 
                    }
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Portfolio projects', 'data': data}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)



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

'''
KANBAN PART
'''


class GetBoardView(APIView):
    def get(self, request, pf, prjct):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        if not portfolio is None:
            project = portfolio.kanbanboard_set.filter(name=prjct)
            if project:
                project = project.first()
                columns = project.boardcol_set.all()
                info = [{cl.col_name: [{"Discription": tsk.des, "col id": tsk.id_col} for tsk in cl.task_set.all()]} for cl in columns]
                data = {"Project Name": project.name, "Project Description": project.project_description,
                        "Agile Framwork": project.agile_framwork,
                        "Product Owner": project.product_owner, "Scrum Master": project.scrum_master,
                        "columns": info}
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Kanban Project', 'data': data}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)
        


class CreateKanbanBoardView(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = KanbanBoardSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=user_data["portfolio"]).first()
            try:
                kanban = KanbanBoard.objects.create(portfolio=portfolio, name=user_data["name"], 
                                                    project_description=user_data["projectdescription"],
                                                    agile_framwork=user_data["agileframwork"],
                                                    product_owner=user_data["productowner"],
                                                    scrum_master=user_data["scrummaster"])
                BoardCol.objects.bulk_create([BoardCol(board=kanban, col_name="Backlog"),
                                            BoardCol(board=kanban, col_name="To Do"),
                                            BoardCol(board=kanban, col_name="In Progress"),
                                            BoardCol(board=kanban, col_name="Done")])
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project Already exist in the portfolio'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
            
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{user_data["name"]} Kanban board has been created.'}
            return Response(response)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)



'''
Tasks PART
'''

class CreateTaskView(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=user_data["portfolio"]).first()
            project = KanbanBoard.objects.filter(portfolio=pf, name=user_data["project"]).first()
            clmn = BoardCol.objects.filter(board=project, col_name=user_data["col"]).first()
            if not clmn is None:
                count = clmn.task_set.count()
                Task.objects.create(col=clmn, des=user_data["description"], id_col=count+1)
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'The task has been created.'}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Column not exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class GetTaskView(APIView):
    def get(self, request, pf, prjct, col, task_col_id):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        project = KanbanBoard.objects.filter(portfolio=pf, name=prjct).first()
        clmn = BoardCol.objects.filter(board=project, col_name=col).first()
        tsk = Task.objects.filter(col=clmn, id_col=task_col_id).first()
        if not tsk is None:
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Task info.', "data": {"task des": tsk.des, "task id": tsk.id_col}}
            return Response(response)
        response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Bad request'}
        return Response(response, status.HTTP_400_BAD_REQUEST)



'''
Change task or multimple tasks status
'''
class ChangeMultipleTasksCol(APIView):
    def get(self, request, pf, prjct, col, task_col_ids, to_col):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        project = KanbanBoard.objects.filter(portfolio=pf, name=prjct).first()
        clmn = BoardCol.objects.filter(board=project, col_name=col).first()
        ids_list = task_col_ids.split(",")
        tsks = Task.objects.filter(col=clmn, id_col__in=ids_list) 
        newclmn = BoardCol.objects.filter(board=project, col_name=to_col).first()
        if not newclmn is None:
            count = newclmn.task_set.count()
            for tsk in tsks:
                count += 1
                tsk.col = newclmn
                tsk.id_col = count
                tsk.save()
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Task(s) column has been changed.'}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Column not exists'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
Add & delete Column status
'''
class AddCol(APIView):
    def get(self, request, pf, prjct, colname):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        project = KanbanBoard.objects.filter(portfolio=pf, name=prjct).first()
        if not project is None:
            try:
                BoardCol.objects.create(board=project, col_name=colname)
            except IntegrityError:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Column name is already exists.'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{colname} column has been added sucessfuly.'}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists.'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class DeleteCol(APIView):
    def get(self, request, pf, prjct, colname):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
        project = KanbanBoard.objects.filter(portfolio=pf, name=prjct).first()
        if not project is None:
            cl = BoardCol.objects.filter(board=project, col_name=colname).first()
            if not cl is None:
                cl.delete()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{colname} column has been deleted sucessfuly.'}
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project column not exists.'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists.'}
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











# class ChangeTaskCol(APIView):
#     def get(self, request, pf, prjct, col, task_col_id, to_col):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
#         project = KanbanBoard.objects.filter(portfolio=pf, name=prjct).first()
#         clmn = BoardCol.objects.filter(board=project, col_name=col).first()
#         tsk = Task.objects.filter(col=clmn, id_col=task_col_id).first()
#         newclmn = BoardCol.objects.filter(board=project, col_name=to_col).first()
#         if not newclmn is None:
#             count = newclmn.task_set.count()
#             tsk.col = newclmn
#             tsk.id_col = count + 1
#             tsk.save()
#             response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Task column has been changed.'}
#             return Response(response)
#         else:
#             response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Column not exists'}
#             return Response(response, status.HTTP_400_BAD_REQUEST)v