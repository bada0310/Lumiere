from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.core.files.base import ContentFile


MIN_IMAGE_SIDE = 480
MIN_BLUR_VARIANCE = 60.0
MIN_BRIGHTNESS = 45
MAX_BRIGHTNESS = 230


@dataclass
class ImageQualityResult:
    ok: bool
    code: str = ''
    message: str = ''
    processed_image: ContentFile | None = None
    processed_filename: str = ''
    metrics: dict = field(default_factory=dict)


def validate_and_prepare_image(uploaded_file):
    from PIL import Image, ImageStat

    try:
        image = Image.open(uploaded_file)
        image.load()
    except Exception:
        return ImageQualityResult(False, 'invalid_image', '이미지 파일을 열 수 없습니다.')

    image = image.convert('RGB')
    width, height = image.size
    if min(width, height) < MIN_IMAGE_SIDE:
        return ImageQualityResult(
            False,
            'low_resolution',
            f'이미지 해상도가 너무 낮습니다. 최소 {MIN_IMAGE_SIDE}px 이상의 얼굴 사진을 사용해 주세요.',
            metrics={'width': width, 'height': height},
        )

    brightness = ImageStat.Stat(image.convert('L')).mean[0]
    if brightness < MIN_BRIGHTNESS:
        return ImageQualityResult(False, 'too_dark', '이미지가 너무 어둡습니다. 밝은 자연광에서 다시 촬영해 주세요.', metrics={'brightness': brightness})
    if brightness > MAX_BRIGHTNESS:
        return ImageQualityResult(False, 'too_bright', '이미지가 너무 밝습니다. 과한 조명을 피해서 다시 촬영해 주세요.', metrics={'brightness': brightness})

    cv2 = _load_cv2()
    if cv2 is None:
        return ImageQualityResult(False, 'face_detection_unavailable', '얼굴 감지 모듈을 사용할 수 없습니다.')

    gray = _pil_to_gray_array(image, cv2)
    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_variance < MIN_BLUR_VARIANCE:
        return ImageQualityResult(False, 'blurry', '이미지가 너무 흐릿합니다. 흔들림 없이 다시 촬영해 주세요.', metrics={'blur': blur_variance})

    faces = _detect_faces(gray, cv2)
    if not faces:
        return ImageQualityResult(False, 'no_face', '얼굴이 감지되지 않았습니다. 정면 얼굴 사진을 업로드해 주세요.')
    if len(faces) > 1:
        return ImageQualityResult(False, 'multiple_faces', '한 명의 얼굴만 포함된 사진을 업로드해 주세요.', metrics={'faceCount': len(faces)})

    processed = _crop_face(image, faces[0])
    content = _image_to_content_file(processed)
    return ImageQualityResult(
        True,
        processed_image=content,
        processed_filename=f'diagnosis-processed-{uuid4().hex}.jpg',
        metrics={
            'width': width,
            'height': height,
            'brightness': round(brightness, 2),
            'blur': round(blur_variance, 2),
            'faceCount': 1,
        },
    )


def _load_cv2():
    try:
        import cv2
    except ImportError:
        return None
    return cv2


def _pil_to_gray_array(image, cv2):
    import numpy as np

    rgb = np.array(image)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def _detect_faces(gray, cv2):
    cascade_path = Path(cv2.data.haarcascades) / 'haarcascade_frontalface_default.xml'
    classifier = cv2.CascadeClassifier(str(cascade_path))
    if classifier.empty():
        return []
    faces = classifier.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(120, 120))
    return sorted([tuple(map(int, face)) for face in faces], key=lambda face: face[2] * face[3], reverse=True)


def _crop_face(image, face):
    x, y, w, h = face
    pad_x = int(w * 0.55)
    pad_y_top = int(h * 0.65)
    pad_y_bottom = int(h * 0.45)
    left = max(0, x - pad_x)
    top = max(0, y - pad_y_top)
    right = min(image.width, x + w + pad_x)
    bottom = min(image.height, y + h + pad_y_bottom)
    return image.crop((left, top, right, bottom))


def _image_to_content_file(image):
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=92, optimize=True)
    return ContentFile(buffer.getvalue())
