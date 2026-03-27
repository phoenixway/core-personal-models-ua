---
up:
  - "[[middle-term-strategy]]"
---

```dataviewjs
// Вкажіть назву вашої нотатки тут
const noteName = "middle-term-strategy"; // Замініть на точну назву вашої нотатки

const page = dv.page(noteName);

if (!page) {
    dv.paragraph(`**Помилка:** Нотатка "${noteName}" не знайдена.`);
} else {
    const backlogItems = [];
    let inBacklogSection = false;

    // Отримуємо вміст нотатки
    const content = await dv.io.load(page.file.path);
    const lines = content.split('\n');

    for (const line of lines) {
        // Перевіряємо, чи це підзаголовок, що містить "Backlog"
        if (line.match(/^#+\s.*Backlog/i)) {
            inBacklogSection = true;
            continue; // Переходимо до наступного рядка
        }

        // Якщо ми в секції "Backlog" і рядок є елементом списку
        if (inBacklogSection && line.trim().startsWith('- ')) {
            const taskText = line.substring(line.indexOf('- ') + 2).trim();

            // Витягуємо поля за допомогою регулярного виразу
            const parentValueMatch = taskText.match(/\[parent_value::\s*([\d.-]+)\]/);
            const impactMatch = taskText.match(/\[impact::\s*([\d.-]+)\]/);
            const costsMatch = taskText.match(/\[costs::\s*([\d.-]+)\]/);

            // --- ЗМІНА: Перевіряємо, чи всі три поля присутні ---
            if (parentValueMatch && impactMatch && costsMatch) {
                const parent_value_str = parentValueMatch[1];
                const impact_str = impactMatch[1];
                const costs_str = costsMatch[1];

                // Перетворюємо значення на числа
                const parent_value = parseFloat(parent_value_str);
                const impact = parseFloat(impact_str);
                const costs = parseFloat(costs_str);

                // --- ЗМІНА: Перевіряємо, чи всі значення є дійсними числами ---
                if (isNaN(parent_value) || isNaN(impact) || isNaN(costs)) {
                    // Якщо одне з полів не є числом, пропускаємо цей елемент
                    // dv.paragraph(`Пропущено: "${taskText}" - одне з полів не є числом.`); // Для дебагу
                    continue;
                }

                // Видаляємо поля з тексту завдання для чистого відображення
                let cleanTaskText = taskText
                    .replace(/\[parent_value::\s*[\d.-]+\]/, '')
                    .replace(/\[impact::\s*[\d.-]+\]/, '')
                    .replace(/\[costs::\s*[\d.-]+\]/, '')
                    .trim();

                // Обчислюємо goal_rating
                let goal_rating;
                if (costs === 0) {
                    // Обробка випадку, коли витрати дорівнюють нулю
                    if (parent_value * impact > 0) {
                        goal_rating = Infinity; // Дуже високий пріоритет, якщо є позитивна цінність/вплив
                    } else if (parent_value * impact < 0) {
                        goal_rating = -Infinity; // Дуже низький пріоритет
                    } else {
                        goal_rating = 0; // Якщо цінність/вплив також нульові
                    }
                } else {
                    goal_rating = (parent_value * impact) / costs;
                }

                backlogItems.push({
                    text: cleanTaskText,
                    parent_value: parent_value,
                    impact: impact,
                    costs: costs,
                    goal_rating: goal_rating
                });
            }
        } else if (inBacklogSection && line.match(/^#+/)) {
            // Якщо ми в секції "Backlog" і зустріли наступний заголовок, зупиняємося
            inBacklogSection = false;
        }
    }

    if (backlogItems.length > 0) {
        // Сортуємо список за goal_rating від більшого до меншого
        const sortedItems = backlogItems.sort((a, b) => {
            // Обробка Infinity та -Infinity для коректного сортування
            if (b.goal_rating === Infinity && a.goal_rating === Infinity) return 0;
            if (b.goal_rating === Infinity) return 1;
            if (a.goal_rating === Infinity) return -1;
            if (b.goal_rating === -Infinity && a.goal_rating === -Infinity) return 0;
            if (b.goal_rating === -Infinity) return -1;
            if (a.goal_rating === -Infinity) return 1;
            return b.goal_rating - a.goal_rating;
        });


        dv.header(3, "Пріоритезований Backlog (з усіма полями)");
        dv.list(sortedItems.map(item => {
            let ratingDisplay = item.goal_rating.toFixed(3);
            if (item.goal_rating === Infinity) ratingDisplay = "Дуже високий";
            if (item.goal_rating === -Infinity) ratingDisplay = "Дуже низький";
            return `${item.text} (Рейтинг: ${ratingDisplay})`;
        }));
    } else {
        dv.paragraph("У секції 'Backlog' не знайдено елементів списку з усіма трьома числовими полями (parent_value, impact, costs), або сама секція 'Backlog' відсутня.");
    }
}
```
