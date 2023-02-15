item_actions = {}

class ItemAction():
    def __init__(self, name):
        self.targeted = False
        item_actions[name] = self

add_card = ItemAction("add_card")

combine_card = ItemAction("combine_card")
combine_card.targeted = True

insert_card = ItemAction("insert_card")
insert_card.targeted = True

remove_card = ItemAction("remove_card")

punch_card = ItemAction("punch_card")
punch_card.targeted = True

#todo: add support for custom punch