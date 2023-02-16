item_actions = {}

class ItemAction():
    def __init__(self, name):
        self.targeted = False
        self.prompt = ""
        self.error_prompt = ""
        item_actions[name] = self
    
    def prompt_message(self, item_name):
        return self.prompt.format(item_name)

    def error_message(self, item_name):
        return self.error_prompt.format(item_name)


add_card = ItemAction("add_card")
add_card.error_prompt = "You are at the maximum amount of empty cards."

combine_card = ItemAction("combine_card")
combine_card.targeted = True
combine_card.prompt = "Combine {} with what (&&)?"
combine_card.error_prompt = ""

uncombine_card = ItemAction("uncombine_card")
uncombine_card.error_prompt = "This card is not combined."

insert_card = ItemAction("insert_card")
insert_card.targeted = True
insert_card.prompt = "Insert what into the {}?"
insert_card.error_prompt = "Something is already inserted."

remove_card = ItemAction("remove_card")
remove_card.prompt = "There's nothing to remove!"

punch_card = ItemAction("punch_card")
punch_card.targeted = True
punch_card.prompt = "Which item's code should be punched?"
punch_card.error_prompt = "No card is inserted."

#todo: add support for custom punch