-- contexts/profile.lua
return function(params)
    local user = params.user or {}
    local stats = params.stats or {}
    
    -- Устанавливаем обязательные значения по умолчанию
    user.username = user.username or "Без имени"
    stats.messages = stats.messages or 0
    stats.completed_tasks = stats.completed_tasks or 0
    stats.active_tasks = stats.active_tasks or 0
    
    -- Логика уровней
    local level = 1
    local exp = stats.messages
    while exp >= level * 100 do
        exp = exp - level * 100
        level = level + 1
    end
    
    local progress = math.floor((exp / (level * 100)) * 100)
    
    -- Возвращаем гарантированно заполненный контекст
    return {
        user = user,
        stats = stats,
        level_info = {
            level = level,
            progress = progress,
            next_level = level + 1,
            exp = exp,
            required_exp = level * 100
        },
        is_admin = user.is_admin or false,
        is_premium = user.premium or false
    }
end