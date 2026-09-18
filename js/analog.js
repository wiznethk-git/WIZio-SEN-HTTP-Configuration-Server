const MAX_AIN = 2;

const MAX_AI_VOLT = 10; // V
const MAX_AI_CURR = 20; // mA


function onRecvAnalogIn(data){
	for (const [key, item] of Object.entries(data)) {
		// Paylod : {'AI0':{'value': x, 'mode': y}, ...}
		const idx = key.at(-1);
		const select = document.getElementById(`ai-mode-${idx}`);
		const options = select.children;
		const progress = document.getElementById(`ai-progress-${idx}`);
		const value = document.getElementById(`ai-value-${idx}`);

		const minValue = document.getElementById(`ai-min-${idx}`);
		const midValue = document.getElementById(`ai-mid-${idx}`);
		const maxValue = document.getElementById(`ai-max-${idx}`);

		if (item.mode == 0){ 	// Voltage Mode
			minValue.textContent = '0V';
			midValue.textContent = '5V';
			maxValue.textContent = '10V';

			const measuredVoltage = Math.min(MAX_AI_VOLT,parseFloat(item.value).toFixed(2));
			value.textContent = measuredVoltage + 'V';
			progress.style.width = measuredVoltage / 10 * 100 + '%';
			options[0].selected = true;
			options[1].selected = false;


		} else {
			minValue.textContent = '0mA';
			midValue.textContent = '10mA';
			maxValue.textContent = '20mA';

			const measuredCurrent = Math.min(MAX_AI_CURR,parseFloat(item.value).toFixed(2));
			value.textContent = measuredCurrent + 'mA';	
			progress.style.width = measuredCurrent / 20 * 100 + '%';
			options[0].selected = false;
			options[1].selected = true;

		}

	}

}


// Add onchange to select option
document.addEventListener('DOMContentLoaded', ()=>{
	for (let i = 0; i < MAX_AIN; i++){
		const select = document.getElementById(`ai-mode-${i}`);
		select.addEventListener('change', ()=>{
			const slider_value = document.getElementById(`ai-value-${i}`);
			const slider_min = document.getElementById(`ai-min-${i}`);
			const slider_mid = document.getElementById(`ai-mid-${i}`);
			const slider_max = document.getElementById(`ai-max-${i}`);

			if (select.value == 'voltage'){
				slider_value.textContent = '0.00 V';
				slider_min.textContent = '0V';
				slider_mid.textContent = '5V';
				slider_max.textContent = '10V';
			}
			else {
				slider_value.textContent = '0.00 mA';
				slider_min.textContent = '0mA';
				slider_mid.textContent = '10mA';
				slider_max.textContent = '20mA';

			}



		})
	}
})



// Fetch state
document.addEventListener('DOMContentLoaded', () => {
	let err_count = 0;
	const intervalId = setInterval(() => {
		fetch('/analog_io/state')
			.then(response => {
				if (!response.ok){
					throw new Error('HTTP error. Status: ', response.status);
				}
				return response.json()
			})
			.then(data => {
				onRecvAnalogIn(data);
			})
			.catch(error => {
				err_count++;
				if (err_count == 5){
					clearInterval(intervalId);
					console.log('Stopped.');
				}
				console.log(error);
			});		
	}, 1000);
})

//Fetch state, save ram, dont use websocket
// document.addEventListener('DOMContentLoaded' , () => {
// 	const ip = window.location.hostname;
// 	const wsPort = 8080;
// 	const socket = new WebSocket(`ws://${ip}:${wsPort}`);

// 	// On connect
// 	socket.addEventListener('open', ()=> {
// 		console.log("Connected to ws. Wait for message.")
// 	})

// 	// On messsage
// 	socket.addEventListener('message', (event) => {
// 		const payload = JSON.parse(event.data);
// 		const data = payload.ain;
// 		onRecvAnalogIn(data);
// 	})
// })