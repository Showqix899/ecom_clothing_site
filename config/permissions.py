
def is_user_admin(user):
    
    if user['role'] == 'admin':
        return True
    return False
def is_user_moderator(user):
    
    if user['role'] == 'moderator':
        return True
    return False