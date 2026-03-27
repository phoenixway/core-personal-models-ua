---
up:
  - "[[failure-patterns]]"
---
PATTERN:
GO → OPS без проміжних рівнів

SYMPTOMS:
- задачі не пов’язані зі стратегією
- “зайнятий, але не рухаюсь”
- важко пояснити навіщо це робиться

ROOT CAUSE:
відсутність KF/SO/STR

DETECTED BY:
X-V1 No Level Skipping
OPS-V1 Traceability

FIX:
1. взяти задачу
2. підняти:
   task → mission → SO → KF → GO
3. якщо зв’язку нема → task видалити або створити KF/SO

PREVENTION:
ніколи не створювати задачі напряму