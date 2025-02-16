total_profile_amout = 350
profile_index = 0
my_str = 'Кашапов Салават(55), Кашапов Салават(0), Кашапов Салават(55), Кашапов Салават'
arr_str = my_str.split(', ')
for value in arr_str:
  start_i = value.find('(')
  end_i = value.find(')')
  try:
    int_data = int(value[start_i + 1:end_i])
    profile_index = profile_index + int_data
    print(f'{value[0:start_i]} изготовил {int_data} ед. профиля')
  except Exception as e:
    int_data = total_profile_amout - profile_index
    print(f'{value[0:start_i]} изготовил {int_data} ед. профиля')
   
    