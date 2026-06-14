// Spustí se až po kompletním načtení stránky
document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("typeMeasurement");
    const block = document.getElementById("sessionBlock");
    const startBtn = document.getElementById("startBtn");
    const updateBtn = document.getElementById("updateBtn");

    // Získání deviceID z data-atributu tagu <body>
    const deviceID = document.body.getAttribute("data-device-id");

    // 1. Přepínání viditelnosti bloku se session
    function updateVisibility() {
        block.style.display = (select.value === "SESSION") ? "block" : "none";
    }
    select.addEventListener("change", updateVisibility);
    updateVisibility(); // Spuštění při inicializaci

    // 2. Odeslání konfigurace
    async function sendConfig() {
        const dataConfig = {
            deviceID: deviceID,
            typeMeasurement: select.value,
            measContinuity: document.getElementById("measContinuity").value,
            measIntervalHz: parseFloat(document.getElementById("hz").value),
            sessionName: select.value === "SESSION"
                ? document.getElementById("sessionText").value
                : null
        };

        try {
            const response = await fetch("/devices/config/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dataConfig)
            });
            if (response.ok) {
                alert("Config updated");
            } else {
                alert("Server error during update");
            }
        } catch (error) {
            console.error("Error:", error);
        }
    }
    updateBtn.addEventListener("click", sendConfig);

    // 3. Spuštění / Zastavení session
    async function startSession() {
        // Přečteme aktuální stav z tlačítka a otočíme ho
        let isRunning = startBtn.getAttribute("data-running") === "true";
        isRunning = !isRunning;

        const dataStart = {
            deviceID: deviceID,
            start: isRunning
        };

        try {
            const response = await fetch("/devices/config/start-session", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dataStart)
            });

            if (response.ok) {
                // Uložíme nový stav zpět do tlačítka a změníme text
                startBtn.setAttribute("data-running", isRunning ? "true" : "false");
                startBtn.textContent = isRunning ? "STOP" : "START";
            } else {
                alert("Server error during session toggle");
            }
        } catch (error) {
            console.error("Error:", error);
        }
    }
    if (startBtn) {
        startBtn.addEventListener("click", startSession);
    }
});