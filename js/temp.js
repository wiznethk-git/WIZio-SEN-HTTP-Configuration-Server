 // Set thermocouple temp.（Channel 0-1，0-1300℃）
function setThermocouple(channel, value) {
    if (![0, 1].includes(channel) || typeof value !== 'number' || isNaN(value)) {
        console.error('Channel error. Channels can only be in 0 or 1.');
        return false;
    }

    // Bounds value between (0,1300)
    const clampedValue = Math.max(0, Math.min(1300, value));
    console.log(clampedValue);
    updateThermocoupleUI(channel, clampedValue);
    return true;
}

// Update Thermocouple UI
function updateThermocoupleUI(channel, value) {
    const displayValue = value.toFixed(1);
    const percentage = (value / 1300) * 100;

    document.getElementById(`thermocouple-value-k${channel + 1}`).textContent = `${displayValue} ℃`;
    document.getElementById(`thermocouple-progress-k${channel + 1}`).style.width = `${percentage}%`;
}


// Websocket
document.addEventListener('DOMContentLoaded', () => {
	const ip = window.location.hostname;
	const wsPort = 8080;
	const socket = new WebSocket(`ws://${ip}:${wsPort}`);

	// On connect
	socket.addEventListener('open', ()=> {
		console.log("Connected to ws. Wait for message.")
	})

	// On messsage
	socket.addEventListener('message', (event) => {
		const data = JSON.parse(event.data);
		const dType = data.type ?? null;
		const temp_array = data.temperature ?? null;		
		
		if (dType !== 5) return;
		if (!temp_array || temp_array.length === 0 || Array.isArray(temp_array) != 1) return;

		temp_array.forEach((temp, channel) => {
			setThermocouple(channel, temp);
		})
		
	})

	window.addEventListener('pagehide', (event) => {
        if (socket.readyState === WebSocket.OPEN) {
        	socket.send('disconnect');
    	}
	    socket.close();
    	console.log('WebSocket disconnected on page load.');
	});
})
