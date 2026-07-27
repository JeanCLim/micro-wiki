from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, login_type=None, **kwargs):
        UserModel = get_user_model()
        
        company_id = request.session.get('company_id') if request else None

        # Intercepta acesso via alias para superadmins locais da empresa.
        if username == 'superadmin' and company_id:
            real_username = f"superadmin_company_{company_id}"
            try:
                user = UserModel.objects.get(username=real_username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except UserModel.DoesNotExist:
                pass
                
        if login_type == 'employee_code':
            try:
                user = UserModel.objects.get(employee_code=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except UserModel.DoesNotExist:
                return None
        else:
            # Executa a autenticação via endereço de e-mail.
            try:
                user = UserModel.objects.get(email=username)
                if user.check_password(password) and self.user_can_authenticate(user):
                    return user
            except UserModel.DoesNotExist:
                return None
        
        return None
