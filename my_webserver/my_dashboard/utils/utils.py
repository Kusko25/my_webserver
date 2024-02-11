def process_show_name(show_name):
    processed_show_name = ""
    show_name = show_name.strip()
    # Cast to title case but preserve uppercase letters
    for i,c in enumerate(show_name.title()):
        if show_name[i].isupper():
            processed_show_name += show_name[i]
        else:
            processed_show_name += c

    return processed_show_name