function addMessageToBox(msg, direction){
	const box = document.getElementById('serial-messages');
	const span = document.createElement('span');
	if (direction == "send") {
		span.style.color = "blue";
	} else {
		span.style.color = "green";
	}
	span.textContent = msg + '\n';
	box.appendChild(span);
	box.appendChild(document.createElement('br'));
}


// Button
function onClickSendBtn(element){
	const input = element.previousElementSibling;
	let data = {};
	addMessageToBox(input.value, 'send');
	data.message = input.value;
	fetch("/serial",{
		method:'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(data),
	})
		.then(response => {
			if (!response.ok){
				throw new Error("HTTP error! Status: " + response.status);
			}
		})
		.then(data => {
			addMessageToBox(data.message, "send");
		})
		.catch(error => {
			console.log(error)
		})
}



// Create websocket connection
document.addEventListener('DOMContentLoaded' , () => {
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
		const message = data.message ?? null;
		
		if (dType !== 3) return;
		if (!message|| message.length === 0) return;
		addMessageToBox(message, "recv");
	})

	window.addEventListener('pagehide', (event) => {
        if (socket.readyState === WebSocket.OPEN) {
        	socket.send('disconnect');
    	}
	    socket.close();
    	console.log('WebSocket disconnected on page load.');
	});
})



// Depricated
// Fetch data, polling
// let err_count = 0
// document.addEventListener('DOMContentLoaded', ()=> {
// 	let started = false;
// 	let intervalId = setInterval(() => {
// 		if (started) return;
// 		started = true;
// 		fetch("/serial/recv")
// 			.then(response => {
// 				if (!response.ok){
// 					throw new Error("HTTP error! Status: " + response.status);
// 				}
// 				return response.json()
// 			})
// 			.then(data => {
// 				if (data.message){
// 					console.log(data.message)
// 					addMessageToBox(data.message, "recv");
// 				}
// 			})
// 			.catch(error => {
// 				err_count++;
// 				console.log('Error conunted. Num: ' + err_count);
// 				if (err_count > 5){
// 					clearInterval(intervalId);
// 				}
// 				console.log(error)
// 			})
// 			.finally(()=> {
// 				started = false;
// 			})

// 	}, 1000)
// })