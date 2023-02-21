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
        try: return self.prompt.format(iname=item_name)
        except IndexError: return self.prompt

    def error_message(self, item_name, target_name: Optional[str]=None):
        try:
            if target_name is None: self.error_prompt.format(iname=item_name)
            return self.error_prompt.format(iname=item_name, tname=target_name)
        except IndexError: return self.error_prompt
    
    def use_message(self, item_name, target_name: Optional[str]=None):
        try:
            if target_name is None: self.use_prompt.format(iname=item_name)
            return self.use_prompt.format(iname=item_name, tname=target_name)
        except IndexError: return self.use_prompt


add_card = ItemAction("add_card")
add_card.error_prompt = "You are at the maximum amount of empty cards."
add_card.use_prompt = "You add the {iname} to your sylladex."

computer = ItemAction("computer")
computer.use_prompt = "You boot up the {iname}."

install_sburb = ItemAction("install_sburb")
install_sburb.targeted = True
install_sburb.prompt = "What should you install Sburb on?"
install_sburb.use_prompt = "You install Sburb onto the {tname}."

install_gristtorrent = ItemAction("install_gristtorrent")
install_gristtorrent.targeted = True
install_gristtorrent.prompt = "What should you install gristTorrent on?"
install_gristtorrent.use_prompt = "You install gristTorrent onto the {tname}."

combine_card = ItemAction("combine_card")
combine_card.targeted = True
combine_card.prompt = "Combine {iname} with what (&&)?"
combine_card.error_prompt = ""
combine_card.use_prompt = "You combine {iname} with {tname}."

uncombine_card = ItemAction("uncombine_card")
uncombine_card.error_prompt = "This card is not combined."
uncombine_card.use_prompt = "You uncombine the cards."

insert_card = ItemAction("insert_card")
insert_card.targeted = True
insert_card.prompt = "Insert what into the {iname}?"
insert_card.error_prompt = "Something is already inserted."
insert_card.use_prompt = "You insert the card for {tname}."

remove_card = ItemAction("remove_card")
remove_card.prompt = "There's nothing to remove!"
remove_card.use_prompt = "You remove the card inserted into the {iname}."

punch_card = ItemAction("punch_card")
punch_card.targeted = True
punch_card.prompt = "Which item's code should be punched?"
punch_card.error_prompt = "No card is inserted."
punch_card.use_prompt = "You punch the card with the code for {tname}."

#todo: add support for custom punch

cruxtrude = ItemAction("cruxtrude")
cruxtrude.use_prompt = "A cruxite dowel flies out of the {iname}!"

insert_dowel = ItemAction("insert_dowel")
insert_dowel.targeted = True
insert_dowel.prompt = "Insert what into the {iname}?"
insert_dowel.error_prompt = "There's already a dowel inserted."
insert_dowel.use_prompt = "You insert {tname} into the {iname}."

insert_carved_dowel = ItemAction("insert_carved_dowel")
insert_carved_dowel.targeted = True
insert_carved_dowel.prompt = "Insert what into the {iname}?"
insert_carved_dowel.error_prompt = "There's already a dowel inserted."
insert_carved_dowel.use_prompt = "You insert {tname} into the {iname}."

remove_dowel = ItemAction("remove_dowel")
remove_dowel.error_prompt = "No dowel is inserted."
remove_dowel.use_prompt = "You eject the dowel from the {iname}."

lathe = ItemAction("lathe")
lathe.targeted = True
lathe.prompt = "Which punched card should you lathe?"
lathe.error_prompt = "No dowel is inserted."
lathe.use_prompt = "The dowel ejects after you lathe it with the code for {tname}."