def extract_identity(update) -> dict:
    user = update.effective_user
    chat = update.effective_chat
    return {
        "user_id": user.id if user else None,
        "chat_id": chat.id if chat else None,
    }
