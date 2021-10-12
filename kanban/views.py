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



class Search4Project(APIView):
    def get(self, request, project_name):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        projects = Project.objects.filter(name__icontains=project_name, portfolio__portfolio_user=user)  # TODO set all others this way
        if projects:
            data = {"projects":  PPSerializer(projects, many=True).data} 
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Search result', 'data': data}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'No project exists'}
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
class CreateTaskView(APIView):
    def post(self, request):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.data
            project = Project.objects.filter(name=user_data["project"], portfolio__portfolio_user=user, portfolio__portfolio_name=user_data["portfolio"]).first()
            if project:        
                for i, d in enumerate(project.board["board"]):
                    if user_data["col"] in d:
                        tasks_list = project.board["board"][i][user_data["col"]]
                        tasks_list.append({"task_des": user_data["description"]})
                        project.save()
                        response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'The task has been created.'}
                        return Response(response)
                else:
                    response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Board column not exists'}
                    return Response(response, status.HTTP_400_BAD_REQUEST)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'The Project or the Portfolio not exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return Response(response, status.HTTP_400_BAD_REQUEST)



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
Change task or multimple tasks status
'''

class ChangeTasksCol(APIView):
    def get(self, request, pf, prjct, from_col, tasks_ids, to_col, in_pos): # tasks_ids should be in order from top to buttom
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        try:
            if project:  
                col_values = project.board["board"] # col_values = [{'Backlog': [{'task_des': 'task kkkk', 'task_pos': 0}, {'task_des': 'task kkkk22222', 'task_pos': 1}]}, {'To Do': []}, {'In Progress': []}, {'Done': []}]
                tasks_2_move = []
                # cut the tasks
                for c in col_values:
                    if from_col in c:
                        if c[from_col]:
                            ids_list = tasks_ids.split(",")
                            for i in ids_list:
                                tasks_2_move.append(c[from_col].pop(int(i)))
                            break
                        else:
                            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'No tasks to move.'}
                            return Response(response)
                # paste the tasks
                for cl in col_values:
                    if to_col in cl:
                        in_pos = in_pos
                        for t in tasks_2_move:
                            cl[to_col].insert(in_pos, t)
                            in_pos += 1
                        break
                project.save()
                response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Tasks moved successfuly.', "data": project.board["board"]} # to return the full project
                return Response(response)
            else:
                response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'The Project or the Portfolio not exists'}
                return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Bad request.'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


'''
Add, delete & Change order column
'''
class AddCol(APIView):
    def get(self, request, pf, prjct, colname):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        if project:
            project.board["board"].append({colname: []}) # should be checked from the front thats the column not exists.
            project.save()
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'{colname} column has been added sucessfuly.'}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists.'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class DeleteCol(APIView):
    def get(self, request, pf, prjct, col_index):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        if project:
            del project.board["board"][col_index] # should shows popup warning from the front tells thats all column contents tasks will be deleted.
            project.save()
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': f'The column has been deleted sucessfuly.'}
            return Response(response)
        else:
            response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists.'}
            return Response(response, status.HTTP_400_BAD_REQUEST)


class ChangeColOrder(APIView):
    def get(self, request, pf, prjct, col_index, to_index):
        payload = permission_authontication_jwt(request)
        user = User.objects.filter(id=payload['id']).first()
        project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()
        if project:
            col2changeorder = project.board["board"].pop(col_index)
            project.board["board"].insert(to_index, col2changeorder)
            project.save()
            response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'The column order has been changed sucessfuly.'}
            return Response(response)
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
#             return Response(response, status.HTTP_400_BAD_REQUEST)



# for i, d in enumerate(project.board["board"]):
#     if col in d:
#         tasks_list = project.board["board"][i][col]
#         for j, t in enumerate(tasks_list):
#             if t["task_pos"] == int(task_col_id):
#                 data = tasks_list[j]
#                 response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Task info.', "data": data}
#                 return Response(response)
# else:
#     response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Task not exists in the project column'}
#     return Response(response, status.HTTP_400_BAD_REQUEST)


# class PortfolioProjectsView(APIView):
#     def get(self, request, pf):
#         payload = permission_authontication_jwt(request)
#         user = User.objects.filter(id=payload['id']).first()
#         # TODO later
#         return Response({})
#         portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
#         if not portfolio is None:
#             projects = portfolio.kanbanboard_set.all()
#             data = {"Portfolio_Name": portfolio.portfolio_name,
#                     "Projects": [{"Project Name": prj.name, "Agile Framwork": prj.agile_framwork,
#                                 "Product Owner": prj.product_owner, "Scrum Master": prj.scrum_master} 
#                                 for prj in projects] 
#                     }
#             response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Portfolio projects', 'data': data}
#             return Response(response)
#         else:
#             response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists'}
#             return Response(response, status.HTTP_400_BAD_REQUEST)



# portfolio = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
# if not portfolio is None:
#     project = portfolio.project_set.filter(name=prjct)
#     if project:
#         project = project.first()
#         data = {"Project Name": project.name, "Project Description": project.project_description,
#                 "Agile Framwork": project.agile_framwork,
#                 "Product Owner": project.product_owner, "Scrum Master": project.scrum_master,
#                 "board": project.board["board"]}
#         response = {'status': 'success', 'code': status.HTTP_200_OK, 'message': 'Project Details', 'data': data}
#         return Response(response)
#     else:
#         response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Project not exists'}
#         return Response(response, status.HTTP_400_BAD_REQUEST)
# else:
#     response = {'status': 'error', 'code': status.HTTP_400_BAD_REQUEST, 'message': 'Portfolio not exists'}
#     return Response(response, status.HTTP_400_BAD_REQUEST)


# pf = Portfolio.objects.filter(portfolio_user=user, portfolio_name=pf).first()
# ==============
# project = Project.objects.filter(portfolio=pf, name=prjct).first()
# project = Project.objects.filter(name=prjct, portfolio__portfolio_user=user, portfolio__portfolio_name=pf).first()


