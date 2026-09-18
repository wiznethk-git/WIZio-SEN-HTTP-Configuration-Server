const MAX_WEIGHT = 10;

// 设置称重传感器值（0-3968对应0-10V，即0-10KG）
function set_weight(value) {
    if (typeof value !== 'number' || isNaN(value)) {
        console.error('称重传感器值必须是有效的数字');
        return false;
    }
    updateWeightDisplay(value);
    return true;
}


// 更新称重显示
function updateWeightDisplay(value) {
    // Fixed digits for weights
    const weightKg = value.toFixed(2)
    const weightG = (value * 1000).toFixed(0);

    const isKg = document.getElementById('weight-unit-kg').checked;
    const displayValue = isKg ? `${weightKg} kg` : `${weightG} g`;

    // 更新UI显示
    document.getElementById('weight-value').textContent = displayValue;

    // 更新进度条（0-100%）
    const percentage = (value/ MAX_WEIGHT) * 100;
    document.getElementById('weight-progress').style.width = `${percentage}%`;

    // 更新刻度显示
    document.getElementById('weight-min').textContent = isKg ? '0kg' : '0g';
    document.getElementById('weight-mid').textContent = isKg ? '5kg' : '5000g';
    document.getElementById('weight-max').textContent = isKg ? '10kg' : '10000g';
}

// On Press Icon
document.addEventListener('DOMContentLoaded',  () =>{        
    document.getElementById('weight-unit-kg').addEventListener('change', function () {
        updateWeightDisplay(0);
    });
    document.getElementById('weight-unit-g').addEventListener('change', function () {
        updateWeightDisplay(0);
    });
})

// Websocket
document.addEventListener('DOMContentLoaded' , () => {
	const ip = window.location.hostname;
	const wsPort = 8080;
	const socket = new WebSocket(`ws://${ip}:${wsPort}`);
	const decoder = new TextDecoder("utf-8");

	// On connect
	socket.addEventListener('open', ()=> {
		console.log("Connected to ws. Wait for message.");
	})

	// On messsage
	socket.addEventListener('message', (event) => {
		const data = JSON.parse(event.data);
		const dType = data.type ?? null;

		
		let resultString = null;
		if (dType !== 4) return;
		if ((!data.weight) || (data.weight == null)) return;
        set_weight(data.weight);
	})



	window.addEventListener('pagehide', (event) => {
        if (socket.readyState === WebSocket.OPEN) {
        	socket.send('disconnect');
    	}
	    socket.close();
    	console.log('WebSocket disconnected on page load.');
	});


})