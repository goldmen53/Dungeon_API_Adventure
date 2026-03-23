/**
 * dungeon_crawler_game - Full Game Logic
 */


// --- 1. GLOBAL VARIABLES AND CONSTANTS ---
let isGlobalBattleLock = false; // Map interface lock

const roomNames = { 
    "B": "Battle", 
    "BOSS": "Boss", 
    "E": "Event", 
    "R": "Rest", 
    "S": "Shop" 
};
let currentHeroCache = null;

// Interface elements
const modalAuth = document.getElementById("modalAuth");
const btnSubmitAuth = document.getElementById("btnSubmitAuth");
const closeAuthBtn = document.getElementById("btnCloseAuth");

// --- 2. HELPER FUNCTIONS ---

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

// --- 3. HERO LOGIC ---

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

            updateNavigationUI(hero.current_room); // Update Floor/Room
            renderStats(hero);

            // NEW: CHECK FOR LOOT
            if (hero.pending_loot && hero.pending_loot.length > 0) {
                showPickLootModal(hero.pending_loot);
            }
            
            

        } else if (response.status === 404) {
            currentHeroCache = null;
            document.getElementById('statsContent').innerHTML = `
                <div class="panel-notice">
                    <p>You don't have a hero yet or they fell in battle.</p>
                    <button onclick="window.openCreateHeroModal()" class="primary-btn">Create Hero</button>
                </div>
            `;
            const controls = document.getElementById('movementControls');
            if (controls) controls.innerHTML = "";
        }
    } catch (error) {
        console.error("Critical load error:", error);
    }
}

function renderStats(hero) {
    const content = document.getElementById('statsContent');
    if (!content) return;

    const artifactsHtml = (hero.artifacts || []).map(art => 
        `<span class="item-tag rarity-${art.rarity}" title="${art.description}">${art.name}</span>`
    ).join(' ') || '<span style="color: #666;">Empty</span>';

    const spellsHtml = (hero.spells || []).map(spell => 
        `<span class="item-tag rarity-${spell.rarity}" title="${spell.description}">${spell.name}</span>`
    ).join(' ') || '<span style="color: #666;">No spells</span>';

    content.innerHTML = `
        <div class="stat-line"><span>Name:</span> <b>${hero.name}</b></div>
        <div class="stat-line"><span>Level:</span> <span>${hero.level}</span></div>
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
                                <div style="font-size: 0.8rem; color: var(--accent-color); margin-bottom: 5px;">Artifacts:</div>
                                <div class="items-container">${artifactsHtml}</div>
                            </div>

                            <div style="margin-top:10px;">
                                <div style="font-size: 0.8rem; color: var(--accent-color); margin-bottom: 5px;">Spells:</div>
                                <div class="items-container">${spellsHtml}</div>
                            </div>
    `;
}

// --- 4. MAP LOGIC ---

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

        // Hide everything by default
        if (restUI) restUI.style.display = 'none';
        if (shopUI) shopUI.style.display = 'none';
        if (movementUI) movementUI.style.display = 'flex';
        if (eventUI) eventUI.style.display = 'none';

        if (currentRoomType === "R") {
            if (restUI) restUI.style.display = 'flex';
            if (movementUI) movementUI.style.display = 'none';
        } 
        else if (currentRoomType === "S") {
            // WE'RE IN SHOP
            if (shopUI) shopUI.style.display = 'flex';
            if (movementUI) movementUI.style.display = 'none';
            loadShopCatalog(); // Load items from backend  
        }

        else if (currentRoomType === "E") {
            if (eventUI) eventUI.style.display = 'flex';
            if (movementUI) movementUI.style.display = 'none';
            // Delegate all checks to the event loading function itself
            loadCurrentEvent();
        }

        const currentFloor = data.hero_position.floor;
        const currentLane = data.hero_position.lane;

        // 1. Calculate next floor number (loop after 10)
        // If currentFloor = 10, then (10 % 10) + 1 = 1
        let nextFloorNum = (currentFloor % 10) + 1;

        // 2. Search data in map_preview
        // Check both formats: number 1 and string "F1"
        let nextFloorData = data.map_preview.find(f => 
            f.floor === `F${nextFloorNum}` || 
            f.floor === nextFloorNum ||
            f.floor === `F${currentFloor + 1}` // in case there are more than 10 floors
        );

        // 3. Protection: if we're on BOSS and next floor data still not found
        if (!nextFloorData && data.hero_position.room_type === "BOSS") {
            addLog("Path is clear! Transition to new cycle...");
            // Create virtual transition to floor 1 in center lane
            nextFloorData = { lanes: { "Center (1)": "B" } }; 
        }

        // 4. Rendering
        if (nextFloorData) {
            renderMovementButtons(currentLane, nextFloorData.lanes);
        } else {
            console.error("Could not find path forward!");
            // If everything is lost, give "Return to start" button manually
            const container = document.getElementById('movementControls');
            container.innerHTML = `<button class="move-btn" onclick="moveHero(1)">Start Path</button>`;
        }

        renderMovementButtons(currentLane, nextFloorData.lanes);
    } catch (error) {
        console.error("Map update error:", error);
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
            // Update stats (HP and Gold) so player sees result
            await loadHeroData(); 
        } else {
            addLog(`❌ Error: ${data.detail}`);
        }
    } catch (e) {
        console.error("Rest error:", e);
    }
};

// Same for "Continue" button
window.continueJourney = function() {
    const restUI = document.getElementById('restInterface');
    const movementUI = document.getElementById('movementControls');
    
    if (restUI && movementUI) {
        restUI.style.display = 'none';
        movementUI.style.display = 'block';
        addLog("⛺ You broke camp and continued your journey.");
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
            container.innerHTML = "<p>Goods are sold out.</p>";
            return;
        }

        data.items_for_sale.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.style = "border:  1px solid #777;  padding: 10px; border-radius: 5px; width: 200px; height: 80px; text-align: center; ";
            itemDiv.innerHTML = `
                <div style="font-weight: bold; margin-top: 10px;">${item.name}</div>
                <div style="color: #ffd700;">${item.cost} 🪙 </div>
                <button onclick="buyItem(${item.id})" style="margin-top: 5px; flex-end; cursor: pointer;">Buy</button>
            `;
            container.appendChild(itemDiv);
        });
    } catch (e) { console.error("Shop load error:", e); }
};

function updateNavigationUI(totalRooms) {
    if (totalRooms === undefined || totalRooms === null) return;

    const floor = (Math.floor(totalRooms / 10)) +1;
    const room = (totalRooms % 10) ;

    const floorElem = document.getElementById('displayFloor');
    const roomElem = document.getElementById('displayRoom');
    const progressElem = document.getElementById('floorProgressBar');
    const progressContainer = document.getElementById('progressContainer');

    // Show progress bar container
    if (progressContainer) progressContainer.style.display = 'block';

    if (floorElem && roomElem) {
        floorElem.textContent = floor;
        // If room 0 and we passed at least one room - this is 10th (Boss)
        const isBoss = (room === 0 && totalRooms > 0);
        roomElem.textContent = isBoss ? "10 (BOSS)" : room;
        roomElem.style.color = isBoss ? "#ff4444" : "var(--accent-color)";
    }

    if (progressElem) {
        // Calculate percentage
        let percentage = (room === 0 && totalRooms > 0) ? 100 : (room / 10) * 100;
        progressElem.style.width = percentage + "%";

        // Change color to red only if Boss, otherwise - main accent
        if (room === 0 && totalRooms > 0) {
            progressElem.style.backgroundColor = "#ff4444";
            progressElem.style.boxShadow = "0 0 15px #ff4444";
        } else {
            progressElem.style.backgroundColor = "var(--accent-color)";
            progressElem.style.boxShadow = "0 0 10px var(--accent-color)";
        }
    }
}

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
            await loadHeroData();     // Update stats (gold)
            await loadShopCatalog();  // Redraw items (so purchased disappears)
        } else {
            addLog(`❌ Shop error: ${data.detail}`);
        }
    } catch (e) { console.error("Purchase error:", e); }
};

window.continueJourneyFromShop = function() {
    document.getElementById('shopInterface').style.display = 'none';
    document.getElementById('movementControls').style.display = 'block';
    addLog("You said goodbye to the merchant and moved on.");
};


function renderMovementButtons(currentLane, nextLanes) {
    const controls = document.getElementById('movementControls');
    controls.innerHTML = ''; 
    const directions = [
        { label: "Left", lane: currentLane - 1 },
        { label: "Center", lane: currentLane },
        { label: "Right", lane: currentLane + 1 }
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

        if (response.ok) 
            {
            updateDungeonUI(data.current_floor, data.room_type);

            if (data.monster) {
                document.getElementById('monsterName').textContent = data.monster.name;
                const currentHp = data.monster.current_hp !== undefined ? data.monster.current_hp : data.monster.hp;
                updateMonsterUI(`${currentHp}/${data.monster.max_hp}`);
            }
            
            addLog(`You entered the room. ${data.event || ""}`);
            await loadHeroData();
            await updateMap(); 
        } else {
            
            if (response.status === 400) {
                addLog(`Path blocked: ${data.detail}`);
                // FORCE refresh hero data to enable battle mode
                await loadHeroData(); 
            } else {
                addLog(`Error: ${data.detail}`);
            }
        }
    } catch (e) { 
        console.error("Movement error:", e); 
    }
}

// --- 5. BATTLE LOGIC ---

function showDeathScreen(heroName) {
    const modal = document.getElementById('modalDeath');
    const msg = document.getElementById('deathMessage');
    if (modal && msg) {
        msg.textContent = `Hero ${heroName} fell bravely in battle with the monster.`;
        modal.style.display = 'block';
        
        // Close other windows
        if (typeof modalAuth !== 'undefined') modalAuth.style.display = "none";
        const lootModal = document.getElementById('modalLoot');
        if (lootModal) lootModal.style.display = 'none';
        
        // Clear ONLY hero data, NOT account
        // localStorage.removeItem('heroData'); // If you store hero cache separately
        // DON'T touch token to avoid logging out
    }
}

function showBattleMode(isBattle) {
    const battleUI = document.getElementById('battleInterface');
    const navigationUI = document.getElementById('navigationBlock');
    
    isGlobalBattleLock = isBattle; // Set lock

    if (isBattle) {
        battleUI.style.display = 'block';
        navigationUI.style.display = 'none';
        renderBattleSpells();
        // ... your monster rendering code ...
    } else {
        battleUI.style.display = 'none';
        navigationUI.style.display = 'block';
    }
}



function updateMonsterUI(hpData) {
    if (hpData === undefined || hpData === null) return;
    
    let current, max;
    
    // If passed string "5/10"
    if (typeof hpData === 'string' && hpData.includes('/')) {
        [current, max] = hpData.split('/').map(Number);
    } 
    // If passed just current HP, max HP from cache
    else if (currentHeroCache && currentHeroCache.active_monster) {
        current = Number(hpData);
        max = currentHeroCache.active_monster.max_hp;
    } else {
        return; // Not enough data to update
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
    
    container.innerHTML = ''; // Clear old buttons

    // Get spells array from hero cache
    const spells = currentHeroCache.spells || [];

    if (spells.length === 0) {
        container.innerHTML = '<p style="font-size: 0.8rem; color: #666;">No spells learned</p>';
        return;
    }

    spells.forEach(spell => {
        const btn = document.createElement('button');
        btn.className = 'spell-btn';
        
        // Check if enough mana
        const canCast = currentHeroCache.mp >= spell.mp_cost;
        
        btn.innerHTML = `
            <span class="spell-name">${spell.name}</span>
            <span class="spell-cost">${spell.mp_cost} MP</span>
        `;
        
        btn.disabled = !canCast;
        btn.title = spell.description || "";

        // On click call cast function
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

        // 1. Output logs to general chat
        if (data.log) data.log.forEach(msg => addLog(msg));

        // 2. HERO DEATH
        if (data.status === "defeat") {
            showDeathScreen(data.hero_name || "Your hero");
            return;
        }

        // 3. VICTORY OVER MONSTER
        if (data.status === "victory") {
            updateMonsterUI("0/1"); 
            // Reset enemy text
            document.getElementById('monsterName').textContent = "Enemy"; 
            document.getElementById('monsterHpText').textContent = "HP: 0/0";

            showBattleMode(false); // Hide battle buttons
            
            // Show loot modal (only on victory!)
            const victoryMsg = data.log ? data.log[data.log.length - 1] : "Victory!";
            showLootModal(victoryMsg);
            
            await loadHeroData(); // Update gold/XP in UI
            return;
        }

        // 4. BATTLE CONTINUES (ongoing)
        if (data.status === "ongoing") {
            updateMonsterUI(data.monster_hp);
            // If hero data in response, update their HP bar
            if (data.hero_hp) {
                // Assuming you have renderStats or similar function
                await loadHeroData(); 
            }
        }

    } catch (e) { 
        console.error("Attack error:", e); 
        addLog("Server connection error");
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

        // 1. Battle logs (damage, misses) — always write to general game log
        if (data.log) {
            data.log.forEach(msg => addLog(msg));
        }

        // 2. Hero death — show mourning window
        if (data.status === "defeat") {
            showDeathScreen(data.hero_name || "Your hero");
            return; 
        }

        if (response.ok) {
            // 3. Update hero stats (mana spent, HP decreased)
            if (data.hero) {
                // Keep spell/artifacts cache
                if ((!data.hero.spells || data.hero.spells.length === 0) && currentHeroCache.spells) {
                    data.hero.spells = currentHeroCache.spells;
                }
                currentHeroCache = data.hero;
                renderStats(currentHeroCache);
            }

            // 4. REAL VICTORY
            if (data.status === "victory") {
                updateMonsterUI("0/1"); 
                showBattleMode(false); // Hide battle interface
                
                // Show loot window ONLY HERE
                const victoryMsg = data.log ? data.log[data.log.length - 1] : "Victory!";
                showLootModal(victoryMsg);
                
                await loadHeroData();
                return; // Exit function
            }

            // 5. BATTLE CONTINUES
            // If we're here - nobody died. Just update HP bars.
            if (data.monster_hp) {
                updateMonsterUI(data.monster_hp);
            }
            
            renderBattleSpells(); // Update buttons (in case mana ran out)
        }
    } catch (e) { 
        console.error("Cast error:", e); 
    }
}

function updateDungeonUI(floor, type) {
    const floorElem = document.getElementById('floorNumber');
    const typeElem = document.getElementById('roomTypeLabel');
    
    if (!floorElem || !typeElem) return;

    floorElem.textContent = floor;

    // Type mapping from your Python code
    const typeNames = {
        'B': 'CRYPT (BATTLE)',
        'S': 'MERCHANT SHOP',
        'R': 'REST',
        'E': 'UNKNOWN',
        'BOSS': 'BOSS HALL'
    };

    typeElem.textContent = typeNames[type] || 'EXPLORATION';
    
    // Optionally: change color based on danger
    if (type === 'BOSS') typeElem.style.color = '#ff4444';
    else if (type === 'S') typeElem.style.color = '#ffd700';
    else if (type === 'R') typeElem.style.color = '#44ff44';
    else typeElem.style.color = 'var(--accent-color)';
}


function showLootModal(message) {
    const modal = document.getElementById('modalLoot');
    const resultDiv = document.getElementById('lootResult');
    
    if (modal && resultDiv) {
        resultDiv.textContent = message;
        modal.style.display = 'block';
    }
    
    // Hide battle interface since enemy is defeated
    showBattleMode(false); 
}

// --- 6. AUTH AND INITIALIZATION ---

function updateUI() {
    const token = localStorage.getItem('token');
    const guestBlock = document.getElementById('guestBlock');
    const userBlock = document.getElementById('userBlock');
    
    
    if (token) {
        
        guestBlock.style.display = 'none';
        userBlock.style.display = 'flex';
        document.getElementById('playerName').textContent = formatHeroName(localStorage.getItem('username'));
        
        
        // Instead of just loadHeroData() we run our bundle:
        checkHeroAndInit(); 
        
    } else {
        guestBlock.style.display = 'block';
        userBlock.style.display = 'none';
    }
}

// Auth form handling
btnSubmitAuth?.addEventListener('click', async () => {
    const mode = document.getElementById('modalTitle').textContent;
    const username = document.getElementById('authUsername').value;
    const password = document.getElementById('authPassword').value;
    
    if (mode === "Register") {

        
        const usernameRegex = /^[\x00-\x7F]{5,}$/;
        
        const passwordRegex = /^[\x00-\x7F]{6,}$/;

        if (!usernameRegex.test(username)) {
            showAuthMessage("Account name: Latin only, minimum 5 character");
            return;
        }

        if (!passwordRegex.test(password)) {
            showAuthMessage("Password: Latin/numbers, minimum 6 characters");
            return;
        }



        const res = await fetch('http://127.0.0.1:8000/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (res.ok) {
            // Instead of "Please login", immediately call login
            await loginUser(username, password);
        } else {
            const d = await res.json();
            showAuthMessage(d.detail || "Registration error");
        }
    } else {
        // Regular login
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
        
        // 1. Update UI (login/logout buttons)
        updateUI(); 
        
        // 2. Check for hero existence
        await checkHeroAndInit();
    } else {
        showAuthMessage("Login error after registration");
    }
}


// Modal events
document.getElementById('btnLogin')?.addEventListener('click', () => {
    document.getElementById('modalTitle').textContent = "Login";
    modalAuth.style.display = "block";
});
document.getElementById('btnRegister')?.addEventListener('click', () => {
    document.getElementById('modalTitle').textContent = "Register";
    modalAuth.style.display = "block";
});
document.getElementById('btnLogout')?.addEventListener('click', () => {
    localStorage.clear();
    location.reload();
});
if (closeAuthBtn) {
    closeAuthBtn.onclick = () => modalAuth.style.display = "none";
}

// Also close auth modal when clicking outside
document.getElementById('modalAuth').addEventListener('click', function(e) {
    if (e.target === this) {
        this.style.display = "none";
    }
});

// Global functions for HTML
window.openCreateHeroModal = () => document.getElementById('modalCreateHero').style.display = 'block';
window.sendAttack = sendAttack;
window.closeLootModal = async () => {
    document.getElementById('modalLoot').style.display = 'none';
    // Force false so updateMap doesn't get blocked
    isGlobalBattleLock = false; 
    await updateMap(); 
};
window.openUpgradeModal = () => {
    document.getElementById('modalUpgrade').style.display = 'block';
    renderUpgradeOptions();
};

// --- 7. UPGRADE AND CREATION ---

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
    } catch (e) { console.log(e); }
}

async function checkHeroAndInit() {
    const token = localStorage.getItem('token');
    try {
        const res = await fetch('http://127.0.0.1:8000/heroes/me', { // Assuming you have such endpoint
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.status === 404 || (res.ok && !(await res.json()))) {
            // If no hero — open creation modal
            window.openCreateHeroModal();
        } else {
            // If hero exists — load game
            await loadHeroData();
            await updateMap();
        }
    } catch (e) {
        console.error("Error checking hero:", e);
    }
}

function renderUpgradeOptions() {
    const hero = currentHeroCache;
    if (!hero) return;

    document.getElementById('availablePoints').textContent = hero.stat_points;
    const list = document.getElementById('upgradeList');

    // Add 'field' property that corresponds to key in hero object
    const stats = [
        {k:'str', l:'Strength', field: 'strength'}, 
        {k:'agi', l:'Agility', field: 'agility'}, 
        {k:'vit', l:'Vitality', field: 'vitality'}, 
        {k:'int', l:'Intelligence', field: 'intelligence'}, 
        {k:'dex', l:'Dexterity', field: 'dexterity'}
    ];

    list.innerHTML = stats.map(s => {
        // Get current value from cache. 
        // If data didn't come, set 0 to avoid undefined
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
// Open create hero modal
window.openCreateHeroModal = function() {
    const modal = document.getElementById('modalCreateHero');
    if (modal) {
        modal.style.display = 'block';
    } else {
        console.error("Modal modalCreateHero not found in HTML!");
    }
};

// Close create hero modal
window.closeCreateHeroModal = function() {
    document.getElementById('modalCreateHero').style.display = 'none';
};

// Creation confirmation function (bound to button in modal)
document.getElementById('btnConfirmCreate')?.addEventListener('click', async () => {
    const nameInput = document.getElementById('newHeroName');
    const name = nameInput ? nameInput.value : "";
    const token = localStorage.getItem('token');

    if (!name) {
        alert("Enter hero name!");
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/heroes/create?name=${encodeURIComponent(name)}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            addLog(`Hero ${name} created successfully!`);
            window.closeCreateHeroModal();
            // Immediately update data and map
            await loadHeroData();
            await updateMap();
        } else {
            const data = await response.json();
            alert(data.detail || "Error creating hero");
        }
    } catch (error) {
        console.error("Create request error:", error);
        alert("Server not responding");
    }
});

function showPickLootModal(lootItems) {
    const modal = document.getElementById('modalPickLoot');
    const container = document.getElementById('pendingLootContainer');
    if (!modal || !container) return;

    container.innerHTML = ''; // Clear old buttons

    lootItems.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'loot-choice-btn';
        btn.style.padding = '10px';
        btn.style.cursor = 'pointer';
        
        const typeLabel = item.type === 'artifact' ? 'Artifact' : 'Spell';
        btn.innerHTML = `<b>${item.name}</b><br><small style="color:#aaa;">${typeLabel}</small>`;
        btn.title = item.description || "Description hidden";
        
        // On click send request
        btn.onclick = () => sendPickLoot(item.type, item.id);
        
        container.appendChild(btn);
    });

    modal.style.display = 'block';
}

// Function to send choice to backend
async function sendPickLoot(choiceType, choiceId) {
    const token = localStorage.getItem('token');
    try {
        // Make sure URL is correct (if router has /battle prefix, add it)
        const response = await fetch(`http://127.0.0.1:8000/world/pick_loot?choice_type=${choiceType}&choice_id=${choiceId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('modalPickLoot').style.display = 'none';
            addLog(`Reward received: ${data.message}`);
            await loadHeroData(); // Update stats with new artifact
        } else {
            alert("Choice error: " + data.detail);
        }
    } catch (e) {
        console.error("Loot selection error:", e);
    }
}

window.continueJourney = function() {
    document.getElementById('restInterface').style.display = 'none';
    document.getElementById('movementControls').style.display = 'block';
    addLog("You left the cozy camp and moved on.");
};

// Requests event data and generates buttons
window.loadCurrentEvent = async function() {
    const token = localStorage.getItem('token');
    try {
        const response = await fetch('http://127.0.0.1:8000/world/current_event', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            // BUGFIX: If server returned 400 or 404 (event already completed),
            // we just hide event window and show movement buttons!
            document.getElementById('eventInterface').style.display = 'none';
            document.getElementById('movementControls').style.display = 'flex'; // Or 'grid'
            return; 
        }
        
        const data = await response.json();

        // Fill texts
        document.getElementById('eventName').textContent = data.name;
        document.getElementById('eventDescription').textContent = data.description;
        
        // Clear old buttons
        const container = document.getElementById('eventChoicesContainer');
        container.innerHTML = '';
        
        // Create new
        data.choices.forEach(choice => {
            const btn = document.createElement('button');
            btn.textContent = choice.text;
            btn.style = "background: #9c27b0; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 80%; max-width: 300px; font-weight: bold;";
            btn.onclick = () => resolveEvent(choice.value); 
            container.appendChild(btn);
        });

    } catch (e) { console.error("Event load error:", e); }
};

// Sends decision to server
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
            await loadHeroData(); // Update stats (e.g., if +Strength given)
            
            // Event completed, return movement buttons
            document.getElementById('eventInterface').style.display = 'none';
            document.getElementById('movementControls').style.display = 'block';
        } else {
            addLog(`❌ Error: ${data.detail}`);
        }
    } catch (e) { console.error("Choice error:", e); }
};

function handleRebirth() {
    // Just reload the page. 
    // Script on startup will see token, won't find hero, and open creation.
    location.reload();
}


// --- 8. HIGH SCORES ---

window.showHighScores = async function() {
    const modal = document.getElementById('modalHighScores');
    const container = document.getElementById('highScoresList');
    if (!modal || !container) return;

    modal.style.display = 'block';
    container.innerHTML = '<p style="text-align: center;">Loading legends...</p>';

    try {
        const response = await fetch('http://127.0.0.1:8000/highscore/');
        if (!response.ok) throw new Error("Load error");
        
        const scores = await response.json();
        
        if (scores.length === 0) {
            container.innerHTML = '<p style="text-align: center;">Chronicles are still empty. Be the first!</p>';
            return;
        }

        let html = `
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: monospace;">
                <thead>
                    <tr style="border-bottom: 2px solid var(--accent-color); color: var(--accent-color);">
                        <th style="padding: 10px;">Player</th>
                        <th style="padding: 10px;">Hero</th>
                        <th style="padding: 10px;">Lvl</th>
                        <th style="padding: 10px;">Floor</th>
                        <th style="padding: 10px;">Gold</th>
                        <th style="padding: 10px;">Date</th>
                    </tr>
                </thead>
                <tbody>
        `;

        scores.forEach(s => {
            html += `
                <tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 10px;">${s.username}</td>
                    <td style="padding: 10px; color: #fff;">${s.hero_name}</td>
                    <td style="padding: 10px;">${s.level}</td>
                    <td style="padding: 10px; color: var(--accent-color);">${s.floor}</td>
                    <td style="padding: 10px; color: #ffd700;">${s.gold}</td>
                    <td style="padding: 10px; font-size: 0.8rem; color: #888;">${s.date}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;

    } catch (e) {
        container.innerHTML = `<p style="text-align: center; color: #ff5555;">Could not load scores: ${e.message}</p>`;
    }
}

// Close highscores modal handler
document.getElementById('btnCloseHighScores')?.addEventListener('click', () => {
    document.getElementById('modalHighScores').style.display = 'none';
});


function formatHeroName(name) {
    if (!name) return "";
    
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
}

// Start
updateUI();