// Constants
const G = 9.81;
const RHO_WATER = 1025; // kg/m^3 (Sea water)
const RHO_BONITO = 1050; // kg/m^3 (Bonito fish density)
const DRUM_RADIUS = 0.25; // m
const TRANSMISSION_EFFICIENCY = 0.85;

// Motor Database
const ENGINES = {
    yanmar_3: { name: "Yanmar 3TNV88", power: 18000 }, // 18 kW
    caterpillar_15: { name: "Caterpillar C1.5", power: 15000 }, // 15 kW
    chongqing_mini: { name: "Chongqing Mini", power: 12000 } // 12 kW
};

// Canvas Setup
const canvas = document.getElementById('sim-canvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    const rect = canvas.parentNode.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// Simulation State
let time = 0;

// UI Elements
const inputMass = document.getElementById('catch-mass');
const valMass = document.getElementById('val-mass');
const inputSpeed = document.getElementById('winch-speed');
const valSpeed = document.getElementById('val-speed');
const inputSubmerged = document.getElementById('state-submerged');
const selectPulley = document.getElementById('pulley-system');
const inputWaveAmp = document.getElementById('wave-amp');
const valWaveAmp = document.getElementById('val-wave-amp');
const inputWavePeriod = document.getElementById('wave-period');
const valWavePeriod = document.getElementById('val-wave-period');
const selectEngine = document.getElementById('engine-select');

// DOM Metrics
const metricWeight = document.getElementById('metric-weight');
const metricBuoyancy = document.getElementById('metric-buoyancy');
const metricDrag = document.getElementById('metric-drag');
const metricTensionNet = document.getElementById('metric-tension-net');
const metricTensionWinch = document.getElementById('metric-tension-winch');
const metricTorque = document.getElementById('metric-torque');
const metricPower = document.getElementById('metric-power');
const metricPowerHp = document.getElementById('metric-power-hp');
const engineStatusBadge = document.getElementById('engine-status-badge');
const engineLoadBar = document.getElementById('engine-load-bar');
const engineLoadPct = document.getElementById('engine-load-pct');
const engineLimitText = document.getElementById('engine-limit');

// Math and Simulation Loop
function updateSimulation() {
    time += 0.016; // Approx 60 FPS

    // 1. Read UI inputs
    const mass = parseFloat(inputMass.value);
    const speed = parseFloat(inputSpeed.value);
    const isSubmerged = inputSubmerged.checked;
    const vm = parseInt(selectPulley.value);
    const waveAmp = parseFloat(inputWaveAmp.value);
    const wavePeriod = parseFloat(inputWavePeriod.value);
    const engineKey = selectEngine.value;

    valMass.innerText = mass;
    valSpeed.innerText = speed.toFixed(1);
    valWaveAmp.innerText = waveAmp.toFixed(1);
    valWavePeriod.innerText = wavePeriod.toFixed(1);

    // 2. Wave Dynamics
    // y = A * sin(omega * t)
    const omega = (2 * Math.PI) / wavePeriod;
    const yWave = waveAmp * Math.sin(omega * time);
    const vWave = waveAmp * omega * Math.cos(omega * time);
    const aWave = -waveAmp * omega * omega * Math.sin(omega * time);

    // 3. Physics Calculations (Purse Seiner Extraction)
    const weight = mass * G;
    
    // Volume of catch (Bonito)
    const volume = mass / RHO_BONITO;
    
    // Archimedes Buoyancy
    const buoyancy = isSubmerged ? (RHO_WATER * volume * G) : 0;

    // Projected area for drag (scales with catch size)
    const projectedArea = 0.5 * Math.pow(mass / 100, 2/3); 
    const cd = 1.2; // Drag coefficient of net mesh
    const relativeVelocity = speed + vWave;
    const drag = isSubmerged ? (0.5 * cd * RHO_WATER * projectedArea * relativeVelocity * Math.abs(relativeVelocity)) : 0;

    // Dynamic tension at net block: T - P + E - Fd = m * a
    // Since gravity and acceleration act vertical, and drag opposes motion:
    // T = P + Fd + m * aWave - E
    let tensionNet = weight + drag + (mass * aWave) - buoyancy;
    if (tensionNet < 0) tensionNet = 0; // Cables can't push

    // Winch Tension
    const tensionWinch = tensionNet / vm;

    // Torque on Drum
    const torque = tensionWinch * DRUM_RADIUS;

    // Required Power (kW)
    // P = (F * v) / efficiency
    const rawPower = (tensionNet * speed) / TRANSMISSION_EFFICIENCY; // Watts
    const powerKw = rawPower / 1000;
    const powerHp = powerKw * 1.34102;

    // 4. Update UI Metrics
    metricWeight.innerText = `${Math.round(weight)} N`;
    metricBuoyancy.innerText = `${Math.round(buoyancy)} N`;
    metricDrag.innerText = `${Math.round(Math.abs(drag))} N`;
    metricTensionNet.innerText = `${Math.round(tensionNet)} N`;
    metricTensionWinch.innerText = `${Math.round(tensionWinch)} N`;
    metricTorque.innerText = `${torque.toFixed(1)} N·m`;
    metricPower.innerText = `${powerKw.toFixed(3)} kW`;
    metricPowerHp.innerText = `${powerHp.toFixed(3)} HP`;

    // 5. Engine Match
    const engine = ENGINES[engineKey];
    const loadPct = (rawPower / engine.power) * 100;
    engineLimitText.innerText = `${(engine.power / 1000).toFixed(1)} kW`;
    engineLoadPct.innerText = `${Math.round(loadPct)}%`;
    
    let loadBarWidth = Math.min(loadPct, 100);
    engineLoadBar.style.width = `${loadBarWidth}%`;

    // Color and status badge based on load
    if (loadPct > 100) {
        engineStatusBadge.className = "status-badge state-overload";
        engineStatusBadge.innerText = "SOBRECARGA";
        engineLoadBar.style.backgroundColor = "#ef4444";
    } else if (loadPct > 80) {
        engineStatusBadge.className = "status-badge state-warning";
        engineStatusBadge.innerText = "ADVERTENCIA";
        engineLoadBar.style.backgroundColor = "#f59e0b";
    } else if (loadPct < 15) {
        engineStatusBadge.className = "status-badge state-warning";
        engineStatusBadge.innerText = "SUBUTILIZADO";
        engineLoadBar.style.backgroundColor = "#38bdf8";
    } else {
        engineStatusBadge.className = "status-badge state-ok";
        engineStatusBadge.innerText = "ÓPTIMO";
        engineLoadBar.style.backgroundColor = "#10b981";
    }

    // 6. Draw on Canvas
    drawCanvas(yWave, isSubmerged, tensionNet, weight, buoyancy, drag);

    requestAnimationFrame(updateSimulation);
}

function drawCanvas(yWave, isSubmerged, tension, weight, buoyancy, drag) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerY = canvas.height * 0.5;
    const waveOffset = yWave * 20; // scale meters to pixels

    // Draw Water Background (Ocean depth)
    ctx.fillStyle = '#08172c';
    ctx.fillRect(0, centerY + waveOffset, canvas.width, canvas.height);

    // Draw Wave Surface
    ctx.beginPath();
    ctx.moveTo(0, centerY + waveOffset);
    for (let x = 0; x < canvas.width; x += 10) {
        const xRad = (x / canvas.width) * 4 * Math.PI + time;
        const waveY = centerY + Math.sin(xRad) * 15 + waveOffset;
        ctx.lineTo(x, waveY);
    }
    ctx.lineTo(canvas.width, canvas.height);
    ctx.lineTo(0, canvas.height);
    ctx.closePath();
    ctx.fillStyle = 'rgba(14, 116, 144, 0.4)';
    ctx.fill();

    // Draw Vessel (Boat profile) heaving
    const boatX = canvas.width * 0.35;
    const boatY = centerY - 30 + waveOffset;
    
    // Hull
    ctx.fillStyle = '#cbd5e1';
    ctx.beginPath();
    ctx.moveTo(boatX - 80, boatY);
    ctx.lineTo(boatX + 100, boatY);
    ctx.lineTo(boatX + 130, boatY - 40);
    ctx.lineTo(boatX - 100, boatY - 40);
    ctx.closePath();
    ctx.fill();

    // Cabin
    ctx.fillStyle = '#475569';
    ctx.fillRect(boatX - 60, boatY - 70, 70, 30);
    ctx.fillStyle = '#38bdf8'; // Windows
    ctx.fillRect(boatX - 15, boatY - 65, 20, 15);
    ctx.fillRect(boatX - 45, boatY - 65, 20, 15);

    // Winch drum on deck
    ctx.fillStyle = '#1e293b';
    ctx.beginPath();
    ctx.arc(boatX - 80, boatY - 45, 12, 0, 2 * Math.PI);
    ctx.fill();

    // Boom (Pluma de izaje)
    ctx.strokeStyle = '#64748b';
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(boatX + 30, boatY - 40);
    ctx.lineTo(boatX + 120, boatY - 120); // Boom tip
    ctx.stroke();

    const boomTipX = boatX + 120;
    const boomTipY = boatY - 120;

    // Red (Catch net)
    const netX = boomTipX;
    // Net position: submerged deep or high in the air
    const netY = isSubmerged ? (centerY + waveOffset + 100) : (centerY + waveOffset - 20);

    // Cable from boom tip to net
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(boomTipX, boomTipY);
    ctx.lineTo(netX, netY);
    ctx.stroke();

    // Cable from boom tip back to winch
    ctx.beginPath();
    ctx.moveTo(boomTipX, boomTipY);
    ctx.lineTo(boatX - 80, boatY - 45);
    ctx.stroke();

    // Draw the Net (mesh bag filled with bonita fish)
    ctx.fillStyle = 'rgba(251, 146, 60, 0.6)';
    ctx.beginPath();
    ctx.arc(netX, netY, 35, 0, Math.PI, false);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = '#f97316';
    ctx.lineWidth = 3;
    ctx.stroke();

    // draw fish inside
    ctx.fillStyle = '#0ea5e9';
    for (let i = 0; i < 6; i++) {
        ctx.beginPath();
        ctx.ellipse(netX - 20 + (i * 8), netY + 15, 10, 5, Math.PI / 6 * (i%2?1:-1), 0, 2 * Math.PI);
        ctx.fill();
    }

    // DRAW DCL VECTORS (Arrows)
    const vectorScale = 0.08; // scale Newtons to pixels
    const originX = netX;
    const originY = netY + 10;

    // 1. Weight (Red, Down)
    drawVector(originX, originY, 0, weight * vectorScale, '#f87171', 'P');

    // 2. Buoyancy (Green, Up)
    if (buoyancy > 0) {
        drawVector(originX, originY, 0, -buoyancy * vectorScale, '#34d399', 'E');
    }

    // 3. Drag (Orange, Up/Down depending on relative motion)
    if (drag !== 0) {
        drawVector(originX, originY, 0, drag * vectorScale, '#fb923c', 'Fd');
    }

    // 4. Tension (Blue, Up)
    drawVector(originX, originY, 0, -tension * vectorScale, '#38bdf8', 'T');
}

function drawVector(x, y, dx, dy, color, label) {
    if (Math.abs(dx) < 2 && Math.abs(dy) < 2) return;

    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 3;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + dx, y + dy);
    ctx.stroke();

    // Draw arrowhead
    const angle = Math.atan2(dy, dx);
    ctx.beginPath();
    ctx.moveTo(x + dx, y + dy);
    ctx.lineTo(x + dx - 10 * Math.cos(angle - Math.PI / 6), y + dy - 10 * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(x + dx - 10 * Math.cos(angle + Math.PI / 6), y + dy - 10 * Math.sin(angle + Math.PI / 6));
    ctx.closePath();
    ctx.fill();

    // Text Label
    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 12px Outfit';
    ctx.fillText(label, x + dx + 8 * Math.cos(angle), y + dy + 8 * Math.sin(angle) + 4);
}

// Start simulation loop
requestAnimationFrame(updateSimulation);
