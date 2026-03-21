/**
 * dungeon_crawler_game - Full Game Logic
 */


// --- 1. ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ И КОНСТАНТЫ ---
let isGlobalBattleLock = false; // Блокировка интерфейса картой

const roomNames = { 
    "B": "Бой", 
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
        <div class="stat-line"><span>SP:</span> <span style="color: #3434eb;">${hero.mp}/${hero.max_mp}</span></div>
                        <div class="stat-line"><span>Gold:</span> <span style="color: #ffd700;">${hero.gold}</span></div>

                        <div class="stat-line">
                        <span>Stat Points:</span> 
                        <span>
                            ${hero.stat_points} 
                            ${hero.stat_points > 0 ? '<button onclick="openUpgradeModal()" style="padding: 2px 5px; margin-left:5px;">+</button>' : ''}
                        </span>
                        </div>
        <div style="margin-top:10px; border-top: 1px solid #444; padding-top:20px;">
                            <div class="stat-line">
                                <span>Strength:</span> 
                                <div>
                                    <span>${hero.strength}</span>
                                    <span style="color: #4caf50;">+${hero.total_strength - hero.strength}</span>
                                </div>
                            </div>
                            <div class="stat-line">
                                <span>Dexterity:</span> 
                                <div>
                                    <span>${hero.dexterity}</span>
                                    <span style="color: #4caf50;">+${hero.total_dexterity - hero.dexterity}</span>
                                </div>
                            </div>
                            <div class="stat-line">
                                <span>Agility:</span> 
                                <div>
                                    <span>${hero.agility}</span>
                                    <span style="color: #4caf50;">+${hero.total_agility - hero.agility}</span>
                                </div>
                            </div>
                            <div class="stat-line">
                                <span>Intelligence:</span> 
                                <div>
                                    <span>${hero.intelligence}</span>
                                    <span style="color: #4caf50;">+${hero.total_intelligence - hero.intelligence}</span>
                                </div>
                            </div>
                            <div class="stat-line">
                                <span>Vitality:</span> 
                                <div>
                                    <span>${hero.vitality}</span>
                                    <span style="color: #4caf50;">+${hero.total_vitality - hero.vitality}</span>
                                </div>
                            </div>
                            <div class="stat-line">
                                <span>Flee:</span> 
                                <span>${hero.total_flee}</span>
                            </div>
                            <div class="stat-line">
                                <span>Crit:</span> 
                                <span>${hero.total_crit}%</span>
                            </div>
                        </div>

                        <div style="margin-top:10px; border-top: 1px solid #444; padding-top:25px;">
                                <div style="margin-top:10px;">
                                <div style="font-size: 0.8rem; color: var(--accent-color); margin-bottom: 5px;">Артефакты:</div>
                                <div class="items-container">${artifactsHtml}</div>
                            </div>

                            <div style="margin-top:10px;">
                                <div style="font-size: 0.8rem; color: var(--accent-color); margin-bottom: 5px;">Заклинания:</div>
                                <div class="items-container">${spellsHtml}</div>
                            </div>
    `;
}

// --- 4. ЛОГИКА КАРТЫ ---

async function updateMap() {
    if (isGlobalBattleLock) return;
    const token = localStorage.getItem('token');
    if (!token) return;

    if (currentHeroCache && currentHeroCache.active_monster_id) {
        showBattleMode(true);
        return; 
    }

    try {
        const res = await fetch('http://127.0.0.1:8000/heroes/map', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) return;
        const data = await res.json();

        if (data.hero_position && data.hero_position.active_monster_id) {
            showBattleMode(true);
            return;
        }

        showBattleMode(false);
        
        const restUI = document.getElementById('restInterface');
        const shopUI = document.getElementById('shopInterface');
        const movementUI = document.getElementById('movementControls');
        const eventUI = document.getElementById('eventInterface');
        
        const currentRoomType = data.hero_position ? data.hero_position.room_type : null;

        // Скрываем всё по умолчанию
        if (restUI) restUI.style.display = 'none';
        if (shopUI) shopUI.style.display = 'none';
        if (movementUI) movementUI.style.display = 'flex';
        if (eventUI) eventUI.style.display = 'none';

        if (currentRoomType === "R") {
            if (restUI) restUI.style.display = 'flex';
            if (movementUI) movementUI.style.display = 'none';
        } 
        else if (currentRoomType === "S") {
            // МЫ В МАГАЗИНЕ
            if (shopUI) shopUI.style.display = 'flex';
            if (movementUI) movementUI.style.display = 'none';
            loadShopCatalog(); // Загружаем товары с бэкенда  
        }

        else if (currentRoomType === "E") {
            // МЫ В СОБЫТИИ
            if (eventUI) eventUI.style.display = 'flex';
            if (movementUI) movementUI.style.display = 'none';
            loadCurrentEvent(); // Запрашиваем текст и кнопки с сервера
        }

        const currentFloor = data.hero_position.floor;
        const currentLane = data.hero_position.lane;
        const nextFloorNum = currentFloor + 1;
        let nextFloorData = data.map_preview.find(f => f.floor === `F${nextFloorNum}` || f.floor === nextFloorNum);
        
        if (!nextFloorData) {
            nextFloorData = { lanes: [0, 1, 2] }; 
        }

        renderMovementButtons(currentLane, nextFloorData.lanes);
    } catch (error) {
        console.error("Ошибка обновления карты:", error);
    }
}

window.sendRest = async function() {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://127.0.0.1:8000/world/rest', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addLog(`✅ ${data.message}`);
            // Обновляем статы (HP и Золото), чтобы игрок видел результат
            await loadHeroData(); 
        } else {
            addLog(`❌ Ошибка: ${data.detail}`);
        }
    } catch (e) {
        console.error("Ошибка при отдыхе:", e);
    }
};

// Заодно сделаем то же самое для кнопки "Идти дальше"
window.continueJourney = function() {
    const restUI = document.getElementById('restInterface');
    const movementUI = document.getElementById('movementControls');
    
    if (restUI && movementUI) {
        restUI.style.display = 'none';
        movementUI.style.display = 'block';
        addLog("⛺ Вы свернули лагерь и продолжили путь.");
    }
};

window.loadShopCatalog = async function() {
    const token = localStorage.getItem('token');
    const container = document.getElementById('shopItemsContainer');
    try {
        const response = await fetch('http://127.0.0.1:8000/world/shop', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();

        document.getElementById('shopHeroGold').textContent = data.hero_gold;
        container.innerHTML = '';

        if (data.items_for_sale.length === 0) {
            container.innerHTML = "<p>Товары закончились.</p>";
            return;
        }

        data.items_for_sale.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.style = "border:  1px solid #777;  padding: 10px; border-radius: 5px; width: 200px; height: 80px; text-align: center; ";
            itemDiv.innerHTML = `
                <div style="font-weight: bold; margin-top: 10px;">${item.name}</div>
                <div style="color: #ffd700;">${item.cost} 🪙 </div>
                <button onclick="buyItem(${item.id})" style="margin-top: 5px; flex-end; cursor: pointer;">Купить</button>
            `;
            container.appendChild(itemDiv);
        });
    } catch (e) { console.error("Ошибка загрузки магазина:", e); }
};

window.buyItem = async function(itemId) {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`http://127.0.0.1:8000/world/buy?artifact_id=${itemId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();

        if (response.ok) {
            addLog(`💰 ${data.message}`);
            await loadHeroData();     // Обновляем статы (золото)
            await loadShopCatalog();  // Перерисовываем товары (чтобы купленный исчез)
        } else {
            addLog(`❌ Ошибка магазина: ${data.detail}`);
        }
    } catch (e) { console.error("Ошибка покупки:", e); }
};

window.continueJourneyFromShop = function() {
    document.getElementById('shopInterface').style.display = 'none';
    document.getElementById('movementControls').style.display = 'block';
    addLog("Вы попрощались с торговцем и пошли дальше.");
};


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
            await loadHeroData();
            await updateMap(); 
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

function showDeathScreen(heroName) {
    const modal = document.getElementById('modalDeath');
    const msg = document.getElementById('deathMessage');
    if (modal && msg) {
        msg.textContent = `Герой ${heroName} пал смертью храбрых в битве с чудовищем.`;
        modal.style.display = 'block';
        
        // Закрываем другие окна
        if (typeof modalAuth !== 'undefined') modalAuth.style.display = "none";
        const lootModal = document.getElementById('modalLoot');
        if (lootModal) lootModal.style.display = 'none';
        
        // ОЧИЩАЕМ ТОЛЬКО ДАННЫЕ ГЕРОЯ, НО НЕ АККАУНТ
        // localStorage.removeItem('heroData'); // Если ты хранишь кэш героя отдельно
        // Токен НЕ ТРОГАЕМ, чтобы не разлогинило
    }
}

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

async function sendAttack() {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://127.0.0.1:8000/battle/attack', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();

        // 1. Выводим логи в общий чат логов
        if (data.log) data.log.forEach(msg => addLog(msg));

        // 2. СМЕРТЬ ГЕРОЯ
        if (data.status === "defeat") {
            showDeathScreen(data.hero_name || "Ваш герой");
            return;
        }

        // 3. ПОБЕДА НАД МОНСТРОМ
        if (data.status === "victory") {
            updateMonsterUI("0/1"); 
            // Сбрасываем текст врага
            document.getElementById('monsterName').textContent = "Враг"; 
            document.getElementById('monsterHpText').textContent = "HP: 0/0";

            showBattleMode(false); // Прячем кнопки боя
            
            // Показываем модалку лута (только при победе!)
            const victoryMsg = data.log ? data.log[data.log.length - 1] : "Победа!";
            showLootModal(victoryMsg);
            
            await loadHeroData(); // Обновляем золото/опыт в интерфейсе
            return;
        }

        // 4. БОЙ ПРОДОЛЖАЕТСЯ (ongoing)
        if (data.status === "ongoing") {
            updateMonsterUI(data.monster_hp);
            // Если в ответе есть данные героя, обновляем его полоску HP
            if (data.hero_hp) {
                // Предположим, у вас есть функция renderStats или аналогичная
                await loadHeroData(); 
            }
        }

    } catch (e) { 
        console.error("Ошибка атаки:", e); 
        addLog("Ошибка соединения с сервером");
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

        // 1. Логи боя (урон, промахи) — пишем всегда в общий лог игры
        if (data.log) {
            data.log.forEach(msg => addLog(msg));
        }

        // 2. Смерть героя — показываем траурное окно
        if (data.status === "defeat") {
            showDeathScreen(data.hero_name || "Ваш герой");
            return; 
        }

        if (response.ok) {
            // 3. Обновляем статы героя (мана потратилась, хп убавилось)
            if (data.hero) {
                // Сохраняем кеш спеллов/артефактов
                if ((!data.hero.spells || data.hero.spells.length === 0) && currentHeroCache.spells) {
                    data.hero.spells = currentHeroCache.spells;
                }
                currentHeroCache = data.hero;
                renderStats(currentHeroCache);
            }

            // 4. РЕАЛЬНАЯ ПОБЕДА
            if (data.status === "victory") {
                updateMonsterUI("0/1"); 
                showBattleMode(false); // Прячем интерфейс боя
                
                // Показываем окно лута ТОЛЬКО ТУТ
                const victoryMsg = data.log ? data.log[data.log.length - 1] : "Победа!";
                showLootModal(victoryMsg);
                
                await loadHeroData();
                return; // Выходим из функции
            }

            // 5. БОЙ ПРОДОЛЖАЕТСЯ
            // Если мы здесь — значит никто не умер. Просто обновляем HP полоски.
            if (data.monster_hp) {
                updateMonsterUI(data.monster_hp);
            }
            
            renderBattleSpells(); // Обновляем кнопки (вдруг мана кончилась)
        }
    } catch (e) { 
        console.error("Ошибка каста:", e); 
    }
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

        if (res.ok) {
            // ВМЕСТО сообщения "Войдите", сразу вызываем логин
            await loginUser(username, password);
        } else {
            const d = await res.json();
            showAuthMessage(d.detail || "Ошибка регистрации");
        }
    } else {
        // Обычный вход
        await loginUser(username, password);
    }
});

async function loginUser(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch('http://127.0.0.1:8000/auth/token', { 
        method: 'POST', 
        body: formData 
    });

    if (res.ok) {
        const data = await res.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('username', username);
        
        modalAuth.style.display = "none";
        
        // 1. Обновляем интерфейс (кнопки войти/выйти)
        updateUI(); 
        
        // 2. Проверяем наличие героя
        await checkHeroAndInit();
    } else {
        showAuthMessage("Ошибка входа после регистрации");
    }
}


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

async function checkHeroAndInit() {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch('http://127.0.0.1:8000/heroes/me', { // Предположим, у вас есть такой эндпоинт
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 404 || (res.ok && !(await res.json()))) {
            // Если героя нет — открываем модалку создания
            window.openCreateHeroModal();
        } else {
            // Если герой есть — загружаем игру
            await loadHeroData();
            await updateMap();
        }
    } catch (e) {
        console.error("Ошибка при проверке героя:", e);
    }
}

function renderUpgradeOptions() {
    const hero = currentHeroCache;
    if (!hero) return;

    document.getElementById('availablePoints').textContent = hero.stat_points;
    const list = document.getElementById('upgradeList');

    // Добавляем свойство 'field', которое соответствует ключу в объекте hero
    const stats = [
        {k:'str', l:'Сила', field: 'strength'}, 
        {k:'agi', l:'Ловкость', field: 'agility'}, 
        {k:'vit', l:'Живучесть', field: 'vitality'}, 
        {k:'int', l:'Интеллект', field: 'intelligence'}, 
        {k:'dex', l:'Меткость', field: 'dexterity'}
    ];

    list.innerHTML = stats.map(s => {
        // Получаем текущее значение из кэша. 
        // Если вдруг данные не пришли, ставим 0, чтобы не было undefined
        const currentVal = hero[s.field] || 0;

        return `
            <div class="upgrade-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span>${s.l} <b>${currentVal}</b></span>
                <button onclick="sendUpgrade('${s.k}')" 
                        ${hero.stat_points <= 0 ? 'disabled' : ''} 
                        style="padding: 2px 10px;">+</button>
            </div>
        `;
    }).join('');
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

window.continueJourney = function() {
    document.getElementById('restInterface').style.display = 'none';
    document.getElementById('movementControls').style.display = 'block';
    addLog("Вы покинули уютный лагерь и отправились дальше.");
};

// Запрашивает данные события и генерирует кнопки
window.loadCurrentEvent = async function() {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://127.0.0.1:8000/world/current_event', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) return;
        
        const data = await response.json();

        // Заполняем тексты
        document.getElementById('eventName').textContent = data.name;
        document.getElementById('eventDescription').textContent = data.description;
        
        // Очищаем старые кнопки
        const container = document.getElementById('eventChoicesContainer');
        container.innerHTML = '';
        
        // Создаем новые кнопки из массива
        data.choices.forEach(choice => {
            const btn = document.createElement('button');
            btn.textContent = choice.text;
            btn.style = "background: #9c27b0; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 80%; max-width: 300px; font-weight: bold;";
            
            // При клике отправляем value на сервер
            btn.onclick = () => resolveEvent(choice.value); 
            container.appendChild(btn);
        });

    } catch (e) { console.error("Ошибка загрузки события:", e); }
};

// Отправляет решение на сервер
window.resolveEvent = async function(choiceValue) {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`http://127.0.0.1:8000/world/resolve_event?choice=${choiceValue}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            addLog(`✨ ${data.message}`);
            await loadHeroData(); // Обновляем статы (например, если дали +Силу)
            
            // Событие пройдено, возвращаем кнопки движения
            document.getElementById('eventInterface').style.display = 'none';
            document.getElementById('movementControls').style.display = 'block';
        } else {
            addLog(`❌ Ошибка: ${data.detail}`);
        }
    } catch (e) { console.error("Ошибка при выборе:", e); }
};

function handleRebirth() {
    // Просто перезагружаем страницу. 
    // Скрипт при старте увидит токен, не найдет героя и откроет создание.
    location.reload();
}


// Старт
updateUI();