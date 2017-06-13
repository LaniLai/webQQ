from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from bbs import models
from django.db.models import Count, Sum
from functools import reduce
from collections import Counter, defaultdict
from django.core.exceptions import ObjectDoesNotExist
import json
from bbs import forms
from bbs import comment_handler
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Create your views here.
category_list = models.Category.objects.filter(set_as_top_menu=True).order_by('position_index')


def account_login(request):
    context = dict()
    if request.method == 'POST':
        user = authenticate(username=request.POST.get('username'),
                            password=request.POST.get('password'),
                            )
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect(request.GET.get('next') or '/bbs')
            else:
                context['login_err'] = '该账号被禁用'
        else:
            context['login_err'] = '用户名或密码错误'
    context['category_list'] = category_list
    return render(request, 'accounts/pages-login.html', context)


def account_logout(request):
    logout(request)
    return redirect(request.GET.get('next') or '/bbs')


def set_paginator(request, model_data):
    """为数据设置分页"""
    max_record = request.GET.get('max_record')  # 获取每页显示多少条数据
    try:
        if max_record:
            max_num = int(max_record)
        else:
            max_num = 3  # 默认显示10条数据
    except ValueError:
        max_num = 3
    paginator = Paginator(model_data, max_num)
    page = request.GET.get('page')
    try:
        model_data = paginator.page(page)  # 获取第几页数据
    except PageNotAnInteger:
        model_data = paginator.page(1)  # 默认显示第一页数据
    except EmptyPage:
        model_data = paginator.page(paginator.num_pages)  # 如果获取的分页数据不存在,则显示最后一页数据
    return model_data


def index(request):
    context = dict()
    try:
        category_obj = models.Category.objects.get(position_index=1)
        context['category_obj'] = category_obj
    except ObjectDoesNotExist:
        pass
    article_list = models.Article.objects.filter(status='published').order_by('-pub_date')
    context['category_list'] = category_list

    article_list = set_paginator(request, article_list)
    context['article_list'] = article_list
    return render(request, 'bbs/index.html', context)


def category(request, category_id):
    context = dict()
    try:
        category_obj = models.Category.objects.get(position_index=category_id)
        if category_obj.position_index == 1:
            article_list = models.Article.objects.filter(status='published').order_by('-pub_date')
        else:
            article_list = models.Article.objects.filter(status='published', category_id=category_obj.id).order_by('-pub_date')

        article_list = set_paginator(request, article_list)
        context['category_obj'] = category_obj
        context['article_list'] = article_list
        context['category_list'] = category_list
    except ObjectDoesNotExist:
        pass
    return render(request, 'bbs/index.html', context)


def article_detail(request, article_id):
    context = dict()
    context['category_list'] = category_list
    article_obj = models.Article.objects.get(id=article_id)
    # comment_tree = comment_handler.build_tree(article_obj.comment_set.select_related(),
    #                                           )
    context['article_obj'] = article_obj
    return render(request, 'bbs/article_detail.html', context)


def comment(request):
    """发表评论
    """
    ret = {'status': True, 'comment': ''}
    print(request.POST)
    if request.method == 'POST':
        comment_type = request.POST.get('comment_type')
        article_id = request.POST.get('article_id')
        try:
            comment_type_set = None
            if str(comment_type) == '2':
                comment_type_set = models.Comment.objects.filter(
                    user_id=request.user.userprofile.id,
                    comment_type=comment_type,
                    article_id=article_id,
                )
            if comment_type_set:
                models.Comment.objects.filter(
                    user_id=request.user.userprofile.id,
                    comment_type=comment_type,
                    article_id=article_id
                ).first().delete()
                ret['count'] = -1
            else:
                new_comment = models.Comment(
                    article_id=article_id,
                    parent_comment_id=request.POST.get('parent_id' or None),
                    comment_type=comment_type,
                    user_id=request.user.userprofile.id,
                    comment=request.POST.get('comment'),
                )
                new_comment.save()
                ret['comment'] = request.POST.get('comment')
                ret['count'] = 1
        except Exception as e:
            ret['status'] = False
            ret['comment'] = e

    return HttpResponse(json.dumps(ret))


def get_comments(request, article_id):
    """获取评论"""
    article_obj = models.Article.objects.get(id=article_id)
    comment_tree = comment_handler.build_tree(article_obj.comment_set.select_related().order_by('parent_comment', '-id'))
    tree_html = comment_handler.render_commnet_tree(comment_tree)
    return HttpResponse(tree_html)


def publish(request):
    """发布文章"""
    context = {}
    instance = None  # 初始化实例属性为空
    form_data = forms.ArticleForm(instance=instance)  # 尝试获取model form对象
    if request.method == 'POST':
        form_data = forms.ArticleForm(request.POST, request.FILES)  # 如果是POST请求,则进行校验数据
        if form_data.is_valid():
            article_data = form_data.cleaned_data
            article_data['author_id'] = request.POST.get('author')
            models.Article.objects.create(**article_data)
            return redirect('/bbs')
        else:
            error_message = "添加失败"
            if instance:
                error_message = "修改失败"
            context["error_message"] = error_message
    context["model_form"] = form_data  # 返回model form 对象
    return render(request, 'bbs/pub_article.html', context)
