from math import ceil, floor
import json

with open("texted_image/characters_sizes.json") as f:
    chars_sizes: dict[str, dict[str, int | str]] = json.load(f)

DISTANCE_BETWEEN_LINES = 117

def get_lined_text(text: str, canvas_size: dict[str, int]):
    canvas_w, canvas_h = canvas_size['width'] * 0.9, canvas_size['height'] * 0.9
    lines, font_size = __get_lines(text, canvas_w, canvas_h)
    lines = __restore_lines_transitions(text, lines) 
    
    return '\n'.join(lines), font_size

        
def __get_words_lengths(words: list):
    return [sum([chars_sizes[character]['width'] for character in word if character in chars_sizes]) for word in words]


def __get_text_length(text: str):
    return sum([chars_sizes[c]['width'] for c in text if c in chars_sizes])


def __get_lines_data(text_length: int, canvas_w: int, canvas_h: int, transitions: int):
    font_size = 100
    ratio: float = text_length / canvas_w
    lines_amount = ceil(ratio) + transitions
    max_lines_amount = floor(canvas_h / DISTANCE_BETWEEN_LINES)
    multiplier = 1
    while lines_amount > max_lines_amount:
        multiplier -= .01
        font_size -= 1
        lines_amount = ceil(ratio * multiplier)
        max_lines_amount = floor(canvas_h / (DISTANCE_BETWEEN_LINES * multiplier))
    
    return font_size, lines_amount, multiplier
    
def __get_words(text: str):
    words = text.split(' ')
    if len(words) == 1:
        words = text
    return words, __get_words_lengths(words)

def __get_lines(text: str, width: int, height: int):
    transitions = text.count('\n\n')
    text = text.replace('\n', '')
    text_length = __get_text_length(text)
    font_size, lines_amount, multiplier = __get_lines_data(text_length, width, height, transitions)
    words, words_lengths = __get_words(text)
    
    lines = []
    offset = 0  
    j = 0
    text_width = width / multiplier
    for _ in range(lines_amount):
        s = 0
        sum_without_space = s - chars_sizes[' ']['width']
        while sum_without_space < text_width:
            if j == len(words_lengths):
                break
            s += words_lengths[j] + chars_sizes[' ']['width']
            j += 1
            sum_without_space = s - chars_sizes[' ']['width']
        j -= 1 if j == len(words_lengths) - 1 or sum_without_space > text_width else 0
        line = ' '.join(words[offset:j]) if isinstance(words, list) else words[offset:j]
        lines.append(line)    
        offset = j
    
    while '' in lines: lines.remove('')
    return lines, font_size


def __restore_lines_transitions(text: str, lines: list[str]):
    output = []
    for line in lines:
        inds = (line.find('Негативный'), line.find('Стиль:'))
        if inds[0] == -1 and inds[1] == -1:
            output.append(line)
            continue
        for ind in inds:
            if ind != -1:
                output.append(line[:ind] + '\n\n' + line[ind:])
            
            
    return output
