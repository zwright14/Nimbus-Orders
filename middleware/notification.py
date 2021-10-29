class Notification:

    def triggerNotification(path):
        print("In Trigger")
        print(path)
        pathList = ['/', '/orders']
        if path in pathList:
            print("In PathList")
