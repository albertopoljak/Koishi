from gh_md_to_html.core_converter import markdown as generate_markdown
from os.path import join as join_paths, isfile as is_file, split as split_path
from os import listdir as list_directory
import hata

TOPICS_FOLDER = join_paths(split_path(split_path(hata.__file__)[0])[0], 'docs', 'topics')
TOPICS_ASSETS_FOLDER = join_paths(TOPICS_FOLDER, 'assets')

MARKDOWN_CACHE = {}

def get_markdown(name):
    try:
        item = MARKDOWN_CACHE[name]
    except KeyError:
        return None
    
    is_path, value, title = item
    if is_path:
        value = create_markdown(value)
        MARKDOWN_CACHE[name] = (False, value, title)
    
    return value, title


def create_markdown(path):
    with open(path, 'r') as file:
        content = file.read()
        markdown = generate_markdown(content)
    
    return markdown


def markdown_name_to_title(name):
    return name[:-3].replace('_', ' ').capitalize()


def find_markdowns():
    for name in list_directory(TOPICS_FOLDER):
        
        case_fold_name = name.casefold()
        if not name.endswith('.md'):
            continue
        
        if ('readme' in case_fold_name) or ('wip' in case_fold_name) or ('deprecated' in case_fold_name):
            continue
        
        file_path = join_paths(TOPICS_FOLDER, name)
        if not is_file(file_path):
            continue
        
        MARKDOWN_CACHE[name[:-3]] = (True, file_path, markdown_name_to_title(name))


find_markdowns()
