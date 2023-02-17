from typing import Optional

item_actions = {}

class ItemAction():
    def __init__(self, name):
        self.targeted = False
        self.prompt = ""
        self.error_prompt = ""
        self.use_prompt = ""
        item_actions[name] = self
    
    def prompt_message(self, item_name):
        return self.prompt.format(iname=item_name)

    def error_message(self, item_name, target_name: Optional[str]=None):
        return self.error_prompt.format(iname=item_name, tname=target_name)
    
    def use_message(self, item_name, target_name: Optional[str]=None):
        return self.use_prompt.format(iname=item_name, tname=target_name)


add_card = ItemAction("add_card")
add_card.error_prompt = "You are at the maximum amount of empty cards."
add_card.use_prompt = "You add the {iname} to your sylladex."

combine_card = ItemAction("combine_card")
combine_card.targeted = True
combine_card.prompt = "Combine {iname} with what (&&)?"
combine_card.error_prompt = ""
combine_card.use_prompt = "You combine {iname} with {tname}."

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

cruxtrude = ItemAction("cruxtrude")

insert_dowel = ItemAction("insert_dowel")
insert_dowel.targeted = True
insert_dowel.prompt = "Insert what into the {}?"
insert_dowel.error_prompt = "There's already a dowel inserted."

remove_dowel = ItemAction("remove_dowel")
remove_dowel.error_prompt = "No dowel is inserted."

lathe = ItemAction("lathe")
lathe.targeted = True
lathe.prompt = "Which punched card should you lathe?"
lathe.error_prompt = "No dowel is inserted."