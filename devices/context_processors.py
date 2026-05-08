from django.utils.translation import get_language


def active_language(request):
    """Expose the currently active language code to all templates."""
    lang = get_language() or 'en'
    # Normalize: 'en-us' -> 'en', 'ru' -> 'ru', 'uz' -> 'uz'
    return {
        'ACTIVE_LANG': lang.split('-')[0].lower(),
    }