/**
 * dungeon_crawler_game - Full Game Logic
 */


// --- 1. ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ И КОНСТАНТЫ ---
let isGlobalBattleLock = false; // Блокировка интерфейса картой

const roomNames = { 
    "B": "Схватка", 
    "BOSS": "Главарь", 
    "E": "Событие", 
    "R": "Отдых", 
    "S": "Магазин" 
};
let currentHeroCache = null;

// Элементы интерфейса
const modalAuth = document.getElementById("modalAuth");
const btnSubmitAuth = document.getElementById("btnSubmitAuth");
const closeAuthBtn = document.querySelector(".close");

// --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

function addLog(message) {
    const logContent = document.getElementById('logContent');
    if (!logContent) return;
    const newEntry = document.createElement('div');
    newEntry.className = 'log-entry new';
    newEntry.textContent = `> ${message}`;
    logContent.appendChild(newEntry);
    const logPanel = document.querySelector('.log-panel');
    if (logPanel) logPanel.scrollTop = logPanel.scrollHeight;
}

function showAuthMessage(text, isError = true) {
    const msgDiv = document.getElementById('authMessage');
    if (!msgDiv) return;
    msgDiv.textContent = text;
    msgDiv.style.display = 'block';
    msgDiv.style.color = isError ? '#ff5555' : '#55ff55';
}

// --- 3. ЛОГИКА ГЕРОЯ ---

async function loadHeroData() {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        const response = await fetch('http://127.0.0.1:8000/heroes/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const hero = await response.json();
            currentHeroCache = hero;
            renderStats(hero);

            // НОВОЕ: ПРОВЕРКА НА ЛУТ
            if (hero.pending_loot && hero.pending_loot.length > 0) {
                showPickLootModal(hero.pending_loot);
            }
            
            // Если герой жив и загружен, обновляем карту
            await updateMap(); 
        } else if (response.status === 404) {
            // Если героя нет, зачищаем интерфейс и предлагаем создать
            currentHeroCache = null;
            document.getElementById('statsContent').innerHTML = `
                <div class="panel-notice">
                    <p>У вас еще нет героя или он пал в бою.</p>
                    <button onclick="window.openCreateHeroModal()" class="primary-btn">Создать героя</button>
                </div>
            `;
            // Скрываем карту, так как ходить некому
            const controls = document.getElementById('movementControls');
            if (controls) controls.innerHTML = "";
        }
    } catch (error) {
        console.error("Критическая ошибка загрузки:", error);
    }
}

function renderStats(hero) {
    const content = document.getElementById('statsContent');
    if (!content) return;

    const artifactsHtml = (hero.artifacts || []).map(art => 
        `<span class="item-tag rarity-${art.rarity}" title="${art.description}">${art.name}</span>`
    ).join(' ') || '<span style="color: #666;">Пусто</span>';

    const spellsHtml = (hero.spells || []).map(spell => 
        `<span class="item-tag rarity-${spell.rarity}" title="${spell.description}">${spell.name}</span>`
    ).join(' ') || '<span style="color: #666;">Нет заклинаний</span>';

    content.innerHTML = `
        <div class="stat-line"><span>Имя:</span> <b>${hero.name}</b></div>
        <div class="stat-line"><span>Уровень:</span> <span>${hero.level}</span></div>
        <div class="stat-line"><span>XP:</span> <span>${hero.xp}/100</span></div>
        <div class="stat-line"><span>HP:</span> <span style="color: #ff5555;">${hero.hp}/${hero.max_hp}</span></div>
        <div class="stat-line"><span>MP:</span> <span style="color: #3434eb;">${hero.mp}/${hero.max_mp}</span></div>
        <div class="stat-line"><span>Золото:</span> <span style="color: #ffd700;">${hero.gold}</span></div>
        <div class="stat-line"><span>Очки статов:</span> 
            <span>${hero.stat_points} 
            ${hero.stat_points > 0 ? '<button onclick="openUpgradeModal()" class="small-btn">+</button>' : ''}
            </span>
        </div>
        <div style="margin-top:10px; border-top: 1px solid #444; padding-top:10px;">
            <div class="stat-line"><span>Сила:</span> <span>${hero.total_strength}</span></div>
            <div class="stat-line"><span>Ловкость:</span> <span>${hero.total_agility}</span></div>
            <div class="stat-line"><span>Интеллект:</span> <span>${hero.total_intelligence}</span></div>
        </div>
        <div style="margin-top:10px;">
            <div style="font-size: 0.8rem; color: #aaa;">Артефакты:</div>
            <div class="items-container">${artifactsHtml}</div>
            <div style="font-size: 0.8rem; color: #aaa; margin-top:5px;">Заклинания:</div>
            <div class="items-container">${spellsHtml}</div>
        </div>
    `;
}

// --- 4. ЛОГИКА КАРТЫ ---

async function updateMap() {
    if (isGlobalBattleLock) return;
    const token = localStorage.getItem('token');
    if (!token) return;

    // 1. ПРОВЕРКА КЕША: Если в герое уже сидит монстр — только бой, никакой карты!
    if (currentHeroCache && currentHeroCache.active_monster_id) {
        console.log("Бой активен (из кеша), блокируем обновление карты.");
        showBattleMode(true);
        return; // ПРЕРЫВАЕМ функцию здесь
    }

    try {
        const res = await fetch('http://127.0.0.1:8000/heroes/map', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) return;
        const data = await res.json();

        // 2. ПРОВЕРКА ПОСЛЕ ЗАПРОСА: Если бэк внезапно сказал, что монстр есть
        if (data.hero_position && data.hero_position.active_monster_id) {
            showBattleMode(true);
            return;
        }

        // 3. РИСУЕМ КАРТУ (только если боя точно нет)
        showBattleMode(false);
        
        const currentFloor = data.hero_position.floor;
        const currentLane = data.hero_position.lane;
        const nextFloorNum = currentFloor + 1;
        let nextFloorData = data.map_preview.find(f => f.floor === `F${nextFloorNum}` || f.floor === nextFloorNum);
        
        if (!nextFloorData) {
            console.log("Данные следующего этажа не найдены в превью, генерируем стандартные переходы.");
            // Создаем заглушку, чтобы кнопки отрисовались в любом случае
            nextFloorData = { lanes: [0, 1, 2] }; 
        }

        renderMovementButtons(currentLane, nextFloorData.lanes);
    } catch (error) {
        console.error("Ошибка обновления карты:", error);
    }
}

function renderMovementButtons(currentLane, nextLanes) {
    const controls = document.getElementById('movementControls');
    controls.innerHTML = ''; 
    const directions = [
        { label: "Влево", lane: currentLane - 1 },
        { label: "Прямо", lane: currentLane },
        { label: "Вправо", lane: currentLane + 1 }
    ];
    const laneKeys = ["Left (0)", "Center (1)", "Right (2)"];

    directions.forEach(dir => {
        if (dir.lane >= 0 && dir.lane <= 2) {
            const laneKey = laneKeys[dir.lane];
            const typeCode = nextLanes[laneKey];
            const btn = document.createElement('button');
            btn.className = 'move-btn';
            btn.innerHTML = `<span class="direction">${dir.label}</span><span class="room-type">${roomNames[typeCode] || "???"}</span>`;
            btn.onclick = () => moveHero(dir.lane);
            controls.appendChild(btn);
        }
    });
}

async function moveHero(targetLane) {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`http://127.0.0.1:8000/heroes/move?target_lane=${targetLane}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();

        if (response.ok) {
            if (data.monster) {
                document.getElementById('monsterName').textContent = data.monster.name;
                const currentHp = data.monster.current_hp !== undefined ? data.monster.current_hp : data.monster.hp;
                updateMonsterUI(`${currentHp}/${data.monster.max_hp}`);
            }
            
            addLog(`Вы вошли в комнату. ${data.event || ""}`);
            await loadHeroData(); // Это обновит currentHeroCache и включит бой
        } else {
            
            if (response.status === 400) {
                addLog(`Путь прегражден: ${data.detail}`);
                // ПРИНУДИТЕЛЬНО освежаем данные героя, чтобы включился режим боя
                await loadHeroData(); 
            } else {
                addLog(`Ошибка: ${data.detail}`);
            }
        }
    } catch (e) { 
        console.error("Ошибка перемещения:", e); 
    }
}

// --- 5. ЛОГИКА БОЯ ---

function showBattleMode(isBattle) {
    const battleUI = document.getElementById('battleInterface');
    const navigationUI = document.getElementById('navigationBlock');
    
    isGlobalBattleLock = isBattle; // Устанавливаем блокировку

    if (isBattle) {
        battleUI.style.display = 'block';
        navigationUI.style.display = 'none';
        renderBattleSpells();
        // ... твой код отрисовки монстра ...
    } else {
        battleUI.style.display = 'none';
        navigationUI.style.display = 'block';
    }
}

async function sendAttack() {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://127.0.0.1:8000/battle/attack', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (data.log) data.log.forEach(msg => addLog(msg));

        if (data.status === "victory") {
            // ВАЖНО: Сбрасываем интерфейс старого монстра!
            updateMonsterUI("0/1"); // Обнулит полоску
            document.getElementById('monsterName').textContent = "Враг"; 
            document.getElementById('monsterHpText').textContent = "HP: ??/??";

            showBattleMode(false); 
            showLootModal(data.log ? data.log[data.log.length-1] : "Победа!");
            await loadHeroData();

        } else if (data.status === "defeat") {
            alert("Вы погибли!");
            location.reload();
        } else {
            updateMonsterUI(data.monster_hp);
            await loadHeroData();
        }
    } catch (e) { console.error("Ошибка атаки:", e); }
}

function updateMonsterUI(hpData) {
    if (hpData === undefined || hpData === null) return;
    
    let current, max;
    
    // Если передали строку "5/10"
    if (typeof hpData === 'string' && hpData.includes('/')) {
        [current, max] = hpData.split('/').map(Number);
    } 
    // Если передали просто текущее ХП, а макс ХП берем из кеша
    else if (currentHeroCache && currentHeroCache.active_monster) {
        current = Number(hpData);
        max = currentHeroCache.active_monster.max_hp;
    } else {
        return; // Недостаточно данных для обновления
    }

    const percent = Math.max(0, (current / max) * 100);
    const bar = document.getElementById('monsterHpBar');
    if (bar) bar.style.width = percent + '%';
    
    const text = document.getElementById('monsterHpText');
    if (text) text.textContent = `HP: ${current}/${max}`;
}

function renderBattleSpells() {
    const container = document.getElementById('spellsActions');
    if (!container || !currentHeroCache) return;
    
    container.innerHTML = ''; // Очищаем старые кнопки

    // Берем массив заклинаний из кеша героя
    const spells = currentHeroCache.spells || [];

    if (spells.length === 0) {
        container.innerHTML = '<p style="font-size: 0.8rem; color: #666;">Нет изученных заклинаний</p>';
        return;
    }

    spells.forEach(spell => {
        const btn = document.createElement('button');
        btn.className = 'spell-btn';
        
        // Проверяем, хватает ли маны
        const canCast = currentHeroCache.mp >= spell.mp_cost;
        
        btn.innerHTML = `
            <span class="spell-name">${spell.name}</span>
            <span class="spell-cost">${spell.mp_cost} MP</span>
        `;
        
        btn.disabled = !canCast;
        btn.title = spell.description || "";

        // При клике вызываем функцию каста
        btn.onclick = () => sendCast(spell.id);
        
        container.appendChild(btn);
    });
}

async function sendCast(spellId) {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`http://127.0.0.1:8000/battle/cast/${spellId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();

        if (response.ok) {
            if (data.message) addLog(data.message);
            
            // 1. Сначала полностью обновляем данные героя (статы, мана, активный монстр)
            await loadHeroData(); 

            // 2. Проверяем, не умер ли монстр от магии
            // (Бэкенд в /cast должен возвращать статус боя, если он там считается)
            // Если статус победы не приходит из /cast, проверим через кеш:
            if (!currentHeroCache.active_monster_id) {
                showBattleMode(false);
                // Показываем обычное окно лута (золото/опыт)
                showLootModal(data.message || "Победа магией!");
                return; 
            }

            // 3. Если бой продолжается — обновляем интерфейс монстра
            const m = currentHeroCache.active_monster;
            if (m) {
                const c_hp = m.current_hp !== undefined ? m.current_hp : m.hp;
                updateMonsterUI(`${c_hp}/${m.max_hp}`);
            }
            
            renderBattleSpells(); // Перерисовываем кнопки (проверка маны)
            
        } else {
            addLog(`Ошибка: ${data.detail}`);
        }
    } catch (e) { 
        console.error("Ошибка при касте:", e); 
    }
}

async function sendCast(spellId) {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`http://127.0.0.1:8000/battle/cast/${spellId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();

        if (response.ok) {

            if (data.hero) {
                // Если в пришедшем герое нет спеллов, но в нашем кеше они были - сохраняем старые
                if ((!data.hero.spells || data.hero.spells.length === 0) && currentHeroCache.spells) {
                    data.hero.spells = currentHeroCache.spells;
                }
                if ((!data.hero.artifacts || data.hero.artifacts.length === 0) && currentHeroCache.artifacts) {
                    data.hero.artifacts = currentHeroCache.artifacts;
                }
                
                currentHeroCache = data.hero;
                renderStats(currentHeroCache);
            }

            if (data.message) addLog(data.message);
            
            // 1. Сначала обновляем статы героя (мана и т.д.)
            if (data.hero) {
                currentHeroCache = data.hero;
                renderStats(currentHeroCache);
            }

            // 2. СРОЧНОЕ ОБНОВЛЕНИЕ МОНСТРА
            // Если твой бэк в /cast возвращает монстра (проверь это в консоли), 
            // то берем данные оттуда. Если нет - берем из data.monster_hp (если ты его добавил в return)
            if (data.monster_hp) {
                updateMonsterUI(data.monster_hp);
            } else {
                // Если бэк не шлет монстра в ответе /cast, нам нужно сделать 
                // запрос loadHeroData и ПОДОЖДАТЬ его выполнения
                await loadHeroData();
                
                // После loadHeroData монстр в кэше должен быть свежим
                if (currentHeroCache && currentHeroCache.active_monster) {
                    const m = currentHeroCache.active_monster;
                    const c_hp = m.current_hp !== undefined ? m.current_hp : m.hp;
                    updateMonsterUI(`${c_hp}/${m.max_hp}`);
                }
            }

            // 3. ПРОВЕРКА ПОБЕДЫ
            // Если ID монстра исчез из героя — значит, он умер
            if (!currentHeroCache.active_monster_id) {
                updateMonsterUI("0/100"); // Визуально обнуляем полоску
                showBattleMode(false);
                showLootModal(data.message || "Монстр повержен магией!");
            }

            renderBattleSpells(); // Обновляем кнопки спеллов (доступность по мане)
        }
    } catch (e) { console.error("Ошибка каста:", e); }
}

function showLootModal(message) {
    const modal = document.getElementById('modalLoot');
    const resultDiv = document.getElementById('lootResult');
    
    if (modal && resultDiv) {
        resultDiv.textContent = message;
        modal.style.display = 'block';
    }
    
    // Прячем интерфейс боя, так как враг повержен
    showBattleMode(false); 
}

// --- 6. АВТОРИЗАЦИЯ И ИНИЦИАЛИЗАЦИЯ ---

function updateUI() {
    const token = localStorage.getItem('token');
    const guestBlock = document.getElementById('guestBlock');
    const userBlock = document.getElementById('userBlock');
    
    if (token) {
        guestBlock.style.display = 'none';
        userBlock.style.display = 'flex';
        document.getElementById('playerName').textContent = localStorage.getItem('username');
        loadHeroData(); // updateMap вызовется внутри неё только при успехе
    } else {
        guestBlock.style.display = 'block';
        userBlock.style.display = 'none';
    }
}

// Обработка формы Auth
btnSubmitAuth?.addEventListener('click', async () => {
    const mode = document.getElementById('modalTitle').textContent;
    const username = document.getElementById('authUsername').value;
    const password = document.getElementById('authPassword').value;

    if (mode === "Регистрация") {
        const res = await fetch('http://127.0.0.1:8000/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (res.ok) showAuthMessage("Успех! Войдите.", false);
        else { const d = await res.json(); showAuthMessage(d.detail); }
    } else {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        const res = await fetch('http://127.0.0.1:8000/auth/token', { method: 'POST', body: formData });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', username);
            modalAuth.style.display = "none";
            updateUI();
        } else { showAuthMessage("Ошибка входа"); }
    }
});

// События модалок
document.getElementById('btnLogin')?.addEventListener('click', () => {
    document.getElementById('modalTitle').textContent = "Вход";
    modalAuth.style.display = "block";
});
document.getElementById('btnRegister')?.addEventListener('click', () => {
    document.getElementById('modalTitle').textContent = "Регистрация";
    modalAuth.style.display = "block";
});
document.getElementById('btnLogout')?.addEventListener('click', () => {
    localStorage.clear();
    location.reload();
});
if (closeAuthBtn) closeAuthBtn.onclick = () => modalAuth.style.display = "none";

// Глобальные функции для HTML
window.openCreateHeroModal = () => document.getElementById('modalCreateHero').style.display = 'block';
window.sendAttack = sendAttack;
window.closeLootModal = async () => {
    document.getElementById('modalLoot').style.display = 'none';
    // Принудительно ставим false, чтобы updateMap не блокировался
    isGlobalBattleLock = false; 
    await updateMap(); 
};
window.openUpgradeModal = () => {
    document.getElementById('modalUpgrade').style.display = 'block';
    renderUpgradeOptions();
};

// --- 7. ПРОКАЧКА И СОЗДАНИЕ ---

async function sendUpgrade(statKey) {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch(`http://127.0.0.1:8000/heroes/upgrade?stat=${statKey}&amount=1`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            await loadHeroData();
            renderUpgradeOptions();
        }
    } catch (e) { console.error(e); }
}

function renderUpgradeOptions() {
    const hero = currentHeroCache;
    if (!hero) return;
    document.getElementById('availablePoints').textContent = hero.stat_points;
    const list = document.getElementById('upgradeList');
    const stats = [
        {k:'str', l:'Сила'}, {k:'agi', l:'Ловкость'}, {k:'vit', l:'Живучесть'}, 
        {k:'int', l:'Интеллект'}, {k:'dex', l:'Меткость'}
    ];
    list.innerHTML = stats.map(s => `
        <div class="upgrade-row">
            <span>${s.l}</span>
            <button onclick="sendUpgrade('${s.k}')" ${hero.stat_points <= 0 ? 'disabled' : ''}>+</button>
        </div>
    `).join('');
}

// Открыть модалку создания
window.openCreateHeroModal = function() {
    const modal = document.getElementById('modalCreateHero');
    if (modal) {
        modal.style.display = 'block';
    } else {
        console.error("Модалка modalCreateHero не найдена в HTML!");
    }
};

// Закрыть модалку создания
window.closeCreateHeroModal = function() {
    document.getElementById('modalCreateHero').style.display = 'none';
};

// Функция подтверждения создания (привязана к кнопке в модалке)
document.getElementById('btnConfirmCreate')?.addEventListener('click', async () => {
    const nameInput = document.getElementById('newHeroName');
    const name = nameInput ? nameInput.value : "";
    const token = localStorage.getItem('token');

    if (!name) {
        alert("Введите имя героя!");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/heroes/create?name=${encodeURIComponent(name)}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            addLog(`Герой ${name} успешно создан!`);
            window.closeCreateHeroModal();
            // Сразу обновляем данные и карту
            await loadHeroData();
            await updateMap();
        } else {
            const data = await response.json();
            alert(data.detail || "Ошибка при создании героя");
        }
    } catch (error) {
        console.error("Ошибка запроса на создание:", error);
        alert("Сервер не отвечает");
    }
});

function showPickLootModal(lootItems) {
    const modal = document.getElementById('modalPickLoot');
    const container = document.getElementById('pendingLootContainer');
    if (!modal || !container) return;

    container.innerHTML = ''; // Очищаем старые кнопки

    lootItems.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'loot-choice-btn';
        btn.style.padding = '10px';
        btn.style.cursor = 'pointer';
        
        const typeLabel = item.type === 'artifact' ? 'Артефакт' : 'Заклинание';
        btn.innerHTML = `<b>${item.name}</b><br><small style="color:#aaa;">${typeLabel}</small>`;
        btn.title = item.description || "Описание скрыто";
        
        // При клике отправляем запрос
        btn.onclick = () => sendPickLoot(item.type, item.id);
        
        container.appendChild(btn);
    });

    modal.style.display = 'block';
}

// Функция отправки выбора на бэкенд
async function sendPickLoot(choiceType, choiceId) {
    const token = localStorage.getItem('token');
    try {
        // Убедись, что URL правильный (если роутер имеет префикс /battle, добавь его)
        const response = await fetch(`http://127.0.0.1:8000/world/pick_loot?choice_type=${choiceType}&choice_id=${choiceId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('modalPickLoot').style.display = 'none';
            addLog(`Награда получена: ${data.message}`);
            await loadHeroData(); // Обновляем статы с новым артефактом
        } else {
            alert("Ошибка выбора: " + data.detail);
        }
    } catch (e) {
        console.error("Ошибка при выборе лута:", e);
    }
}



// Старт
updateUI();