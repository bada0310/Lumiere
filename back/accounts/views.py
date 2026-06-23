from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.mail import send_mail
from django.db import transaction
from django.utils.crypto import get_random_string
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CurrentUserSerializer, UserSerializer


class SignupView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': '회원가입이 완료되었습니다.'}, status=status.HTTP_201_CREATED)


class SessionLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response({'error': '아이디 또는 비밀번호가 틀렸습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        return Response({'message': f'{user.username}님, 세션 로그인 성공!'})


class SessionLogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logout(request)
        return Response({'message': '로그아웃 되었습니다.'})


class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        return delete_current_user(request)


class CurrentUserUpdateView(generics.UpdateAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['patch']

    def get_object(self):
        return self.request.user


class CurrentUserDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        return delete_current_user(request)


def delete_current_user(request):
    confirmation = request.data.get('confirmation', '')
    password = request.data.get('password', '')

    if confirmation != '탈퇴합니다':
        return Response(
            {'confirmation': '회원탈퇴 확인 문구를 정확히 입력해주세요.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    if user.has_usable_password() and not user.check_password(password):
        return Response(
            {'password': '비밀번호가 일치하지 않습니다.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_id = user.pk
    with transaction.atomic():
        get_user_model().objects.filter(pk=user_id).delete()

    return Response({'message': '회원탈퇴가 완료되었습니다.'}, status=status.HTTP_200_OK)


class CheckUsernameView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        if not username:
            return Response({'error': '아이디를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return Response({'is_available': False, 'message': '이미 사용 중인 아이디입니다.'})
        return Response({'is_available': True, 'message': '사용 가능한 아이디입니다.'})


class CheckNicknameView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        nickname = request.data.get('nickname', '').strip()
        if not nickname:
            return Response(
                {'is_available': False, 'message': '닉네임을 입력해주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        exists = User.objects.exclude(pk=request.user.pk).filter(nickname=nickname).exists()
        if exists:
            return Response({'is_available': False, 'message': '이미 사용 중인 닉네임입니다.'})
        return Response({'is_available': True, 'message': '사용 가능한 닉네임입니다.'})


class FindPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'error': '이메일을 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': '가입되지 않은 이메일입니다.'}, status=status.HTTP_404_NOT_FOUND)

        temp_password = get_random_string(length=8)
        user.set_password(temp_password)
        user.save()

        try:
            send_mail(
                '[Lumiere] 임시 비밀번호 발급 안내',
                (
                    f'안녕하세요, {user.nickname}님.\n\n'
                    f'요청하신 임시 비밀번호는 다음과 같습니다.\n\n'
                    f'임시 비밀번호: {temp_password}\n\n'
                    '로그인 후 마이페이지에서 비밀번호를 변경해주세요.'
                ),
                'noreply@lumiere.local',
                [user.email],
                fail_silently=False,
            )
        except Exception as exc:
            print('메일 발송 오류:', exc)
            return Response({'error': '메일 발송 중 서버 오류가 발생했습니다.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': '임시 비밀번호가 이메일로 발송되었습니다.'})
