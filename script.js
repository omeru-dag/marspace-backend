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

                // --- SENARYO TELEMETRİSİ ARAYÜZDEN OTONOM YÖNETİLİYOR ---
                // Arka plandaki eski rastgele sensör test verilerinin (simulate_sensor) 
                // arayüzdeki animasyonları (crisisInterval vb.) ezmemesi için dışarıdan 
                // telemetri güncellemeleri iptal edildi. Sadece dışarıdan faz tetiklemeleri dinlenir.
                
                if (data.solar_wind > 1000 || data.kp > 7) {
                    // Log basıyorduk ama artık UI mantığına bıraktık.
                }
            }
        } catch (e) { console.error("Status fetch error:", e); } 
    }, 1500); 

    // --- SESLİ KOMUT (WHISPER CPP) MANTIĞI ---
    let audioContext;
    let processor;
    let input;
    let audioData = [];
    let isRecording = false;

    const micBtn = document.getElementById('btn-mic-toggle');
    const micStatus = document.getElementById('mic-status-text');

    if (micBtn) {
        micBtn.onclick = async () => {
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
                    input = audioContext.createMediaStreamSource(stream);
                    processor = audioContext.createScriptProcessor(4096, 1, 1);
                    
                    audioData = [];
                    processor.onaudioprocess = (e) => {
                        const channelData = e.inputBuffer.getChannelData(0);
                        audioData.push(new Float32Array(channelData));
                    };

                    input.connect(processor);
                    processor.connect(audioContext.destination);
                    
                    isRecording = true;
                    micBtn.classList.add('recording');
                    micStatus.textContent = "DİNLENİYOR... (Durdurmak için tıkla)";
                } catch (err) {
                    console.error("Mic error:", err);
                    alert("Mikrofon erişimi engellendi veya hata oluştu.");
                }
            } else {
                // Kaydı Bitir
                isRecording = false;
                micBtn.classList.remove('recording');
                micStatus.textContent = "SES İŞLENİYOR...";

                // Audio stop
                processor.disconnect();
                input.disconnect();
                audioContext.close();

                // Flatten and Encode to WAV
                const merged = flattenArray(audioData);
                const wavBlob = encodeWAV(merged, 16000);
                
                try {
                    const response = await fetch('/voice_command', {
                        method: 'POST',
                        body: wavBlob
                    });
                    const result = await response.json();
                    
                    // AI Yanıtını işle (Aksiyonları tetikle)
                    const processedAI = processAIResponse(result.ai_text);

                    // Chat geçmişine ekle
                    addChatMessage(result.user_text, 'user');
                    addChatMessage(processedAI, 'ai');

                    printTerminalLog(`[SES-KOMUT] Ben: ${result.user_text}`);
                    printTerminalLog(`[SES-YANIT] MARSPACE: ${processedAI}`, true);
                    
                    if (result.audio_url) {
                        new Audio(result.audio_url).play();
                    }
                    micStatus.textContent = "TAMAMLANDI.";
                    setTimeout(() => micStatus.textContent = "KOMUT BEKLENİYOR...", 3000);
                } catch (err) {
                    micStatus.textContent = "BAĞLANTI HATASI.";
                }
            }
        };
    }
});

function flattenArray(channelBuffer) {
    let result = new Float32Array(channelBuffer.reduce((acc, b) => acc + b.length, 0));
    let offset = 0;
    for (let buffer of channelBuffer) {
        result.set(buffer, offset);
        offset += buffer.length;
    }
    return result;
}

function encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
    };
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, samples.length * 2, true);
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([view], { type: 'audio/wav' });
}

// Helper for Updating Values with LEDs
function updateValue(id, val, unit = "", isCritical = null, isWarning = null) {
    const el = document.getElementById(id);
    if (!el || val === undefined) return;
    
    let displayVal = val;
    if (typeof val === 'number' && !id.includes('nodes')) {
        displayVal = val.toFixed(id.includes('freq') ? 2 : 1);
    }
    
    el.textContent = displayVal + unit;
    
    // Find associated LED (it is the next sibling of the container usually, or inside seeker)
    const container = el.closest('.value-row');
    const led = container ? container.querySelector('.status-led') : null;
    
    if (isCritical && isCritical(val)) {
        el.className = "widget-value critical blink";
        if (led) led.className = "status-led led-red led-blink";
    } else if (isWarning && isWarning(val)) {
        el.className = "widget-value warning";
        if (led) led.className = "status-led led-orange";
    } else {
        el.className = "widget-value ok";
        if (led) led.className = "status-led led-green";
    }
}

function updateTextAndLed(id, text, statusFn) {
    const el = document.getElementById(id);
    if (!el || !text) return;
    el.textContent = text;
    
    const container = el.closest('.value-row');
    const led = container ? container.querySelector('.status-led') : null;
    const status = statusFn(text);
    
    if (status === "critical") {
        el.className = "widget-value critical blink";
        if (led) led.className = "status-led led-red led-blink";
    } else if (status === "warning") {
        el.className = "widget-value warning";
        if (led) led.className = "status-led led-orange";
    } else if (status === "ok") {
        el.className = "widget-value ok";
        if (led) led.className = "status-led led-green";
    }
}

// -----------------------------------------------------
// FAZ KONTROL MANTIĞI & OTONOM LLM VERİ İŞLEME
// -----------------------------------------------------

function triggerSystemVoice(message) {
    if (!message) return;
    fetch(`/tts?text=${encodeURIComponent(message)}`)
        .then(res => res.json())
        .then(data => {
            if (data.audio_url) new Audio(data.audio_url).play();
        })
        .catch(err => console.error("TTS Error:", err));
}

let crisisInterval = null;

function triggerPhase(phaseNum, silent = false) {
    [btnPhase1, btnPhase2, btnPhase3, btnPhase4].forEach(btn => btn.classList.remove('active'));
    document.getElementById(`btn-phase-${phaseNum}`).classList.add('active');
    printLogicalSeparator(`FAZ ${phaseNum} TETİKLENDİ`);

    if (crisisInterval) {
        clearInterval(crisisInterval);
        crisisInterval = null;
    }

    switch (phaseNum) {
        case 1: executePhase1(silent); break;
        case 2: executePhase2(silent); break;
        case 3: executePhase3(silent); break;
        case 4: executePhase4(silent); break;
    }
}

function executePhase1(silent = false) {
    statusMain.textContent = "SARI ALARM"; statusMain.className = "widget-value warning blink";
    if (!silent) triggerSystemVoice("Güneş patlaması gözlemlendi. Şebeke alarm moduna geçiyor.");
    
    // 1. UZAY HAVASI PANELİ
    updateValue('val-wind', 700, " km/s", v => v > 1000, v => v > 600);
    updateValue('val-bz', -10, " nT", v => v < -20, v => v < 0);
    updateValue('val-kp', 6.0, "", v => v > 7, v => v > 4);
    updateTextAndLed('val-xray', "X10.5", v => "critical"); // YOLOv8 tespiti sonrası fırlar

    // 2. SCADA
    updateValue('val-gic-amp', 0.5, " A", v => v > 80, v => v > 20);
    updateValue('val-trafo', 55, " °C", v => v > 100, v => v > 80);
    updateValue('val-freq', 50.00, " Hz", v => v < 49.85, v => v < 49.95);
    updateTextAndLed('val-sst', "BEKLEMEDE", v => "ok");

    // 3. ULAŞIM
    updateTextAndLed('val-gps', "KONTROL EDİLİYOR", v => "warning");
    updateValue('val-ray-volt', 0, " V DC", v => v > 100, v => v > 50);
    updateTextAndLed('val-marmaray', "OPERASYONEL", v => "ok");

    // 4. HABERLEŞME
    updateTextAndLed('val-internet', "BAĞLI", v => "ok");
    updateTextAndLed('val-llm-mode', "İZLEME MODU (IDLE)", v => "ok");
    updateTextAndLed('val-aredn', "YEDEK BEKLEMEDE", v => "warning");

    setTimeout(() => printTerminalLog("SARI ALARM: YOLOv8 X-SINIFI CME TESPİT ETTİ. ÇARPIŞMA SÜRESİ: 72 SAAT. DÜŞÜK YÖRÜNGE UYDULARI GÜVENLİ MODA ALINIYOR...", true), 500);

    // Map & AREDN Logic
    setTimeout(() => {
        gpsNodes.forEach(node => { node.setStyle({ fillColor: '#00d2ff' }); }); 
    }, 1600);

    triggerLLMDataProcessing("Faz 1: Güneş CME patlaması. Kp: 6.0. GPS ve HF koptu. Askeri bir durum analizi ver (tek cümle).");
}

function executePhase2() {
    statusMain.textContent = "KIRMIZI ALARM"; statusMain.className = "widget-value critical fast-blink";
    
    // Faz 2 başlangıcı: Değerler hafif yükselmeye başlar ama asıl zıplamalar interval içinde olur
    updateTextAndLed('val-gps', "SİNYAL ZAYIF", v => "warning");
    
    setTimeout(() => printTerminalLog("KIRMIZI ALARM: L1 SENSÖRÜ AŞILDI. BULUT BAĞLANTISI KESİLİYOR. YEREL LLM TAM KONTROLDE. RAYLI SİSTEMLER TAHLİYE EDİLİYOR. VERİ MERKEZLERİ SOĞUK DEPO MODUNDA.", true), 500);

    setTimeout(() => { gridLines.forEach(line => line.setStyle({ color: '#444444' })); metroLines.forEach(line => line.setStyle({ color: '#ff9900' })); }, 2200);
    setTimeout(() => { metroLines.forEach(line => line.setStyle({ color: '#444444' })); criticalNodes.forEach(node => node.setStyle({ fillColor: '#ffcc00', color: '#cc9900' })); }, 4500);

    let winSpeed = 450;
    let bzTemp = 2.0;
    let gicTemp = 0.5;
    let freqTemp = 50.00;
    let rayVolt = 0;
    let tickCount = 0;

    crisisInterval = setInterval(() => {
        tickCount++;
        
        // Güneş rüzgarı saniyede artış
        if (winSpeed < 1850) winSpeed += Math.floor(Math.random() * 40) + 40;
        updateValue('val-wind', winSpeed, " km/s", v => v > 1000, v => v > 600);
        
        // Bz aniden düşer
        if (tickCount === 3) {
            updateTextAndLed('val-xray', "X8.5", v => "critical"); // X-Ray fırlar
            updateValue('val-kp', 8.5, "", v => true); 
        }
        if (tickCount >= 3 && bzTemp > -45) bzTemp -= Math.random() * 8;
        updateValue('val-bz', bzTemp, " nT", v => v < -20, v => v < 0);
        
        // GIC Yükselir
        if (tickCount > 4 && gicTemp < 135) gicTemp += Math.random() * 20;
        updateValue('val-gic-amp', gicTemp, " A", v => v > 80, v => v > 20);

        // Ray Gerilimi
        if (tickCount > 5 && rayVolt < 120) rayVolt += 15;
        updateValue('val-ray-volt', rayVolt, " V DC", v => v > 100, v => v > 50);

        // Şebeke Frekansı
        if (tickCount > 7 && freqTemp > 49.82) freqTemp -= 0.02;
        updateValue('val-freq', freqTemp, " Hz", v => v < 49.85, v => v < 49.95);

        if (tickCount === 9) {
            // SST Devreye Girer (Parlak Yeşil)
            const sstEl = document.getElementById('val-sst');
            sstEl.textContent = "DEVREDE - ADA MODU AKTİF";
            sstEl.className = "widget-value ok";
            sstEl.style.textShadow = "0 0 10px #00ff66";
            sstEl.style.color = "#00ff66";
            document.getElementById('led-sst').className = "status-led led-green led-blink";

            updateValue('val-trafo', 115, " °C", v => true); // Trafo Kritik
            updateTextAndLed('val-marmaray', "GÜVENLİ DURUŞ / TAHLİYE EDİLDİ", v => "critical");
        }

    }, 1000);

    triggerLLMDataProcessing("Faz 2: Plazma bulutu L1'i geçti. Kp 8.5+. Marmaray tahliye ediliyor. Önleyici elektrik kesintisi başlatıldı.");
}

function executePhase3() {
    statusMain.textContent = "EVAKUATION/BLACKOUT"; statusMain.className = "widget-value critical fast-blink";
    updateValue('val-wind', 1850, " km/s", v => true);
    updateValue('val-kp', 9.5, "", v => true);
    updateValue('val-bz', -50, " nT", v => true);
    updateTextAndLed('val-xray', "X10.0", v => "critical");
    
    updateValue('val-gic-amp', 150.0, " A", v => true);
    updateValue('val-trafo', 135, " °C", v => true);
    updateValue('val-freq', 49.72, " Hz", v => true);
    updateTextAndLed('val-sst', "DEVREDE (İZOLE)", v => "ok");

    updateTextAndLed('val-gps', "SİNYAL KAYBI - ATOMİK SAAT HOLDOVER AKTİF", v => "critical");
    updateValue('val-ray-volt', 120, " V DC", v => true);
    updateTextAndLed('val-marmaray', "TAHLİYE EDİLDİ", v => "critical");

    updateTextAndLed('val-internet', "BAĞLANTI KOPTU - İZOLE EDİLDİ", v => "critical");
    
    const llmModeEl = document.getElementById('val-llm-mode');
    llmModeEl.textContent = "TAM KONTROL - AKTİF";
    llmModeEl.className = "widget-value";
    llmModeEl.style.color = "#00d2ff"; // Neon Mavi
    llmModeEl.style.textShadow = "0 0 10px #00d2ff";
    document.getElementById('led-llm-mode').className = "status-led led-blue led-blink";
    
    const arednEl = document.getElementById('val-aredn');
    arednEl.textContent = "BİRİNCİL AĞ - 142 NODE AKTİF";
    arednEl.className = "widget-value ok";
    arednEl.style.color = "#00ff66"; // Neon Yeşil
    arednEl.style.textShadow = "0 0 10px #00ff66";
    document.getElementById('led-aredn').className = "status-led led-green led-blink";

    setTimeout(() => printTerminalLog("ÇARPIŞMA DOĞRULANDI! GIC KRİTİK SEVİYEDE. SST TRİSTÖRLERİ AKTİF. ŞEBEKE İZOLE EDİLDİ. İNTERNET ÇÖKTÜ. AREDN MESH AĞI BİRİNCİL İLETİŞİM OLARAK DEVREDE.", true), 600);

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
    }, 2700);

    triggerLLMDataProcessing("Faz 3: T+0 Çarpışma anı. GIC akımları maksimum. AREDN mesh aktif. Komuta özet raporunu ver.");
}

function executePhase4() {
    statusMain.textContent = "RECOVERY MODU"; statusMain.className = "widget-value ok";
    
    updateValue('val-wind', 400, " km/s", v => v > 1000, v => v > 600);
    updateValue('val-kp', 3.0, "", v => true);
    updateValue('val-bz', 2.0, " nT", v => v < -20, v => v < 0);
    updateTextAndLed('val-xray', "A1.2", v => "ok");
    
    updateValue('val-gic-amp', 0.5, " A", v => false, v => false);
    updateValue('val-trafo', 55, " °C", v => false, v => false);
    updateValue('val-freq', 50.00, " Hz", v => false, v => false);
    
    const sstEl = document.getElementById('val-sst');
    sstEl.textContent = "BEKLEMEDE";
    sstEl.style.color = "";
    sstEl.style.textShadow = "";
    updateTextAndLed('val-sst', "BEKLEMEDE", v => "ok");

    updateTextAndLed('val-gps', "KİLİTLİ (3D FIX)", v => "ok");
    updateValue('val-ray-volt', 0, " V DC", v => false, v => false);
    updateTextAndLed('val-marmaray', "OPERASYONEL", v => "ok");

    updateTextAndLed('val-internet', "BAĞLI", v => "ok");
    
    const llmModeEl = document.getElementById('val-llm-mode');
    llmModeEl.textContent = "İZLEME MODU (IDLE)";
    llmModeEl.style.color = "";
    llmModeEl.style.textShadow = "";
    updateTextAndLed('val-llm-mode', "İZLEME MODU (IDLE)", v => "ok");
    
    const arednEl = document.getElementById('val-aredn');
    arednEl.textContent = "YEDEK BEKLEMEDE";
    arednEl.style.color = "";
    arednEl.style.textShadow = "";
    updateTextAndLed('val-aredn', "YEDEK BEKLEMEDE", v => "warning");

    setTimeout(() => printTerminalLog("UZAY HAVASI STABİL. İZOLASYON KALDIRILIYOR. ROV FİLOSU FİBER OPTİK HATLARDA DEVREYE ALINDI. BLACK START (ŞEBEKE KURTARMA) PROTOKOLÜ BAŞLATILIYOR...", true), 1500);

    // Kademeli başlatma (Yavaş aktivasyon simülasyonu)
    setTimeout(() => { 
        printTerminalLog("ADIM 1: KRİTİK ALTYAPI (ŞEHİR HASTANELERİ VE ASKERİ ÜSLER) ANA ŞEBEKEYE BAĞLANDI.");
        criticalNodes.forEach(node => node.setStyle({ fillColor: '#00ff66', color: '#000' })); 
    }, 2500);
    
    setTimeout(() => { 
        printTerminalLog("ADIM 2: ULUSAL ENERJİ ŞEBEKESİ (TEİAŞ) YENİDEN ENERJİLENDİRİLİYOR.");
        gridLines.forEach(line => line.setStyle({ color: '#00ff66' })); 
    }, 5500);

    setTimeout(() => { 
        printTerminalLog("ADIM 3: RAYLI SİSTEMLER VE ULAŞIM AĞLARI ENERJİYİ GERİ ALDI.");
        metroLines.forEach(line => line.setStyle({ color: '#00ff66' })); 
    }, 8500);

    setTimeout(() => { 
        printTerminalLog("ADIM 4: İLETİŞİM ALTYAPISI NORMALE DÖNDÜ. GPS VE HABERLEŞME AKTİF.");
        gpsNodes.forEach(node => node.setStyle({ fillColor: '#00d2ff' })); 
        document.getElementById('val-gps').textContent = "KİLİTLİ (3D FIX)";
        arednArcs.forEach(line => map.removeLayer(line)); arednArcs = []; 
    }, 11500);

    setTimeout(() => {
        const rovCoords = [[40.85, 28.9], [40.9, 29.05], [40.8, 28.7]];
        const rovIcon = L.divIcon({ className: 'rov-icon', html: '🤖 ROV', iconSize: [40, 20] });
        rovCoords.forEach(pos => { let marker = L.marker(pos, { icon: rovIcon }).addTo(map); rovMarkers.push(marker); });
    }, 3000);

    triggerLLMDataProcessing("Faz 4: Tehlike geçti. Şebeke kademeli kaldırılıyor. Fiber tamiri sürüyor. Kapanış onayını ver (tek cümle).");
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
            const processed = processAIResponse(response);
            loadDiv.textContent = processed;
        } else {
            loadDiv.textContent = "BAĞLANTI HATASI: LM Studio yanıt vermiyor veya model yüklenmedi.";
            loadDiv.classList.add('error');
        }
    }
}

function processAIResponse(rawText) {
    if (!rawText) return "";
    let finalMsg = rawText;

    // AI Aksiyon (Function Calling) Yakalayıcı - Silent=true (YZ zaten sesli yanıt veriyor)
    if (finalMsg.includes("[ACTION: PHASE1]")) { triggerPhase(1, true); finalMsg = finalMsg.replace("[ACTION: PHASE1]", "").trim(); }
    else if (finalMsg.includes("[ACTION: PHASE2]")) { triggerPhase(2, true); finalMsg = finalMsg.replace("[ACTION: PHASE2]", "").trim(); }
    else if (finalMsg.includes("[ACTION: PHASE3]")) { triggerPhase(3, true); finalMsg = finalMsg.replace("[ACTION: PHASE3]", "").trim(); }
    else if (finalMsg.includes("[ACTION: PHASE4]")) { triggerPhase(4, true); finalMsg = finalMsg.replace("[ACTION: PHASE4]", "").trim(); }

    return finalMsg;
}

async function fetchFromLMStudio(prompt, systemPrompt) {
    try {
        const response = await fetch(LM_STUDIO_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messages: [
                    { role: "system", content: systemPrompt },
                    { role: "user", content: prompt }
                ],
                temperature: 0.7,
                max_tokens: 150
            })
        });

        if (!response.ok) throw new Error(`API Hatası: ${response.status}`);
        const data = await response.json();

        // Standard OpenAI Response Parsing
        if (data.choices && data.choices.length > 0) {
            return data.choices[0].message.content;
        }

        // Fallback for custom LM Studio outputs
        if (data.reply) return data.reply;
        if (data.response) return data.response;
        if (data.message && typeof data.message === 'string') return data.message;
        if (data.message && data.message.content) return data.message.content;
        if (data.content) return data.content;

        return "RAW_JSON_DUMP: " + JSON.stringify(data);
    } catch (err) {
        console.error("LM Studio Bağlantı Hatası:", err);
        return null;
    }
}

function addChatMessage(message, sender) {
    const div = document.createElement('div');
    const id = 'msg-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
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
