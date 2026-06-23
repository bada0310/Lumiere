from django.db import transaction

from diagnosis.models import DiagnosisResult


def diagnosis_queryset_for_user(user, queryset=None):
    source = queryset if queryset is not None else DiagnosisResult.objects
    return source.filter(user=user)


def get_primary_diagnosis_for_user(user, queryset=None):
    if not user or not user.is_authenticated:
        return None

    user_queryset = diagnosis_queryset_for_user(user, queryset)
    return user_queryset.filter(is_primary=True).order_by('-created_at', '-id').first()


def user_has_primary_diagnosis(user):
    return DiagnosisResult.objects.filter(user=user, is_primary=True).exists()


@transaction.atomic
def set_primary_diagnosis(diagnosis):
    list(DiagnosisResult.objects.select_for_update().filter(user=diagnosis.user).only('id'))
    DiagnosisResult.objects.filter(user=diagnosis.user).update(is_primary=False)
    diagnosis.is_primary = True
    diagnosis.save(update_fields=['is_primary'])
    return diagnosis


@transaction.atomic
def unset_primary_diagnosis(diagnosis):
    list(DiagnosisResult.objects.select_for_update().filter(user=diagnosis.user).only('id'))
    if diagnosis.is_primary:
        diagnosis.is_primary = False
        diagnosis.save(update_fields=['is_primary'])
    return diagnosis


@transaction.atomic
def delete_diagnosis_without_reassign(diagnosis):
    user = diagnosis.user
    deleted_id = diagnosis.pk
    was_primary = diagnosis.is_primary

    list(DiagnosisResult.objects.select_for_update().filter(user=user).only('id'))
    diagnosis.delete()

    return deleted_id, was_primary, None
