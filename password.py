def checklength(password):
    if len(password) > 7:
        return False
    return True

def checkletter(password):
    for item in password:
        if item.isupper():
            return False
    return True

def checknumber(password):
    for item in password:
        if item.isdigit():
            return False
    return True


