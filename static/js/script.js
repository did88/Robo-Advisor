document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatHistory = document.getElementById('chatHistory');
    const infoTitle = document.getElementById('infoTitle');
    const metricContainer = document.getElementById('metricContainer');

    function interpret(metric, value) {
        let val = parseFloat(String(value).replace(/[^0-9.-]/g, ''));
        let comment = '-';
        let status = 'neutral';
        switch (metric) {
            case 'per':
                if (val <= 15) { status = 'good'; comment = '저평가'; }
                else if (val <= 25) { status = 'neutral'; comment = '보통'; }
                else { status = 'bad'; comment = '고평가'; }
                break;
            case 'roe':
                if (val >= 15) { status = 'good'; comment = '우수'; }
                else if (val >= 10) { status = 'neutral'; comment = '양호'; }
                else { status = 'bad'; comment = '낮음'; }
                break;
            case 'debt_ratio':
                if (val < 50) { status = 'good'; comment = '건전'; }
                else if (val < 100) { status = 'neutral'; comment = '주의'; }
                else { status = 'bad'; comment = '위험'; }
                break;
            case 'risk_level':
                if (value === '낮음') { status = 'good'; comment = '안정적'; }
                else if (value === '중간') { status = 'neutral'; comment = '보통'; }
                else { status = 'bad'; comment = '높음'; }
                break;
            case 'sales':
            case 'market_cap':
                if (!isNaN(val) && val >= 100) { status = 'good'; comment = '대형'; }
                else if (!isNaN(val) && val >= 50) { status = 'neutral'; comment = '중간'; }
                else { status = 'bad'; comment = '소형'; }
                break;
        }
        return { comment, status };
    }

    function updateMetrics(info) {
        metricContainer.innerHTML = '';
        if (!info || !info.name) {
            infoTitle.textContent = '종목을 선택하면 지표가 표시됩니다.';
            return;
        }
        infoTitle.textContent = `${info.name} (${info.sector || ''})`;
        const metrics = [
            { key: 'per', label: 'PER', icon: '📈' },
            { key: 'roe', label: 'ROE', icon: '💸' },
            { key: 'debt_ratio', label: '부채비율', icon: '🏦' },
            { key: 'sales', label: '매출액', icon: '💰' },
            { key: 'market_cap', label: '시가총액', icon: '🏢' },
            { key: 'risk_level', label: '위험도', icon: '⚠️' },
        ];
        metrics.forEach(m => {
            const value = info[m.key];
            if (value == null) return;
            const { comment, status } = interpret(m.key, value);
            const card = document.createElement('div');
            card.className = `metric-card ${status}`;
            card.innerHTML = `<div class="metric-title">${m.icon} ${m.label}</div>` +
                             `<div class="metric-value">${value}</div>` +
                             `<div class="metric-comment">${comment}</div>`;
            metricContainer.appendChild(card);
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
            updateMetrics(data);
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
