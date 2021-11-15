import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .serializers import TaskSerializer, PPSerializer, KanbanboardSerializer, BPPSerializer, PSerializer
from .models import Portfolio, Project, Board, InvitedProjects
from vifApp.models import User, UserNotification
from vifApp.utils import VifUtils
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.db.models import Q
# from threading import Thread


class BoardConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.prjid = parse_qs(self.scope["query_string"].decode("utf8"))["prj_uid"][0]
        self.project_owner_user = await self.project_owner(self.prjid)
        prms_dict = self.scope['url_route']['kwargs']
        self.pf = prms_dict['pf']
        self.pj = prms_dict['prjct']
        self.room_name = self.prjid + self.pf + self.pj  # should be reated to specific group
        self.room_group_name = 'team_%s' % self.room_name
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    # Receive message from WebSocket
    async def receive_json(self, text_data, **kwargs):
        request_id = text_data['request_id']
        data = text_data['data']
        await self.single_user_response(request_id, data)
        

    @sync_to_async
    def project_owner(self, prj_uid):
        return User.objects.filter(portfolio__project__project_uuid=prj_uid).first()

    # for single user response
    async def single_user_response(self, request_id, data):
        if request_id == "get-board":
            await self.get_board(request_id, data)
        elif request_id == "get-task":
            await self.get_task(request_id, data)
        elif request_id == "search-project":
            res_state_ok = await self.search_project(request_id, data)
        else:
            if request_id == "create-task":
                res_state_ok = await self.create_task(request_id, data)
            elif request_id == "create-board":
                res_state_ok = await self.create_board(request_id, data)
            elif request_id == "change-tasks-col":
                res_state_ok = await self.change_tasks_col(request_id, data)
            elif request_id == "add-col":
                res_state_ok = await self.add_col(request_id, data)
            elif request_id == "delete-col":
                res_state_ok = await self.delete_col(request_id, data)
            elif request_id == "change-col-order":
                res_state_ok = await self.change_col_order(request_id, data)
            elif request_id == "invite-users":
                res_state_ok = await self.invite_users(request_id, data)
            if res_state_ok:
                await self.channel_layer.group_send(self.room_group_name, {"type": "notify.team", 'user': self.user.email , 'request_id': request_id, "notification": "update"})

        
    async def notify_team(self, event):
        response =  {'user': event['user'] , 'request_id': event['request_id'], "updated": True}
        await self.send_json(response)


    async def get_board(self, request_id, data):
        try:
            board = await self.role_permission({"board": data["name"]}, access_role_permissions=['Product owner', 'Scrum master', 'Project manager']) # board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, self.user)
            if board:
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'({data["name"]}) Kanban board info.', "data": {"board": board.board}}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board not exists.'}
                await self.send_json(response) 
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def get_task(self, request_id, data):
        try:
            board = await self.role_permission({"board": data["board"]}, access_role_permissions=['Product owner', 'Scrum master', 'Project manager']) # board = await database_sync_to_async(self.get_board_db)({"board": data["board"]}, self.user)
            if board:  
                try:
                    col_values = board.board[data["col_index"]].values()
                    data = list(col_values)[0][int(data["task_index"])]
                    response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Task info.', "data": data}
                    await self.send_json(response)
                    return  True
                except Exception:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
                    await self.send_json(response) 
                    return False
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The Project or the Portfolio not exists'}
                await self.send_json(response) 
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def create_task(self, request_id, data):
        try:
            serializer = TaskSerializer(data=data)
            if serializer.is_valid():
                user_data = serializer.data
                board = await self.role_permission(data, access_role_permissions=['Product owner', 'Scrum master']) # to set access_role_permissions later # board = await database_sync_to_async(self.get_board_db)(user_data, self.user)
                my_task = {"name": user_data["name"], "files": data["files"], "assignees": data["assignees"], "story": data["story"], "due_date": data["due_date"]}
                await database_sync_to_async(self.notify_assignees)(data["assignees"], user_data["name"])
                if board:        
                    for i, d in enumerate(board.board):
                        if user_data["col"] in d:
                            tasks_list = board.board[i][user_data["col"]]
                            tasks_list.append(my_task)
                            await database_sync_to_async(self.save_db)(board)
                            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The task has been created.'}
                            await self.send_json(response)
                            return True
                    else:
                        response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board column not exists'}
                        await self.send_json(response) 
                        return False
                else:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The Project or the Portfolio not exists'}
                    await self.send_json(response) 
                    return False
            else:
                err = list(serializer.errors.items())
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
                await self.send_json(response) 
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False

    

    async def create_board(self, request_id, data):
        try:
            project = await database_sync_to_async(self.get_project_db)()
            board = await self.role_permission({"board": data["name"]}, access_role_permissions=['Product owner', 'Scrum master', 'Project manager']) # board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, self.user)
            if board:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board already exists.'}
                await self.send_json(response) 
                return False 
            else:
                if data["name"].strip() == "":
                    board_count = await database_sync_to_async(Board.objects.filter)(prj=project)
                    board_count = await sync_to_async(board_count.count)()
                    await database_sync_to_async(self.db_create_board)(prj=project, name=f"kanban Board {board_count+1}")
                else:
                    await database_sync_to_async(self.db_create_board)(prj=project, name=data["name"])
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Board task has been created.'}
                await self.send_json(response)
                return True
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def change_tasks_col(self, request_id, data):
        try:
            board = await self.role_permission(data, access_role_permissions=['Product owner', 'Scrum master']) # board = await database_sync_to_async(self.get_board_db)(data, self.user)
            if board:  
                col_values = board.board
                tasks_2_move = []
                from_col = data["from_col"]
                to_col = data["to_col"]
                # cut the tasks
                for c in col_values:
                    if from_col in c:
                        if c[from_col]:
                            ids_list = data["tasks_ids"]
                            for i in ids_list:
                                tasks_2_move.append(c[from_col].pop(int(i)))
                            break
                        else:
                            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'No tasks to move.'}
                            await self.send_json(response)
                            return True
                # paste the tasks
                for cl in col_values:
                    if to_col in cl:
                        in_pos = data["in_pos"]
                        for t in tasks_2_move:
                            cl[to_col].insert(in_pos, t)
                            in_pos += 1
                        break
                await database_sync_to_async(self.save_db)(board)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Tasks moved successfuly.', "data": board.board} # to return the full project
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The Project or the Portfolio not exists'}
                await self.send_json(response)
                return False
        except Exception:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
            await self.send_json(response)
            return False


    async def add_col(self, request_id, data):
        try:
            board = await self.role_permission(data, access_role_permissions=['Product owner', 'Scrum master'])
            colname = data["colname"]
            if board:
                if not any(colname in b for b in board.board):
                    board.board.append({colname: []})
                else:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board already exists.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'{colname} column has been added sucessfuly.'}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'board not exists.'}
                await self.send_json(response)
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False
            
        
    async def delete_col(self, request_id, data):
        try:
            board = await self.role_permission(data, access_role_permissions=['Product owner', 'Scrum master']) # board = await database_sync_to_async(self.get_board_db)(data, self.user)
            col_index = data["col_index"]
            if board:
                try:
                    del board.board[col_index] # should shows popup warning from the front tells thats all column contents tasks will be deleted.
                except IndexError:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'column index out of range.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'The column has been deleted sucessfuly.'}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists.'}
                await self.send_json(response)
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def change_col_order(self, request_id, data):
        try:
            board = await self.role_permission(data, access_role_permissions=['Product owner', 'Scrum master']) # board = await database_sync_to_async(self.get_board_db)(data, self.user)
            col_index = data["col_index"]
            to_index = data["to_index"]
            if board:
                col2changeorder = board.board.pop(col_index)
                board.board.insert(to_index, col2changeorder)
                await database_sync_to_async(self.save_db)(board)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The column order has been changed sucessfuly.'}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists.'}
                await self.send_json(response)
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def invite_users(self, request_id, data):
        if self.project_owner_user == self.user:
            invited_users = data['users_email']
            await database_sync_to_async(self.set_invited)(invited_users) # , data["project_path"]
            response = {'status': 'ok', 'code': 200, 'request_id': request_id, 'message': 'user invited to project', "data": {"notification": f"{invited_users} has been invited to ({self.pj}) project"}}
            await self.send_json(response)
            return True
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'bad request'}
            await self.send_json(response) 
            return False


    async def search_project(self, request_id, data):
        try:
            if self.project_owner_user == self.user:
                data = await self.search_prj(data, usr=self.user)
            else:
                assignee = await database_sync_to_async(self.get_project_assignee_db)(self.project_owner_user)
                if self.user.email in assignee:
                    if assignee[self.user.email]["role"] in ['Product owner', 'Scrum master', 'Project manager']:
                        data = await self.search_prj(data, usr=self.project_owner_user)
                    else:
                        raise PermissionError('You dont have permission')
            if data:
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Search result', 'data': data}
                return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'No resluts found.'}
                return await self.send_json(response)
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            return await self.send_json(response)


    @database_sync_to_async
    def search_prj(self, user_data, usr):
        query = user_data["search_query"]
        boards = Board.objects.filter(name__contains=query, prj__portfolio__portfolio_user=usr)
        portfolios = Portfolio.objects.filter(portfolio_name__contains=query, portfolio_user=usr)
        projects = Project.objects.filter(name__icontains=query, portfolio__portfolio_user=usr)
        boards_tsks = Board.objects.filter(prj__portfolio__portfolio_user=usr)
        tasks = []
        for x in boards_tsks:
            for col in x.board:
                if col:
                    tsks = list(col.values())[0]
                    for i, tsk in enumerate(tsks):
                        if tsk["name"].lower().find(query.lower()) != -1:
                            tasks.append((list(col.keys())[0], i, tsk))
        if projects or boards or portfolios or tasks:
            data = {'portfolios': PSerializer(portfolios, many=True).data, 
                    'projects': PPSerializer(projects, many=True).data,
                    'boards': BPPSerializer(boards, many=True).data, 'tasks': tasks}
            return data
        else:
            return None


    def set_invited(self, invited_users):
        invprj, ntfs, invusrs = [], [], []
        for invited in invited_users:
            invited_user = User.objects.filter(email=invited["email"]).first()
            project = f'{self.pf}/{self.pj}'
            inviter_prj = Project.objects.filter(portfolio__portfolio_user=self.user, portfolio__portfolio_name=self.pf, name=self.pj).first()
            if inviter_prj.invited_users is None:
                inviter_prj.invited_users = {}
            inviter_prj.invited_users[str(invited["email"])] = {"profile_img": str(invited_user.profile_image), "role": invited["role"]}
            inviter_prj.save()
            if invited_user:
                project_url = f"http://localhost:8000/api/dash/project/{project}/?invited=1"  # will change to front
                email_body = f'Hi, you have been invited by {self.user.name} ({self.user.email}) to the project ({project_url}).'
                invusrs.append(invited_user.email)
                invprj.append(InvitedProjects(iuser=invited_user, inviter=self.user.email, project=project, project_uid=inviter_prj.project_uuid))
                ntfs.append(UserNotification(notification_user=invited_user, notification_text=email_body, notification_from=self.user, notification_url=project_url))
        InvitedProjects.objects.bulk_create(invprj)
        UserNotification.objects.bulk_create(ntfs)
        data = {'email_body': email_body, 'email_subject': 'you have been invited to project', "to_email": invusrs}
        VifUtils.send_email(data)


    def notify_assignees(self, assignees, task_name):
        assignee_users, notfs = [], []
        for asgn in assignees:
            assignee_user = User.objects.filter(email=asgn).first()
            project_url = f"http://localhost:8000/api/dash/project/{self.pf}/{self.pj}/?invited=1"  # will change to front
            email_body = f'Hi , you are assigned to a Task ({task_name})\nof the following Project: {project_url}.'
            assignee_users.append(assignee_user.email)
            notfs.append(UserNotification(notification_user=assignee_user, notification_text=email_body, notification_from=self.user, notification_url=project_url))
        UserNotification.objects.bulk_create(notfs)
        data = {'email_body': email_body, 'email_subject': 'Task assigned to you', "to_email": assignee_users}
        VifUtils.send_email(data)


    def get_board_db(self, user_data, usr):
        return Board.objects.filter(name=user_data["board"], prj__name=self.pj, prj__portfolio__portfolio_user=usr, prj__portfolio__portfolio_name=self.pf).first() 

    def get_project_db(self):
        return Project.objects.filter(name=self.pj, portfolio__portfolio_user=self.user, portfolio__portfolio_name=self.pf).first()

    def get_project_assignee_db(self, usr):
        prjct = Project.objects.filter(name=self.pj, portfolio__portfolio_user=usr, portfolio__portfolio_name=self.pf, project_uuid=self.prjid).first()
        return prjct.invited_users

    def db_create_board(self, prj, name):
        brd = Board(prj=prj, name=name)
        brd.save()
            
    
    def save_db(self, obj):
        obj.save()


    async def role_permission(self, data, access_role_permissions):
        if self.project_owner_user == self.user:  # current user is the owner
            board = await database_sync_to_async(self.get_board_db)(data, usr=self.user)
        else:
            assignee = await database_sync_to_async(self.get_project_assignee_db)(self.project_owner_user)
            if self.user.email in assignee:
                if assignee[self.user.email]["role"] in access_role_permissions:
                    board = await database_sync_to_async(self.get_board_db)(data, usr=self.project_owner_user)
                else:
                    raise PermissionError('You dont have permission')
            else:
                raise PermissionError('You dont have assecc to this project')
        return board





# if str(request_id).startswith("get-"):
#     # Send message to singal user
#     await self.single_user_response(request_id, data)
# else:
#     # Send message to room group
#     await self.channel_layer.group_send(
#         self.room_group_name,
#         {
#             'type': 'group_response',
#             'request_id': request_id,
#             "data": data
#         }
#     )


# Receive message from room group
# async def group_response(self, event):
#     request_id = event['request_id']
#     data = event['data']
#     if request_id == "create-task":
#         await self.create_task(request_id, data)
#     elif request_id == "create-board":
#         await self.create_board(request_id, data)
#     elif request_id == "change-tasks-col":
#         await self.change_tasks_col(request_id, data)
#     elif request_id == "add-col":
#         await self.add_col(request_id, data)
#     elif request_id == "delete-col":
#         await self.delete_col(request_id, data)
#     elif request_id == "change-col-order":
#         await self.change_col_order(request_id, data)
#     elif request_id == "search-project":
#         await self.search_project(request_id, data)
#     elif request_id == "invite-users":
#         await self.invite_users(request_id, data)


# to add this to a function since its will repeated (for permission)
# if self.project_owner_user == self.user:  # current user is the owner
#     board = await database_sync_to_async(self.get_board_db)(data, usr=self.user)
# else:
#     assignee = await database_sync_to_async(self.get_project_assignee_db)(self.project_owner_user)
#     if self.user.email in assignee:
#         if assignee[self.user.email]["role"] in ['Product owner', 'Scrum master']:
#             board = await database_sync_to_async(self.get_board_db)(data, usr=self.project_owner_user)
#         else:
#             response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You dont have permission'}
#             return await self.send_json(response)
#     else:
#         response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You dont have assecc to this project'}
#         return await self.send_json(response)