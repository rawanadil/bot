def unread_notifications(request):
    """عدد الإشعارات غير المقروءة، يظهر بالشريط العلوي بكل الصفحات."""
    if request.user.is_authenticated:
        return {"unread_count": request.user.notifications.filter(is_read=False).count()}
    return {}
