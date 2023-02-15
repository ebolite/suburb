item_actions = {}

class ItemAction():
    def __init__(self, name):
        self.targeted = False
        self.prompt = ""
        self.error_prompt = ""
        item_actions[name] = self

add_card = ItemAction("add_card")

combine_card = ItemAction("combine_card")
combine_card.targeted = True
combine_card.prompt = "Combine with what?"

uncombine_card = ItemAction("uncombine_card")

insert_card = ItemAction("insert_card")
insert_card.targeted = True
insert_card.prompt = "Insert what into the punch designix?"

remove_card = ItemAction("remove_card")

punch_card = ItemAction("punch_card")
punch_card.targeted = True
punch_card.prompt = "What items code should be punched into the designix?"

#todo: add support for custom punch