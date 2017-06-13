from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
import queue
import json
import time
from webchat import settings
import os

# Create your views here.

MSG_QUEUE = {}  # 定义消息队列


def receive_file(file_list):
    """该方法处理多文件上传保存
    file_list: 上传文件的列表对象
    """
    file_name_list = []
    for data in file_list:
        uploads_folder = os.path.join(settings.BASE_DIR, 'uploads')  # 指定保存目录位置
        if not os.path.exists(uploads_folder):
            try:
                os.makedirs(uploads_folder)
            except PermissionError:
                print('暂时忽略权限错误,请自觉手动创建该目录')
                pass
        file_name = data.name
        while os.path.exists(os.path.join(uploads_folder, file_name)):  # 判断是否有重名文件,确保不存在同名文件
            name, suffix = str(file_name).split('.', maxsplit=1)  # 分隔文件名与后缀
            file_name = name + str(int(time.time())) + '.' + suffix
        else:
            file_name_list.append(file_name)  # 将保存的文件名追加的列表,最后返回
            with open("%s/%s" % (uploads_folder, file_name), 'wb') as store_file:
                for bin_data in data.chunks():
                    store_file.write(bin_data)
    return file_name_list


@login_required
def dashboard(request):
    return render(request, 'chat/webchat.html')


def send_msg(request):
    retstatus = {
        "result": [],
        "retcode": 0
    }
    file_list = request.FILES.getlist('uploadfile')  # 获取上传文件对input标签属性name为uploadfile的值,也就是文件列表
    file_name_list = receive_file(file_list)  # 如果存在文件,则返回文件列表,并保存文件,否则为空列表

    if request.method == 'POST':
        user = request.user.userprofile.id  # 获取发消息的用户
        data = request.POST.get('data')  # 获取消息主体
        if file_name_list:
            data = request.POST
            friend_id = data.get('friendid')
            data.pop('csrfmiddlewaretoken')
            data['message'] = file_name_list  # 定义消息为文件列表
            data['file'] = True  # 标识消息类型
        else:  # 否则尝试解析json数据格式
            try:
                data = json.loads(data)
                friend_id = data.get('friendid')  # 获取收信人
            except TypeError:
                friend_id = None
                retstatus['retcode'] = 10003  # 消息格式不正确
        if friend_id:  # 只有获取到有效的收信人ID,才对消息进行处理
            try:
                if data.get('friendtype') == 'group':
                    data['groupid'] = friend_id
                    data['friendid'] = user
                    group = request.user.userprofile.group_members.select_related().filter(id=friend_id).first()
                    members = group.members.select_related()  # 获取组成员
                    for member in members:
                        if member.id not in MSG_QUEUE:
                            MSG_QUEUE[member.id] = queue.Queue()
                        if member.id is user:
                            continue
                        MSG_QUEUE[member.id].put(data)
                else:
                    friend_id = int(friend_id)
                    data['friendid'] = user  # 把收信人改为自己,方便对方回复
                    if friend_id not in MSG_QUEUE:  # 如果用户不存在消息队列,则创建对列
                        MSG_QUEUE[friend_id] = queue.Queue()
                    MSG_QUEUE[friend_id].put(data)
            except (AttributeError or ValueError):
                retstatus['retcode'] = 10001  # group id不存在
                retstatus['result'] = 'error message !!!'
    return HttpResponse(json.dumps(retstatus))


def get_msg(request):
    """获取消息"""
    retstatus = {
        "result": [],
        "retcode": 0
    }
    user = request.user.userprofile.id
    if user not in MSG_QUEUE:
        MSG_QUEUE[user] = queue.Queue()
    msg_queue = MSG_QUEUE.get(user)
    if msg_queue.qsize() > 0:
        for msg in range(msg_queue.qsize()):
            retstatus['result'].append(msg_queue.get())
    else:
        try:
            retstatus['result'].append(msg_queue.get(timeout=25))
        except queue.Empty:
            retstatus['retcode'] = 10002  # 目前没有人向用户发送消息
    print(retstatus)
    return HttpResponse(json.dumps(retstatus))



