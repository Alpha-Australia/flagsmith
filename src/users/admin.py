from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import FFAdminUser, Invite


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = FFAdminUser
    list_display = ['email', 'get_number_of_organisations']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'organisations',),
        })
    )

    fieldsets = UserAdmin.fieldsets + (
        (_('Organisations'), {'fields': ('organisations',)}),
        (_('Statistics'), {'fields': ('get_number_of_organisations',
                                      'get_number_of_projects',
                                      'get_number_of_features',
                                      'get_number_of_environments')})
    )

    readonly_fields = ['get_number_of_organisations',
                       'get_number_of_projects',
                       'get_number_of_features',
                       'get_number_of_environments']

    def get_number_of_organisations(self, obj):
        return obj.get_number_of_organisations()
    get_number_of_organisations.short_description = "Number of Organisations"

    def get_number_of_projects(self, obj):
        return obj.get_number_of_projects()
    get_number_of_projects.short_description = "Number of Projects"

    def get_number_of_features(self, obj):
        return obj.get_number_of_features()
    get_number_of_features.short_description = "Number of Features"

    def get_number_of_environments(self, obj):
        return obj.get_number_of_environments()
    get_number_of_environments.short_description = "Number of Environments"


admin.site.register(FFAdminUser, CustomUserAdmin)
admin.site.register(Invite)
