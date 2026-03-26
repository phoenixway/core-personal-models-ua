## принципи
- Постійно на ходу тримати баланс в структурі доби. Як в їзді на велосипеді.
- різним типам дня - різні оптимальні моделі управління і жтд. Криза, тд
## algorithm 
- якщо є щось термінове і критичне
	-  робити негайно
- інакше - далі 
- пар 
- якщо треба - ранкове лікування 
## deprecated 

IF dayState == D0:
    SelectDailyFocus()
    dayState = D1

IF dayState == D1:
    ExecutePrimaryAction()
    dayState = D2

IF dayState == D2:
    RecordExecution()
    dayState = D3

IF dayState == D3:
    ResetForNextDay()
    dayState = D0

