return function(user, stats)
    return {
        user = user,
        stats = {
            messages = 0,
            completed_tasks = 0,
            active_tasks = 0,
        },
        is_admin = user.is_admin
    }
end