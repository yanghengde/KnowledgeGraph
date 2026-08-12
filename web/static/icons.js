(() => {
    "use strict";

    const paths = {
        package: '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5M12 22V12"/>',
        factory: '<path d="M3 21V9l5 3V8l5 3V4h3v7l5 3v7Z"/><path d="M7 21v-4h3v4M15 16h2M15 19h2"/>',
        cpu: '<rect x="7" y="7" width="10" height="10" rx="2"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3M10 10h4v4h-4z"/>',
        car: '<path d="m5 17-1 2v2h3v-2h10v2h3v-2l-1-2-2-7H7Z"/><path d="M5 17h14M7 10l1-4h8l1 4M7.5 14h.01M16.5 14h.01"/>',
        battery: '<rect x="3" y="6" width="17" height="12" rx="2"/><path d="M20 10h2v4h-2M11 9l-2 4h3l-2 4"/>',
        wrench: '<path d="M14.7 6.3a4 4 0 0 0-5-5L12 3.6 9.6 6 7.3 3.7a4 4 0 0 0 5 5l-8.6 8.6a2 2 0 1 0 2.8 2.8Z"/>',
        flask: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3"/><path d="M7.5 15h9"/>',
        truck: '<path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z"/><circle cx="7" cy="19" r="2"/><circle cx="18" cy="19" r="2"/>',
        layers: '<path d="m12 2 9 5-9 5-9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
        inbox: '<path d="M4 4h16v16H4z"/><path d="M4 14h4l2 3h4l2-3h4"/>',
        alert: '<path d="M10.3 2.9 1.8 17a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 2.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
        save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
        copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3"/>',
        check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
        xCircle: '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>',
        user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
        clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4a3 3 0 0 1 6 0v2H9ZM9 11h6M9 15h6"/>',
        clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
        message: '<path d="M21 15a3 3 0 0 1-3 3H8l-5 3V6a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3Z"/>',
        fileText: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
        bot: '<rect x="4" y="7" width="16" height="12" rx="3"/><path d="M12 3v4M8 12h.01M16 12h.01M8 16h8"/>',
        plus: '<path d="M12 5v14M5 12h14"/>',
        refresh: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
        loader: '<circle cx="12" cy="12" r="9" stroke-opacity=".25"/><path d="M21 12a9 9 0 0 0-9-9"/>',
    };

    const aliases = {
        "\uD83D\uDCE6": "package",
        "\u26A1": "battery",
        "\u26A1\uFE0F": "battery",
        "\uD83E\uDD16": "bot",
        "\uD83D\uDCED": "inbox",
        "\u26A0\uFE0F": "alert",
        "\u26A0": "alert",
        "\uD83D\uDCBE": "save",
        "\uD83D\uDCCB": "clipboard",
        "\u2705": "check",
        "\u274C": "xCircle",
        "\uD83D\uDC64": "user",
        "\u23F1": "clock",
        "\u23F1\uFE0F": "clock",
        "\uD83D\uDCAC": "message",
        "\uD83D\uDCDD": "fileText",
    };

    const catalog = [
        ["package", "通用 / 包装"],
        ["factory", "工厂 / 制造"],
        ["cpu", "半导体 / 电子"],
        ["car", "汽车制造"],
        ["battery", "新能源 / 储能"],
        ["wrench", "设备 / 维护"],
        ["flask", "质量 / 实验"],
        ["truck", "物流 / 供应链"],
        ["layers", "流程 / 本体"],
    ];

    function normalize(name) {
        const key = aliases[name] || name;
        return paths[key] ? key : "layers";
    }

    function svg(name, options = {}) {
        const key = normalize(name);
        const size = Number(options.size) || 16;
        const className = ["app-icon", options.className || ""].filter(Boolean).join(" ");
        return `<svg class="${className}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${options.strokeWidth || 1.8}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[key]}</svg>`;
    }

    function hydrate(root = document) {
        root.querySelectorAll("[data-app-icon]").forEach((element) => {
            element.innerHTML = svg(element.dataset.appIcon, {
                size: element.dataset.iconSize || 16,
                className: element.dataset.iconClass || "",
            });
        });
    }

    window.AppIcons = Object.freeze({ svg, normalize, catalog, hydrate });
    document.addEventListener("DOMContentLoaded", () => hydrate());
})();
