import { App, Plugin, MarkdownView, ItemView, WorkspaceLeaf } from 'obsidian';

export default class MyPlugin extends Plugin {
    async onload() {
        // Додаємо іконку в бічну панель для відкриття нашої панелі
        this.addRibbonIcon('link', 'Open Links Panel', () => {
            this.activateView();
        });

        // Реєструємо нашу бічну панель
        this.registerView(
            'links-panel',
            (leaf: WorkspaceLeaf) => new LinksPanelView(leaf)
        );

        // Відкриваємо бічну панель при запуску плагіна (опціонально)
        this.app.workspace.onLayoutReady(() => {
            this.activateView();
        });

        // Оновлюємо вміст панелі при зміні активної нотатки
        this.registerEvent(
            this.app.workspace.on('active-leaf-change', () => this.updateView())
        );

        // Оновлюємо вміст панелі при зміні вмісту редактора
        this.registerEvent(
            this.app.workspace.on('editor-change', () => this.updateView())
        );

        // Додаємо команду для показу/сховання панелі
        this.addCommand({
            id: 'toggle-links-panel',
            name: 'Toggle Links Panel',
            callback: () => this.toggleView(),
        });
    }

    // Метод для перемикання видимості панелі
    async toggleView() {
        const leaves = this.app.workspace.getLeavesOfType('links-panel');

        if (leaves.length > 0) {
            // Якщо панель відкрита, закриваємо її
            await this.app.workspace.detachLeavesOfType('links-panel');
        } else {
            // Якщо панель закрита, відкриваємо її
            this.activateView();
        }
    }

    async activateView() {
        const { workspace } = this.app;

        // Перевіряємо, чи вже відкрита наша панель
        let leaf: WorkspaceLeaf | null = null;
        const leaves = workspace.getLeavesOfType('links-panel');

        if (leaves.length > 0) {
            // Якщо панель вже відкрита, використовуємо її
            leaf = leaves[0];
        } else {
            // Якщо панель не відкрита, створюємо нову
            leaf = workspace.getRightLeaf(false);
            if (leaf) {
                await leaf.setViewState({ type: 'links-panel', active: true });
            } else {
                console.error('Failed to create a new leaf for the links panel.');
                return;
            }
        }

        // Активація панелі
        workspace.revealLeaf(leaf);
    }

    async updateView() {
        const leaves = this.app.workspace.getLeavesOfType('links-panel');

        if (leaves.length > 0) {
            const view = leaves[0].view as LinksPanelView;
            view.update();
        }
    }
}

class LinksPanelView extends ItemView {
    constructor(leaf: WorkspaceLeaf) {
        super(leaf);
    }

    getViewType(): string {
        return 'links-panel';
    }

    getDisplayText(): string {
        return 'Links Panel';
    }

    getIcon(): string {
        return 'link';
    }

    async onOpen() {
        const container = this.containerEl.children[1];
        container.empty();
        container.createEl('div', { cls: 'links-container' });

        this.update();
    }

    async update() {
        const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
        const container = this.containerEl.querySelector('.links-container');

        if (activeView && container) {
            const content = activeView.getViewData();
            const linksSection = this.extractLinksSection(content);

            if (linksSection) {
                container.innerHTML = this.renderLinks(linksSection);
            } else {
                container.innerHTML = 'No links found.';
            }
        }
    }

    extractLinksSection(content: string): string | null {
        // Оновлений регулярний вираз для пошуку секції Links
        const linksRegex = /##\s*.*Links.*\n([\s\S]*?)(?=\n##|$)/i;
        const match = content.match(linksRegex);
        return match ? match[1].trim() : null;
    }

    renderLinks(linksContent: string): string {
        // Регулярний вираз для пошуку всіх посилань між [[ і ]]
        const linkRegex = /\[\[(.*?)\]\]/g;
        const matches = linksContent.matchAll(linkRegex);

        let result = '<ul>'; // Початок списку
        for (const match of matches) {
            const link = match[1]; // Отримуємо вміст посилання (те, що всередині [[ ]])
            const [filePath, displayText] = link.split('|'); // Розділяємо на шлях до файлу та текст для відображення

            // Якщо displayText не вказано, використовуємо filePath як текст для відображення
            const linkText = displayText || filePath;

            result += `<li class="link-item"><a href="#" data-href="${filePath}" onclick="app.workspace.openLinkText('${filePath}', '', 'tab'); return false;">${linkText}</a></li>`;
        }
        result += '</ul>'; // Кінець списку

        return result || 'No links found.'; // Повертаємо список або повідомлення, якщо посилань немає
    }
}