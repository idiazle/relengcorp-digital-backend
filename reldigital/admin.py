from django.contrib import admin
from reldigital.models import User, Entity, Report, Notice

class UserAdmin(admin.ModelAdmin):
    pass
class EntityAdmin(admin.ModelAdmin):
    pass
class ReportAdmin(admin.ModelAdmin):
    pass
class NoticeAdmin(admin.ModelAdmin):
    pass

admin.site.register(User, UserAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Notice, NoticeAdmin)



# Register your models here.
