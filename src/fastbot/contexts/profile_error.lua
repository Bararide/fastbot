return function(user, error_message)
    return {
        user = user,
        stats = {
            messages = 0,
            completed_tasks = 0,
            active_tasks = 0,
        },
        is_admin = user.is_admin,
        error_message = error_message
    }
end 