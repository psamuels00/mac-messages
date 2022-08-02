from .config import search_all_identifier


def search_all(search):
    return search is None or search == search_all_identifier
