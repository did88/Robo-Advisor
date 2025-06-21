document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatHistory = document.getElementById('chatHistory');

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = 'message ' + sender;
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function showLoading() {
        const div = document.createElement('div');
        div.className = 'message bot loading';
        div.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return div;
    }

    function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        addMessage(text, 'user');
        input.value = '';
        const loader = showLoading();

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
        .then(res => res.json())
        .then(data => {
            loader.remove();
            addMessage(data.reply, 'bot');
        })
        .catch(() => {
            loader.remove();
            addMessage('오류가 발생했습니다.', 'bot');
        });
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
});
