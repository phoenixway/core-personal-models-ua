```dataviewjs 
const items = dv.pages('"/"').file.tasks.where(t => !t.completed && t.text.includes("#middle-term")).sort(t => t.value*t.impact/t.time_costs, "desc")
dv.table( [ "Task", "Rating", "Link" ], items.map(i => [ i.text.replace(/\[[a-zA-Z_]+::\d+(\.\d+)?\]/g, ""), i.value*i.impact/i.time_costs, i.link ]) ) 

// change column width
this.container.querySelectorAll(".table-view-table td").forEach(s => s.style.width ="1000px");
dv.container.className += " uniqueId"
```