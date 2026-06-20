from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from rest_framework import status
from .serializers import UserSerializer

from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model

from django.core.mail import send_mail
from django.utils.crypto import get_random_string
# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info_view(request):
    return Response({
        "username": request.user.username, # ★ 이 줄 추가!
        "nickname": request.user.nickname,
        "email": request.user.email
    })

@api_view(['POST'])
def session_login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    # DB에 해당 유저가 있는지 확인
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)  # 이 코드가 실행되면 서버가 응답 헤더에 Set-Cookie를 담아 보냅니다.
        return Response({"message": f"{user.username}님, 세션 로그인 성공!"})
    return Response({"error": "아이디 또는 비밀번호가 틀렸습니다."}, status=400)

@api_view(['POST'])
def session_logout_view(request):
    logout(request) # 서버에서 세션을 파기하고 쿠키를 삭제합니다.
    return Response({"message": "로그아웃 되었습니다."})

@api_view(['POST'])
def signup_view(request):
    # 1. 프론트엔드에서 온 데이터(request.data)를 Serializer에 넣습니다.
    serializer = UserSerializer(data=request.data)
    
    # 2. 데이터가 유효한지 검사합니다. (아이디 중복 여부 등)
    if serializer.is_valid(raise_exception=True):
        serializer.save() # 3. DB에 유저 저장
        return Response({"message": "회원가입이 완료되었습니다!"}, status=status.HTTP_201_CREATED)
    
@api_view(['POST'])
@permission_classes([AllowAny]) # 회원가입 전이므로 누구나 찔러볼 수 있게 허용!
def check_username_view(request):
    username = request.data.get('username', '').strip()
    
    if not username:
        return Response({"error": "아이디를 입력해주세요."}, status=400)

    User = get_user_model()
    # 입력받은 아이디가 DB에 이미 존재하는지 검사합니다.
    if User.objects.filter(username=username).exists():
        return Response({"is_available": False, "message": "이미 사용 중인 아이디입니다."})
    else:
        return Response({"is_available": True, "message": "사용 가능한 아이디입니다."})
    

@api_view(['POST'])
@permission_classes([AllowAny]) # 로그인 전이므로 누구나 접근 가능해야 함
def find_password_view(request):
    # 1. 프론트엔드에서 보낸 이메일 꺼내기 (앞뒤 공백 제거)
    email = request.data.get('email', '').strip()

    if not email:
        return Response({"error": "이메일을 입력해주세요."}, status=400)

    User = get_user_model()
    try:
        # 2. 해당 이메일로 가입한 유저 찾기
        user = User.objects.get(email=email)

        # 3. 8자리의 랜덤한 임시 비밀번호 생성 (예: 'x9A2kLp1')
        temp_password = get_random_string(length=8)

        # 4. ★ 가장 중요한 보안 로직: 비밀번호 단방향 암호화(해싱) 후 저장
        user.set_password(temp_password) 
        user.save()

        # 5. 유저의 메일로 편지 발송
        subject = '[Lumiere] 임시 비밀번호 발급 안내'
        message = f'안녕하세요, {user.nickname}님.\n\n요청하신 임시 비밀번호는 다음과 같습니다.\n\n임시 비밀번호: {temp_password}\n\n로그인 후 반드시 마이페이지에서 비밀번호를 변경해 주세요.'
        
        # settings.py에 적었던 내 구글 이메일을 발신자로 설정
        from_email = '수빈님의구글이메일@gmail.com' 
        
        # send_mail(제목, 내용, 발신자, [수신자 리스트])
        send_mail(subject, message, from_email, [user.email], fail_silently=False)

        return Response({"message": "임시 비밀번호가 이메일로 발송되었습니다."})

    except User.DoesNotExist:
        return Response({"error": "가입되지 않은 이메일입니다."}, status=404)
    except Exception as e:
        print("메일 발송 에러 상세:", e)
        return Response({"error": "메일 발송 중 서버 오류가 발생했습니다."}, status=500)