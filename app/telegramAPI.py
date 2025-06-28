import telebot;

class TelegramBot(): 
      
  bot = telebot.TeleBot('7582098919:AAGKT8xmgr0W9a7wq_JjbBlPXi7ni671i8c')  
  chat_id = '-1002783674704' 
  
  
  def send_text(self, text):
    self.bot.send_message(self.chat_id, text) 