from django.db import models
from bbs.models import UserProfile
# Create your models here.


class WebGroup(models.Model):

    name = models.CharField(max_length=64)
    brief = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(UserProfile)
    admins = models.ManyToManyField(UserProfile, blank=True, related_name='group_admins')
    members = models.ManyToManyField(UserProfile, blank=True, related_name='group_members')
    max_members = models.IntegerField(default=200)
    head_img = models.ImageField(
        blank=True, null=True, verbose_name=u'头像', upload_to='uploads')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = u'群友关系'
        verbose_name_plural = u'群友关系'
