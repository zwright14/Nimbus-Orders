import boto3
import json

class Notification:

    def triggerNotification(path):
        pathList = ['/', '/orders']
        if path in pathList:
            notification = "Get Event received for path: " + path
            client = boto3.client('sns', region_name='us-east-1')
            response = client.publish (
            TargetArn = "arn:aws:sns:us-east-1:998678863102:GetEventTopic",
            Message = json.dumps({'default': notification}), MessageStructure='json')
            return {'statusCode': 200,'body': json.dumps(response)}
