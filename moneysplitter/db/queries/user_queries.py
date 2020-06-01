from ..models import User, UserSettings


def exists(session, user_id):
    user_query = session.query(User).filter(User.id == user_id)
    user_count = user_query.count() > 0
    return user_count


def register(session, telegram_user):
    user = User(telegram_user.id, telegram_user.username, telegram_user.first_name, telegram_user.last_name)
    session.add(user)
    session.flush()
    session.add(UserSettings(telegram_user.id))
    session.commit()


def find(session, user_id):
    user = session.query(User).filter(User.id == user_id).one()
    return user


def refresh(session, telegram_user):
    user = session.query(User).filter(User.id == telegram_user.id).scalar()
    if user is None:
        return

    if user.username == telegram_user.username:
        return

    user.username = telegram_user.username
    session.commit()


def get_selected_checklist(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.selected_checklist


def select_checklist(session, checklist_id, user_id):
    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'checklist_id': checklist_id})
    session.commit()


def set_deleting_checklist(session, user_id, checklist_id):
    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'deleting_checklist_id': checklist_id})
    session.commit()


def get_deleting_checklist(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.deleting_checklist


def set_participant_delete(session, user_id, reset=False):
    if reset:
        checklist_id = None
    else:
        checklist_id = get_selected_checklist(session, user_id).id

    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'participant_delete_id': checklist_id})
    session.commit()


def get_participant_delete_id(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.participant_delete_id


def set_transaction_payoff(session, user_id, reset=False):
    if reset:
        checklist_id = None
    else:
        checklist_id = get_selected_checklist(session, user_id).id

    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'transaction_payoff_id': checklist_id})
    session.commit()


def get_transaction_payoff_id(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.transaction_payoff_id


def set_item_delete(session, user_id, reset=False):
    if reset:
        checklist_id = None
    else:
        checklist_id = get_selected_checklist(session, user_id).id

    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'item_delete_id': checklist_id})
    session.commit()


def get_item_delete_id(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.item_delete_id


def set_purchase_edit(session, operator_id, purchase_id=None):
    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == operator_id) \
        .update({'purchase_edit_id': purchase_id})
    session.commit()


def get_purchase_edit_id(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.purchase_edit_id


def set_purchase_distribution(session, operator_id, distribution_id=None):
    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == operator_id) \
        .update({'purchase_distribution_id': distribution_id})
    session.commit()


def get_purchase_distribution_id(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.purchase_distribution_id
