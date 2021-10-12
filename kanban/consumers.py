import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .serializers import TaskSerializer, PPSerializer
from .models import Project
from channels.db import database_sync_to_async

class BoardConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        self.user = user
        prms_dict = self.scope['url_route']['kwargs']
        pf = prms_dict['pf']
        pj = prms_dict['prjct']
        self.room_name = user.username + pf + pj
        self.room_group_name = 'team_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        request_id = text_data_json['request_id']
        data = text_data_json['data']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'group_response',
                'request_id': request_id,
                "data": data
            }
        )

    # Receive message from room group
    async def group_response(self, event):
        request_id = event['request_id']
        data = event['data']
        if request_id == "create-task":
            await self.create_task(request_id, data)
        elif request_id == "change-tasks-col":
            await self.change_tasks_col(request_id, data)
        elif request_id == "add-col":
            await self.add_col(request_id, data)
        elif request_id == "delete-col":
            await self.delete_col(request_id, data)
        elif request_id == "change-col-order":
            await self.change_col_order(request_id, data)
        elif request_id == "search-project":
            await self.search_project(request_id, data)


    async def create_task(self, request_id, data):
        serializer = TaskSerializer(data=data)
        if serializer.is_valid():
            user_data = serializer.data
            project = await database_sync_to_async(self.get_project)(user_data)
            if project:        
                for i, d in enumerate(project.board["board"]):
                    if user_data["col"] in d:
                        tasks_list = project.board["board"][i][user_data["col"]]
                        tasks_list.append({"task_des": user_data["description"]})
                        await database_sync_to_async(self.save_db)(project)
                        response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The task has been created.'}
                        return await self.send(text_data=json.dumps(response))
                else:
                    response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Board column not exists'}
                    return await self.send(text_data=json.dumps(response)) 
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The Project or the Portfolio not exists'}
                return await self.send(text_data=json.dumps(response)) 
        else:
            err = list(serializer.errors.items())
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': '(' + err[0][0] + ') ' + err[0][1][0]}
            return await self.send(text_data=json.dumps(response)) 
    

    async def change_tasks_col(self, request_id, data):
        project = await database_sync_to_async(self.get_project)(data)
        try:
            if project:  
                col_values = project.board["board"] # col_values = [{'Backlog': [{'task_des': 'task kkkk', 'task_pos': 0}, {'task_des': 'task kkkk22222', 'task_pos': 1}]}, {'To Do': []}, {'In Progress': []}, {'Done': []}]
                tasks_2_move = []
                from_col = data["from_col"]
                to_col = data["to_col"]
                # cut the tasks
                for c in col_values:
                    if from_col in c:
                        if c[from_col]:
                            ids_list = data["tasks_ids"].split(",")
                            for i in ids_list:
                                tasks_2_move.append(c[from_col].pop(int(i)))
                            break
                        else:
                            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'No tasks to move.'}
                            return await self.send(text_data=json.dumps(response))
                # paste the tasks
                for cl in col_values:
                    if to_col in cl:
                        in_pos = data["in_pos"]
                        for t in tasks_2_move:
                            cl[to_col].insert(in_pos, t)
                            in_pos += 1
                        break
                await database_sync_to_async(self.save_db)(project)
                response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Tasks moved successfuly.', "data": project.board["board"]} # to return the full project
                return await self.send(text_data=json.dumps(response))
            else:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'The Project or the Portfolio not exists'}
                return await self.send(text_data=json.dumps(response))
        except Exception:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Bad request.'}
            return await self.send(text_data=json.dumps(response))


    async def add_col(self, request_id, data):
        project = await database_sync_to_async(self.get_project)(data)
        colname = data["colname"]
        if project:
            project.board["board"].append({colname: []}) # should be checked from the front thats the column not exists.
            await database_sync_to_async(self.save_db)(project)
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'{colname} column has been added sucessfuly.'}
            return await self.send(text_data=json.dumps(response))
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists.'}
            return await self.send(text_data=json.dumps(response))


    async def delete_col(self, request_id, data):
        project = await database_sync_to_async(self.get_project)(data)
        col_index = data["col_index"]
        if project:
            try:
                del project.board["board"][col_index] # should shows popup warning from the front tells thats all column contents tasks will be deleted.
            except IndexError:
                response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'column index out of range.'}
                return await self.send(text_data=json.dumps(response))
            await database_sync_to_async(self.save_db)(project)
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': f'The column has been deleted sucessfuly.'}
            return await self.send(text_data=json.dumps(response))
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists.'}
            return await self.send(text_data=json.dumps(response))


    async def change_col_order(self, request_id, data):
        project = await database_sync_to_async(self.get_project)(data)
        col_index = data["col_index"]
        to_index = data["to_index"]
        if project:
            col2changeorder = project.board["board"].pop(col_index)
            project.board["board"].insert(to_index, col2changeorder)
            await database_sync_to_async(self.save_db)(project)
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'The column order has been changed sucessfuly.'}
            return await self.send(text_data=json.dumps(response))
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'Project not exists.'}
            return await self.send(text_data=json.dumps(response))


    async def search_project(self, request_id, data):
        data = await self.search_prj(data)
        if data:
            response = {'status': 'success', 'code': 200, 'request_id': request_id, 'message': 'Search result', 'data': data}
            return await self.send(text_data=json.dumps(response))
        else:
            response = {'status': 'error', 'code': 400, 'request_id': request_id, 'message': 'No project exists'}
            return await self.send(text_data=json.dumps(response))


    def get_project(self, user_data):
        return Project.objects.filter(name=user_data["project"], portfolio__portfolio_user=self.user, portfolio__portfolio_name=user_data["portfolio"]).first()

    @database_sync_to_async
    def search_prj(self, user_data):
        projects = Project.objects.filter(name__icontains=user_data["project"], portfolio__portfolio_user=self.user)
        if projects:
            data = {"projects":  PPSerializer(projects, many=True).data} 
            return data
        else:
            return None
    
    def save_db(self, obj):
        obj.save()