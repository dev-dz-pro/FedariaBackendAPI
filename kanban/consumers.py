import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .serializers import (TaskSerializer, PPSerializer, BPPSerializer, PSerializer, KanbanProjectSerializer, UserMsgsSerializer, 
                        BoardActivitiesSerializer, ProjectRolesSerializer, InviteUsersSerializer, GroupeChatSerializer)
from .models import Portfolio, Project, Board, InvitedProjects, BoardActivities, UserDirectMessages
from vifApp.models import User, UserNotification
from .models import ProjectGroupeChat
from channels.db import database_sync_to_async
from django.db.utils import IntegrityError
import hashlib
from datetime import datetime as dt
from django.core.mail import send_mass_mail
from django.conf import Settings, settings
import redis
from vifApp.utils import VifUtils
from urllib.parse import urlparse
import requests
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q


class BoardConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        prms_dict = self.scope['url_route']['kwargs']
        self.ws = prms_dict['workspace']
        self.pf = prms_dict['portfolio']
        self.pj = prms_dict['project']
        self.r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        try:
            self.room_name = self.ws + self.pf + self.pj + settings.SECRET_LINKTOKEN_KEY
            encoded=self.room_name.encode()
            self.room_group_name = hashlib.sha256(encoded).hexdigest()

            my_room = self.user.email + settings.SECRET_LINKTOKEN_KEY
            encoded=my_room.encode()
            self.my_room_name = hashlib.sha256(encoded).hexdigest()

            self.project_owner_user, self.project = await self.project_owner(self.ws, self.pf, self.pj)
        except PermissionError:
            return await self.disconnect(close_code=403)
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        # For direct messagges
        await self.channel_layer.group_add(self.my_room_name, self.channel_name)
        # notify others im online
        await self.channel_layer.group_send(self.room_group_name, {"type": "notify.online", 'email': self.user.email, "name": self.user.name, 'request_id': "user-online"})
        self.r.rpush('online_users', self.user.email)
        await self.accept()



    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.my_room_name, self.channel_name)
        self.r.lrem("online_users", 0, self.user.email)



    # Receive message from WebSocket
    async def receive_json(self, text_data, **kwargs):
        request_id = text_data['request_id']
        data = text_data['data']
        await self.single_user_response(request_id, data)
        

    @sync_to_async
    def project_owner(self, ws_uid, pf_uid,  pj_uid):
        project = Project.objects.filter(portfolio__workspace__workspace_uuid=ws_uid, 
                    portfolio__portfolio_uuid=pf_uid,  project_uuid=pj_uid).first()
        if project:
            owner = project.portfolio.workspace.workspace_user
            if self.user.email in project.invited_users or owner == self.user:
                return owner, project
            else:
                raise PermissionError("You are not invited to this project.")
        else:
            raise PermissionError("You are not invited to this project.")


    async def notify_online(self, event):
        response =  {'email': event["email"], "name": event["name"], 'request_id': event['request_id']}
        await self.send_json(response)


    # for single user response
    async def single_user_response(self, request_id, data):
        if request_id == "project-online-users":
            await self.project_online_users(request_id)
        elif request_id == "get-board":
            await self.get_board(request_id, data)
        elif request_id == "get-board-tasks":
            await self.get_board_tasks(request_id, data)
        elif request_id == "get-task":
            await self.get_task(request_id, data)
        elif request_id == "create-project":
            await self.create_project(request_id, data)
        elif request_id == "delete-project":
            await self.delete_project(request_id, data)
        elif request_id == "search-project":
            await self.search_project(request_id, data)
        elif request_id == "search-boards":
            await self.search_boards(request_id, data)
        elif request_id == "remove-user":
            await self.remove_user(request_id, data)
        elif request_id == "change-user-role":
            await self.change_user_role(request_id, data)
        elif request_id == "delete-aws-file":
            await self.delete_aws_file(request_id, data)
        elif request_id == "get-aws-file":
            await self.get_aws_file(request_id, data)
        elif request_id == "get-project-activities":
            await self.get_project_activities(request_id, data)
        elif request_id == "export-board":
            await self.export_board(request_id, data)
        elif request_id == "get-chat-messages":
            await self.get_chat_messages(request_id, data)
        elif request_id == "get-inbox":
            await self.get_inbox(request_id, data)
        else:
            if request_id == "create-task":
                is_updated = await self.create_task(request_id, data)
            elif request_id == "delete-task":
                is_updated = await self.delete_task(request_id, data)
            elif request_id == "rename-subtask" or request_id == "delete-subtask" or request_id == "add-subtask" or request_id == "set-subtask":
                is_updated = await self.update_subtask(request_id, data)
            elif request_id == "add-label" or request_id == "remove-label":
                is_updated = await self.update_task_labels(request_id, data)
            elif request_id == "create-board":
                is_updated = await self.create_board(request_id, data)
            elif request_id == "update-board":
                is_updated = await self.update_board(request_id, data)
            elif request_id == "delete-board":
                is_updated = await self.delete_board(request_id, data)
            elif request_id == "change-tasks-col":
                is_updated = await self.change_tasks_col(request_id, data)
            elif request_id == "add-col":
                is_updated = await self.add_col(request_id, data)
            elif request_id == "rename-col":
                is_updated = await self.rename_col(request_id, data)
            elif request_id == "delete-col":
                is_updated = await self.delete_col(request_id, data)
            elif request_id == "change-col-order":
                is_updated = await self.change_col_order(request_id, data)
            elif request_id == "invite-users":
                is_updated = await self.invite_users(request_id, data)
            elif request_id == "groupe-chat":
                is_updated = await self.groupe_chat(request_id, data)
            elif request_id == "direct-message":
                is_updated = await self.direct_msg(request_id, data)
            if is_updated:
                await self.channel_layer.group_send(self.room_group_name, {"type": "notify.team", 'user': self.user.email , 'request_id': request_id, "notification": "update"})

        

    async def notify_team(self, event):
        response =  {'user': event['user'] , 'request_id': event['request_id'], "update": True}
        await self.send_json(response)


    '''
    Project part
    '''


    async def project_online_users(self, request_id):
        online_users = set(self.r.lrange("online_users", 0, -1))
        data = [{"user_email": x.decode("utf8")} for x in online_users]
        response = {'request_id': request_id, 'data': data}
        await self.send_json(response)



    async def create_project(self, request_id, data):
        try:
            # roles and permissions part

            # current_user_role = None
            # if self.project_owner_user == self.user:
            #     usr = self.user
            # else:
            #     assignee = await database_sync_to_async(self.get_project_assignee_db)(self.project_owner_user)
            #     if self.user.email in assignee:
            #         current_user_role = assignee[self.user.email]["role"]
            #         if current_user_role in ['Product owner', 'Project manager']:
            #             usr = self.project_owner_user
            #         else:
            #             response = {'status': 'error', 'code': 403, 'request_id': request_id, 'message': 'You are not allowed to create project.'}
            #             return await self.send_json(response)
            #     else:
            #         response = {'status': 'error', 'code': 403, 'request_id': request_id, 'message': 'You dont have assecc to this project'}
            #         return await self.send_json(response)

            usr, current_user_role = await self.role_permission(access_role_permissions=['Product owner', 'Project manager'])

            serializer = KanbanProjectSerializer(data=data)
            if serializer.is_valid():
                user_data = serializer.data
                pfl = await database_sync_to_async(Portfolio.objects.filter)(
                    workspace__workspace_user=usr, 
                    workspace__workspace_uuid=self.ws, 
                    portfolio_uuid=self.pf
                )
                portfolio = await sync_to_async(pfl.first)()
                try:
                    if portfolio:
                        prdowner_scrummster_json = {}
                        if current_user_role:
                            prdowner_scrummster_json[self.user.email] = {"profile_img": self.user.profile_image, "role": current_user_role}
                        if user_data["productowner"]:
                            img = await database_sync_to_async(self.get_img_url_by_email)(user_data["productowner"])
                            prdowner_scrummster_json[user_data["productowner"]] = {"profile_img": img, "role": "Product owner"}
                        if user_data["scrummaster"]:
                            img = await database_sync_to_async(self.get_img_url_by_email)(user_data["scrummaster"])
                            prdowner_scrummster_json[user_data["scrummaster"]] = {"profile_img": img, "role": "Scrum master"}
                        await database_sync_to_async(self.set_invited)([{"email": user_data["productowner"], "role": "Project manager"}, {"email": user_data["scrummaster"], "role": "Scrum master"}])
                        await database_sync_to_async(Project.objects.create)(
                            portfolio=portfolio, name=user_data["name"], 
                            project_description=user_data["projectdescription"],
                            agile_framwork=user_data["agileframwork"],
                            invited_users=prdowner_scrummster_json
                        )
                        response = {'status': 'ok', 'code': 200, 'request_id': request_id, 'message': f'({user_data["name"]}) Project has been created.', "data": []}
                        return await self.send_json(response)
                    else:
                        response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Portfolio not exists'}
                        return await self.send_json(response) 
                except IntegrityError:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project Already exist in the portfolio'}
                    return await self.send_json(response) 
            else:
                err = list(serializer.errors.items())
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
                return await self.send_json(response)
                
        except PermissionError as pe:
            response = {'status': 'error', 'code': 403, 'request_id': request_id, 'message': pe}
            return await self.send_json(response)
        


    async def delete_project(self, request_id, data):
        if self.project_owner_user == self.user:
            # project = await database_sync_to_async(self.get_project_db)(self.user) 
            if self.project:
                await database_sync_to_async(self.delete_db)(self.project)
                response = {'status': 'ok', 'code': 200, 'request_id': request_id, 'message': 'Project deleted.', "data": []}
                return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists'}
                return await self.send_json(response) 
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'you dont have permission to delete project'}
            return await self.send_json(response) 


    async def invite_users(self, request_id, data):
        serializer = InviteUsersSerializer(data=data)
        if serializer.is_valid():
            if self.project_owner_user == self.user:
                invited_users = serializer.data['users_email']
                await database_sync_to_async(self.set_invited)(invited_users) 
                response = {'status': 'ok', 'code': 200, 'request_id': request_id, 'message': 'user invited to project', "data": {"notification": f"{invited_users} has been invited to ({self.pj}) project"}}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You not allowed to invite users.'}
                await self.send_json(response) 
                return False
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return await self.send_json(response)
        

    
    async def change_user_role(self, request_id, data):
        serializer = ProjectRolesSerializer(data=data)
        if serializer.is_valid():
            if self.project_owner_user == self.user:
                try:
                    # project = await database_sync_to_async(self.get_project_db)(self.user) 
                    self.project.invited_users[data["email"]]["role"] = serializer.data["role"]   
                    await database_sync_to_async(self.project.save)()
                    response = {'status': 'ok', 'code': 200, 'request_id': request_id, 'message': 'Role updated seccessfuly', "data": []}
                    return await self.send_json(response)
                except:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Email not found.'}
                    return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You not allowed to invite users.'}
                return await self.send_json(response) 
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return await self.send_json(response)

    
    async def remove_user(self, request_id, data):
        if self.project_owner_user == self.user:
            # project = await database_sync_to_async(self.get_project_db)(self.user) 
            eml = data["email"]
            invtdusr = await database_sync_to_async(InvitedProjects.objects.filter)(iuser__email=eml, inviter_project=self.project)
            invtdusr = await sync_to_async(invtdusr.first)()
            if eml in self.project.invited_users and invtdusr:
                del self.project.invited_users[eml]
                await database_sync_to_async(self.project.save)()
                await database_sync_to_async(invtdusr.delete)()
                response = {'status': 'ok', 'code': 200, 'request_id': request_id, 'message': 'User removed seccessfuly', "data": []}
                return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Email not exists.'}
                return await self.send_json(response)
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You not allowed to delete users.'}
            return await self.send_json(response)


    async def search_project(self, request_id, data):
        try:

            # if self.project_owner_user == self.user:
            #     data = await self.search_prj(data, usr=self.user)
            # else:
            #     assignee = await database_sync_to_async(self.get_project_assignee_db)(self.project_owner_user)
            #     if self.user.email in assignee:
            #         if assignee[self.user.email]["role"] in ['Product owner', 'Scrum master', 'Project manager', 'Team member']:
            #             data = await self.search_prj(data, usr=self.project_owner_user)
            #         else:
            #             raise PermissionError('You dont have permission')

            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager', 'Team member'])
            data = await self.search_prj(data, usr=usr)

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
        if usr == self.user:
            boards = Board.objects.filter(prj__portfolio__workspace__workspace_user=usr, 
                                        prj__portfolio__workspace__workspace_uuid=self.ws, name__contains=query)  
            portfolios = Portfolio.objects.filter(workspace__workspace_user=usr,
                                                workspace__workspace_uuid=self.ws, portfolio_name__contains=query)
            projects = Project.objects.filter(portfolio__workspace__workspace_user=usr,
                                            portfolio__workspace__workspace_uuid=self.ws, name__icontains=query)
            boards_tsks = Board.objects.filter(prj__portfolio__workspace__workspace_user=usr, 
                                            prj__portfolio__workspace__workspace_uuid=self.ws)
        else:
            projects, portfolios = [], []
            boards = Board.objects.filter(prj__portfolio__workspace__workspace_user=usr, 
                                        prj__portfolio__workspace__workspace_uuid=self.ws,
                                        prj__portfolio__portfolio_uuid=self.pf, prj__project_uuid=self.pj, name__contains=query)  
            boards_tsks = Board.objects.filter(prj__portfolio__workspace__workspace_user=usr, 
                                        prj__portfolio__workspace__workspace_uuid=self.ws,
                                        prj__portfolio__portfolio_uuid=self.pf, prj__project_uuid=self.pj)  
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
            if invited != "":
                invited_user = User.objects.filter(email=invited["email"]).first()
                if invited_user:
                    inviter_prj = Project.objects.filter(portfolio__workspace__workspace_user=self.user, 
                                                        portfolio__workspace__workspace_uuid=self.ws,
                                                        portfolio__portfolio_uuid=self.pf, project_uuid=self.pj).first()
                    if inviter_prj.invited_users is None:
                        inviter_prj.invited_users = {}
                    inviter_prj.invited_users[str(invited["email"])] = {"profile_img": str(invited_user.profile_image), "role": invited["role"]}
                    inviter_prj.save()
                    project_url = f"http://localhost:8000/api/dash/workspaces/{self.ws}/portfolios/{self.pf}/projects/{self.pj}/"  # will change to front
                    email_body = f'Hi, you have been invited by {self.user.name} ({self.user.email}) to the project ({project_url}).'
                    invusrs.append(('you have been invited to project', email_body, settings.EMAIL_HOST_USER, [invited_user.email]))
                    prj = Project.objects.filter(portfolio__workspace__workspace_user=self.project_owner_user, portfolio__workspace__workspace_uuid=self.ws, portfolio__portfolio_uuid=self.pf, project_uuid=self.pj).first()
                    invprj.append(InvitedProjects(iuser=invited_user, inviter_project=prj, workspace_uid=self.ws, portfolio_uid=self.pf, project_uid=self.pj))  # , inviter=self.user.email
                    ntfs.append(UserNotification(notification_user=invited_user, notification_text=email_body, notification_from=self.user, notification_url=project_url))
        if invusrs:
            InvitedProjects.objects.bulk_create(invprj)
            UserNotification.objects.bulk_create(ntfs)
            send_mass_mail(invusrs)
        

    async def get_project_activities(self, request_id, data):
        try:
            await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager'])
            # project = await database_sync_to_async(self.get_project_db)(usr)
            if self.project:
                data = await self.board_project_activities(self.project, data)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Project activities', 'data': data}
                return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists.'}
                return await self.send_json(response)
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            return await self.send_json(response)

    @database_sync_to_async
    def board_project_activities(self, project, data):
        dct = {"board__prj": project}
        if data["board"]:
            dct["board__name"] = data["board"]
        if data["type_of_activity"]:
            dct["activity_type"] = data["type_of_activity"]
        if data["user_email"]:
            dct["activity_user_email"] = data["user_email"]
        boards = BoardActivities.objects.filter(**dct) 
        return BoardActivitiesSerializer(boards, many=True).data

    
    async def export_board(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager']) # board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, self.user)
            board = await database_sync_to_async(self.get_board_db)({"board": data["board"]}, usr=usr)
            if board:
                res_brd = []
                for col in board.board:
                    for col_name, tsks in col.items():
                        for tsk in tsks:
                            aging = None
                            if "first_move_date" in tsk and "last_move_date" in tsk:
                                d1 = dt.strptime(tsk["first_move_date"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                                d2 = dt.strptime(tsk["last_move_date"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
                                aging = str(d2-d1)
                            pf_name, pj_name = await sync_to_async(self.get_pf_pj)(board)
                            res_brd.append({"portfolio_name": pf_name, "project_name": pj_name, "board_name": data["board"], "col_name": col_name, "name": tsk["name"], "created_at": tsk["created_at"], 
                                        "story": tsk["story"], "due_date": tsk["due_date"], "aging": aging, 
                                        "files": tsk["files"], "labels": tsk["labels"], "subtasks": tsk["subtasks"], "assignees": tsk["assignees"]})
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Board task has been created.', 'data': res_brd}
                return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board not exists.'}
                await self.send_json(response) 
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False

    def get_pf_pj(self, board):
        return board.prj.portfolio.portfolio_name, board.prj.name


    '''
    Board Part
    '''

    async def get_board_tasks(self, request_id, data):
        try:
            a = dt.strptime("10/12/13", "%m/%d/%y")
            b = dt.strptime("10/15/13", "%m/%d/%y")
            a > b
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager', 'Team member'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, usr=usr)
            if board:
                query = data["filters"]
                results = []

                if not query:  
                    for x in board.board:
                        tsks = list(x.values())[0]
                        for t in tsks:
                            results.append(t)

                else:
                    for x in board.board:
                        tsks = list(x.values())[0]
                        for y in tsks:
                            tsk = self.get_stages_task_filter(query, tsk=y, col=x)
                            if tsk:
                                tsk = self.get_stories_task_filter(query, tsk=tsk)
                                if tsk:
                                    tsk = self.get_dates_task_filter(tsk=tsk, query=query)
                                    if tsk:
                                        tsk = self.get_labels_task_filter(tsk=tsk, query=query)
                            if tsk:
                                results.append(tsk)


                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'({data["name"]}) Kanban board info.', "data": {"Tasks": results}}
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

    def get_stages_task_filter(self, query, tsk, col):
        if "stages" in query:
            for z in query["stages"]:
                if z in col and col[z]:
                    return tsk
        else:
            return tsk


    def get_stories_task_filter(self, query, tsk):
        if "story" in query:
            story = query["story"]
            if story and story[0] == "+":
                if tsk["story"] > int(story[1:]):
                    return tsk
            elif story and story[0] == "-":
                if tsk["story"] < int(story[1:]):
                    return tsk 
            else:
                if story and tsk["story"] == int(story):
                    return tsk
        else:
            return tsk
    
    def get_dates_task_filter(self, query, tsk):
        if "due_date" in query:
            selected_date = query["due_date"]
            if selected_date:
                frm = selected_date["from"]
                to = selected_date["to"]
                frm = dt.strptime(frm, '%Y-%m-%d')
                to = dt.strptime(to, '%Y-%m-%d')
                due_date = dt.strptime(tsk["due_date"].split("T")[0], '%Y-%m-%d')
                if frm <= due_date <= to:
                    return tsk
        else:
            return tsk


    def get_labels_task_filter(self, query, tsk):
        if "labels" in query:
            for z in query["labels"]:
                if z in tsk["labels"]:
                    return tsk
        else:
            return tsk

    async def get_board(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager', 'Team member'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, usr=usr)
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


    async def update_board(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["old_name"]}, usr=usr)
            if board:
                board.name = data["new_name"]
                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="update-board", activity_description=f"Board name has been updated.")
                notification_text, notification_url = f"({board.name}) Board name has been updated to {board.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'({data["old_name"]}) Kanban board name updated.', "data": {"board": board.board}}
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


    async def create_board(self, request_id, data):
        try:
            # if self.project_owner_user == self.user:
            #     project = await database_sync_to_async(self.get_project_db)(self.user) 
            # else:
            #     project = await database_sync_to_async(self.get_project_db)(self.project_owner_user)
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, usr=usr)
            if board:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board already exists.'}
                await self.send_json(response) 
                return False 
            else:
                if data["name"].strip() == "":
                    board_count = await database_sync_to_async(Board.objects.filter)(prj=self.project)
                    board_count = await sync_to_async(board_count.count)()
                    await database_sync_to_async(self.db_create_board)(prj=self.project, name=f"kanban Board {board_count+1}")
                else:
                    await database_sync_to_async(self.db_create_board)(prj=self.project, name=data["name"])
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="create-board", activity_description=f"New Board has been created.")
                notification_text, notification_url = f"Board ({board.name}) has been created on project {self.project.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Board task has been created.'}
                await self.send_json(response)
                return True
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def delete_board(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Project manager'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, usr=usr)
            if board:
                await database_sync_to_async(self.delete_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="delete-board", activity_description=f"Board has been deleted.")
                notification_text, notification_url = f"({board.name}) Board has been deleted.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'({data["name"]}) Kanban board deleted.'}
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
        

    async def search_boards(self, request_id, data):
        try: 
            data = await self.search_brd(data)
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
    def search_brd(self, user_data):
        query = user_data["search_query"]
        boards = Board.objects.filter(prj__portfolio__workspace__workspace_user=self.project_owner_user, 
                                        prj__portfolio__workspace__workspace_uuid=self.ws,
                                        prj__portfolio__portfolio_uuid=self.pf, prj__project_uuid=self.pj, name__contains=query)  
        return BPPSerializer(boards, many=True).data

        
    async def add_col(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            colname = data["colname"]
            if board:
                if not any(colname in b for b in board.board):
                    board.board.append({colname: []})
                else:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board already exists.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email,
                                    activity_type="add-col", activity_description=f"New Column ({colname}) has been added.")
                notification_text, notification_url = f"New Column ({colname}) has been added to board {board.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
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
            

    async def rename_col(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            colname = data["col_name"]
            new_colname = data["new_name"]
            if board:
                for b in board.board:
                    if colname in b:
                        b[new_colname] = b[colname]
                        del b[colname]
                        break
                else:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Column name not exists.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email,
                                    activity_type="rename-col", activity_description=f"Column ({colname}) has been renamed > {new_colname}.")
                notification_text, notification_url = f"Column ({colname}) has been renamed > {new_colname} on board {board.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'{colname} column has been renamed sucessfuly.'}
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
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            col_index = data["col_index"]
            if board:
                try:
                    del board.board[col_index] # should shows popup warning from the front tells thats all column contents tasks will be deleted.
                except IndexError:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'column index out of range.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email,
                                    activity_type="delete-col", activity_description="A column has been deleted.")
                notification_text, notification_url = f"A column has been deleted on board {board.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
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
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            col_index = data["col_index"]
            to_index = data["to_index"]
            if board:
                col2changeorder = board.board.pop(col_index)
                board.board.insert(to_index, col2changeorder)
                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email,
                                    activity_type="change-col-order", activity_description="A column order has been changed.")
                notification_text, notification_url = f"A column order has been changed on board {board.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
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


    '''
    Tasks Part
    '''
    async def get_task(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Scrum master', 'Project manager', 'Team member'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["board"]}, usr=usr)
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
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The board not exists'}
                await self.send_json(response) 
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def delete_task(self, request_id, data): 
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager', 'Scrum master'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["board"]}, usr=usr)
            if board:
                try:
                    dict_col = board.board[data["col_index"]]
                    col_name = list(dict_col.keys())[0]
                    del board.board[data["col_index"]][col_name][data["task_index"]]
                except (IndexError, KeyError):
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                activity_type="delete-task", activity_description=f"Task has been deleted.")
                notification_text, notification_url = f"Task on board ({board.name}) has been deleted.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The task has been deleted sucessfuly.'}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The board not exists'}
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
                usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager', 'Scrum master'])
                board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
                try:
                    created_time, end_date = self.set_datetime_format(data["due_date"])
                except ValueError as ve:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(ve)}
                    await self.send_json(response)
                    return False
                task_title = user_data["name"]
                my_task = {"name": task_title, "files": data["files"], "assignees": data["assignees"], "subtasks": data["subtasks"], "labels": data["labels"], "story": data["story"], "created_at": created_time, "due_date": end_date}
                if board:        
                    for i, d in enumerate(board.board):
                        if user_data["col"] in d:
                            tasks_list = board.board[i][user_data["col"]]
                            tasks_list.append(my_task)
                            await database_sync_to_async(self.save_db)(board)
                            calendar = data["calendar"]
                            if calendar["is_google"]:
                                await self.add_task_to_ggl_calendar(my_task, token=calendar["token"])
                            else:
                                await self.add_task_to_ms_calendar(my_task, token=calendar["token"])
                            await database_sync_to_async(self.notify_assignees)(data["assignees"], task_title)
                            await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, activity_type="create-task", activity_description=f"({task_title}) Task has been created.")
                            notification_text, notification_url = f"New Task ({task_title}) has been created on board ({board.name}).", "http://will-be-front-board-page-route.com"
                            await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The task has been created.'}
                            await self.send_json(response)
                            return True
                    else:
                        response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board column not exists'}
                        await self.send_json(response) 
                        return False
                else:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The board not exists'}
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

    def set_datetime_format(self, due_date):
        try:
            dt.strptime(due_date.strip(), '%Y-%m-%d')
        except ValueError:
            raise ValueError('Incorrect data format, should be YYYY-MM-DD')
        time_now = dt.now()
        created_time = time_now.isoformat()
        tm = created_time.split("T")[1]
        due_date = due_date.strip() + "T" + tm
        return created_time, due_date


    async def add_task_to_ms_calendar(self, data, token):
        header = {"Authorization": "Bearer " + token, "Content-type": "application/json"}
        attendees = [{"emailAddress": {"address": x, "name": x.split("@")[0]}, "type": "required"} for x in data["assignees"]]
        info = {
            "subject": "Task : "+ data["name"],
            "body": {
                "contentType": "HTML",
                "content": data["name"]
            },
            "start": {
                "dateTime": data["due_date"],
                "timeZone": "America/Los_Angeles"
            },
            "end": {
                "dateTime": data["due_date"],
                "timeZone": "America/Los_Angeles"
            },
            "attendees": attendees,
            "allowNewTimeProposals": True
        }
        requests.post("https://graph.microsoft.com/v1.0/me/events", 
                    data=json.dumps(info), headers=header)

    
    async def add_task_to_ggl_calendar(self, data, token):
        header = {"Authorization": "Bearer " + token, "Content-type": "application/json"}
        event = {
            'summary': "Task : "+ data["name"],
            'description': data["name"],
            'start': {
                'dateTime': data["due_date"],
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': data["due_date"],
                'timeZone': 'America/Los_Angeles',
            },
            'attendees': [{'email': x}  for x in data["assignees"]],
            'reminders': {
                'useDefault': True
            },
        }
        requests.post("https://www.googleapis.com/calendar/v3/calendars/primary/events", 
                    data=json.dumps(event), headers=header)


    async def update_subtask(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager', 'Scrum master'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            if board:
                try:
                    dict_col = board.board[data["col_index"]]
                    col_name = list(dict_col.keys())[0]
                    dict_task = board.board[data["col_index"]][col_name][int(data["task_index"])]
                    if request_id == "delete-subtask" or request_id == "update-subtask":
                        old_name = data["old_name"]
                        if old_name in dict_task["subtasks"]:
                            if request_id == "update-subtask":
                                new_name = data["new_name"]
                                dict_task["subtasks"][new_name] = dict_task["subtasks"][old_name]
                                del dict_task["subtasks"][old_name]
                                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="update-subtask", activity_description=f"Subtask name has been updated.")
                            else:
                                del dict_task["subtasks"][old_name]
                                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="delete-subtask", activity_description=f"Subtask has been deleted.")
                        else:
                            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The subtask not exists'}
                            await self.send_json(response)
                            return False
                    elif request_id == "set-subtask":
                        if data["name"] in dict_task["subtasks"]:
                            dict_task["subtasks"][data["name"]] = data["is_done"]
                            await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="set-subtask", activity_description=f"Subtask status has been updated.")
                        else:
                            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The subtask not exists'}
                            await self.send_json(response)
                            return False
                    elif request_id == "add-subtask":
                        dict_task["subtasks"][data["name"]] = False
                        await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="set-subtask", activity_description=f"Subtask has been addedd.")
                    else:
                        response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
                        await self.send_json(response)
                        return False
                except (IndexError, KeyError):
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                notification_text, notification_url = f"There is an Subtask update on board ({board.name}).", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The subtasks has been updated sucessfuly.'}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The board not exists'}
                await self.send_json(response)
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def update_task_labels(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager', 'Scrum master'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            if board:
                try:
                    dict_col = board.board[data["col_index"]]
                    col_name = list(dict_col.keys())[0]
                    dict_task = board.board[data["col_index"]][col_name][int(data["task_index"])]
                    if request_id == "add-label":
                        dict_task["labels"].append(data["label"])
                        await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="add-label", activity_description=f"New Label has been addedd.")
                    elif request_id == "remove-label":
                        if data["label"] in dict_task["labels"]:
                            dict_task["labels"].remove(data["label"])
                            await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="remove-label", activity_description=f"Label has been deleted.")
                        else:
                            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The label not exists'}
                            await self.send_json(response)
                            return False
                except (IndexError, KeyError):
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
                    await self.send_json(response)
                    return False
                await database_sync_to_async(self.save_db)(board)
                notification_text, notification_url = f"There is an Label update on board ({board.name}).", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The labels has been updated sucessfuly.'}
                await self.send_json(response)
                return True
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The board not exists'}
                await self.send_json(response)
                return False
        except PermissionError as pe:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
            await self.send_json(response)
            return False


    async def change_tasks_col(self, request_id, data):
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Product owner', 'Project manager', 'Scrum master', 'Team member'])
            board = await database_sync_to_async(self.get_board_db)(data, usr=usr)
            if board:  
                col_values = board.board
                tasks_2_move = []
                from_col = data["from_col"]
                to_col = data["to_col"]
                
                # cut the tasks
                if_from_col_there = False
                for c in col_values:
                    if from_col in c:
                        if c[from_col]:
                            ids_list = data["tasks_ids"]
                            for i in ids_list:
                                tasks_2_move.append(c[from_col].pop(int(i)))
                            if_from_col_there = True
                            break
                        else:
                            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'No tasks to move.'}
                            await self.send_json(response)
                            return True

                # paste the tasks
                if_to_col_there = False
                for j, cl in enumerate(col_values):
                    if to_col in cl:
                        in_pos = data["in_pos"]
                        for t in tasks_2_move:
                            cl[to_col].insert(in_pos, t)
                            in_pos += 1
                            time_now = dt.now() # This for Aging (card move to the second column) 
                            if j == 1: 
                                t["first_move_date"] = time_now.isoformat()
                            elif j > 1:
                                t["last_move_date"] = time_now.isoformat()
                        if_to_col_there = True
                        break

                # check if col name exists
                if not if_from_col_there or not if_to_col_there:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Column name not exists.'}
                    await self.send_json(response)
                    return False

                await database_sync_to_async(self.save_db)(board)
                await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email, 
                                    activity_type="move-task", activity_description=f"Task(s) has been moved from {from_col} > {to_col}.")
                notification_text, notification_url = f"Task(s) has been moved from {from_col} > {to_col} on board {board.name}.", "http://will-be-front-board-page-route.com"
                await database_sync_to_async(self.notify_group)(board, notification_text, notification_url)
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


    def notify_assignees(self, assignees, task_name):
        assignee_users, notfs = [], []
        for asgn in assignees:
            assignee_user = User.objects.filter(email=asgn).first()
            if assignee_user:
                project_url = f"http://localhost:8000/api/dash/project/{self.pf}/{self.pj}/?invited=1"  # will change to front
                email_body = f'Hi , you are assigned to a Task ({task_name})\nof the following Project: {project_url}.'
                assignee_users.append(('Task assigned to you', email_body, settings.EMAIL_HOST_USER, [assignee_user.email]))
                notfs.append(UserNotification(notification_user=assignee_user, notification_text=email_body, notification_from=self.user, notification_url=project_url))
        if assignee_users:
            UserNotification.objects.bulk_create(notfs)
            send_mass_mail(assignee_users)

    '''
    S3 Storage part
    '''
    async def get_aws_file(self, request_id, data):
        try:
            file_url = data["file_url"]
            res = requests.get(file_url)
            if res.status_code <= 200:
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'file info.', "data": {"file_url": file_url}}
                return await self.send_json(response)
            else:
                file_aws_name = urlparse(file_url).path[1:]
                utils_cls = VifUtils()
                file_url = utils_cls.create_presigned_url(bucket_name=settings.BUCKET_NAME, region_name=settings.REGION_NAME, object_name=file_aws_name, expiration=600000)
                # TODO to updqte task file url also
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'file info.', "data": {"file_url": file_url}}
                return await self.send_json(response)
        except:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'bad request'}
            return await self.send_json(response)


    async def delete_aws_file(self, request_id, data): 
        try:
            usr, _ = await self.role_permission(access_role_permissions=['Project manager'])
            board = await database_sync_to_async(self.get_board_db)({"board": data["board"]}, usr=usr)
            if board:  
                try:
                    is_deleted = self.dltfl(data["file_url"])
                    if is_deleted:
                        await database_sync_to_async(BoardActivities.objects.create)(board=board, activity_user_email=self.user.email,
                                            activity_type="delete-file", activity_description="A file has been deleted.")
                        response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'File seccessfuly deleted.'}
                        return await self.send_json(response)
                    else:
                        response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'File not deleted.'}
                        return await self.send_json(response)
                except FileNotFoundError as e:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(e)}
                    return await self.send_json(response)
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The board not exists'}
                return await self.send_json(response)
        except PermissionError as e:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(e)}
            return await self.send_json(response)


    def dltfl(self, file_url):
        try:
            file_aws_name = urlparse(file_url).path[1:]
            utils_cls = VifUtils()
            is_deleted = utils_cls.delete_from_s3(self.project_owner_user, file_aws_name)
            if is_deleted:
                return True
            else:
                return False
        except:
            raise FileNotFoundError("File not found")

    '''
    Group Messages Part
    '''
    async def groupe_chat(self, request_id, data):
        try:
            await database_sync_to_async(ProjectGroupeChat.objects.create)(prj=self.project, auditor=self.user, content=data["content"], attachments=data["attachments"])
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'New message in group chat.', "data": {"auditor_name": self.user.name, "auditor_email": self.user.email, "content": data["content"], "attachments": data["attachments"]}}
            await self.send_json(response)
            return True
        except Exception:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': "bad request"}
            await self.send_json(response)
            return False


    async def get_chat_messages(self, request_id, data):
        try:      
            json_data = await database_sync_to_async(self.get_chat_data)(int(data["page"]))
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Group chat.', "data": json_data}
            await self.send_json(response)
            return True
        except Exception:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': "bad request"}
            await self.send_json(response)
            return False

    def get_chat_data(self, page_num):
        chat_group = ProjectGroupeChat.objects.filter(prj=self.project).order_by("-timestamp")
        p = Paginator(chat_group, 10)
        try:
            page = p.page(page_num)
        except EmptyPage:
            page = p.page(1)
        return GroupeChatSerializer(page.object_list, many=True).data


    '''
    Direct Messages Part
    '''
    async def direct_msg(self, request_id, data):
        try:
            saved = await database_sync_to_async(self.save_direct_message_db)(data)
            if saved:
                usrkey = data['email'] + settings.SECRET_LINKTOKEN_KEY
                encoded=usrkey.encode()
                usrhash = hashlib.sha256(encoded).hexdigest()
                await self.channel_layer.group_send(usrhash, {"type": "direct.message", 'user': self.user.email , 'request_id': request_id, "data": {"message": data['message'], "attachments": data['attachments']}})
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': "bad request"}
                await self.send_json(response)
        except Exception:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': "bad request, message not sent."}
            await self.send_json(response)

    async def direct_message(self, event):
        response =  {'user': event['user'] , 'request_id': event['request_id'], "data": event["data"]}
        await self.send_json(response)

    def save_direct_message_db(self, data):
        obj_usr = User.objects.filter(email=data['email']).first()
        if obj_usr:
            UserDirectMessages.objects.create(sender_user=self.user, receiver_user=obj_usr, content=data['message'], attachments=data['attachments'])
            return True
        else:
            return False


    async def get_inbox(self, request_id, data):
        try:
            info = await database_sync_to_async(self.get_inbox_db)(data)
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Direct messages.', "data": info}
            await self.send_json(response)
        except Exception:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': "bad request."}
            await self.send_json(response)

    def get_inbox_db(self, data):
        query = UserDirectMessages.objects.filter(Q(sender_user=self.user) | Q(receiver_user=self.user)).order_by("-timestamp")
        p = Paginator(query, 10)
        try:
            page = p.page(data["page"])
        except EmptyPage:
            page = p.page(1)
        return UserMsgsSerializer(page, many=True).data


    '''
    database query functions
    '''
    def get_board_db(self, user_data, usr):
        # return Board.objects.filter(prj__portfolio__workspace__workspace_user=usr, 
        #                             prj__portfolio__workspace__workspace_uuid=self.ws, prj__portfolio__portfolio_uuid=self.pf,
        #                             prj__project_uuid=self.pj, name=user_data["board"]).first() 
        return self.project.board_set.filter(name=user_data["board"]).first()

    # def get_project_db(self, usr):
    #     return Project.objects.filter(portfolio__workspace__workspace_user=usr, 
    #                                 portfolio__workspace__workspace_uuid=self.ws, 
    #                                 portfolio__portfolio_uuid=self.pf,
    #                                 project_uuid=self.pj).first()

    # def get_project_assignee_db(self, usr):
    #     prjct = Project.objects.filter(portfolio__workspace__workspace_user=usr, 
    #                                 portfolio__workspace__workspace_uuid=self.ws, 
    #                                 portfolio__portfolio_uuid=self.pf, project_uuid=self.pj).first()
    #     return prjct.invited_users


    def get_img_url_by_email(self, eml):
        usr_obj = User.objects.filter(email=eml).first()
        return usr_obj.profile_image if usr_obj else "https://vifbox.org/api/media/default.jpg"

    def db_create_board(self, prj, name):
        brd = Board(prj=prj, name=name)
        brd.save()
            
    
    def save_db(self, obj):
        obj.save()

    
    def delete_db(self, obj):
        obj.delete()


    def notify_group(self, board, notification_text, notification_url):
        invited_users_json = board.prj.invited_users
        owner_user = board.prj.portfolio.workspace.workspace_user
        for eml in invited_users_json.keys():
            if self.user != owner_user:
                UserNotification.objects.create(notification_user=owner_user, notification_from=self.user, notification_text=notification_text, notification_url=notification_url)
            else:
                usr = User.objects.filter(email=eml).first()
                if usr and usr != self.user:
                    UserNotification.objects.create(notification_user=usr, notification_from=self.user, notification_text=notification_text, notification_url=notification_url)


    '''
    user role permission
    '''
    async def role_permission(self, access_role_permissions):
        if self.project_owner_user == self.user:
            return self.user, None
        else:
            assignee = self.project.invited_users
            if self.user.email in assignee:
                current_user_role = assignee[self.user.email]["role"]
                if current_user_role in access_role_permissions:
                    return self.project_owner_user, current_user_role
                else:
                    raise PermissionError('You dont have permission')
            else:
                raise PermissionError('You dont have assecc to this project')







class UserConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        my_room = self.user.email + settings.SECRET_LINKTOKEN_KEY
        encoded=my_room.encode()
        self.my_room_name = hashlib.sha256(encoded).hexdigest()
        await self.channel_layer.group_add(self.my_room_name, self.channel_name)
        self.groups_names = await database_sync_to_async(self.add_user_projects)()
        for grps in self.groups_names:
            await self.channel_layer.group_add(grps, self.channel_name)
        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.my_room_name, self.channel_name)
        for grps in self.groups_names:
            await self.channel_layer.group_discard(grps, self.channel_name)

    def add_user_projects(self):
        groups_names = []
        user_projects = Project.objects.filter(portfolio__workspace__workspace_user=self.user)
        for prj in user_projects:
            self.room_name = str(prj.portfolio.workspace.workspace_uuid) + str(prj.portfolio.portfolio_uuid) + str(prj.project_uuid) + settings.SECRET_LINKTOKEN_KEY
            encoded=self.room_name.encode()
            self.room_group_name = hashlib.sha256(encoded).hexdigest()
            groups_names.append(self.room_group_name)
        invited_projects = InvitedProjects.objects.filter(iuser=self.user)
        for inv_prj in invited_projects:
            self.room_name = str(inv_prj.workspace_uid) + str(inv_prj.portfolio_uid) + str(inv_prj.project_uid) + settings.SECRET_LINKTOKEN_KEY
            encoded=self.room_name.encode()
            self.room_group_name = hashlib.sha256(encoded).hexdigest()
            groups_names.append(self.room_group_name)
        return groups_names

    
    async def direct_message(self, event):
        response =  {'user': event['user'] , 'request_id': event['request_id'], "data": event["data"]}
        await self.send_json(response)


    async def notify_team(self, event):
        response =  {'user': event['user'] , 'request_id': event['request_id'], "updated": True}
        await self.send_json(response)







    # async def delete_aws_file(self, request_id, data): 
    #     try:
    #         if self.user == self.project_owner_user:
    #             is_deleted = self.dltfl(data["file_url"])
    #             if is_deleted:
    #                 response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'File seccessfuly deleted.'}
    #                 return await self.send_json(response)
    #             else:
    #                 response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'File not deleted.'}
    #                 return await self.send_json(response)
    #         else:
    #             assignee = await database_sync_to_async(self.get_project_assignee_db)(self.project_owner_user)
    #             if self.user.email in assignee:
    #                 if assignee[self.user.email]["role"] == "Project manager":
    #                     is_deleted = self.dltfl(data["file_url"])
    #                     if is_deleted:
    #                         response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'File seccessfuly deleted.'}
    #                         return await self.send_json(response)
    #                     else:
    #                         response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'File not deleted.'}
    #                         return await self.send_json(response)
    #                 else:
    #                     response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You dont have permission'}
    #                     return await self.send_json(response)
    #             else:
    #                 response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'You dont have assecc to this project'}
    #                 return await self.send_json(response)
    #     except FileNotFoundError as e:
    #         response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(e)}
    #         return await self.send_json(response)



    # async def get_board_activities(self, request_id, data):
    #     try:
    #         board = await self.role_permission({"board": data["board"]}, access_role_permissions=['Product owner', 'Scrum master', 'Project manager', 'Team member']) # board = await database_sync_to_async(self.get_board_db)({"board": data["name"]}, self.user)
    #         if board:
    #             data = await self.board_activities(board)
    #             response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Board activities', 'data': data}
    #             return await self.send_json(response)
                
    #         else:
    #             response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board not exists.'}
    #             return await self.send_json(response) 
    #     except PermissionError as pe:
    #         response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': str(pe)}
    #         return await self.send_json(response)



    # @database_sync_to_async
    # def board_activities(self, board):
    #     board_activities = BoardActivities.objects.filter(board=board)   
    #     return BoardActivitiesSerializer(board_activities, many=True).data



# query = data["filters"]
                # if "story" in query:
                #     story = query["story"]
                # results = []
                # for x in board.board:
                #     tsks = list(x.values())[0]
                #     for y in tsks:
                #         found = False 
                #         if "story" in query:
                #             if story and story[0] == "+":
                #                 if y["story"] > int(story[1:]):
                #                     results.append(y)
                #                     found = True 
                #             elif story and story[0] == "-":
                #                 if y["story"] < int(story[1:]):
                #                     results.append(y)
                #                     found = True 
                #             else:
                #                 if story and y["story"] == int(story):
                #                     results.append(y)
                #                     found = True 
                #         if "stages" in query and not found:
                #             for z in query["stages"]:
                #                 if z in x and x[z]:
                #                     results.append(y)
                #                     found = True 
                #                     break
                #         if "due_date" in query and not found:
                #             selected_date = query["due_date"]
                #             if selected_date:
                #                 query_date = dt.strptime(selected_date, '%Y-%m-%d')
                #                 due_date = dt.strptime(y["due_date"].split("T")[0], '%Y-%m-%d')
                #                 if due_date == query_date:
                #                     results.append(y)
                #                     found = True
                #         if "labels" in query and not found:
                #             for z in query["labels"]:
                #                 if z in y["labels"]:
                #                     results.append(y)
                #                     found = True
                #                     break
                # else:
                #     if not found:
                #         for x in board.board:
                #             tsks = list(x.values())[0]
                #             for t in tsks:
                #                 results.append(t)



# if "stages" in query:
                #     for x in board.board:
                #         for y in query["stages"]:
                #             if y in x and x[y]:
                #                 results.append(x[y])
                # if "due_date" in query:
                #     query_date = dt.strptime(query["due_date"], '%Y-%m-%d')
                #     for x in board.board:
                #         tsks = list(x.values())[0]
                #         for y in tsks:
                #             due_date = dt.strptime(y["due_date"].split("T")[0], '%Y-%m-%d')
                #             if due_date == query_date:
                #                 results.append(x)
                # if "story" in query:
                #     story = query["story"]
                #     for x in board.board:
                #         tsks = list(x.values())[0]
                #         for y in tsks:
                #             if story[0] == "+":
                #                 if y["story"] > int(story[1:]):
                #                     results.append(y)
                #             elif story[0] == "-":
                #                 if y["story"] < int(story[1:]):
                #                     results.append(y)
                #             else:
                #                 if y["story"] == int(story):
                #                     results.append(y)