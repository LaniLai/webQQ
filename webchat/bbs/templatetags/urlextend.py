#!/usr/bin/env python
# encoding:utf8

from django.template import Library
from django.utils.html import format_html
from collections import Counter
import datetime


register = Library()


@register.filter
def show_img(img_obj):
    print('15---', img_obj)
    if hasattr(img_obj, 'name'):
        return str(img_obj.name).split('/', maxsplit=1)[-1]
    else:
        return ''


@register.simple_tag
def resolve_comment(article_obj):
    reduce_list = article_obj.comment_set.select_related().all().values('comment_type')
    comment_types = list(Counter([str(list(new_dict.values())[0]) for new_dict in reduce_list]).items())
    return dict(comment_types)


# @register.simple_tag
# def show_comment(article_obj):
#     # print(article_obj.comment_set.select_related())
#     return


@register.filter
def diff_time(timedate):
    if type(timedate) is not datetime.datetime:
        return ''
    show_time = []
    current_datetime = datetime.datetime.now()
    diff_datetime = current_datetime - timedate.replace(tzinfo=None)
    total_seconds = diff_datetime.total_seconds()  # 将时间转换为秒数
    if total_seconds >= 86400:
        before_datetime = int(divmod(total_seconds, 86400)[0])
        show_time.append(u"%s天" % before_datetime)
        total_seconds -= 86400 * before_datetime
    if total_seconds >= 3600:
        before_datetime = int(divmod(total_seconds, 3600)[0])
        show_time.append(u"%s小时" % before_datetime)
        total_seconds -= 3600 * before_datetime
    if total_seconds >= 60:
        before_datetime = int(divmod(total_seconds, 60)[0])
        show_time.append(u"%s分钟" % before_datetime)
        total_seconds -= 60 * before_datetime
    if not show_time:
        show_time.append(u'%s秒' % int(total_seconds))
    show_time = u"%s前" % ''.join(show_time[:2])
    return show_time


@register.simple_tag
def paginator(model_data, per_page=4):
    """
    model_data: 含有paginator的数据对象
    per_page: 每次显示最长页码
    """
    page_elem = ""  # 中间页面元素
    page_pre_elem = """
        <li class="%s">
            <a href="?page=%s" aria-label="Previous">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
    """  # 上一页按钮
    page_next_elem = """
        <li class="%s">
            <a href="?page=%s" aria-label="Previous">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
    """  # 下一页按钮
    for page_num in model_data.paginator.page_range:
        offset = abs(model_data.number - page_num)
        if offset < per_page:
            if model_data.number == page_num:
                page_elem += "<li class='active'><a href='?page=%s'>%s</a></li>" % (page_num, page_num)
            else:
                page_elem += "<li><a href='?page=%s'>%s</a></li>" % (page_num, page_num)

    if model_data.has_previous():
        page_pre_elem = page_pre_elem % ("", model_data.previous_page_number())
    else:
        page_pre_elem = ""

    if model_data.has_next():
        page_next_elem = page_next_elem % ("", model_data.next_page_number())
    else:
        page_next_elem = ""

    page_html = """
        <nav>
            <ul class="pagination">
                %s
                %s
                %s
            </ul>
        </nav>
    """ % (page_pre_elem, page_elem, page_next_elem)
    return format_html(page_html)  # 返回分页html元素