def is_admin(user):
    return user.get("role") == "admin"

def is_manager(user):
    return user.get("role") == "manager"

def is_agent(user):
    return user.get("role") == "agent"
