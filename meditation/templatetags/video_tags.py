from django import template
import re

register = template.Library()

@register.filter
def get_youtube_id(url):
    """Extract the YouTube video ID from a URL"""
    if not url:
        return ""
    # Regular expression to extract YouTube video ID
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    if match:
        return match.group(1)
    return ""