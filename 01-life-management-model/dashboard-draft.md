---
up:
  - "[[01-life-management-model]]"
---
# 🗺 SYSTEM STATUS BOARD

## Як читати
- READY = рівень достатній для роботи нижче
- CONDITIONAL = можна рухатись, але є хвіст
- BLOCKED = вниз іти не можна
- OUTDATED = сам рівень колись був ок, але застарів після змін вище
- DEFECTED = є системний дефект, який б’є по рівню

---

## GLOBAL STATE
- CURRENT MODE:
- CURRENT ACTIVE LEVEL:
- MAIN BLOCKER:
- MAIN DEFECT:
- LAST REVIEW:
- NEXT REVIEW:

---

## LEVELS

| LEVEL | STATE | USABLE | TRANSFER DOWN | FRESHNESS | MAIN BLOCKER | NEXT ACTION |
|---|---|---:|---|---|---|---|
| Main Beacons | READY | yes | complete | fresh | - | monthly review |
| Realization Models | READY | yes | complete | fresh | - | - |
| Mandatory Core | CONDITIONAL | yes | partial | fresh | 2 beacons still rough | finalize MVR |
| Strategic Projecting | BLOCKED | no | none | outdated | core not frozen | sync after core |
| Long-term Strategy | CONDITIONAL | yes | partial | needs review | exclusions unclear | revise strategy lines |
| Medium-term Program | OUTDATED | yes | partial | outdated | parent changed | resync month |
| Week | OUTDATED | yes | complete | outdated | month changed | rebuild weekly focus |
| Day | OUTDATED | yes | complete | outdated | week changed | rebuild action units |

---

## STATUS LEGEND

### STATE
- READY
- CONDITIONAL
- BLOCKED
- DEFECTED

### USABLE
- yes
- conditional
- no

### TRANSFER DOWN
- none
- partial
- complete

### FRESHNESS
- fresh
- needs review
- outdated

---

## RULES

### READY
Рівень достатній якщо:
- дає результат
- використовується
- дозволяє виконувати
- зрозумілий наступний крок

### CONDITIONAL
Можна рухатись нижче, якщо:
- основне вже є
- хвости не блокують нижчий рівень
- є deadline доопрацювання

### BLOCKED
Не можна йти нижче, якщо:
- незрозуміло, що передавати вниз
- немає usable result
- рівень не пройшов done condition

### OUTDATED
Рівень був валідний раніше, але:
- вище щось змінилось
- нижчий рівень ще не синхронізовано

---

## FIRST INVALID / FIRST PROBLEM
Перший рівень, де відповідь “ні” або “неясно”:
- LEVEL:
- WHY:
- TYPE:
  - [ ] readiness issue
  - [ ] sync issue
  - [ ] defect issue

---

## TODAY’S REQUIRED SYSTEM MOVE
- 1.
- 2.
- 3.