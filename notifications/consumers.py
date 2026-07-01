# notifications/consumers.py

# from channels.generic.websocket import AsyncWebsocketConsumer
# import json
# from asgiref.sync import async_to_sync
# class NotificationConsumer(AsyncWebsocketConsumer):

#     async def connect(self):

#         # self.partner_id = self.scope['url_route']['kwargs']['partner_id']

#         # self.group_name = f"partner_{self.partner_id}"

#         await self.channel_layer.group_add(
#             "notification_group",
#             self.channel_name
#         )
#         print("connectin established ")
#         await self.accept()

#     async def disconnect(self, close_code):

#         await self.channel_layer.group_discard(
#             self.group_name,
#             self.channel_name
#         )

#     async def notify(self, event):

#         await self.send(text_data=json.dumps({
#             "message": event["message"]
#         }))