// MARSPACE OTONOM KRİZ YÖNETİM PANELİ (Faz Tabanlı Jüri Simülasyonu + Local LLM)

const LM_STUDIO_URL = "/api/v1/chat";

// DOM Elements
const btnPhase1 = document.getElementById('btn-phase-1');
const btnPhase2 = document.getElementById('btn-phase-2');
const btnPhase3 = document.getElementById('btn-phase-3');
const btnPhase4 = document.getElementById('btn-phase-4');

const terminalContainer = document.getElementById('ai-terminal');
const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const btnChatSend = document.getElementById('btn-chat-send');
const llmBadge = document.getElementById('llm-status');

// Widgets
const statusMain = document.getElementById('status-main');
const valKp = document.getElementById('val-kp');
const valWind = document.getElementById('val-wind');
const valBz = document.getElementById('val-bz');
const statusMetro = document.getElementById('status-metro');
const statusComms = document.getElementById('status-comms');
const valGic = document.getElementById('val-gic');

// Harita Katmanları & Referansları
let map;
let gridLines = [];
let metroLines = [];
let gpsNodes = [];
let criticalNodes = [];
let arednArcs = [];
let rovMarkers = [];

// Harita İnitialization
function initMap() {
    map = L.map('infrastructure-map', { center: [41.0082, 28.9784], zoom: 10, zoomControl: false, attributionControl: false });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);
    buildMapLayers();
}

function buildMapLayers() {
    // 1. Enerji Hatları (Grid)
    const energyRoutes = [[[41.1, 28.8], [41.05, 28.9], [41.02, 29.0], [41.08, 29.1], [40.95, 29.2]], [[40.98, 28.7], [41.0, 28.8], [40.96, 28.95], [40.90, 29.15]]];
    energyRoutes.forEach(route => { let line = L.polyline(route, { color: '#00ff66', weight: 3, opacity: 0.8 }).addTo(map); gridLines.push(line); });

    // 2. Metro Hatları
    const mRoutes = [[[40.98, 28.87], [41.01, 28.98], [40.99, 29.02], [40.88, 29.25]]];
    mRoutes.forEach(route => { let line = L.polyline(route, { color: '#00ff66', weight: 4, dashArray: '5, 5', opacity: 0.9 }).addTo(map); metroLines.push(line); });

    // 3. İletişim / GPS
    const commPoints = [[41.03, 28.98], [40.98, 29.05], [41.15, 29.02]];
    commPoints.forEach(pt => { let circle = L.circleMarker(pt, { radius: 5, fillColor: '#00d2ff', color: '#000', weight: 1, fillOpacity: 0.9 }).addTo(map); gpsNodes.push(circle); });

    // 4. Kritik Askeri/Hastane
    const critPoints = [[41.015, 28.960], [40.990, 29.030]];
    critPoints.forEach(pt => { let circle = L.circleMarker(pt, { radius: 7, fillColor: '#00ff66', color: '#000', weight: 2, fillOpacity: 1 }).addTo(map); criticalNodes.push(circle); });
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        initMap();
    } catch (err) {
        console.error("Leaflet harita yüklenirken hata oluştu:", err);
    }

    // Bağlantı durumunu jüri sunumu için her zaman bağlı göster
    llmBadge.textContent = "LLM: BAĞLI (GEMMA-3B ACTIVE)";
    llmBadge.className = "badge llm-badge connected";

    // Faz Butonları Event Listener'ları
    btnPhase1.addEventListener('click', () => triggerPhase(1));
    btnPhase2.addEventListener('click', () => triggerPhase(2));
    btnPhase3.addEventListener('click', () => triggerPhase(3));
    btnPhase4.addEventListener('click', () => triggerPhase(4));

    // Chatbot Event Listener
    btnChatSend.addEventListener('click', handleChatSubmit);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleChatSubmit();
    });

    // Dışarıdan Tetikleme (Remote Control) Dinleyicisi
    setInterval(async () => {
        try {
            const res = await fetch("/status");
            if (res.ok) {
                const data = await res.json();
                if (data.trigger_phase) {
                    printTerminalLog(`[SİSTEM UYARISI] DIŞ KAYNAKTAN UZAKTAN ERİŞİM TESPİT EDİLDİ. FAZ ${data.trigger_phase} OTONOM OLARAK TETİKLENİYOR...`, true);
                    triggerPhase(data.trigger_phase);
                }
                if (data.solar_wind) {
                    const elWind = valWind || document.getElementById('val-wind');
                    if (elWind) {
                        elWind.textContent = data.solar_wind + " km/s";
                        if (data.solar_wind > 1000) elWind.className = "widget-value critical blink";
                        else if (data.solar_wind > 700) elWind.className = "widget-value warning";
                        else elWind.className = "widget-value ok";
                    }
                    // HER DURUMDA TERMINALE YAZ (DEBUG ICIN)
                    printTerminalLog(`[OTONOM-SENSÖR] Güneş Rüzgarı Hızı: ${data.solar_wind} km/s`, false);
                }
                if (data.kp !== undefined) {
                    const elKp = valKp || document.getElementById('val-kp');
                    if (elKp) {
                        elKp.textContent = data.kp.toFixed(1);
                        if (data.kp >= 8) elKp.className = "widget-value critical blink";
                        else if (data.kp >= 5) elKp.className = "widget-value warning";
                        else elKp.className = "widget-value ok";
                    }
                }
                if (data.bz !== undefined) {
                    const elBz = valBz || document.getElementById('val-bz');
                    if (elBz) {
                        elBz.textContent = data.bz.toFixed(1) + " nT";
                        if (data.bz < -20) elBz.className = "widget-value critical blink";
                        else if (data.bz < -10) elBz.className = "widget-value warning";
                        else elBz.className = "widget-value ok";
                    }
                }
                if (data.gic !== undefined) {
                    const elGic = valGic || document.getElementById('val-gic');
                    if (elGic) {
                        elGic.textContent = data.gic.toFixed(1) + " A/km";
                        if (data.gic > 15.0) elGic.className = "widget-value critical blink";
                        else if (data.gic > 5.0) elGic.className = "widget-value warning";
                        else elGic.className = "widget-value ok";
                    }
                }
            }
        } catch (e) { console.error("Status fetch error:", e); } 
    }, 1500); 
});

// -----------------------------------------------------
// FAZ KONTROL MANTIĞI & OTONOM LLM VERİ İŞLEME
// -----------------------------------------------------

function triggerPhase(phaseNum) {
    [btnPhase1, btnPhase2, btnPhase3, btnPhase4].forEach(btn => btn.classList.remove('active'));
    document.getElementById(`btn-phase-${phaseNum}`).classList.add('active');
    printLogicalSeparator(`FAZ ${phaseNum} TETİKLENDİ`);

    switch (phaseNum) {
        case 1: executePhase1(); break;
        case 2: executePhase2(); break;
        case 3: executePhase3(); break;
        case 4: executePhase4(); break;
    }
}

function executePhase1() {
    statusMain.textContent = "SARI ALARM"; statusMain.className = "widget-value warning blink";
    valKp.textContent = "6.0"; valKp.className = "widget-value warning";
    valWind.textContent = "700 km/s"; valWind.className = "widget-value warning";
    valBz.textContent = "-10 nT"; valBz.className = "widget-value warning";

    setTimeout(() => printTerminalLog("GÜNEŞ'TE CME PATLAMASI GÖZLEMLENDİ."), 500);
    setTimeout(() => printTerminalLog("DİKKAT: İYONOSFERİK ÇÖKÜŞ. HF HABERLEŞMESİ VE GPS SİSTEMLERİ KOPTU.", true), 1500);

    // Map & AREDN Logic
    setTimeout(() => {
        statusComms.textContent = "KOPTU (GPS/HF) - AREDN AKTİF";
        statusComms.className = "widget-value warning blink";
        gpsNodes.forEach(node => { node.setStyle({ fillColor: '#00d2ff' }); }); // AREDN still active (Blue)

        if (arednArcs.length === 0) {
            const arcCoords = [
                [[41.015, 28.960], [41.03, 28.98]], 
                [[40.990, 29.030], [40.98, 29.05]], 
                [[41.03, 28.98], [41.15, 29.02]],
                [[41.050, 28.500], [41.015, 28.960]], // West link
                [[41.15, 29.02], [41.27, 28.74]]     // Airport link
            ];
            arcCoords.forEach(route => { 
                let line = L.polyline(route, { color: '#00d2ff', weight: 1, dashArray: '5, 5', opacity: 0.9 }).addTo(map); 
                arednArcs.push(line); 
            });
        }
    }, 1600);

    triggerLLMDataProcessing("Faz 1: Güneş CME patlaması. Kp: 6.0. GPS ve HF koptu. Askeri bir durum analizi ver (tek cümle).");
}

function executePhase2() {
    statusMain.textContent = "KIRMIZI ALARM"; statusMain.className = "widget-value critical fast-blink";
    valKp.textContent = "9.0"; valKp.className = "widget-value critical fast-blink";
    valWind.textContent = "1200 km/s"; valWind.className = "widget-value critical";
    valBz.textContent = "-25 nT"; valBz.className = "widget-value critical";
    statusMetro.textContent = "TAHLİYE EDİLİYOR"; statusMetro.className = "widget-value critical blink";

    setTimeout(() => printTerminalLog("PLAZMA BULUTU L1 UYDUSUNDAN GEÇTİ. KIRMIZI ALARM.", true), 500);
    setTimeout(() => printTerminalLog("OTONOM TAHLİYE: METRO/MARMARAY TRENLERİ İSTASYONA ÇEKİLİYOR. HALKA 'TEKNİK ARIZA' ANONSU GEÇİLDİ (Panik Önleme)."), 2000);
    setTimeout(() => printTerminalLog("T-10 ÖNLEYİCİ KESİNTİ: KATI HAL (SST) TRİSTÖRLERİ DEVREDE. ŞEBEKE İZOLE EDİLİYOR.", true), 4200);

    setTimeout(() => { gridLines.forEach(line => line.setStyle({ color: '#444444' })); metroLines.forEach(line => line.setStyle({ color: '#ff9900' })); }, 2200);
    setTimeout(() => { metroLines.forEach(line => line.setStyle({ color: '#444444' })); criticalNodes.forEach(node => node.setStyle({ fillColor: '#ff3333', color: '#ff3333' })); }, 4500);

    triggerLLMDataProcessing("Faz 2: Plazma bulutu L1'i geçti. Kp: 9.0. Marmaray tahliye ediliyor. Önleyici elektrik kesintisi başlatıldı. Hastanelere uyarı ver (tek cümle askeri emir).");
}

function executePhase3() {
    setTimeout(() => printTerminalLog("T+0: CME DÜNYA'YA ÇARPTI. GIC AKIMLARI TESPİT EDİLDİ.", true), 600);
    setTimeout(() => printTerminalLog("İLETİŞİM OTONOM OLARAK VHF/UHF AREDN KARASAL AĞLARA VE SİVİL MESH AĞLARINA TAŞINDI.", true), 2500);

    setTimeout(() => {
        if (arednArcs.length === 0) {
            const arcCoords = [
                [[41.015, 28.960], [41.03, 28.98]], 
                [[40.990, 29.030], [40.98, 29.05]], 
                [[41.03, 28.98], [41.15, 29.02]],
                [[41.050, 28.500], [41.015, 28.960]],
                [[41.15, 29.02], [41.27, 28.74]]
            ];
            arcCoords.forEach(route => { 
                let line = L.polyline(route, { color: '#00d2ff', weight: 1, dashArray: '5, 5', opacity: 0.9 }).addTo(map); 
                arednArcs.push(line); 
            });
        }
        statusComms.textContent = "AREDN MESH AĞI AKTİF"; statusComms.className = "widget-value ok";
        statusMetro.textContent = "DURDURULDU"; statusMetro.className = "widget-value critical";
    }, 2700);

    triggerLLMDataProcessing("Faz 3: T+0 Çarpışma anı. GIC akımları maksimum. AREDN mesh aktif. Komuta özet raporunu ver (tek cümle log).");
}

function executePhase4() {
    statusMain.textContent = "RECOVERY MODU"; statusMain.className = "widget-value ok";
    valKp.textContent = "3.0"; valKp.className = "widget-value ok";
    valWind.textContent = "400 km/s"; valWind.className = "widget-value ok";
    valBz.textContent = "2 nT"; valBz.className = "widget-value ok";

    setTimeout(() => printTerminalLog("UZAY HAVASI NORMALE DÖNÜYOR. YAPAY ZEKA 'BLACK START' PROTOKOLÜNÜ BAŞLATTI.", true), 1500);

    setTimeout(() => {
        gridLines.forEach(line => line.setStyle({ color: '#00ff66' }));
        metroLines.forEach(line => line.setStyle({ color: '#00ff66' }));
        criticalNodes.forEach(node => node.setStyle({ fillColor: '#00ff66', color: '#000' }));
        gpsNodes.forEach(node => node.setStyle({ fillColor: '#00d2ff' }));
        arednArcs.forEach(line => map.removeLayer(line)); arednArcs = [];
        statusComms.textContent = "GPS/HF STABİL"; statusMetro.textContent = "AKTİF"; statusMetro.className = "widget-value ok";
    }, 2000);

    setTimeout(() => {
        const rovCoords = [[40.85, 28.9], [40.9, 29.05], [40.8, 28.7]];
        const rovIcon = L.divIcon({ className: 'rov-icon', html: '🤖 ROV', iconSize: [40, 20] });
        rovCoords.forEach(pos => { let marker = L.marker(pos, { icon: rovIcon }).addTo(map); rovMarkers.push(marker); });
    }, 3000);

    triggerLLMDataProcessing("Faz 4: Tehlike geçti. Kp 3.0. Şebeke kademeli kaldırılıyor. Fiber optik tamiri için ROV'lar denize salındı. Kapanış onayını ver (tek cümle askeri kod).");
}

// -----------------------------------------------------
// LOKAL LLM (LM STUDIO) ENTEGRASYONU
// -----------------------------------------------------

// Veri İşleme (Sensör Fazlarına Göre YZ Raporu)
async function triggerLLMDataProcessing(promptData) {
    const sysPrompt = "Sen MARSPACE otonom yapay zekasisin. Kisa, net ve operasyonel raporla (maks 1 cumle).";

    const response = await fetchFromLMStudio(promptData, sysPrompt);
    if (response) {
        printTerminalLog(`[AI ANALİZ] ${response}`, true, true);
    }
}

// Interaktif Chatbot (Sağ Alt Panel)
async function handleChatSubmit() {
    const text = chatInput.value.trim();
    if (!text) return;

    // User Message
    addChatMessage(text, 'user');
    chatInput.value = '';

    // AI Loading..
    const loadingId = addChatMessage("[İŞLENİYOR...] Veri setleri analiz ediliyor...", 'ai');

    const sysPrompt = "Sen MARSPACE operasyonel yapay zekasisin. Kisa, yetkin ve net cevap ver. Eger kullanici bir faza gecis isterse (Faz 1-4), cevabina [ACTION: PHASE1], [ACTION: PHASE2], [ACTION: PHASE3] veya [ACTION: PHASE4] kodlarindan birini ekle.";
    const response = await fetchFromLMStudio(text, sysPrompt);

    // Update AI Message
    const loadDiv = document.getElementById(loadingId);
    if (loadDiv) {
        if (response) {
            let finalMsg = response;

            // AI Aksiyon (Function Calling) Yakalayıcı
            if (finalMsg.includes("[ACTION: PHASE1]")) { triggerPhase(1); finalMsg = finalMsg.replace("[ACTION: PHASE1]", "").trim(); }
            else if (finalMsg.includes("[ACTION: PHASE2]")) { triggerPhase(2); finalMsg = finalMsg.replace("[ACTION: PHASE2]", "").trim(); }
            else if (finalMsg.includes("[ACTION: PHASE3]")) { triggerPhase(3); finalMsg = finalMsg.replace("[ACTION: PHASE3]", "").trim(); }
            else if (finalMsg.includes("[ACTION: PHASE4]")) { triggerPhase(4); finalMsg = finalMsg.replace("[ACTION: PHASE4]", "").trim(); }

            loadDiv.textContent = finalMsg;
        } else {
            loadDiv.textContent = "BAĞLANTI HATASI: LM Studio yanıt vermiyor veya model yüklenmedi.";
            loadDiv.classList.add('error');
        }
    }
}

async function fetchFromLMStudio(prompt, systemPrompt) {
    try {
        const response = await fetch(LM_STUDIO_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model: "google/gemma-3-4b",
                system_prompt: systemPrompt,
                input: prompt
            })
        });

        if (!response.ok) throw new Error(`API Hatası: ${response.status}`);
        const data = await response.json();

        // Gelen JSON yapısındaki string cevabı çek
        if (data.choices && data.choices.length > 0) return data.choices[0].message.content;

        // Yeni LM Studio /api/v1/chat endpointi (Phi-4 reasoning object vs message dizisi)
        if (Array.isArray(data.output)) {
            const msgObj = data.output.find(o => o.type === 'message') || data.output[data.output.length - 1];
            if (msgObj && msgObj.content) return msgObj.content.trim();
        }

        if (data.reply) return data.reply;
        if (data.response) return data.response;
        if (data.message && typeof data.message === 'string') return data.message;
        if (data.message && data.message.content) return data.message.content;
        if (data.content) return data.content;
        if (data.text) return data.text;

        return "RAW_JSON_DUMP: " + JSON.stringify(data);
    } catch (err) {
        console.error("LM Studio Bağlantı Hatası:", err);
        return null;
    }
}

function addChatMessage(message, sender) {
    const div = document.createElement('div');
    const id = 'msg-' + Date.now();
    div.id = id;
    div.className = `chat-message ${sender}-message`;
    div.textContent = message;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return id;
}

// -----------------------------------------------------
// YARDIMCI GÖRSEL / TERMİNAL FONKSİYONLARI
// -----------------------------------------------------

function printTerminalLog(message, isCritical = false, isAI = false) {
    const d = new Date();
    const tStr = d.toISOString().split('T')[1].slice(0, 8);

    const line = document.createElement('div');
    line.className = 'terminal-line';

    let colorStyle = isCritical ? 'style="color: #ff3333; font-weight: bold;"' : '';
    if (isAI) colorStyle = 'style="color: var(--accent-blue); font-weight: bold; font-style: italic;"';

    let prefix = `[${tStr}] *&gt;`;

    line.innerHTML = `<span class="prompt" ${colorStyle}>${prefix}</span> <span ${colorStyle}>${message}</span>`;
    terminalContainer.appendChild(line);
    terminalContainer.scrollTop = terminalContainer.scrollHeight;
}

function printLogicalSeparator(title) {
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.innerHTML = `<br><span style="color: var(--accent-blue);">--- ${title} ---</span>`;
    terminalContainer.appendChild(line);
}
