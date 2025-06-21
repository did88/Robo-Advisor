document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatHistory = document.getElementById('chatHistory');
    const chartTitle = document.getElementById('chartTitle');
    let chart;

    function updateChart(info) {
        if (!info || !info.stock_name) {
            chartTitle.textContent = '해당 종목의 재무 지표를 찾을 수 없습니다';
            if (chart) { chart.destroy(); chart = null; }
            return;
        }
        chartTitle.textContent = info.stock_name + ' 주요 지표';
        const ctx = document.getElementById('stockChart').getContext('2d');
        const per = parseFloat(info.per);
        const roe = parseFloat(String(info.roe).replace('%', ''));
        const debt = parseFloat(String(info.debt_ratio).replace('%', ''));
        const values = [per, roe, debt];
        const colors = [
            per > 20 ? '#e74c3c' : '#4a76a8',
            roe >= 15 ? '#2ecc71' : '#f1c40f',
            debt > 50 ? '#e74c3c' : '#2ecc71'
        ];
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['PER', 'ROE', '부채비율'],
                datasets: [{
                    data: values,
                    backgroundColor: colors
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });
    }

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
            updateChart(data);
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
